import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import numpy as np
from faster_whisper import WhisperModel

# Whisper en CPU: libera ~1GB de VRAM para Ollama + XTTS (los que necesitan GPU).
# STT en CPU ronda 1-2s, aceptable; la GPU queda para LLM y voz.
_model = WhisperModel("small", device="cpu", compute_type="int8")
print("[stt] Whisper en CPU (int8)")


def transcribe(audio: np.ndarray) -> str:
    segments, _ = _model.transcribe(
        audio,
        language="es",
        beam_size=1,
        vad_filter=False,
        initial_prompt="Conversación con la asistente Joi. Luis habla con Joi.",
    )
    return "".join(seg.text for seg in segments).strip()


def warmup_stt() -> None:
    silence = np.zeros(16000, dtype=np.float32)
    transcribe(silence)