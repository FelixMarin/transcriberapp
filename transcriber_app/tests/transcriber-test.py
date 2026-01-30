import sys
import types

# Mock 'whisper' to avoid importing torch/ffmpeg/etc during tests
whisper = types.SimpleNamespace()

def fake_load_model(size, device=None):
    class Model:
        def transcribe(self, path, language=None, fp16=False):
            return {"text": f"transcripción simulada para {path}"}
    return Model()

whisper.load_model = fake_load_model
sys.modules['whisper'] = whisper

import transcriber_app.modules.transcriber as trans_mod
from transcriber_app.modules.transcriber import Transcriber

# Avoid running ffmpeg during tests by bypassing ensure_wav
trans_mod.ensure_wav = lambda p: p

# Synchronous test using the mocked model
def test():
    t = Transcriber()
    text = t.transcribe("audios/ejemplo.mp3")
    print(text)

if __name__ == "__main__":
    test()
