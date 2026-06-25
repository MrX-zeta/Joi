import os
os.environ["COQUI_TOS_AGREED"] = "1"

import io
import threading
from contextlib import asynccontextmanager

import numpy as np
import torch
import soundfile as sf
from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
from TTS.utils.manage import ModelManager

import voice_config as vc

_model = None
_gpt_latent = None
_speaker_emb = None
_lock = threading.Lock()  # serializa: XTTS nunca procesa dos a la vez


def _load_model():
    global _model, _gpt_latent, _speaker_emb
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[XTTS] Cargando modelo en {device}…")
    model_path = ModelManager().download_model("tts_models/multilingual/multi-dataset/xtts_v2")[0]
    config = XttsConfig()
    config.load_json(os.path.join(model_path, "config.json"))
    _model = Xtts.init_from_config(config)
    _model.load_checkpoint(config, checkpoint_dir=model_path, eval=True)
    _model.to(device)
    _gpt_latent, _speaker_emb = _model.speaker_manager.speakers[vc.SPEAKER].values()
    print(f"[XTTS] Voz '{vc.SPEAKER}' lista en {device}.")
    # Warmup: primera síntesis para calentar el camino de generación
    print("[XTTS] Calentando…")
    list(_model.inference_stream(
        "Hola.",
        language=vc.LANGUAGE,
        gpt_cond_latent=_gpt_latent,
        speaker_embedding=_speaker_emb,
        temperature=vc.PARAMS["temperature"],
        repetition_penalty=vc.PARAMS["repetition_penalty"],
        top_k=vc.PARAMS["top_k"],
        top_p=vc.PARAMS["top_p"],
        enable_text_splitting=vc.PARAMS["enable_text_splitting"],
    ))
    print("[XTTS] Listo para hablar.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_model()
    yield


app = FastAPI(title="Joi TTS (XTTS)", lifespan=lifespan)


class SpeakRequest(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"status": "ok", "speaker": vc.SPEAKER}


def _synthesize(text: str) -> bytes:
    with _lock:
        out = _model.inference(
            text,
            language=vc.LANGUAGE,
            gpt_cond_latent=_gpt_latent,
            speaker_embedding=_speaker_emb,
            **vc.PARAMS,
        )
    buf = io.BytesIO()
    sf.write(buf, out["wav"], 24000, format="WAV")
    buf.seek(0)
    return buf.read()


@app.post("/speak")
async def speak(req: SpeakRequest):
    audio = await run_in_threadpool(_synthesize, req.text)
    return Response(content=audio, media_type="audio/wav")

@app.post("/speak_stream")
async def speak_stream(req: SpeakRequest):
    def generate():
        with _lock:
            chunks = _model.inference_stream(
                req.text,
                language=vc.LANGUAGE,
                gpt_cond_latent=_gpt_latent,
                speaker_embedding=_speaker_emb,
                temperature=vc.PARAMS["temperature"],
                repetition_penalty=vc.PARAMS["repetition_penalty"],
                top_k=vc.PARAMS["top_k"],
                top_p=vc.PARAMS["top_p"],
                enable_text_splitting=vc.PARAMS["enable_text_splitting"],
            )
            for chunk in chunks:
                # chunk es un tensor float32; convertir a PCM16 bytes
                audio = chunk.cpu().numpy()
                pcm16 = (np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes()
                yield pcm16

    return StreamingResponse(generate(), media_type="application/octet-stream")