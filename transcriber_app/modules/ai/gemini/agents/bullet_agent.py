# transcriber_app/modules/ai/agents/bullet_agent.py
from agno.agent import Agent
from agno.models.google import Gemini
from transcriber_app.config import USE_MODEL, AVAILABLE_MODES_DICT


def load_prompt(name: str) -> str:
    with open(
        f"transcriber_app/modules/ai/gemini/prompts/{name}.md",
        "r",
        encoding="utf-8"
    ) as f:
        return f.read()


bullet_agent = Agent(
    model=Gemini(USE_MODEL),
    instructions=load_prompt(AVAILABLE_MODES_DICT["bullet"]),
)
