import os
import tempfile
import subprocess
import whisper

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
    def __init__(self):
        self.model = whisper.load_model("base", device="cuda")
        self.model = self.model.half()

    def transcribe(self, audio_path: str) -> str:
        wav_path = ensure_wav(audio_path)

        result = self.model.transcribe(
            wav_path,
            language=None,          # auto-detección
            task="transcribe",
            verbose=False,
            fp16=True if IS_JETSON else False
        )

        return result["text"].strip()
