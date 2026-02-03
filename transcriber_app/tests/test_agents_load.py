# transcriber_app/tests/test_agents_load.py

from transcriber_app.modules.ai.gemini.agents.tecnico_agent import tecnico_agent
from transcriber_app.modules.ai.gemini.agents.ejecutivo_agent import ejecutivo_agent
from transcriber_app.modules.ai.gemini.agents.refinamiento_agent import refinamiento_agent
from transcriber_app.modules.ai.gemini.agents.bullet_agent import bullet_agent
from transcriber_app.modules.ai.gemini.agents.default_agent import default_agent
from transcriber_app.modules.ai.gemini.client import GeminiModel


def test_agents_initialize():
    agents = [
        tecnico_agent,
        ejecutivo_agent,
        refinamiento_agent,
        bullet_agent,
        default_agent,
    ]

    for agent in agents:
        # 1. Debe ser instancia de GeminiModel
        assert isinstance(agent, GeminiModel)

        # 2. Debe tener un nombre de modelo válido
        assert hasattr(agent, "model_name")
        assert isinstance(agent.model_name, str)
        assert len(agent.model_name) > 0

        # 3. Debe tener un system_prompt cargado
        assert hasattr(agent, "system_prompt")
        assert isinstance(agent.system_prompt, str)
        assert len(agent.system_prompt) > 0
