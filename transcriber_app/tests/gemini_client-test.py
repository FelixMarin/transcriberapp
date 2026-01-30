import sys
import types

# Mock google.generativeai
genai = types.SimpleNamespace()

def fake_GenerativeModel(name):
    class M:
        def generate_content(self, prompt, stream=False):
            if stream:
                return iter([])
            return types.SimpleNamespace(text="salida simulada")
    return M()

genai.GenerativeModel = fake_GenerativeModel

def configure(api_key=None):
    pass

genai.configure = configure

sys.modules['google.generativeai'] = genai

from transcriber_app.modules.gemini_client import GeminiClient
import os

client = GeminiClient(api_key=os.getenv("GEMINI_API_KEY"))
result = client.analyze("Este es un texto de prueba.")
print(result["output"])
