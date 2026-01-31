# transcriber_app/runner/orchestrator.py
import os
from transcriber_app.modules.logging.logging_config import setup_logging
from transcriber_app.modules.ai.ai_manager import AIManager, log_agent_result

# Logging
logger = setup_logging("transcribeapp")


class Orchestrator:
    def __init__(self, receiver, transcriber, formatter):
        self.receiver = receiver
        self.transcriber = transcriber
        self.formatter = formatter
        logger.info("[ORCHESTRATOR] Orchestrator inicializado con componentes (Agno activado).")

    def run_audio(self, audio_path, mode="default"):
        logger.info(f"[ORCHESTRATOR] Ejecutando flujo de audio para: {audio_path} con modo: {mode}")

        # 1. Cargar audio
        audio_info = self.receiver.load(audio_path)

        # 2. Transcribir
        text = self.transcriber.transcribe(audio_info["path"])

        # 3. Guardar transcripción
        self.formatter.save_transcription(audio_info["name"], text)

        # 4. Resumir con Agno
        summary_output = AIManager.summarize(text, mode)

        # Log en consola
        log_agent_result(summary_output)

        # Guardar métricas en outputs/metrics/*.json
        self.formatter.save_metrics(audio_info["name"], summary_output, mode)

        # Guardar salida final
        return self.formatter.save_output(audio_info["name"], summary_output, mode)

    def run_text(self, text_path, mode="default"):
        logger.info(f"[ORCHESTRATOR] Ejecutando flujo de texto para: {text_path} con modo: {mode}")

        name = os.path.splitext(os.path.basename(text_path))[0]

        # 1. Leer texto
        with open(text_path, "r", encoding="utf-8") as f:
            text = f.read()

        # 2. Resumir con Agno
        summary_output = AIManager.summarize(text, mode)

        # 2.1 Log del agente
        log_agent_result(summary_output)

        # 3. Guardar salida
        return self.formatter.save_output(name, summary_output, mode)
