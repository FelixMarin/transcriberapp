# transcriber_app/tests/test_orchestrator.py

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
    def save_transcription(self, name, text, enforce_save=True):
        return True

    def save_output(self, name, summary, mode, enforce_save=True):
        return f"{name}_{mode}.md"

    def save_metrics(self, name, summary, mode):
        return True


def test_orchestrator_runs(monkeypatch):
    # Mock AIManager.summarize para devolver un texto simple
    from transcriber_app.modules.ai.ai_manager import AIManager
    monkeypatch.setattr(AIManager, "summarize", lambda text, mode: "resumen generado")

    orch = Orchestrator(DummyReceiver(), DummyTranscriber(), DummyFormatter())
    out, text, summary = orch.run_text("transcripts/test.txt", "tecnico")

    assert out == "test_tecnico.md"
    assert text == "contenido de prueba"
    assert summary == "resumen generado"
