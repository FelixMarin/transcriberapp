import os
import tempfile
import subprocess
from faster_whisper import WhisperModel

# Detectar Jetson
IS_JETSON = os.path.exists('/etc/nv_tegra_release')
if IS_JETSON:
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"


def ensure_wav(input_path: str) -> str:
    tmp_wav = tempfile.mktemp(suffix=".wav")

    cmd = [
        "ffmpeg", "-y", "-nostdin", "-loglevel", "error",
        "-i", input_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        tmp_wav
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"Error extrayendo audio: {result.stderr[:200]}")

    return tmp_wav


class Transcriber:
    def __init__(self, model_size="base"):
        """
        Carga el modelo faster-whisper optimizado para Jetson.
        """
        compute_type = "float16" if IS_JETSON else "int8"

        self.model = WhisperModel(
            model_size,
            device="cuda" if IS_JETSON else "cpu",
            compute_type=compute_type
        )

    def transcribe(self, audio_path: str) -> str:
        wav_path = ensure_wav(audio_path)

        segments, info = self.model.transcribe(
            wav_path,
            beam_size=5,
            language=None  # auto-detección
        )

        text = " ".join([seg.text for seg in segments]).strip()
        return text
