# transcriber_app/modules/ai/groq/transcriber.py

import os
import time
import tempfile
import subprocess
import requests
from typing import Tuple, Dict, Any
from transcriber_app.config import GROQ_API_KEY
from transcriber_app.modules.ai.base.transcriber_interface import TranscriberInterface


def ensure_wav(input_path: str) -> str:
    tmp = tempfile.mktemp(suffix=".wav")
    cmd = ["ffmpeg", "-y", "-nostdin", "-loglevel", "error",
           "-i", input_path, "-vn", "-acodec", "pcm_s16le",
           "-ar", "16000", "-ac", "1", tmp]
    subprocess.run(cmd, check=True)
    return tmp


class GroqTranscriber(TranscriberInterface):
    URL = "https://api.groq.com/openai/v1/audio/transcriptions"
    MODEL = "whisper-large-v3"

    def transcribe(self, audio_path: str) -> Tuple[str, Dict[str, Any]]:
        if not GROQ_API_KEY:
            raise RuntimeError("Falta GROQ_API_KEY")

        wav = ensure_wav(audio_path)
        start = time.time()

        with open(wav, "rb") as f:
            resp = requests.post(
                self.URL,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                data={"model": self.MODEL},
                files={"file": ("audio.wav", f, "audio/wav")},
                timeout=300
            )

        os.unlink(wav)
        resp.raise_for_status()

        text = resp.json().get("text", "").strip()
        elapsed = time.time() - start

        return text, {
            "engine": "groq-whisper",
            "model": self.MODEL,
            "transcription_time": elapsed,
        }
