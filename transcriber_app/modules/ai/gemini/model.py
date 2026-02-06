# transcriber_app/modules/ai/gemini/model.py

import google.generativeai as genai
from transcriber_app.config import GOOGLE_API_KEY
from transcriber_app.modules.logging.logging_config import setup_logging

# Logging
logger = setup_logging("transcribeapp")

genai.configure(api_key=GOOGLE_API_KEY)


def normalize_gemini_output(response):
    # Caso 1: string directo
    if isinstance(response, str):
        return response

    # Caso 2: objeto con .text
    if hasattr(response, "text") and isinstance(response.text, str):
        return response.text

    # Caso 3: iterable de eventos (streaming o modelos flash-lite)
    if hasattr(response, "__iter__") and not isinstance(response, (bytes, dict)):
        chunks = []
        for event in response:
            if hasattr(event, "text") and event.text:
                chunks.append(event.text)
            elif isinstance(event, str):
                chunks.append(event)
        return "".join(chunks)

    # Caso 4: dict con contenido
    if isinstance(response, dict):
        if "text" in response:
            return response["text"]
        return str(response)

    # Caso 5: cualquier otra cosa → convertir a string
    return str(response)


class GeminiAgent:
    def __init__(
        self,
        model_name: str,
        system_prompt: str,
        temperature: float = 0.2,
        top_p: float = 0.9,
        top_k: int = 40,
        max_output_tokens: int = 4096,
    ):
        self.model_name = model_name
        self.system_prompt = system_prompt

        self.generation_config = {
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "max_output_tokens": max_output_tokens,
        }

        self._model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config
        )

    def run(self, text: str, stream: bool = False):
        logger.info(f"[GEMINI AGENT] stream recibido: {stream}")
        logger.info(f"[GEMINI AGENT] Texto recibido: {text[:100]}...")

        response = self._model.generate_content(
            self.system_prompt + "\n\n" + text,
            stream=stream
        )

        if stream:
            def generator():
                for chunk in response:
                    if hasattr(chunk, "text") and chunk.text:
                        yield chunk.text
            return generator()

        logger.info(f"[GEMINI AGENT] Respuesta bruta recibida: {repr(response)[:200]}. Tipo: {type(response)}")
        return normalize_gemini_output(response)
