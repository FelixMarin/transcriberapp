# transcriber_app/modules/output_formatter.py

import os
import json
from transcriber_app.modules.logging.logging_config import setup_logging

# Logging
logger = setup_logging("transcribeapp")


class OutputFormatter:
    def save_output(self, base_name: str, content, mode: str) -> str:
        """
        Guarda la salida del agente.
        `content` ahora siempre es texto (str) o un objeto con .text
        """
        logger.info(f"[OUTPUT FORMATTER] Guardando salida para: {base_name} con modo: {mode}")
        os.makedirs("outputs", exist_ok=True)

        output_filename = f"{base_name}_{mode}.md"
        output_path = os.path.join("outputs", output_filename)

        # Normalizar: si el objeto tiene .text → usarlo
        if hasattr(content, "text"):
            text = content.text
        else:
            text = str(content)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        logger.info(f"[OUTPUT FORMATTER] Archivo guardado en: {output_path}")
        return output_path

    def save_transcription(self, base_name: str, text: str) -> str:
        logger.info(f"[OUTPUT FORMATTER] Guardando transcripción para: {base_name}")
        os.makedirs("transcripts", exist_ok=True)
        path = f"transcripts/{base_name}.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info(f"[OUTPUT FORMATTER] Transcripción guardada en: {path}")
        return path

    def save_metrics(self, base_name: str, result, mode: str) -> str:
        """
        Guarda métricas del agente en outputs/metrics/*.json.
        `result` puede ser:
        - None
        - un dict con métricas
        - un objeto con atributos opcionales
        """
        logger.info(f"[OUTPUT FORMATTER] Guardando métricas para: {base_name} con modo: {mode}")

        os.makedirs("outputs/metrics", exist_ok=True)

        metrics_filename = f"{base_name}_{mode}.json"
        metrics_path = os.path.join("outputs/metrics", metrics_filename)

        # Si no hay métricas → guardar un JSON mínimo
        if result is None:
            data = {"info": "No hay métricas disponibles"}
        elif isinstance(result, dict):
            data = result
        else:
            # Extraer atributos opcionales si existen
            data = {
                "model": getattr(result, "model_name", None),
                "temperature": getattr(result, "temperature", None),
                "top_p": getattr(result, "top_p", None),
                "top_k": getattr(result, "top_k", None),
                "max_output_tokens": getattr(result, "max_output_tokens", None),
                "info": "Métricas básicas generadas"
            }

        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        logger.info(f"[OUTPUT FORMATTER] Métricas guardadas en: {metrics_path}")
        return metrics_path
