import os
from modules.logging.logging_config import setup_logging

# Logging
logger = setup_logging("transcribeapp")

class OutputFormatter:
    def save_output(self, base_name: str, content: str, mode: str) -> str:
        logger.info(f"[OUTPUT FORMATTER] Guardando salida para: {base_name} con modo: {mode}")
        os.makedirs("outputs", exist_ok=True)

        # nombre_final = base + "_" + modo + ".md"
        output_filename = f"{base_name}_{mode}.md"
        output_path = os.path.join("outputs", output_filename)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

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
