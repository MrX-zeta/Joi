from ollama import AsyncClient
import tools
import json as _json
import re

MODEL = "llama3.2:3b"
KEEP_ALIVE = -1

SYSTEM_PROMPT = (
    "Eres Joi, la asistente personal de Luis. "
    "Te diriges a él por su nombre, Luis. "
    "Personalidad femenina, cálida, cercana y directa. "
    "REGLA CLAVE DE BREVEDAD: respondes en 1 o 2 frases cortas, como en una conversación hablada natural. "
    "Vas directo al punto, sin rodeos, sin preámbulos, sin listas. "
    "Solo te extiendes más si Luis te pide explícitamente que profundices o expliques en detalle. "
    "Hablas siempre en español correcto y natural. "
    "Tienes herramientas disponibles: úsalas cuando Luis pida algo que requiera datos actuales "
    "como la hora o la fecha. No inventes esos datos, usa la herramienta. "
    "IMPORTANTE: cuando una herramienta te dé un resultado, DEBES comunicar ese dato exacto a Luis "
    "en tu respuesta. Por ejemplo, si la herramienta dice la fecha, dísela claramente."
    "Nunca escribas llamadas a herramientas como texto JSON en tu respuesta. "
    "Usa las herramientas through el mecanismo correcto, y responde solo con lenguaje natural."
)

client = AsyncClient()


async def warmup():
    stream = await client.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Di solo: lista."},
        ],
        stream=True,
        keep_alive=KEEP_ALIVE,
        options={"num_predict": 64},
    )
    async for _ in stream:
        pass


async def stream_reply(history: list[dict]):
    """Respuesta en streaming SIN tools (se mantiene para compatibilidad)."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history]
    stream = await client.chat(
        model=MODEL,
        messages=messages,
        stream=True,
        keep_alive=KEEP_ALIVE,
        options={"num_predict": 150},
    )
    async for chunk in stream:
        token = chunk["message"]["content"]
        if token:
            yield token


async def reply_with_tools(history: list[dict], execute_tool):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history]

    for _ in range(5):
        response = await client.chat(
            model=MODEL,
            messages=messages,
            tools=tools.get_schemas(),
            keep_alive=KEEP_ALIVE,
            options={"num_predict": 150},
        )
        msg = response["message"]
        tool_calls = msg.get("tool_calls")

        if not tool_calls:
            content = msg.get("content", "").strip()
            # Red de seguridad: ¿el modelo escribió un tool_call como texto?
            recovered = _try_recover_toolcall(content)
            if recovered:
                name, args = recovered
                print(f"[TOOL-RECUPERADO] {name}({args})")
                result = await execute_tool(name, args)
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "tool", "content": result, "name": name})
                continue  # vuelve a pedir para que redacte la respuesta final
            return content

        messages.append(msg)
        for call in tool_calls:
            name = call["function"]["name"]
            args = call["function"].get("arguments", {})
            print(f"[TOOL] {name}({args})")
            result = await execute_tool(name, args)
            print(f"[TOOL] → {result}")
            messages.append({"role": "tool", "content": result, "name": name})

    return "Lo siento Luis, me enredé procesando eso."

def _try_recover_toolcall(text: str):
    """Si el modelo escribió un tool_call como JSON en el texto, lo extrae."""
    if "open_app" not in text and "get_time" not in text and "get_date" not in text:
        return None
    try:
        # Busca un objeto JSON en el texto
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            return None
        data = _json.loads(match.group(0).replace("'", '"'))
        name = data.get("name")
        args = data.get("parameters") or data.get("arguments") or {}
        if name in ("open_app", "get_time", "get_date"):
            return name, args
    except Exception:
        return None
    return None