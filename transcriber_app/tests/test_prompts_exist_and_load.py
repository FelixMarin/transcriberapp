# transcriber_app/tests/test_prompts_exist_and_load.py
import os
from transcriber_app.config import AVAILABLE_MODES_DICT

PROMPTS_DIR = "transcriber_app/modules/ai/prompts"


def test_prompts_exist():
    for mode in AVAILABLE_MODES_DICT.values():
        path = os.path.join(PROMPTS_DIR, f"{mode}.md")
        assert os.path.exists(path), f"Falta el prompt: {path}"


def test_prompts_not_empty():
    for mode in AVAILABLE_MODES_DICT.values():
        path = os.path.join(PROMPTS_DIR, f"{mode}.md")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        assert len(content) > 20, f"Prompt demasiado corto: {mode}"


def test_refinamiento_contains_sections():
    path = os.path.join(PROMPTS_DIR, "refinamiento.md")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    required_sections = [
        "Puntos Clave",
        "Tareas y Subtareas",
        "Historias de Usuario",
        "Riesgos",
        "Preguntas para el Arquitecto",
        "Visión Lateral",
    ]

    for section in required_sections:
        assert section in content, f"Falta la sección: {section}"
