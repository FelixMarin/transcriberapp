import yt_dlp
import os
import re
import uuid
from pathlib import Path
import sys

from transcriber_app.modules.logging.logging_config import setup_logging
from transcriber_app.modules.ffmpeg_client import get_audio_info, convert_audio, clean_audio

logger = setup_logging("transcribeapp")


def extract_video_id(url: str) -> str:
    patterns = [
        r"v=([A-Za-z0-9_-]+)",
        r"youtu\.be/([A-Za-z0-9_-]+)",
        r"/video/([A-Za-z0-9_-]+)",
    ]
    for p in patterns:
        match = re.search(p, url)
        if match:
            return match.group(1)
    return str(uuid.uuid4())


def prepare_audio_for_transcription(path: str) -> str:
    cleaned_bytes = clean_audio(path)
    cleaned_path = path.replace(".mp3", "_clean.wav")

    with open(cleaned_path, "wb") as f:
        f.write(cleaned_bytes)

    return cleaned_path


def download_audio(url: str, output_dir: str = "./audios", max_duration: int = 9000) -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    audio_id = extract_video_id(url)
    final_path = os.path.join(output_dir, f"{audio_id}.mp3")

    if os.path.exists(final_path):
        logger.info(f"[AUDIO] Ya existe en caché: {final_path}")
        return final_path

    # 1. Extraer metadata
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        duration = info.get("duration")

        if duration:
            logger.info(f"[AUDIO] Duración detectada: {duration/60:.1f} min")
            if duration > max_duration:
                raise ValueError(f"❌ El audio dura {duration/60:.1f} min, supera el límite.")

    # 2. Descargar sin convertir
    outtmpl = os.path.join(output_dir, f"{audio_id}.%(ext)s")
    ydl_opts = {
        'outtmpl': outtmpl,
        'format': 'bestaudio/best',
        'quiet': True,
    }

    logger.info(f"[AUDIO] Descargando audio desde: {url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Detectar archivo descargado
    downloaded_files = [f for f in os.listdir(output_dir) if f.startswith(audio_id)]
    if not downloaded_files:
        raise RuntimeError("❌ No se descargó ningún archivo de audio.")

    temp_path = os.path.join(output_dir, downloaded_files[0])

    # 3. Obtener duración real si no venía en metadata
    if duration is None:
        info = get_audio_info(temp_path)
        duration = info["duration"]
        logger.info(f"[AUDIO] Duración detectada: {duration/60:.1f} min")

        if duration > max_duration:
            os.remove(temp_path)
            raise ValueError("❌ El audio supera el límite permitido.")

    # 4. Convertir a MP3 usando ffmpeg-api
    logger.info("[AUDIO] Convirtiendo a MP3 vía ffmpeg-api…")
    mp3_bytes = convert_audio(temp_path, fmt="mp3")

    with open(final_path, "wb") as f:
        f.write(mp3_bytes)

    os.remove(temp_path)

    logger.info(f"[AUDIO] Descarga completada: {final_path}")
    return final_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python audio_downloader.py <URL>")
        sys.exit(1)

    url = sys.argv[1]

    try:
        path = download_audio(url)
        print(f"\n✅ Audio descargado en: {path}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
