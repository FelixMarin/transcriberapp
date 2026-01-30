# transcriber_app/modules/transcriber.py
import os
import tempfile
import subprocess
import whisper

# Detectar Jetson
IS_JETSON = os.path.exists('/etc/nv_tegra_release')
if IS_JETSON:
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"


def ensure_wav(input_path: str) -> str:
    """
    Convierte cualquier formato de audio a WAV mono 16 kHz.
    """
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
        Carga el modelo openai-whisper.
        En Jetson usa GPU si torch lo permite.
        """
        device = "cuda" if IS_JETSON else "cpu"

        # Carga del modelo
        self.model = whisper.load_model(model_size, device=device)

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe un archivo de audio usando openai-whisper.
        """
        wav_path = ensure_wav(audio_path)

        result = self.model.transcribe(
            wav_path,
            language=None,   # autodetección
            fp16=IS_JETSON   # Jetson soporta FP16
        )

        text = result.get("text", "").strip()
        return text
