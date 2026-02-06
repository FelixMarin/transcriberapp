# transcriber_app/config.py
import os
from dotenv import load_dotenv
from transcriber_app.modules.logging.logging_config import setup_logging

# Logging
logger = setup_logging("transcribeapp")

load_dotenv()

AVAILABLE_MODES = ["default", "tecnico", "refinamiento", "ejecutivo", "bullet"]

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
USE_MODEL = os.getenv("USE_MODEL", "gemini-2.5-flash-lite")
LANGUAGE = os.getenv("LANGUAGE", "es")

AVAILABLE_MODES_DICT = {
    "default": "default",
    "tecnico": "tecnico",
    "refinamiento": "refinamiento",
    "ejecutivo": "ejecutivo",
    "bullet": "bullet",
}

logger.info("[CONFIG] Configuración cargada correctamente")
