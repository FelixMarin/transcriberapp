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
        wav_path = ensure_wav(audio_path)

        result = self.model.transcribe(
            wav_path,
            language=None,
            fp16=IS_JETSON
        )

        text = result.get("text", "").strip()
        avg_logprob = result.get("avg_logprob", None)
        no_speech_prob = result.get("no_speech_prob", None)
        compression_ratio = result.get("compression_ratio", None)

        # --- VALIDACIONES DE CALIDAD ---
        if no_speech_prob and no_speech_prob > 0.6:
            raise ValueError("Grabación con muy poca voz detectada")

        if avg_logprob and avg_logprob < -1.0:
            raise ValueError("La calidad de audio es demasiado baja para transcribir")

        if compression_ratio and compression_ratio > 2.4:
            raise ValueError("El audio está demasiado comprimido o distorsionado")

        if len(text) < 10:
            raise ValueError("La transcripción es demasiado corta. Posible mala calidad")

        return text
