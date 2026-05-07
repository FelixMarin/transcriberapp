# transcriber_app/modules/output_formatter.py
import os
from transcriber_app.modules.logging.logging_config import setup_logging

# Logging
logger = setup_logging("transcribeapp")

# Rutas absolutas para Docker
APP_BASE_DIR = os.getenv("APP_BASE_DIR", "/app")


class OutputFormatter:
    def save_output(self, base_name: str, content: str, mode: str, enforce_save: bool = True) -> str:
        logger.info(f"[OUTPUT FORMATTER] Guardando salida para: {base_name} "
                    f"con modo: {mode} (enforce_save={enforce_save})")
        output_filename = f"{base_name}_{mode}.md"
        output_path = os.path.join(APP_BASE_DIR, "outputs", output_filename)

        if enforce_save:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"[OUTPUT FORMATTER] Archivo guardado en: {output_path}")
        else:
            logger.info("[OUTPUT FORMATTER] Saltado guardado en disco por configuración")

        return output_path

    def save_transcription(self, base_name: str, text: str, enforce_save: bool = True) -> str:
        """
        Guarda la transcripción en texto plano en /app/transcripts.
        
        Args:
            base_name: Nombre base del archivo
            text: Texto de la transcripción
            enforce_save: Si True, fuerza el guardado en disco
            
        Returns:
            Ruta donde se guardó la transcripción
        """
        logger.info(f"[OUTPUT FORMATTER] Guardando transcripción para: {base_name} (enforce_save={enforce_save})")
        # Usar ruta absoluta /app/transcripts que coincide con el volumen de Docker
        transcripts_dir = os.path.join(APP_BASE_DIR, "transcripts")
        path = os.path.join(transcripts_dir, f"{base_name}.txt")

        if enforce_save:
            os.makedirs(transcripts_dir, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            logger.info(f"[OUTPUT FORMATTER] Transcripción guardada en: {path}")
        else:
            logger.info("[OUTPUT FORMATTER] Saltado guardado en disco por configuración")

        return path

    def save_metrics(self, name: str, summary: str, mode: str):
        """Guarda las métricas en /app/outputs/metrics."""
        metrics = {
            "name": name,
            "mode": mode,
            "length": len(summary),
        }

        # Usar ruta absoluta /app/outputs/metrics que coincide con el volumen de Docker
        metrics_dir = os.path.join(APP_BASE_DIR, "outputs", "metrics")
        path = os.path.join(metrics_dir, f"{name}_{mode}.json")

        # Crear el directorio si no existe
        os.makedirs(metrics_dir, exist_ok=True)

        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)

        logger.info(f"[OUTPUT FORMATTER] Métricas guardadas en: {path}")
