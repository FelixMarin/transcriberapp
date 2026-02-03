# transcriber_app/modules/ai/ai_manager.py

from transcriber_app.modules.logging.logging_config import setup_logging
from transcriber_app.modules.ai.gemini.client import GeminiModel

# Logging
logger = setup_logging("transcribeapp")


def log_agent_result(result):
    """
    Registra información básica del resultado de un agente.
    solo registramos texto o atributos simples.
    """

    try:
        # Si el resultado es un objeto con .text
        if hasattr(result, "text"):
            output = result.text
        else:
            output = str(result)

        preview = output[:200].replace("\n", " ")

        logger.info("[AGENT RESULT] %s...", preview)

    except Exception as e:
        logger.error(f"[AGENT RESULT] Error registrando resultado: {e}")


class AIManager:
    """
    Router central de modelos de IA.
    Cada modelo implementa la interfaz AIModel y gestiona sus propios agentes.
    """

    models = {
        "gemini": GeminiModel(),
        # En el futuro:
        # "openai": OpenAIModel(),
        # "mistral": MistralModel(),
    }

    @staticmethod
    def get_model(model_name: str = "gemini"):
        """
        Devuelve el modelo solicitado. Por defecto, Gemini.
        """
        return AIManager.models.get(model_name, AIManager.models["gemini"])

    @staticmethod
    def summarize(text: str, mode: str, model_name: str = "gemini"):
        """
        Ejecuta un agente del modelo seleccionado.
        """
        model = AIManager.get_model(model_name)
        result = model.run_agent(mode, text)

        # Log básico
        log_agent_result(result)

        return result

    @staticmethod
    def summarize_stream(text: str, mode: str = "default", model_name: str = "gemini"):
        """
        Versión en streaming del agente.
        el streaming se simula dividiendo el texto.
        """
        model = AIManager.get_model(model_name)
        result = model.run_agent(mode, text)

        if hasattr(result, "text"):
            full_text = result.text
        else:
            full_text = str(result)

        # Emitir en chunks de 200 caracteres
        chunk_size = 200
        for i in range(0, len(full_text), chunk_size):
            yield full_text[i:i + chunk_size]

    @staticmethod
    def get_agent(mode: str, model_name: str = "gemini"):
        """
        Devuelve el agente correspondiente al modo solicitado.
        """
        model = AIManager.get_model(model_name)
        return model.agents.get(mode, model.agents["default"])
