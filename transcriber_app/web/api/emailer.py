# transcriber_app/web/api/emailer.py (VERSIÓN MEJORADA)
import os
import smtplib
import ssl
from pathlib import Path
from email.message import EmailMessage
from dotenv import load_dotenv
from transcriber_app.modules.logging.logging_config import setup_logging

# Logging
logger = setup_logging("transcribeapp")

# Cargar variables de entorno
load_dotenv()


def get_smtp_config():
    """Obtiene y valida configuración SMTP"""
    SMTP_HOST = os.getenv("SMTP_HOST", "lin414.loading.es")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
    SMTP_USER = os.getenv("SMTP_USER", "contact@nbes.blog")
    SMTP_PASS = os.getenv("SMTP_PASS", "")

    if not SMTP_PASS:
        logger.warning("[EMAILER] SMTP_PASS no configurada en .env")

    return SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS


def send_email_with_attachment(to: str, subject: str, body: str, attachment_path: str):
    """
    Envía email con adjunto usando autenticación CRAM-MD5 compatible
    """
    logger.info(f"[EMAILER] Iniciando envío a {to}")

    # Obtener configuración
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS = get_smtp_config()

    if not SMTP_PASS:
        logger.error("[EMAILER] No hay contraseña SMTP configurada")
        return False

    # Validar archivo adjunto
    file_path = Path(attachment_path)
    if not file_path.exists():
        logger.error(f"[EMAILER] Archivo no encontrado: {attachment_path}")
        return False

    try:
        # Crear mensaje
        msg = EmailMessage()
        msg["From"] = SMTP_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        # Determinar tipo MIME del adjunto
        file_ext = file_path.suffix.lower()
        mime_types = {
            '.pdf': ('application', 'pdf'),
            '.txt': ('text', 'plain'),
            '.md': ('text', 'plain'),
            '.jpg': ('image', 'jpeg'),
            '.jpeg': ('image', 'jpeg'),
            '.png': ('image', 'png'),
            '.mp3': ('audio', 'mpeg'),
            '.wav': ('audio', 'wav'),
        }

        maintype, subtype = mime_types.get(file_ext, ('application', 'octet-stream'))

        # Adjuntar archivo
        msg.add_attachment(
            file_path.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=file_path.name
        )

        logger.info(f"[EMAILER] Adjunto preparado: {file_path.name} ({maintype}/{subtype})")

    except Exception as e:
        logger.error(f"[EMAILER] Error preparando mensaje: {e}")
        return False

    # Intentar diferentes métodos de conexión
    methods = [
        {"name": "SSL+CRAM-MD5", "ssl": True, "cram_md5": True},
        {"name": "SSL estándar", "ssl": True, "cram_md5": False},
        {"name": "STARTTLS", "ssl": False, "cram_md5": True, "port": 587},
    ]

    for method in methods:
        try:
            logger.info(f"[EMAILER] Probando método: {method['name']}")

            port = method.get("port", SMTP_PORT)

            if method["ssl"]:
                # Crear contexto SSL seguro
                context = ssl.create_default_context()
                smtp = smtplib.SMTP_SSL(
                    SMTP_HOST,
                    port,
                    context=context,
                    timeout=30
                )
            else:
                smtp = smtplib.SMTP(SMTP_HOST, port, timeout=30)
                smtp.starttls()

            # Autenticación
            if method["cram_md5"]:
                smtp.login(SMTP_USER, SMTP_PASS, initial_response_ok=True)
            else:
                smtp.login(SMTP_USER, SMTP_PASS)

            logger.info(f"[EMAILER] Autenticado con {method['name']}")

            # Enviar mensaje
            smtp.send_message(msg)
            smtp.quit()

            logger.info(f"[EMAILER] Email enviado exitosamente usando {method['name']}")
            return True

        except Exception as e:
            logger.warning(f"[EMAILER] Método {method['name']} falló: {str(e)[:100]}")
            continue

    logger.error("[EMAILER] Todos los métodos de envío fallaron")
    return False

# Función adicional para enviar sin adjunto (opcional)


def send_email(to: str, subject: str, body: str):
    """Envía email sin adjunto"""
    logger.info(f"[EMAILER] Enviando email simple a {to}")

    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS = get_smtp_config()

    if not SMTP_PASS:
        logger.error("[EMAILER] No hay contraseña SMTP configurada")
        return False

    try:
        msg = EmailMessage()
        msg["From"] = SMTP_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            smtp.login(SMTP_USER, SMTP_PASS, initial_response_ok=True)
            smtp.send_message(msg)

        logger.info(f"[EMAILER] Email simple enviado a {to}")
        return True

    except Exception as e:
        logger.error(f"[EMAILER] Error enviando email simple: {e}")
        return False
