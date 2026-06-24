import edge_tts

VOICE = "es-MX-DaliaNeural"


async def synthesize(text: str):
    """Genera audio MP3 en streaming (chunks de bytes)."""
    communicate = edge_tts.Communicate(text, VOICE)
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            yield chunk["data"]