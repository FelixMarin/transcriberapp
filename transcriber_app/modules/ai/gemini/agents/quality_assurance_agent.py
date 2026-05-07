# transcriber_app/modules/ai/agents/quality_assurance_agent.py

from transcriber_app.config import USE_MODEL, AVAILABLE_MODES_DICT
from transcriber_app.modules.ai.gemini.model import GeminiAgent


def load_prompt(name: str) -> str:
    with open(
        f"transcriber_app/modules/ai/gemini/prompts/{name}.md",
        "r",
        encoding="utf-8"
    ) as f:
        return f.read()


quality_assurance_agent = GeminiAgent(
    model_name=USE_MODEL,
    system_prompt=load_prompt(AVAILABLE_MODES_DICT["quality_assurance"])
)