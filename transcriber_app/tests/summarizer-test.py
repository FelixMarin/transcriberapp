from transcriber_app.modules.summarizer import Summarizer


class FakeGeminiClient:
    def analyze(self, text, mode="default"):
        return {"output": "resumen simulado"}


def test_summarizer_simple():
    summarizer = Summarizer(FakeGeminiClient())
    result = summarizer.summarize("Texto de prueba.")
    assert "resumen simulado" in result["output"]
