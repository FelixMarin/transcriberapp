from transcriber_app.modules.audio_receiver import AudioReceiver
from transcriber_app.modules.summarizer import Summarizer
from transcriber_app.modules.output_formatter import OutputFormatter
from transcriber_app.runner.orchestrator import Orchestrator

# Lightweight fakes to avoid heavy external deps
class FakeTranscriber:
    def transcribe(self, path):
        return "texto transcrito simulado"

class FakeGeminiClient:
    def analyze(self, text, mode="default"):
        return {"output": f"resumen simulado ({mode})"}

orchestrator = Orchestrator(AudioReceiver(), FakeTranscriber(), Summarizer(FakeGeminiClient()), OutputFormatter())

path = orchestrator.run_audio(audio_path="audios/ejemplo.mp3")
print(path)
