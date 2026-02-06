import pytest
from unittest.mock import MagicMock
from transcriber_app.modules.ai.gemini.client import GeminiModel


def test_gemini_model_run_agent_starlette_response():
    model = GeminiModel()

    # Mocking a Starlette-like response object
    mock_response = MagicMock()
    mock_response.body.decode.return_value = "cuerpo decodificado"
    type(mock_response).__name__ = "Response"

    # Mocking the agent inside the model
    mock_agent = MagicMock()
    mock_agent.run.return_value = mock_response
    model.agents["test"] = mock_agent

    res = model.run_agent("test", "test text")
    assert res == "cuerpo decodificado"


def test_gemini_model_run_agent_error():
    model = GeminiModel()
    mock_agent = MagicMock()
    mock_agent.run.return_value = 123.456  # Un Tipo no soportado
    model.agents["test"] = mock_agent

    with pytest.raises(RuntimeError) as excinfo:
        model.run_agent("test", "test text")
    assert "Tipo inesperado" in str(excinfo.value)
