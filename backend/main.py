import json
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

import conversation
from llm import stream_reply, warmup
from stt import transcribe, warmup_stt
from tts import synthesize

SENTENCE_ENDS = ".!?…\n"


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Joi] Precargando modelo en VRAM…")
    await warmup()
    print("[Joi] Modelo listo.")
    print("[Joi] Precargando Whisper…")
    await run_in_threadpool(warmup_stt)
    print("[Joi] Whisper listo.")
    yield


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
    speak = True  # estado por conexión; el frontend lo sincroniza
    try:
        while True:
            msg = await ws.receive()
            if msg["type"] == "websocket.disconnect":
                break

            # Audio entrante -> STT
            if msg.get("bytes") is not None:
                audio = np.frombuffer(msg["bytes"], dtype=np.float32)
                print(f"[VOICE] audio: {audio.size} muestras")
                text = await run_in_threadpool(transcribe, audio)
                print(f"[VOICE] STT: {text!r}")
                if not text:
                    await ws.send_text(json.dumps({"type": "end"}))
                    continue
                await ws.send_text(json.dumps({"type": "transcript", "text": text}))
                await handle_turn(ws, text, speak)

            # Mensaje JSON: texto escrito o config del toggle
            elif msg.get("text") is not None:
                data = json.loads(msg["text"])
                if data.get("type") == "config":
                    speak = bool(data.get("speak", True))
                    print(f"[VOICE] speak = {speak}")
                elif data.get("type") == "text":
                    content = data.get("content", "").strip()
                    if content:
                        await handle_turn(ws, content, speak)
    except WebSocketDisconnect:
        pass
    print("Cliente de voz desconectado")


async def handle_turn(ws: WebSocket, user_text: str, speak: bool) -> None:
    conversation.append("user", user_text)
    assistant = ""
    buffer = ""
    try:
        async for token in stream_reply(conversation.messages()):
            assistant += token
            buffer += token
            await ws.send_text(json.dumps({"type": "token", "text": token}))
            if speak and any(p in token for p in SENTENCE_ENDS):
                sentence = buffer.strip()
                buffer = ""
                if len(sentence) > 1:
                    await _speak(ws, sentence)
        if speak:
            tail = buffer.strip()
            if len(tail) > 1:
                await _speak(ws, tail)
        conversation.append("assistant", assistant)
    except Exception as e:
        print(f"[VOICE] ERROR: {e!r}")
        conversation.drop_last()
    await ws.send_text(json.dumps({"type": "end"}))


async def _speak(ws: WebSocket, sentence: str) -> None:
    """Sintetiza una frase y la envía como un frame binario (mp3)."""
    audio_bytes = b"".join([chunk async for chunk in synthesize(sentence)])
    if audio_bytes:
        await ws.send_bytes(audio_bytes)