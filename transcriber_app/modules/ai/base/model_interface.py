# transcriber_app/modules/ai/base/model_interface.py

class AIModel:
    """
    Interfaz base para cualquier modelo de IA integrado en TranscriberApp.
    Cada modelo (Gemini, OpenAI, Mistral...) debe implementar estos métodos.
    """

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe un archivo de audio y devuelve el texto resultante.
        Debe ser implementado por cada modelo.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.transcribe() no está implementado."
        )

    def run_agent(self, mode: str, text: str):
        """
        Ejecuta un agente específico (refinamiento, técnico, ejecutivo, etc.)
        sobre un texto ya transcrito.
        Debe devolver el resultado del agente.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.run_agent() no está implementado."
        )
