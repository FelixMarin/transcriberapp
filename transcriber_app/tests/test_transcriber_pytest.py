import pytest
from unittest.mock import MagicMock, patch
from transcriber_app.modules.transcriber_cli import Transcriber


@pytest.fixture
def mock_groq_api():
    with patch("transcriber_app.modules.ai.groq.transcriber.requests.post") as mock_post:
        # Mocking the response from Groq
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "simulated transcription from groq"}
        mock_post.return_value = mock_response

        # Mocking ffmpeg call and file operations
        with patch("transcriber_app.modules.ai.groq.transcriber.ensure_wav", return_value="fake.wav"):
            with patch("builtins.open", MagicMock()):
                with patch("transcriber_app.modules.ai.groq.transcriber.os.unlink", MagicMock()):
                    yield mock_post


def test_transcribe_returns_text(mock_groq_api):
    t = Transcriber()
    out = t.transcribe("audios/ejemplo.mp3")
    assert "simulated transcription from groq" in out
