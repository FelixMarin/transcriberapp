from transcriber_app.modules.summarizer import Summarizer


class FakeClient:
    def analyze(self, text, mode="default"):
        return {"output": "resumen simulado"}


def test_summarize_delegates_to_client():
    s = Summarizer(FakeClient())
    res = s.summarize("Texto ejemplo")
    assert res["output"] == "resumen simulado"
