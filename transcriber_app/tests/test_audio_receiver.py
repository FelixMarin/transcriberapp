import unittest
from unittest.mock import patch
from transcriber_app.modules.audio_receiver import AudioReceiver
import os


class TestAudioReceiver(unittest.TestCase):
    @patch("os.path.exists", return_value=True)
    def test_load(self, mock_exists):
        audio_receiver = AudioReceiver()
        audio_path = "path/to/audio/file.wav"
        result = audio_receiver.load(audio_path)
        self.assertIsNotNone(result)
        self.assertIn("path", result)
        self.assertIn("name", result)

    def test_load_error(self):
        audio_receiver = AudioReceiver()
        audio_path = "path/to/non/existent/audio/file.wav"
        if not os.path.exists(audio_path):
            with self.assertRaises(FileNotFoundError):
                audio_receiver.load(audio_path)
        else:
            self.fail("El archivo existe")


if __name__ == "__main__":
    unittest.main()
