# transcriber_app/tests/test_ai_manager.py
from transcriber_app.modules.ai.ai_manager import AIManager
from transcriber_app.modules.ai.gemini.agents.tecnico_agent import tecnico_agent
from transcriber_app.modules.ai.gemini.agents.refinamiento_agent import refinamiento_agent


def test_ai_manager_selects_correct_agent():
    assert AIManager.get_agent("tecnico") == tecnico_agent
    assert AIManager.get_agent("refinamiento") == refinamiento_agent
    gemini = AIManager.get_model("gemini")
    assert AIManager.get_agent("default") == gemini.agents["default"]


def test_ai_manager_fallback_to_default():
    agent = AIManager.get_agent("modo_inexistente")
    gemini = AIManager.get_model("gemini")
    assert agent == gemini.agents["default"]


def test_ai_manager_summarize_stream(monkeypatch):
    gemini = AIManager.get_model("gemini")
    monkeypatch.setattr(gemini, "run_agent", lambda mode, text: "resultado stream")

    gen = AIManager.summarize_stream("texto", "default")
    result = "".join(list(gen))
    assert result == "resultado stream"
