from .agents.tecnico_agent import tecnico_agent
from .agents.ejecutivo_agent import ejecutivo_agent
from .agents.refinamiento_agent import refinamiento_agent
from .agents.bullet_agent import bullet_agent
from .agents.default_agent import default_agent
from transcriber_app.modules.logging.logging_config import setup_logging

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

    agents = {
        "tecnico": tecnico_agent,
        "ejecutivo": ejecutivo_agent,
        "refinamiento": refinamiento_agent,
        "bullet": bullet_agent,
        "default": default_agent,
    }

    @staticmethod
    def get_agent(mode: str):
        return AIManager.agents.get(mode, default_agent)

    @staticmethod
    def summarize(text: str, mode: str):
        agent = AIManager.get_agent(mode)
        return agent.run(text)

    @staticmethod
    def summarize_stream(text, mode="default"):
        agent = AIManager.get_agent(mode)

        for chunk in agent._run_stream(text):
            yield chunk
