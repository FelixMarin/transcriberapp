# transcriber_app/modules/ai/agents/refinamiento_agent.py

from agno.agent import Agent
from agno.models.google import Gemini
from transcriber_app.config import USE_MODEL, AVAILABLE_MODES_DICT


def load_prompt(name: str) -> str:
    with open(
        f"transcriber_app/modules/ai/prompts/{name}.md",
        "r",
        encoding="utf-8"
    ) as f:
        return f.read()


refinamiento_agent = Agent(
    model=Gemini(
        USE_MODEL,
        temperature=0.2,
        top_p=0.9,
        top_k=40,
        max_output_tokens=4096
    ),

    # Prompt maestro
    system_message=load_prompt(AVAILABLE_MODES_DICT["refinamiento"]),

    # Instrucciones adicionales reforzando el comportamiento
    instructions=[
        "Asegúrate de que el resultado final siga EXACTAMENTE el formato especificado en el prompt.",
        "No incluyas explicaciones sobre tu proceso interno.",
        "No generes contenido fuera de las secciones definidas.",
        "Si el texto es ambiguo, indica qué falta y qué sería necesario.",
        "Si detectas riesgos o incoherencias, destácalos sin suavizarlos."
    ],
)
