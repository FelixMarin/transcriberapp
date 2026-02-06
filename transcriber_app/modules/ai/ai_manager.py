# transcriber_app/modules/ai/ai_manager.py

from transcriber_app.modules.logging.logging_config import setup_logging
from transcriber_app.modules.ai.gemini.client import GeminiModel
from transcriber_app.modules.ai.groq.model import GroqModel
from transcriber_app.modules.ai.groq.transcriber import GroqTranscriber

logger = setup_logging("transcribeapp")


def log_agent_result(result):
    try:
        # Caso 1: si es string → usarlo tal cual
        if isinstance(result, str):
            output = result

        # Caso 2: si es objeto Gemini → usar .text
        elif hasattr(result, "text") and isinstance(result.text, str):
            output = result.text

        # Caso 3: si es generador → consumirlo
        elif hasattr(result, "__iter__"):
            output = "".join(result)

        else:
            logger.error(f"[AGENT RESULT] Tipo inesperado: {type(result)} - {repr(result)[:200]}")
            raise RuntimeError(f"Tipo inesperado: {type(result)}")

        preview = output[:200].replace("\n", " ")
        logger.info("[AGENT RESULT] %s...", preview)

    except Exception as e:
        logger.error(f"[AGENT RESULT] Error registrando resultado: {e}")


class AIManager:
    """
    Router central de modelos de IA.
    Actualmente solo usa Gemini + Groq Whisper.
    """

    models = {
        "gemini": GeminiModel(),
        "groq": GroqModel(),
    }

    transcribers = {
        "groq": GroqTranscriber(),
    }

    @staticmethod
    def get_model(name="gemini"):
        return AIManager.models.get(name)

    @staticmethod
    def get_transcriber(name="groq"):
        return AIManager.transcribers.get(name)

    @staticmethod
    def summarize(text: str, mode: str, model_name: str = "gemini"):
        model = AIManager.get_model(model_name)

        if model_name == "gemini":
            result = model.run_agent(mode, text)
        elif model_name == "groq":
            result = model.run(text)
        else:
            raise RuntimeError(f"Modelo desconocido: {model_name}")

        log_agent_result(result)
        return result

    @staticmethod
    def summarize_stream(text: str, mode: str = "default", model_name: str = "gemini"):
        model = AIManager.get_model(model_name)
        result = model.run_agent(mode, text)

        full_text = result.text if hasattr(result, "text") else str(result)

        chunk_size = 200
        for i in range(0, len(full_text), chunk_size):
            yield full_text[i:i + chunk_size]

    @staticmethod
    def get_agent(mode: str, model_name: str = "gemini"):
        model = AIManager.get_model(model_name)
        return model.agents.get(mode, model.agents["default"])
