# transcriber_app/tests/test_agents_load.py
from agno.agent import Agent
from transcriber_app.modules.ai.agents.tecnico_agent import tecnico_agent
from transcriber_app.modules.ai.agents.ejecutivo_agent import ejecutivo_agent
from transcriber_app.modules.ai.agents.refinamiento_agent import refinamiento_agent
from transcriber_app.modules.ai.agents.bullet_agent import bullet_agent
from transcriber_app.modules.ai.agents.default_agent import default_agent


def test_agents_initialize():
    agents = [
        tecnico_agent,
        ejecutivo_agent,
        refinamiento_agent,
        bullet_agent,
        default_agent,
    ]

    for agent in agents:
        assert isinstance(agent, Agent)
        assert agent.instructions is not None
        assert agent.model is not None
