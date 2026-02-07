import unittest
from transcriber_app.modules.audio_receiver import AudioReceiver

class TestAudioReceiver(unittest.TestCase):
    def test_load(self):
        audio_receiver = AudioReceiver()
        audio_path = "path/to/audio/file.wav"
        result = audio_receiver.load(audio_path)
        self.assertIsNotNone(result)
        self.assertIn("path", result)
        self.assertIn("name", result)

if __name__ == "__main__":
    unittest.main()
import unittest
from transcriber_app.modules.audio_receiver import AudioReceiver

class TestAudioReceiver(unittest.TestCase):
    def test_load_error(self):
        audio_receiver = AudioReceiver()
        audio_path = "path/to/non/existent/audio/file.wav"
        with self.assertRaises(FileNotFoundError):
            audio_receiver.load(audio_path)

if __name__ == "__main__":
    unittest.main()
