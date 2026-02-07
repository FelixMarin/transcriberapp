import unittest
from transcriber_app.modules.audio_receiver import AudioReceiver
import os

class TestAudioReceiver(unittest.TestCase):
    def test_load(self):
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
