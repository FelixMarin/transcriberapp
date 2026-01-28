import os
from pathlib import Path
from email.message import EmailMessage
import aiosmtplib
from dotenv import load_dotenv
from modules.logging.logging_config import setup_logging

# Logging
logger = setup_logging("transcribeapp")

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

async def send_email_with_attachment(to: str, subject: str, body: str, attachment_path: str):
    logger.info(f"[EMAILER] Enviando email a {to} con adjunto {attachment_path}")
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    # Adjuntar archivo
    file_path = Path(attachment_path)
    if not file_path.exists():
        logger.error(f"[EMAILER] No existe el archivo adjunto: {file_path}")
        return

    msg.add_attachment(
        file_path.read_bytes(),
        maintype="application",
        subtype="octet-stream",
        filename=file_path.name
    )

    # Enviar email
    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER,
        password=SMTP_PASS,
        start_tls=True,
    )

    logger.info(f"[EMAILER] Email enviado a {to} con adjunto {file_path.name}")
