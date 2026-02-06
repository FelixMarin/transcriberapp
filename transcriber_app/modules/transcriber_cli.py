from transcriber_app.modules.ai.groq.transcriber import GroqTranscriber


class Transcriber:
    """
    Wrapper para mantener compatibilidad con el CLI antiguo.
    Usa GroqTranscriber internamente.
    """

    def __init__(self):
        self.engine = GroqTranscriber()

    def transcribe(self, audio_path: str):
        text, _ = self.engine.transcribe(audio_path)
        return text
