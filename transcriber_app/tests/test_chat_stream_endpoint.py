# transcriber_app/tests/test_chat_stream_endpoint.py
from fastapi.testclient import TestClient
from transcriber_app.web.web_app import app


client = TestClient(app)


def test_chat_stream_endpoint(monkeypatch):
    from transcriber_app.modules.ai.ai_manager import AIManager
    monkeypatch.setattr(
        AIManager,
        "summarize_stream",
        lambda message, mode: iter(["hola", " mundo"])
    )

    response = client.post(
        "/api/chat/stream",
        json={"message": "hola", "mode": "default"}
    )

    assert response.status_code == 200
    assert "hola" in response.text
