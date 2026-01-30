# transcriber_app/tests/emailer-test.py
import os
from pathlib import Path
from dotenv import load_dotenv
from transcriber_app.web.api.emailer import send_email_with_attachment

# Cargar .env desde la raíz del proyecto
load_dotenv(dotenv_path="/home/jetson/Public/TranscriberApp/.env")


def main():
    print("=== TEST EMAILER (USANDO MÓDULO REAL) ===")

    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = os.getenv("SMTP_PORT")

    print(f"SMTP_USER: {SMTP_USER}")
    print(f"SMTP_PASS: {'OK' if SMTP_PASS else 'MISSING'}")
    print(f"SMTP_HOST: {SMTP_HOST}")
    print(f"SMTP_PORT: {SMTP_PORT}")

    # Archivo de prueba
    attachment_path = "outputs/spring_cloud_tecnico.md"

    if not Path(attachment_path).exists():
        print(f"⚠ El archivo {attachment_path} no existe. Crea uno antes de probar.")
        return

    print("Enviando email usando el módulo emailer.py...")

    ok = send_email_with_attachment(
        to="felixmurcia@gmail.com",
        subject="Test desde módulo emailer.py",
        body="Este es un test usando el módulo emailer.py importado.",
        attachment_path=attachment_path
    )

    if ok:
        print("✅ Email enviado correctamente desde el módulo emailer.py")
    else:
        print("❌ Error enviando email desde el módulo emailer.py")


if __name__ == "__main__":
    main()
