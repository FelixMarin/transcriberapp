# transcriber_app/modules/summarizer.py
from transcriber_app.modules.logging.logging_config import setup_logging

# Logging
logger = setup_logging("transcribeapp")

class Summarizer:
    def __init__(self, gemini_client):
        logger.info(f"[SUMMARIZER] Inicializando Summarizer con GeminiClient")
        self.client = gemini_client

    def summarize(self, text: str, mode="default"):
        logger.info(f"[SUMMARIZER] Resumiendo texto con modo: {mode}")
        return self.client.analyze(text, mode)
