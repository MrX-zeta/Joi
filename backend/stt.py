import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Inyectar DLLs de cuBLAS/cuDNN al PATH ANTES de importar faster-whisper.
def _add_cuda_dlls() -> None:
    import importlib
    found = []
    for sub in ("cublas", "cudnn", "cuda_nvrtc"):
        try:
            mod = importlib.import_module(f"nvidia.{sub}")
        except ImportError:
            continue
        for root in list(getattr(mod, "__path__", [])):
            # DLLs pueden estar en \bin, \lib o sueltas en la raíz del subpaquete
            for folder in ("bin", "lib", ""):
                d = os.path.join(root, folder) if folder else root
                if os.path.isdir(d) and any(f.lower().endswith(".dll") for f in os.listdir(d)):
                    try:
                        os.add_dll_directory(d)
                        os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
                        found.append(d)
                    except Exception:
                        pass
    print(f"[stt] CUDA DLL dirs: {found or 'ninguno'}")

_add_cuda_dlls()

import numpy as np
from faster_whisper import WhisperModel

try:
    _model = WhisperModel("small", device="cuda", compute_type="float16")
    print("[stt] Whisper en GPU (cuda/float16)")
except Exception as e:
    print(f"[stt] CUDA no disponible ({e}); usando CPU")
    _model = WhisperModel("small", device="cpu", compute_type="int8")


def transcribe(audio: np.ndarray) -> str:
    segments, _ = _model.transcribe(
        audio,
        language="es",
        beam_size=1,
        vad_filter=False,
        initial_prompt="Conversación con la asistente Joi. Brian habla con Joi.",
    )
    return "".join(seg.text for seg in segments).strip()


def warmup_stt() -> None:
    silence = np.zeros(16000, dtype=np.float32)
    transcribe(silence)