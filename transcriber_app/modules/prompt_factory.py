# transcriber_app/modules/prompt_factory.py
from transcriber_app.modules.logging.logging_config import setup_logging
from transcriber_app.config import LANGUAGE

# Logging
logger = setup_logging("transcribeapp")


class PromptFactory:
    AVAILABLE_MODES = ["default", "tecnico", "refinamiento", "ejecutivo", "bullet"]

    def __init__(self, target_lang=LANGUAGE):
        logger.info(f"[PROMPT FACTORY] Inicializando con idioma objetivo: {target_lang}")
        self.lang = target_lang

    def get_prompt(self, mode: str, text: str) -> str:
        logger.info(f"[PROMPT FACTORY] Generando prompt para modo: {mode}")
        mode = mode.lower()

        prompts = {
            "tecnico": f"""
Genera un resumen técnico claro, preciso y bien estructurado en {self.lang} basado en el siguiente texto transcrito.

Requisitos del resumen:
- Explica los conceptos con rigor técnico.
- Identifica arquitectura, componentes, flujos de datos y mecanismos internos.
- Corrige errores de transcripción (nombres, términos técnicos, siglas).
- Usa terminología propia de ingeniería de datos, sistemas distribuidos y streaming.
- Añade contexto técnico cuando sea relevante, pero sin inventar información.
- Organiza la salida en secciones con títulos y bullets.
- Mantén un tono profesional y orientado a ingenieros.

Texto a analizar:
{text}
""",

            "refinamiento": f"""
A partir de la siguiente transcripción de una reunión de refinamiento de sprint,
extrae TODAS las tareas, subtareas y elementos accionables mencionados.

=== INSTRUCCIONES ===
1. Identifica todas las tareas mencionadas directa o indirectamente.
2. Divide cada tarea en subtareas si corresponde.
3. Detecta dependencias entre tareas.
4. Identifica responsables si se mencionan.
5. Identifica prioridades si se mencionan.
6. Identifica riesgos, bloqueos o dudas abiertas.
7. Identifica decisiones tomadas.
8. Identifica estimaciones si aparecen.
9. NO inventes información.

=== FORMATO DE SALIDA ===
## Backlog generado a partir de la reunión

### 1. Tareas principales
- **Tarea:** <nombre>
  - **Descripción:** <breve descripción>
  - **Subtareas:**
    - <subtarea 1>
    - <subtarea 2>
  - **Dependencias:** <si las hay>
  - **Responsable:** <si se menciona>
  - **Prioridad:** <si se menciona>
  - **Estimación:** <si se menciona>

### 2. Riesgos y bloqueos
- <riesgo>

### 3. Decisiones tomadas
- <decisión>

### 4. Dudas abiertas
- <duda>

=== TRANSCRIPCIÓN ===
{text}
""",

            "ejecutivo": f"""
Resume el siguiente texto en {self.lang} con un estilo ejecutivo:
- 5 a 8 líneas máximo
- Enfoque en decisiones, impacto y puntos clave
- Sin tecnicismos innecesarios

Texto:
{text}
""",

            "bullet": f"""
Resume el siguiente texto en {self.lang} usando solo bullets claros y concisos.
Máximo 10 bullets.

Texto:
{text}
""",

            "default": f"""
Resume el siguiente texto en {self.lang} de forma clara y concisa:

{text}
"""
        }

        # Si el modo no existe, usar "default"
        return prompts.get(mode, prompts["default"])

    def get_chat_prompt(
        self,
        transcripcion: str,
        resumen: str,
        pregunta: str,
        historial: list[dict] | None = None,
    ) -> str:
        historial = historial or []

        historial_texto = ""
        if historial:
            partes = []
            for h in historial:
                rol = "USUARIO" if h["role"] == "user" else "ASISTENTE"
                partes.append(f"{rol}: {h['content']}")
            historial_texto = "\n".join(partes)

        return f"""
Eres un asistente experto. Responde SIEMPRE en {self.lang}.
Usa la transcripción original y el resumen procesado como contexto principal.

=== CONTEXTO DE LA REUNIÓN ===
[TRANSCRIPCIÓN]
{transcripcion}

[RESUMEN]
{resumen}

=== HISTORIAL DE LA CONVERSACIÓN ===
{historial_texto if historial_texto else "Sin mensajes previos."}

=== PREGUNTA ACTUAL DEL USUARIO ===
{pregunta}

=== RESPUESTA EN {self.lang.upper()} ===
"""
