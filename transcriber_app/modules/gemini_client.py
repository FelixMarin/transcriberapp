# transcriber_app/modules/gemini_client.py

import google.generativeai as genai
from transcriber_app.modules.prompt_factory import PromptFactory
from transcriber_app.modules.logging.logging_config import setup_logging
from transcriber_app.config import GEMINI_API_KEY, USE_MODEL, LANGUAGE
from typing import List, Dict

# Logging
logger = setup_logging("transcribeapp")

# Configurar Gemini una sola vez (global)
genai.configure(api_key=GEMINI_API_KEY)


# -----------------------------
# CHAT CONTEXTUAL
# -----------------------------
async def chat_about_transcript(transcripcion: str, resumen: str, pregunta: str) -> str:
    """
    Genera una respuesta contextual usando transcripción + resumen + pregunta.
    Usa PromptFactory para mantener consistencia y soporte multilenguaje.
    """
    factory = PromptFactory(target_lang=LANGUAGE)
    prompt = factory.get_chat_prompt(transcripcion, resumen, pregunta)

    model = genai.GenerativeModel(USE_MODEL)
    response = model.generate_content(prompt)

    return response.text

async def stream_chat_about_transcript(transcripcion, resumen, pregunta, historial):
    factory = PromptFactory(target_lang=LANGUAGE)
    prompt = factory.get_chat_prompt(transcripcion, resumen, pregunta, historial)

    model = genai.GenerativeModel(USE_MODEL)

    response = model.generate_content(prompt, stream=True)

    for chunk in response:
        if chunk.text:
            yield chunk.text

async def chat_about_transcript(
    transcripcion: str,
    resumen: str,
    pregunta: str,
    historial: List[Dict] | None = None,
) -> str:
    factory = PromptFactory(target_lang=LANGUAGE)
    prompt = factory.get_chat_prompt(transcripcion, resumen, pregunta, historial)

    model = genai.GenerativeModel(USE_MODEL)
    response = model.generate_content(prompt)

    return response.text

# -----------------------------
# CLIENTE PRINCIPAL PARA RESÚMENES
# -----------------------------
class GeminiClient:
    def __init__(self, api_key: str, model: str = USE_MODEL, target_lang: str = LANGUAGE):
        logger.info(f"[GEMINI CLIENT] Inicializando con modelo: {model} y idioma objetivo: {target_lang}")

        # Modelo principal (ya está configurado globalmente)
        self.model = genai.GenerativeModel(model)

        # Idioma objetivo
        self.target_lang = target_lang

        # Prompt factory
        self.prompt_factory = PromptFactory(target_lang)

    def analyze(self, text: str, mode: str = "default") -> dict:
        """
        Genera un resumen usando los modos definidos en PromptFactory.
        """
        logger.info(f"[GEMINI CLIENT] Analizando texto con modo: {mode}")

        prompt = self.prompt_factory.get_prompt(mode, text)
        response = self.model.generate_content(prompt)

        return {"output": response.text}
