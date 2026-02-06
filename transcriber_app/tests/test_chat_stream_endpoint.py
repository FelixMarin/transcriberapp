# transcriber_app/tests/test_chat_stream_endpoint.py
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from transcriber_app.web.web_app import app


client = TestClient(app)


def test_chat_stream_endpoint(monkeypatch):
    from transcriber_app.modules.ai.ai_manager import AIManager

    # Mock agent with run method
    mock_agent = MagicMock()
    mock_agent.run.return_value = iter(["hola", " mundo"])

    monkeypatch.setattr(AIManager, "get_agent", lambda mode: mock_agent)

    response = client.post(
        "/api/chat/stream",
        json={"message": "hola", "mode": "default"}
    )

    assert response.status_code == 200
    assert "hola" in response.text
    assert "mundo" in response.text
