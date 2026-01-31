# transcriber_app/modules/output_formatter.py
import os
import json
from transcriber_app.modules.logging.logging_config import setup_logging

# Logging
logger = setup_logging("transcribeapp")


class OutputFormatter:
    def save_output(self, base_name: str, content, mode: str) -> str:
        """
        Guarda la salida del agente. `content` puede ser:
        - RunOutput (Agno)
        - str (modo legacy)
        """
        logger.info(f"[OUTPUT FORMATTER] Guardando salida para: {base_name} con modo: {mode}")
        os.makedirs("outputs", exist_ok=True)

        output_filename = f"{base_name}_{mode}.md"
        output_path = os.path.join("outputs", output_filename)

        # Normalizar: si es RunOutput → usar content.content
        if hasattr(content, "content"):
            text = content.content
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
        Guarda las métricas del agente en outputs/metrics/*.json
        result es un RunOutput de Agno.
        """
        logger.info(f"[OUTPUT FORMATTER] Guardando métricas para: {base_name} con modo: {mode}")

        os.makedirs("outputs/metrics", exist_ok=True)

        metrics_filename = f"{base_name}_{mode}.json"
        metrics_path = os.path.join("outputs/metrics", metrics_filename)

        # Construir diccionario de métricas
        data = {
            "run_id": getattr(result, "run_id", None),
            "session_id": getattr(result, "session_id", None),
            "agent_id": getattr(result, "agent_id", None),
            "model": getattr(result, "model", None),
            "provider": getattr(result, "model_provider", None),
            "input_preview": getattr(getattr(result, "input", None), "input_content", None),
            "output_preview": getattr(result, "content", None),
            "metrics": {
                "input_tokens": getattr(getattr(result, "metrics", None), "input_tokens", None),
                "output_tokens": getattr(getattr(result, "metrics", None), "output_tokens", None),
                "total_tokens": getattr(getattr(result, "metrics", None), "total_tokens", None),
                "duration": getattr(getattr(result, "metrics", None), "duration", None),
            }
        }

        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        logger.info(f"[OUTPUT FORMATTER] Métricas guardadas en: {metrics_path}")
        return metrics_path
