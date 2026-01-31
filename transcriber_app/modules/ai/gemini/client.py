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

    def __init__(self):
        # Instancia única del transcriptor Whisper
        self.transcriber = Transcriber(model_size="base")

    agents = {
        "tecnico": tecnico_agent,
        "ejecutivo": ejecutivo_agent,
        "refinamiento": refinamiento_agent,
        "bullet": bullet_agent,
        "default": default_agent,
    }

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio usando Whisper (local, optimizado para Jetson).
        """        
        return self.transcriber.transcribe(audio_path)

    def run_agent(self, mode: str, text: str):
        """
        Ejecuta el agente Gemini correspondiente al modo.
        """
        agent = self.agents.get(mode, default_agent)
        return agent.run(text)
