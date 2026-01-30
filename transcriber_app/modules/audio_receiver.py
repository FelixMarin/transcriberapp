# transcriber_app/modules/audio_receiver.py
import os
from transcriber_app.modules.logging.logging_config import setup_logging

# Logging
logger = setup_logging("transcribeapp")

class AudioReceiver:
    def load(self, audio_path: str) -> dict:
        logger.info(f"[AUDIO RECEIVER] Cargando audio desde: {audio_path}")
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        return {
            "path": audio_path,
            "name": base_name
        }
