import pytest
from transcriber_app.modules.ai.gemini.model import normalize_gemini_output, GeminiAgent


class MockResponse:
    def __init__(self, text):
        self.text = text


def test_normalize_gemini_output_str():
    assert normalize_gemini_output("hola") == "hola"


def test_normalize_gemini_output_obj():
    assert normalize_gemini_output(MockResponse("mundo")) == "mundo"


def test_normalize_gemini_output_iter():
    def gen():
        yield MockResponse("parte1")
        yield MockResponse("parte2")
    assert normalize_gemini_output(gen()) == "parte1parte2"


def test_normalize_gemini_output_dict():
    assert normalize_gemini_output({"text": "valor"}) == "valor"
    assert normalize_gemini_output({"otro": "campo"}) == "{'otro': 'campo'}"


def test_normalize_gemini_output_fallback():
    assert normalize_gemini_output(123) == "123"


@pytest.fixture
def mock_genai(monkeypatch):
    import google.generativeai as genai
    from unittest.mock import MagicMock

    mock_model = MagicMock()
    monkeypatch.setattr(genai, "GenerativeModel", lambda **kwargs: mock_model)
    return mock_model


def test_gemini_agent_run(mock_genai):
    agent = GeminiAgent(model_name="test-model", system_prompt="prompt")

    # Mock normal response
    mock_genai.generate_content.return_value = MockResponse("respuesta")
    res = agent.run("pregunta")
    assert res == "respuesta"

    # Mock stream response
    mock_genai.generate_content.return_value = [MockResponse("ch1"), MockResponse("ch2")]
    res_stream = agent.run("pregunta", stream=True)
    assert "".join(res_stream) == "ch1ch2"
