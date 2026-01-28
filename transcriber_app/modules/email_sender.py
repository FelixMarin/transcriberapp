import subprocess
from pathlib import Path

from .emails import RECIPIENTS
from modules.logging.logging_config import setup_logging

# Logging
logger = setup_logging("transcribeapp")

class EmailSender:
    def send_file(self, file_path: str, subject: str = "Transcripción generada"):
        logger.info(f"[EMAIL SENDER] Enviando archivo: {file_path} a {', '.join(RECIPIENTS)}")
        """Envía el contenido del archivo usando el comando 'mail' del sistema."""

        path = Path(file_path)
        if not path.exists():
            logger.error(f"[EMAIL SENDER] No existe el archivo: {file_path}")
            raise FileNotFoundError(f"❌ No existe el archivo: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        for recipient in RECIPIENTS:
            subprocess.run(
                ["mail", "-s", subject, recipient],
                input=content.encode("utf-8"),
                check=True
            )

        logger.info(f"[EMAIL SENDER] Email enviado a: {', '.join(RECIPIENTS)}")
        return f"📨 Email enviado a: {', '.join(RECIPIENTS)}"
