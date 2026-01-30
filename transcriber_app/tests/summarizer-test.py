from transcriber_app.modules.summarizer import Summarizer

class FakeGeminiClient:
    def analyze(self, text, mode="default"):
        return {"output": "resumen simulado"}

summarizer = Summarizer(FakeGeminiClient())

result = summarizer.summarize("Texto de prueba.")
print(result["output"])
