import os
from dotenv import load_dotenv
from modules.logging.logging_config import setup_logging

# Logging
logger = setup_logging("transcribeapp")

load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

logger.info("[CONFIG] Configuración cargada correctamente")