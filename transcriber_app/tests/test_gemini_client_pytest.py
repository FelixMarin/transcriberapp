import sys
import types
import importlib


def test_gemini_analyze_monkeypatched(monkeypatch):
    genai = types.SimpleNamespace()

    def fake_GenerativeModel(name):
        class M:
            def generate_content(self, prompt, stream=False):
                return types.SimpleNamespace(text="simulated output")
        return M()

    genai.GenerativeModel = fake_GenerativeModel
    genai.configure = lambda api_key=None: None

    # Ensure the module import uses our mocked google.generativeai
    monkeypatch.setitem(sys.modules, 'google.generativeai', genai)

    gem_mod = importlib.import_module('transcriber_app.modules.gemini_client')
    # Re-import/create client after the monkeypatch so the module uses the fake genai
    client = gem_mod.GeminiClient(api_key="dummy")
    res = client.analyze("texto de prueba")
    assert res["output"] == "simulated output"
