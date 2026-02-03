# transcriber_app/modules/ai/agents/refinamiento_agent.py

from transcriber_app.config import USE_MODEL, AVAILABLE_MODES_DICT
from transcriber_app.modules.ai.gemini.model import GeminiAgent


def load_prompt(name: str) -> str:
    with open(
        f"transcriber_app/modules/ai/gemini/prompts/{name}.md",
        "r",
        encoding="utf-8"
    ) as f:
        return f.read()


refinamiento_agent = GeminiAgent(
    model_name=USE_MODEL,
    system_prompt=load_prompt(AVAILABLE_MODES_DICT["refinamiento"]),
    temperature=0.2,
    top_p=0.9,
    top_k=40,
    max_output_tokens=4096
)
