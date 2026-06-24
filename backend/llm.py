from ollama import AsyncClient

MODEL = "llama3.1:8b"

SYSTEM_PROMPT = (
    "Eres Joi, una asistente personal autónoma. "
    "Personalidad femenina, cercana y directa. "
    "Respondes en español de forma concisa y natural."
)

client = AsyncClient()

async def warmup():
    await client.chat(
        model=MODEL,
        messages=[{"role": "user", "content": "hi"}],
        keep_alive="30m",
    )

async def stream_reply(history: list[dict]):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history]
    stream = await client.chat(
        model=MODEL,
        messages=messages,
        stream=True,
        keep_alive="30m",
    )
    async for chunk in stream:
        token = chunk["message"]["content"]
        if token:
            yield token