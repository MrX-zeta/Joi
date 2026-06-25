import httpx

TTS_SERVICE_URL = "http://localhost:8001/speak"


async def synthesize(text: str):
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(TTS_SERVICE_URL, json={"text": text})
        resp.raise_for_status()
        yield resp.content