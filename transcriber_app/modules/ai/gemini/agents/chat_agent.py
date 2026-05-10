from transcriber_app.config import USE_MODEL
from transcriber_app.modules.ai.gemini.model import GeminiAgent


def load_prompt(name: str) -> str:
    with open(
        f"transcriber_app/modules/ai/gemini/prompts/{name}.md",
        "r",
        encoding="utf-8"
    ) as f:
        return f.read()


chat_agent = GeminiAgent(
    model_name=USE_MODEL,
    system_prompt=load_prompt("chat"),
    temperature=0.4,
    max_output_tokens=2048,
)
