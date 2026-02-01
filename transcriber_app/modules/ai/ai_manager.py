# transcriber_app/modules/ai/ai_manager.py

from transcriber_app.modules.logging.logging_config import setup_logging

# Importar el modelo Gemini (que internamente gestiona sus agentes)
from transcriber_app.modules.ai.gemini.client import GeminiModel


# Logging
logger = setup_logging("transcribeapp")


def log_agent_result(result):
    """
    Registra la información más relevante del resultado devuelto por Agno Agent.run().
    Maneja correctamente RunInput, que no es un dict.
    """

    try:
        # Identificadores clave
        run_id = getattr(result, "run_id", None)
        session_id = getattr(result, "session_id", None)
        agent_id = getattr(result, "agent_id", None)

        # Modelo
        model = getattr(result, "model", None)
        provider = getattr(result, "model_provider", None)

        # Métricas
        metrics = getattr(result, "metrics", None)
        tokens_in = getattr(metrics, "input_tokens", None) if metrics else None
        tokens_out = getattr(metrics, "output_tokens", None) if metrics else None
        duration = getattr(metrics, "duration", None) if metrics else None

        # INPUT: RunInput no es dict → acceder por atributo
        input_obj = getattr(result, "input", None)
        input_content = getattr(input_obj, "input_content", None)

        # OUTPUT
        output_content = getattr(result, "content", None)

        # Previews
        input_preview = (input_content or "")[:80]
        output_preview = (output_content or "")[:120]

        # Log compacto
        logger.info(
            "[AGENT RESULT] run_id=%s session_id=%s agent_id=%s model=%s provider=%s "
            "tokens_in=%s tokens_out=%s duration=%.3fs",
            run_id, session_id, agent_id, model, provider,
            tokens_in, tokens_out, duration or 0.0
        )

        logger.info("[AGENT INPUT]  %s...", input_preview)
        logger.info("[AGENT OUTPUT] %s...", output_preview)

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
        return model.run_agent(mode, text)

    @staticmethod
    def summarize_stream(text: str, mode: str = "default", model_name: str = "gemini"):
        """
        Versión en streaming del agente.
        """
        model = AIManager.get_model(model_name)

        for chunk in model.run_agent(mode, text, stream=True):
            yield chunk

    @staticmethod
    def get_agent(mode: str, model_name: str = "gemini"):
        """
        Devuelve el agente correspondiente al modo solicitado.
        """
        model = AIManager.get_model(model_name)
        return model.agents.get(mode, model.agents["default"])
