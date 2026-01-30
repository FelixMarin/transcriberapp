# transcriber_app/config.py
import os
from dotenv import load_dotenv
from transcriber_app.modules.logging.logging_config import setup_logging

# Logging
logger = setup_logging("transcribeapp")

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
USE_MODEL = os.getenv("USE_MODEL", "gemini-2.5-flash-lite")
LANGUAGE = os.getenv("LANGUAGE", "es")

logger.info("[CONFIG] Configuración cargada correctamente")