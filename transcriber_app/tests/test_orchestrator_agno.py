# transcriber_app/tests/test_orchestrator_agno.py
import os
from transcriber_app.runner.orchestrator import Orchestrator

# Crear archivo temporal
os.makedirs("transcripts", exist_ok=True)
with open("transcripts/test.txt", "w", encoding="utf-8") as f:
    f.write("contenido de prueba")


class DummyReceiver:
    def load(self, path):
        return {"name": "test", "path": path}


class DummyTranscriber:
    def transcribe(self, path):
        return "texto transcrito"


class DummyFormatter:
    def save_transcription(self, name, text):
        return True

    def save_output(self, name, summary, mode):
        return f"{name}_{mode}.md"


def test_orchestrator_runs_with_agno(monkeypatch):
    # Mock AIManager.summarize
    from transcriber_app.modules.ai.ai_manager import AIManager
    monkeypatch.setattr(AIManager, "summarize", lambda text, mode: "resumen generado")

    orch = Orchestrator(DummyReceiver(), DummyTranscriber(), DummyFormatter())
    out = orch.run_text("transcripts/test.txt", "tecnico")

    assert out == "test_tecnico.md"
