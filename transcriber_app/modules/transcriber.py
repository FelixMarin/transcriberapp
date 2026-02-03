import os
import tempfile
import subprocess
import time
import gc
from typing import Tuple, Optional, Dict, Any
from faster_whisper import WhisperModel


def ensure_wav(input_path: str) -> str:
    """
    Convierte cualquier formato de audio a WAV mono 16 kHz usando ffmpeg.
    Optimizado para Jetson.
    """
    tmp_wav = tempfile.mktemp(suffix=".wav")
    is_jetson = os.path.exists('/etc/nv_tegra_release')

    cmd = [
        "ffmpeg", "-y", "-nostdin", "-loglevel", "error",
        "-i", input_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
    ]

    # Aceleración solo si el archivo es vídeo
    if is_jetson and input_path.lower().endswith((".mp4", ".mkv", ".mov", ".avi")):
        cmd.insert(1, "-hwaccel")
        cmd.insert(2, "cuda")
        cmd.insert(3, "-hwaccel_output_format")
        cmd.insert(4, "cuda")

    cmd.append(tmp_wav)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"Error extrayendo audio: {result.stderr[:200]}")

    return tmp_wav


class Transcriber:
    PRESETS = {
        "jetson_fast": {
            "device": "cuda",
            "compute_type": "int8_float16",
            "beam_size": 3,
            "best_of": 1,
            "num_workers": 1,
            "vad_filter": True,
            "vad_parameters": {"min_silence_duration_ms": 500, "speech_pad_ms": 200}
        },
        "jetson_balanced": {
            "device": "cuda",
            "compute_type": "int8_float16",
            "beam_size": 4,
            "best_of": 1,
            "num_workers": 1,
            "vad_filter": True,
            "vad_parameters": {"min_silence_duration_ms": 300, "speech_pad_ms": 100}
        },
        "jetson_accurate": {
            "device": "cuda",
            "compute_type": "float16",
            "beam_size": 6,
            "best_of": 1,
            "num_workers": 1,
            "vad_filter": True,
            "temperature": [0.0, 0.2, 0.4, 0.6],
            "vad_parameters": {"min_silence_duration_ms": 200, "speech_pad_ms": 50}
        }
    }

    def __init__(self, model_size: str = "base", preset: str = "jetson_balanced"):
        self.model_size = model_size
        self.preset = preset
        self.is_jetson = os.path.exists('/etc/nv_tegra_release')

        config = self.PRESETS.get(preset, self.PRESETS["jetson_balanced"]).copy()

        print("🚀 Inicializando Transcriber")
        print(f"   Modelo: {model_size}")
        print(f"   Preset: {preset}")

        # Ajuste automático para CPU
        if not self.is_jetson:
            config["device"] = "cpu"
            config["compute_type"] = "int8"
            print("   ⚠️ Ejecutando en CPU")

        # Ajuste automático según tamaño del modelo
        if model_size in ("base", "small", "medium") and config["compute_type"] == "float16":
            config["compute_type"] = "int8_float16"

        print(f"   Dispositivo: {config['device']}")
        print(f"   Compute type: {config['compute_type']}")

        # Cargar modelo
        self.model = WhisperModel(
            model_size,
            device=config["device"],
            compute_type=config["compute_type"],
            num_workers=config["num_workers"]
        )

        # Configuración de transcripción
        self.transcribe_config = {
            "beam_size": config.get("beam_size", 4),
            "best_of": config.get("best_of", 1),
            "vad_filter": config.get("vad_filter", True),
            "vad_parameters": config.get("vad_parameters", {}),
            "temperature": config.get("temperature", [0.0]),
            "compression_ratio_threshold": 2.4,
            "log_prob_threshold": -1.0,
            "no_speech_threshold": 0.6,
            "condition_on_previous_text": False,  # evita repeticiones
        }

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        start_time = time.time()

        try:
            wav_path = ensure_wav(audio_path)
            audio_size = os.path.getsize(wav_path) / (1024 * 1024)
            print(f"📁 Procesando audio: {audio_size:.1f} MB")

            segments, info = self.model.transcribe(
                wav_path,
                language=language,
                task="transcribe",
                **self.transcribe_config
            )

            texts = []
            segment_times = []

            for seg in segments:
                texts.append(seg.text)
                segment_times.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text.strip()
                })

            text = " ".join(texts).strip()

            elapsed = time.time() - start_time
            cps = len(text) / elapsed if elapsed > 0 else 0

            metadata = {
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "transcription_time": elapsed,
                "chars_per_second": cps,
                "model_size": self.model_size,
                "preset": self.preset,
                "segments": segment_times,
                "device": self.model.device,
                "compute_type": self.model.compute_type,
            }

            os.unlink(wav_path)
            gc.collect()

            print(f"✅ Transcripción completada en {elapsed:.1f}s")
            print(f"   Idioma: {info.language} ({info.language_probability:.2f})")
            print(f"   Velocidad: {cps:.1f} cps")

            return text, metadata

        except Exception as e:
            # Intentar borrar el WAV temporal solo si existe
            try:
                if wav_path and os.path.exists(wav_path):
                    os.unlink(wav_path)
            except OSError:
                # Solo ignoramos errores específicos del sistema de archivos
                pass

            raise RuntimeError(f"Error en transcripción: {e}") from e

    def get_available_models(self) -> Dict[str, str]:
        models = {
            "tiny": "~1GB RAM",
            "base": "~1.5GB RAM",
            "small": "~3GB RAM",
            "medium": "~5GB RAM",
            "large": "~10GB RAM",
            "large-v2": "~10GB RAM",
            "large-v3": "~10GB RAM",
        }

        if self.is_jetson:
            return {m: mem for m, mem in models.items() if m in ("tiny", "base", "small")}

        return models

    def benchmark(self, test_audio_path: str) -> Dict[str, Any]:
        results = {}

        for preset_name in self.PRESETS.keys():
            print(f"\n🔧 Probando preset: {preset_name}")

            try:
                temp = Transcriber(self.model_size, preset_name)
                start = time.time()
                text, meta = temp.transcribe(test_audio_path)
                elapsed = time.time() - start

                results[preset_name] = {
                    "time": elapsed,
                    "chars_per_second": meta["chars_per_second"],
                    "language": meta["language"],
                    "device": meta["device"],
                    "compute_type": meta["compute_type"]
                }

                print(f"   Tiempo: {elapsed:.1f}s, CPS: {meta['chars_per_second']:.1f}")

            except Exception as e:
                results[preset_name] = {"error": str(e)}
                print(f"   ❌ Error: {e}")

        return results
