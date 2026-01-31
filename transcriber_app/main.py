# transcriber_app/main.py
import os
import sys

from transcriber_app.modules.audio_receiver import AudioReceiver
from transcriber_app.modules.transcriber import Transcriber
from transcriber_app.modules.output_formatter import OutputFormatter
from transcriber_app.runner.orchestrator import Orchestrator
from transcriber_app.config import AVAILABLE_MODES


def mostrar_ayuda():
    print("\n=== TranscriberApp ===")
    print("Procesa audios (.mp3) o textos (.txt) y genera resúmenes con distintos modos.\n")

    print("USO:")
    print("  python -m transcriber_app.main [audio|texto] [nombre] [modo]\n")

    print("PARÁMETROS:")
    print("  audio        Procesa un archivo .mp3 desde la carpeta 'audios/'")
    print("  texto        Procesa un archivo .txt desde la carpeta 'transcripts/'")
    print("  nombre       Nombre del archivo SIN extensión")
    print("  modo         Tipo de resumen a generar\n")

    print("MODOS DISPONIBLES:")
    for m in AVAILABLE_MODES:
        print(f"  - {m}")
    print()

    print("EJEMPLOS:")
    print("  Procesar audio:")
    print("    python -m transcriber_app.main audio reunion1 tecnico")
    print("    (usa audios/reunion1.mp3)\n")

    print("  Procesar texto:")
    print("    python -m transcriber_app.main texto sprint1 refinamiento")
    print("    (usa transcripts/sprint1.txt)\n")

    print("SALIDA:")
    print("  - La transcripción (si es audio) se guarda en: transcripts/<nombre>.txt")
    print("  - El resumen final se guarda en: outputs/<nombre>_<modo>.md\n")


def main():

    # ============================
    #   VALIDACIÓN DE ARGUMENTOS
    # ============================
    if len(sys.argv) < 4:
        mostrar_ayuda()
        return

    input_type = sys.argv[1].lower()
    base_name = sys.argv[2]
    mode = sys.argv[3].lower()

    if mode not in AVAILABLE_MODES:
        print(f"❌ Modo no válido: {mode}\n")
        mostrar_ayuda()
        return

    # ============================
    #   RESOLVER RUTA SEGÚN TIPO
    # ============================
    if input_type == "audio":
        if not base_name.endswith(".mp3"):
            base_name += ".mp3"
        path = os.path.join("audios", base_name)

    elif input_type == "texto":
        if not base_name.endswith(".txt"):
            base_name += ".txt"
        path = os.path.join("transcripts", base_name)

    else:
        print("❌ Primer parámetro debe ser 'audio' o 'texto'\n")
        mostrar_ayuda()
        return

    if not os.path.exists(path):
        print(f"❌ No existe el archivo: {path}\n")
        return

    # ============================
    #   INICIALIZAR PIPELINE
    # ============================
    receiver = AudioReceiver()
    transcriber = Transcriber()
    formatter = OutputFormatter()

    # Nuevo Orchestrator sin summarizer
    orchestrator = Orchestrator(receiver, transcriber, formatter)

    # ============================
    #   EJECUTAR PIPELINE
    # ============================
    try:
        if input_type == "audio":
            output = orchestrator.run_audio(path, mode)
        else:
            output = orchestrator.run_text(path, mode)

    except ValueError as e:
        print(f"[BAD_AUDIO] {e}")
        sys.exit(3)

    print(output)


if __name__ == "__main__":
    main()
