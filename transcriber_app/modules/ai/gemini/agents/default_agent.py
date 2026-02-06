# transcriber_app/modules/ai/agents/default_agent.py

from transcriber_app.config import USE_MODEL, AVAILABLE_MODES_DICT
from transcriber_app.modules.ai.gemini.model import GeminiAgent


def load_prompt(name: str) -> str:
    with open(
        f"transcriber_app/modules/ai/gemini/prompts/{name}.md",
        "r",
        encoding="utf-8"
    ) as f:
        return f.read()


default_agent = GeminiAgent(
    model_name=USE_MODEL,
    system_prompt=load_prompt(AVAILABLE_MODES_DICT["default"])
)
