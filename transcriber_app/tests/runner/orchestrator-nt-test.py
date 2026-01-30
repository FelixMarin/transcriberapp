from transcriber_app.modules.audio_receiver import AudioReceiver
from transcriber_app.modules.summarizer import Summarizer
from transcriber_app.modules.output_formatter import OutputFormatter
from transcriber_app.runner.orchestrator import Orchestrator
import os

# Create a dummy transcript file
os.makedirs('transcripts', exist_ok=True)
with open('transcripts/ejemplo.txt', 'w', encoding='utf-8') as f:
    f.write('Texto de ejemplo para pruebas.')

# Lightweight fakes


class FakeTranscriber:
    def transcribe(self, path):
        return "texto transcrito simulado"


class FakeGeminiClient:
    def analyze(self, text, mode="default"):
        return {"output": f"resumen simulado ({mode})"}


def test_orchestrator_run_text(tmp_path):
    orchestrator = Orchestrator(AudioReceiver(), FakeTranscriber(), Summarizer(FakeGeminiClient()), OutputFormatter())
    path = orchestrator.run_text(text_path="transcripts/ejemplo.txt")
    assert isinstance(path, str) and path.endswith(".md")
