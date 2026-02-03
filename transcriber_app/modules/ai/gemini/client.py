# transcriber_app/modules/ai/gemini/client.py

from transcriber_app.modules.ai.base.model_interface import AIModel
from transcriber_app.modules.transcriber import Transcriber

from .agents import (
    tecnico_agent,
    ejecutivo_agent,
    refinamiento_agent,
    bullet_agent,
    default_agent,
)


class GeminiModel(AIModel):
    """
    Modelo principal que gestiona:
    - Transcripción de audio (Whisper / faster-whisper)
    - Ejecución de agentes Gemini (sin AGNO)
    """

    def __init__(self):
        # Instancia única del transcriptor
        self.transcriber = Transcriber(model_size="base")

        # Diccionario de agentes (todos ya sin AGNO)
        self.agents = {
            "tecnico": tecnico_agent,
            "ejecutivo": ejecutivo_agent,
            "refinamiento": refinamiento_agent,
            "bullet": bullet_agent,
            "default": default_agent,
        }

    # -----------------------------
    #  TRANSCRIPCIÓN DE AUDIO
    # -----------------------------
    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio usando Whisper o faster-whisper según el entorno.
        """
        return self.transcriber.transcribe(audio_path)

    # -----------------------------
    #  EJECUCIÓN DE AGENTES
    # -----------------------------
    def run_agent(self, mode: str, text: str):
        """
        Ejecuta el agente Gemini correspondiente al modo.
        Cada agente es ahora una instancia de GeminiModel (sin AGNO),
        por lo que todos exponen un método .run(text).
        """
        agent = self.agents.get(mode, default_agent)

        if not hasattr(agent, "run"):
            raise RuntimeError(
                f"El agente '{mode}' no implementa el método .run(text)."
            )

        return agent.run(text)
