import sys
import types
import pytest
import importlib


@pytest.fixture(autouse=True)
def mock_whisper(monkeypatch):
    # Mock the whisper module and its load_model function BEFORE importing transcriber
    whisper = types.SimpleNamespace()

    def fake_load_model(size, device=None):
        class Model:
            def transcribe(self, path, language=None, fp16=False):
                return {"text": f"simulated transcription for {path}"}
        return Model()

    whisper.load_model = fake_load_model
    monkeypatch.setitem(sys.modules, "whisper", whisper)

    # Import transcriber module now so it picks the mocked whisper
    trans_mod = importlib.import_module("transcriber_app.modules.transcriber")
    monkeypatch.setattr(trans_mod, "ensure_wav", lambda p: p)

    yield


def test_transcribe_returns_text():
    # Import inside the test to ensure fixture mocking happened first
    Transcriber = importlib.import_module("transcriber_app.modules.transcriber").Transcriber
    t = Transcriber()
    out = t.transcribe("audios/ejemplo.mp3")
    assert "simulated transcription" in out
