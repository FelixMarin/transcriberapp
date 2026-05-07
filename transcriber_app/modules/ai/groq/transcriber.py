# transcriber_app/modules/ai/groq/transcriber.py

import os
import time
import tempfile
import requests
import logging
import subprocess
import json
from typing import Tuple, Dict, Any, Optional

from transcriber_app.config import GROQ_API_KEY, FFMPEG_API_URL
from transcriber_app.modules.ai.base.transcriber_interface import TranscriberInterface
from transcriber_app.modules.ffmpeg_client import (
    check_ffmpeg_api_health,
    check_gpu_status,
    ensure_ffmpeg_api_ready,
    validate_audio,
    convert_audio,
    clean_audio,
    convert_to_mp3_chunked,
)

logger = logging.getLogger("transcribeapp")


class AudioValidationError(Exception):
    """Excepción para errores de validación de audio"""
    def __init__(self, message: str, validation_result: Optional[Dict] = None):
        super().__init__(message)
        self.validation_result = validation_result


class GroqTranscriber(TranscriberInterface):
    URL = os.getenv("GROQ_API_URL", "")
    MODEL = os.getenv("GROQ_MODEL_TRANSCRIBER", "whisper-large-v3")

    def __init__(self, skip_validation: bool = False):
        """
        Inicializa el transcriber de Groq.
        
        Args:
            skip_validation: Si es True, omite la validación del audio (útil para debugging)
        """
        self.skip_validation = skip_validation

    def _ensure_ffmpeg_api_ready(self) -> bool:
        """Verifica que FFmpeg API esté listo"""
        logger.info("[GROQ] Verificando disponibilidad de FFmpeg API...")
        
        if not ensure_ffmpeg_api_ready(timeout=10):
            error_msg = "FFmpeg API no disponible. No se puede procesar el audio."
            logger.error(f"[GROQ] {error_msg}")
            raise ConnectionError(error_msg)
        
        # Verificar GPU status (solo informativo)
        gpu_available, gpu_info = check_gpu_status()
        if gpu_available:
            logger.info(f"[GROQ] GPU disponible para procesamiento: {gpu_info.get('gpu_name')}")
        else:
            logger.info("[GROQ] GPU no disponible, usando CPU para procesamiento")
        
        return True

    def _validate_audio_file(self, audio_path: str) -> Dict[str, Any]:
        """
        Valida el archivo de audio antes de la transcripción.
        Lanza AudioValidationError si el audio no es válido.
        """
        logger.info(f"[GROQ] Validando audio: {audio_path}")
        
        try:
            validation = validate_audio(audio_path)
            
            logger.info(f"[GROQ] Validación completada: válido={validation['valid']}, óptimo={validation['optimal']}")
            
            if not validation['valid']:
                issues = validation.get('issues', [])
                non_length_issues = [
                    issue for issue in issues
                    if "demasiado largo" not in issue.lower() and "too long" not in issue.lower()
                ]

                if non_length_issues:
                    error_msg = f"Audio no válido: {', '.join(non_length_issues)}"
                    logger.error(f"[GROQ] {error_msg}")
                    raise AudioValidationError(error_msg, validation_result=validation)

                logger.warning(
                    "[GROQ] Audio marcado como inválido solo por duración; se continuará con la transcripción."
                )
                validation['valid'] = True
                validation['optimal'] = False
                validation['warnings'] = validation.get('warnings', []) + [
                    issue for issue in issues
                    if "demasiado largo" in issue.lower() or "too long" in issue.lower()
                ]

            if not validation['optimal']:
                warnings = validation.get('warnings', [])
                logger.warning(f"[GROQ] Audio no óptimo: {', '.join(warnings)}")
                recommendations = validation.get('recommendations', [])
                if recommendations:
                    logger.info(f"[GROQ] Recomendaciones: {', '.join(recommendations)}")
            
            return validation
            
        except requests.exceptions.RequestException as e:
            logger.error(f"[GROQ] Error validando audio: {e}")
            # Si no podemos validar, continuamos con advertencia pero no bloqueamos
            logger.warning("[GROQ] No se pudo validar el audio, continuando de todas formas")
            return {"valid": True, "optimal": False, "warnings": ["No se pudo validar el audio"]}
        except AudioValidationError:
            raise
        except Exception as e:
            logger.error(f"[GROQ] Error inesperado en validación: {e}")
            return {"valid": True, "optimal": False, "warnings": [f"Error en validación: {str(e)}"]}

    def ensure_wav(self, input_path: str) -> str:
        """
        Convierte el archivo a WAV 16kHz mono usando ffmpeg-api.
        """
        logger.info(f"[GROQ] ensure_wav: {input_path}")
        
        # Verificar archivo original
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Archivo no existe: {input_path}")
        
        original_size = os.path.getsize(input_path)
        logger.info(f"[GROQ] Archivo original: tamaño={original_size} bytes")
        
        # Verificar que FFmpeg API está disponible
        self._ensure_ffmpeg_api_ready()
        
        # Llamar a FFmpeg API usando la función centralizada
        try:
            wav_bytes = convert_audio(input_path, fmt="wav")
            
            if len(wav_bytes) < 1000:
                logger.error(f"[GROQ] ¡Audio convertido demasiado pequeño! {len(wav_bytes)} bytes")
                # Guardar para debug
                debug_path = "/tmp/debug_convert_failed.wav"
                with open(debug_path, "wb") as f:
                    f.write(wav_bytes)
                logger.error(f"[GROQ] Debug guardado en {debug_path}")
                
                # Verificar con ffprobe
                try:
                    result = subprocess.run(
                        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", debug_path],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        info = json.loads(result.stdout)
                        logger.error(f"[GROQ] ffprobe del archivo fallido: {info}")
                except Exception as e:
                    logger.error(f"[GROQ] Error verificando archivo fallido: {e}")
            
            tmp = tempfile.mktemp(suffix=".wav")
            with open(tmp, "wb") as f:
                f.write(wav_bytes)
            
            logger.info(f"[GROQ] WAV guardado en: {tmp}, tamaño={os.path.getsize(tmp)} bytes")
            return tmp
            
        except Exception as e:
            logger.error(f"[GROQ] Error en conversión: {e}")
            raise

    def clean_wav(self, wav_path: str) -> str:
        """Limpia el audio usando ffmpeg-api (/audio/clean)."""
        logger.info(f"[GROQ] clean_wav: {wav_path}")
        
        if not os.path.exists(wav_path):
            raise FileNotFoundError(f"WAV no existe: {wav_path}")
        
        wav_size = os.path.getsize(wav_path)
        logger.info(f"[GROQ] WAV a limpiar: tamaño={wav_size} bytes")
        
        try:
            cleaned_bytes = clean_audio(wav_path)
            
            if len(cleaned_bytes) < 1000:
                logger.error(f"[GROQ] ¡Audio limpiado demasiado pequeño! {len(cleaned_bytes)} bytes")
                debug_path = "/tmp/debug_clean_failed.wav"
                with open(debug_path, "wb") as f:
                    f.write(cleaned_bytes)
                logger.error(f"[GROQ] Debug guardado en {debug_path}")
            
            cleaned_path = tempfile.mktemp(suffix="_clean.wav")
            with open(cleaned_path, "wb") as f:
                f.write(cleaned_bytes)
            
            logger.info(f"[GROQ] WAV limpio guardado en: {cleaned_path}, tamaño={os.path.getsize(cleaned_path)} bytes")
            return cleaned_path
            
        except Exception as e:
            logger.error(f"[GROQ] Error en limpieza: {e}")
            raise

    def _send_file_to_groq(self, file_path: str, filename: str, content_type: str) -> Tuple[str, float]:
        """Envía un archivo de audio a Groq API y devuelve el texto transcrito y el tiempo de envío."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado para enviar a Groq: {file_path}")

        start = time.time()
        final_size = os.path.getsize(file_path)
        logger.info(f"[GROQ] Enviando {filename} a Groq: {file_path}, tamaño={final_size} bytes")

        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                info = json.loads(result.stdout)
                duration = float(info["format"].get("duration", 0))
                logger.info(f"[GROQ] Duración del audio a enviar: {duration:.2f} segundos")
                if duration < 0.5:
                    logger.error(f"[GROQ] ¡Audio demasiado corto! {duration:.2f} segundos")
                    raise Exception(f"Audio demasiado corto: {duration:.2f} segundos")
        except Exception as e:
            logger.warning(f"[GROQ] No se pudo verificar duración: {e}")

        with open(file_path, "rb") as f:
            logger.info(f"[GROQ] Enviando petición a Groq API...")
            resp = requests.post(
                self.URL,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                data={"model": self.MODEL},
                files={"file": (filename, f, content_type)},
                timeout=300
            )

        elapsed = time.time() - start
        logger.info(f"[GROQ] Respuesta status: {resp.status_code}")
        if resp.status_code != 200:
            logger.error(f"[GROQ] Error en respuesta: {resp.text}")
            resp.raise_for_status()

        text = resp.json().get("text", "").strip()
        logger.info(f"[GROQ] Texto recibido: '{text[:100]}...' (longitud: {len(text)} caracteres)")

        if not text:
            logger.warning(f"[GROQ] ¡Texto vacío recibido de Groq para {filename}!")
        elif len(text) < 10:
            logger.warning(f"[GROQ] Texto muy corto en {filename}: '{text}'")

        return text, elapsed

    def _send_to_groq(self, audio_path: str) -> Tuple[str, float]:
        return self._send_file_to_groq(audio_path, "audio.wav", "audio/wav")

    def _send_to_groq_mp3(self, mp3_path: str) -> Tuple[str, float]:
        return self._send_file_to_groq(mp3_path, "audio.mp3", "audio/mpeg")

    def _send_to_groq_chunks(self, chunk_paths: list[str]) -> Tuple[str, float]:
        """Envía varios MP3 chunks a Groq y concatena los resultados."""
        all_texts = []
        total_time = 0.0
        logger.info(f"[GROQ] Enviando {len(chunk_paths)} chunks a Groq... ")

        for idx, chunk_path in enumerate(chunk_paths, start=1):
            logger.info(f"[GROQ] Enviando chunk {idx}/{len(chunk_paths)}: {chunk_path}")
            text, elapsed = self._send_to_groq_mp3(chunk_path)
            all_texts.append(text)
            total_time += elapsed
            logger.info(f"[GROQ] Chunk {idx} completado en {elapsed:.2f}s")

        combined_text = "\n".join([t for t in all_texts if t])
        logger.info(f"[GROQ] Texto combinado de chunks: {len(combined_text)} caracteres")
        return combined_text, total_time

    def _cleanup_chunked_files(self, chunked: dict) -> None:
        """Elimina archivos temporales generados por el endpoint chunked."""
        chunks = chunked.get("chunks", []) or []
        original_mp3 = chunked.get("original_mp3")

        for chunk_path in chunks:
            try:
                if chunk_path and os.path.exists(chunk_path):
                    os.unlink(chunk_path)
                    logger.info(f"[GROQ] Eliminado chunk temporal: {chunk_path}")
            except Exception as e:
                logger.warning(f"[GROQ] No se pudo eliminar chunk temporal {chunk_path}: {e}")

        if original_mp3:
            try:
                if os.path.exists(original_mp3):
                    os.unlink(original_mp3)
                    logger.info(f"[GROQ] Eliminado MP3 original temporal: {original_mp3}")
            except Exception as e:
                logger.warning(f"[GROQ] No se pudo eliminar MP3 temporal {original_mp3}: {e}")

    def transcribe(self, audio_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Transcribe un archivo de audio usando Groq Whisper.
        
        Args:
            audio_path: Ruta al archivo de audio
            
        Returns:
            Tuple con (texto_transcrito, metadata)
        """
        if not GROQ_API_KEY:
            raise RuntimeError("Falta GROQ_API_KEY")

        logger.info(f"[GROQ] Iniciando transcripción: {audio_path}")
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio no encontrado: {audio_path}")
        
        original_size = os.path.getsize(audio_path)
        logger.info(f"[GROQ] Audio original: {audio_path}, tamaño={original_size} bytes")

        # Verificar FFmpeg API antes de empezar
        self._ensure_ffmpeg_api_ready()
        
        # Validar audio (si no se omite)
        if not self.skip_validation:
            try:
                validation = self._validate_audio_file(audio_path)
                logger.info(f"[GROQ] Validación exitosa: {validation.get('metadata', {}).get('duration_seconds', 0)}s")
            except AudioValidationError as e:
                logger.error(f"[GROQ] Validación fallida: {e}")
                raise

        # Decidir si usar el nuevo endpoint de chunked MP3.
        # Algunas fuentes comprimidas pueden estar por debajo de 25MB en disco,
        # pero el WAV interno crece y supera el límite de Groq.
        transcription_time = 0.0
        chunked = None
        wav = None
        cleaned_wav = None
        chunked_attempted = False

        try:
            if original_size > 25 * 1024 * 1024:
                chunked_attempted = True
                chunked = convert_to_mp3_chunked(audio_path, max_size_mb=22)

            if chunked is None or not chunked.get("chunks"):
                # Convertir a WAV y comprobar su tamaño real antes de enviar a Groq.
                wav = self.ensure_wav(audio_path)
                wav_size = os.path.getsize(wav)
                logger.info(f"[GROQ] WAV temporal generado: {wav} tamaño={wav_size} bytes")

                if wav_size > 25 * 1024 * 1024:
                    chunked_attempted = True
                    logger.info("[GROQ] WAV temporal excede 25MB, usando chunked MP3 en su lugar")
                    chunked = convert_to_mp3_chunked(audio_path, max_size_mb=22)

            if chunked and chunked.get("chunks"):
                chunks = chunked.get("chunks", [])
                logger.info(f"[GROQ] Usando chunked MP3 para audio grande: {len(chunks)} fragments")
                if len(chunks) == 1:
                    text, transcription_time = self._send_to_groq_mp3(chunks[0])
                else:
                    text, transcription_time = self._send_to_groq_chunks(chunks)

                return text, {
                    "engine": "groq-whisper",
                    "model": self.MODEL,
                    "transcription_time": transcription_time,
                    "audio_duration": None,
                }

            if chunked_attempted and (chunked is None or not chunked.get("chunks")):
                logger.warning("[GROQ] No se pudieron obtener chunks válidos; continuando con el flujo WAV tradicional")

            # Si no usamos chunked, continuamos con el flujo WAV normal.
            if wav is None:
                wav = self.ensure_wav(audio_path)

            logger.info(f"[GROQ] Paso 1 completado: WAV en {wav}")

            try:
                cleaned_wav = self.clean_wav(wav)
                logger.info(f"[GROQ] Paso 2 completado: Audio limpio en {cleaned_wav}")
                audio_to_send = cleaned_wav
            except Exception as e:
                logger.warning(f"[GROQ] No se pudo limpiar el audio, usando WAV original: {e}")
                audio_to_send = wav

            text, transcription_time = self._send_to_groq(audio_to_send)

            return text, {
                "engine": "groq-whisper",
                "model": self.MODEL,
                "transcription_time": transcription_time,
                "audio_duration": None,  # Se podría calcular si se quiere
            }
        except Exception as e:
            logger.error(f"[GROQ] Error en transcripción: {e}", exc_info=True)
            raise
        finally:
            if chunked:
                self._cleanup_chunked_files(chunked)
            for tmp_file in [wav, cleaned_wav]:
                if tmp_file and os.path.exists(tmp_file):
                    try:
                        os.unlink(tmp_file)
                        logger.info(f"[GROQ] Eliminado temporal: {tmp_file}")
                    except Exception as e:
                        logger.warning(f"[GROQ] No se pudo eliminar {tmp_file}: {e}")
        
        try:
            # 1. Convertir a WAV estándar
            wav = self.ensure_wav(audio_path)
            logger.info(f"[GROQ] Paso 1 completado: WAV en {wav}")

            # 2. Limpiar audio (opcional pero recomendado)
            # Nota: La limpieza puede fallar si hay problemas con el audio, pero no es crítica
            try:
                cleaned_wav = self.clean_wav(wav)
                logger.info(f"[GROQ] Paso 2 completado: Audio limpio en {cleaned_wav}")
                audio_to_send = cleaned_wav
            except Exception as e:
                logger.warning(f"[GROQ] No se pudo limpiar el audio, usando WAV original: {e}")
                audio_to_send = wav

            # 3. Enviar a Groq
            text, transcription_time = self._send_to_groq(audio_to_send)

            return text, {
                "engine": "groq-whisper",
                "model": self.MODEL,
                "transcription_time": transcription_time,
                "audio_duration": None,  # Se podría calcular si se quiere
            }
            
        except Exception as e:
            logger.error(f"[GROQ] Error en transcripción: {e}", exc_info=True)
            raise
        finally:
            # Limpiar archivos temporales
            for tmp_file in [wav, cleaned_wav]:
                if tmp_file and os.path.exists(tmp_file):
                    try:
                        os.unlink(tmp_file)
                        logger.info(f"[GROQ] Eliminado temporal: {tmp_file}")
                    except Exception as e:
                        logger.warning(f"[GROQ] No se pudo eliminar {tmp_file}: {e}")