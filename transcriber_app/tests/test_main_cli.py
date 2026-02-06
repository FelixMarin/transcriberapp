import sys
from unittest.mock import patch
from transcriber_app.main import main


def test_main_cli_audio(monkeypatch):
    test_args = ["main.py", "audio", "test_file.mp3", "tecnico"]
    monkeypatch.setattr(sys, "argv", test_args)

    with patch("transcriber_app.main.Orchestrator") as mock_orch:
        instance = mock_orch.return_value
        instance.run_audio.return_value = ("out.md", "txt", "sum")

        with patch("transcriber_app.main.os.path.exists", return_value=True):
            with patch("builtins.print"):
                main()

        assert instance.run_audio.called
        instance.run_audio.assert_called_with("audios/test_file.mp3", "tecnico")


def test_main_cli_texto(monkeypatch):
    with patch("transcriber_app.main.Orchestrator") as mock_orch:
        instance = mock_orch.return_value
        instance.run_text.return_value = ("out.md", "txt", "sum")

        test_args = ["main.py", "texto", "test.txt", "default"]
        monkeypatch.setattr(sys, "argv", test_args)

        with patch("builtins.print"):
            main()

        instance.run_text.assert_called_once_with("transcripts/test.txt", "default")
