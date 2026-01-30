import os
from transcriber_app.runner.orchestrator import Orchestrator
from transcriber_app.modules.audio_receiver import AudioReceiver
from transcriber_app.modules.output_formatter import OutputFormatter
from transcriber_app.modules.summarizer import Summarizer


class FakeTranscriber:
    def transcribe(self, path):
        return "fake text"


class FakeGemini:
    def analyze(self, text, mode="default"):
        return {"output": "fake summary"}


def test_run_audio_creates_output(tmp_path):
    # run_audio should return an outputs path ending with _default.md
    orchestrator = Orchestrator(AudioReceiver(), FakeTranscriber(), Summarizer(FakeGemini()), OutputFormatter())

    out = orchestrator.run_audio(audio_path="audios/ejemplo.mp3")
    assert out.endswith("_default.md")
    assert os.path.exists(out)

    # cleanup
    os.remove(out)


def test_run_text_creates_output(tmp_path):
    # create sample transcript file and run run_text
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    txt = transcripts_dir / "ejemplo.txt"
    txt.write_text("Contenido de prueba")

    orchestrator = Orchestrator(AudioReceiver(), FakeTranscriber(), Summarizer(FakeGemini()), OutputFormatter())
    out = orchestrator.run_text(text_path=str(txt))
    assert out.endswith("_default.md")
    assert os.path.exists(out)

    # cleanup
    os.remove(out)
