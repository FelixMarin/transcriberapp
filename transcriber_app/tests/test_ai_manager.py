# transcriber_app/tests/test_ai_manager.py
from transcriber_app.modules.ai.ai_manager import AIManager
from transcriber_app.modules.ai.agents.tecnico_agent import tecnico_agent
from transcriber_app.modules.ai.agents.refinamiento_agent import refinamiento_agent


def test_ai_manager_selects_correct_agent():
    assert AIManager.get_agent("tecnico") == tecnico_agent
    assert AIManager.get_agent("refinamiento") == refinamiento_agent
    assert AIManager.get_agent("default") == AIManager.agents["default"]


def test_ai_manager_fallback_to_default():
    agent = AIManager.get_agent("modo_inexistente")
    assert agent == AIManager.agents["default"]
