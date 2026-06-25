import json
import asyncio
import uuid
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from notifier import reminder_loop
import db
import conversation
import tools
from llm import reply_with_tools, stream_reply, warmup
from stt import transcribe, warmup_stt
from tts import synthesize

SENTENCE_ENDS = ".!?…\n"

# Confirmaciones pendientes: id -> asyncio.Future que se resuelve con True/False
_pending_confirms: dict[str, asyncio.Future] = {}

# Clientes WebSocket de voz conectados (para empujar recordatorios)
_voice_clients: set[WebSocket] = set()


async def _push_reminder(reminder_id: int, text: str):
    """Empuja un recordatorio vencido: notificación al frontend + voz de Joi."""
    frase = f"Luis, te recuerdo: {text}."
    for ws in list(_voice_clients):
        try:
            await ws.send_text(json.dumps({
                "type": "reminder_due",
                "text": text,
                "spoken": frase,
            }))
            await _speak(ws, frase)
        except Exception:
            _voice_clients.discard(ws)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    conversation.load_from_db()
    print("[Joi] Base de datos lista, memoria precargada.")
    print("[Joi] Precargando modelo en VRAM…")
    await warmup()
    print("[Joi] Modelo listo.")
    print("[Joi] Precargando Whisper…")
    await run_in_threadpool(warmup_stt)
    print("[Joi] Whisper listo.")
    task = asyncio.create_task(reminder_loop(_push_reminder))
    print("[Joi] Notificador de recordatorios activo.")
    yield
    task.cancel()


app = FastAPI(title="Joi Brain", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"status": "Joi online"}


def _confirm_label(name: str, args: dict) -> str:
    if name == "open_app":
        return f"¿Abrir {args.get('name', 'la aplicación')}?"
    if name == "open_url":
        return f"¿Abrir {args.get('site', 'el sitio')} en el navegador?"
    return f"¿Confirmas la acción {name}?"


# --- Canal de TEXTO (solo texto, sin voz) ---
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            user_text = await ws.receive_text()
            print(f"[WS] → {user_text!r}")
            conversation.append("user", user_text)
            assistant = ""
            try:
                async for token in stream_reply(conversation.messages()):
                    assistant += token
                    await ws.send_text(token)
                await ws.send_text("[[END]]")
                conversation.append("assistant", assistant)
            except Exception as e:
                print(f"[WS] ERROR: {e!r}")
                conversation.drop_last()
                await ws.send_text("[[END]]")
    except WebSocketDisconnect:
        print("Cliente de texto desconectado")


# --- Canal de VOZ (audio o texto -> LLM -> TTS opcional) ---
@app.websocket("/voice")
async def voice_endpoint(ws: WebSocket):
    await ws.accept()
    _voice_clients.add(ws)
    # Enviar historial del día para poblar el sidebar
    history = await run_in_threadpool(db.get_today)
    await ws.send_text(json.dumps({"type": "history", "messages": history}))
    speak = True

    # Ejecuta una tool, pidiendo confirmación al frontend si la tool lo requiere.
    async def execute_tool(name: str, args: dict) -> str:
        if tools.requires_confirmation(name):
            cid = str(uuid.uuid4())
            fut: asyncio.Future = asyncio.get_event_loop().create_future()
            _pending_confirms[cid] = fut
            await ws.send_text(json.dumps({
                "type": "confirm_request",
                "id": cid,
                "tool": name,
                "args": args,
                "label": _confirm_label(name, args),
            }))
            try:
                approved = await asyncio.wait_for(fut, timeout=60.0)
            except asyncio.TimeoutError:
                approved = False
            finally:
                _pending_confirms.pop(cid, None)
            if not approved:
                return f"Luis canceló la acción ({name})."
        return tools.execute(name, args)

    try:
        while True:
            msg = await ws.receive()
            if msg["type"] == "websocket.disconnect":
                break

            # Audio entrante -> STT
            if msg.get("bytes") is not None:
                import time
                t0 = time.perf_counter()
                audio = np.frombuffer(msg["bytes"], dtype=np.float32)
                text = await run_in_threadpool(transcribe, audio)
                print(f"[TIMING] STT: {time.perf_counter()-t0:.2f}s → {text!r}")
                if not text:
                    await ws.send_text(json.dumps({"type": "end"}))
                    continue
                await ws.send_text(json.dumps({"type": "transcript", "text": text}))
                asyncio.create_task(handle_turn(ws, text, speak, execute_tool))

            # Mensaje JSON: texto escrito, config del toggle o confirmación
            elif msg.get("text") is not None:
                data = json.loads(msg["text"])
                if data.get("type") == "config":
                    speak = bool(data.get("speak", True))
                    print(f"[VOICE] speak = {speak}")
                elif data.get("type") == "confirm_response":
                    cid = data.get("id")
                    approved = bool(data.get("approved"))
                    fut = _pending_confirms.get(cid)
                    if fut and not fut.done():
                        fut.set_result(approved)
                elif data.get("type") == "text":
                    content = data.get("content", "").strip()
                    if content:
                        asyncio.create_task(handle_turn(ws, content, speak, execute_tool))
    except WebSocketDisconnect:
        pass
    finally:
        _voice_clients.discard(ws)
    print("Cliente de voz desconectado")


async def handle_turn(ws: WebSocket, user_text: str, speak: bool, execute_tool) -> None:
    import time
    conversation.append("user", user_text)
    t_start = time.perf_counter()
    try:
        assistant = await reply_with_tools(conversation.messages(), execute_tool)
        print(f"[TIMING] Respuesta (con tools): {time.perf_counter()-t_start:.2f}s")

        await ws.send_text(json.dumps({"type": "token", "text": assistant}))

        if speak and len(assistant) > 1:
            await _speak(ws, assistant)

        conversation.append("assistant", assistant)
    except Exception as e:
        print(f"[VOICE] ERROR: {e!r}")
        conversation.drop_last()
    await ws.send_text(json.dumps({"type": "end"}))


async def _speak(ws: WebSocket, sentence: str) -> None:
    audio_bytes = b"".join([chunk async for chunk in synthesize(sentence)])
    if audio_bytes:
        await ws.send_text(json.dumps({"type": "audio_start"}))
        await ws.send_bytes(audio_bytes)
        await ws.send_text(json.dumps({"type": "audio_end"}))