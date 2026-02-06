# transcriber_app/modules/output_formatter.py
import os
from transcriber_app.modules.logging.logging_config import setup_logging

# Logging
logger = setup_logging("transcribeapp")


class OutputFormatter:
    def save_output(self, base_name: str, content: str, mode: str, enforce_save: bool = True) -> str:
        logger.info(f"[OUTPUT FORMATTER] Guardando salida para: {base_name} con modo: {mode} (enforce_save={enforce_save})")
        output_filename = f"{base_name}_{mode}.md"
        output_path = os.path.join("outputs", output_filename)

        if enforce_save:
            os.makedirs("outputs", exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"[OUTPUT FORMATTER] Archivo guardado en: {output_path}")
        else:
            logger.info("[OUTPUT FORMATTER] Saltado guardado en disco por configuración")

        return output_path

    def save_transcription(self, base_name: str, text: str, enforce_save: bool = True) -> str:
        logger.info(f"[OUTPUT FORMATTER] Guardando transcripción para: {base_name} (enforce_save={enforce_save})")
        path = f"transcripts/{base_name}.txt"

        if enforce_save:
            os.makedirs("transcripts", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            logger.info(f"[OUTPUT FORMATTER] Transcripción guardada en: {path}")
        else:
            logger.info("[OUTPUT FORMATTER] Saltado guardado en disco por configuración")

        return path

    def save_metrics(self, name: str, summary: str, mode: str):
        metrics = {
            "name": name,
            "mode": mode,
            "length": len(summary),
        }

        path = f"outputs/metrics/{name}_{mode}.json"

        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)

        logger.info(f"[OUTPUT FORMATTER] Métricas guardadas en: {path}")
