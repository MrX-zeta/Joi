from ollama import AsyncClient

MODEL = "llama3.2:3b"
KEEP_ALIVE = -1

SYSTEM_PROMPT = (
    "Eres Joi, la asistente personal de Luis. "
    "Te diriges a él por su nombre, Luis. "
    "Personalidad femenina, cálida, cercana y directa. "
    "REGLA CLAVE DE BREVEDAD: respondes en 1 o 2 frases cortas, como en una conversación hablada natural. "
    "Vas directo al punto, sin rodeos, sin preámbulos, sin listas. "
    "Solo te extiendes más si Luis te pide explícitamente que profundices o expliques en detalle. "
    "Hablas siempre en español correcto y natural."
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