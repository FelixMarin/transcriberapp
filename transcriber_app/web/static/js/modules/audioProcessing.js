/**
 * Módulo de procesamiento de audio
 * Gestiona el flujo de grabación, envío y polling
 */

import {
    checkJobStatus,
    loadMarkdownResult,
    loadTranscriptionFile,
    uploadAudio
} from "./api.js";
import { elements } from "./domElements.js";
import {
    hideOverlay,
    setStatusText,
    toggleTranscriptionSection
} from "./ui.js";
import { getStatusMessage, parseMarkdown } from "./utils.js";

/**
 * Inicia el polling del estado de un job
 */
function startJobPolling(jobId, onComplete, onError) {
    const checkStatus = async () => {
        try {
            const data = await checkJobStatus(jobId);

            setStatusText(getStatusMessage(data.status));

            if (data.status === "processing" || data.status === "running") {
                setTimeout(checkStatus, 3000);
                return;
            }

            if (data.status === "bad_audio") {
                hideOverlay();
                alert("La grabación tiene mala calidad y no se ha podido transcribir.");
                if (onError) onError("bad_audio");
                return;
            }

            if (data.status === "done") {
                handleJobCompletion(data, onComplete);
            }

            hideOverlay();
        } catch (error) {
            console.error("Error en polling:", error);
            hideOverlay();
            if (onError) onError(error);
        }
    };

    checkStatus();
}

/**
 * Maneja la finalización de un job
 */
async function handleJobCompletion(data, onComplete) {
    let md = data.markdown || data.resultado || data.md || data.resultado_md;

    // Obtener nombre y modo para cargar resultados
    const nombre = document.getElementById("nombre")?.value?.trim() || "";
    const modo = document.getElementById("modo")?.value || "";

    // Si no viene el markdown en la respuesta, lo cargamos explícitamente (solo para retrocompatibilidad/CLI)
    if (!md && nombre && modo) {
        try {
            md = await loadMarkdownResult(nombre, modo);
        } catch (e) {
            console.warn("No se pudo cargar el markdown desde el servidor, se usará el del job si existe.");
        }
    }

    // Cargar transcripción original (prioridad a la que viene en data)
    let transcriptionText = data.transcription;

    if (!transcriptionText && nombre) {
        try {
            transcriptionText = await loadTranscriptionFile(nombre);
        } catch (e) {
            console.warn("No se pudo cargar la transcripción desde el servidor.");
        }
    }

    if (transcriptionText && elements.transcripcionTexto) {
        elements.transcripcionTexto.innerHTML = parseMarkdown(transcriptionText);
        toggleTranscriptionSection(true);
    }

    if (onComplete) {
        // Asegurar que pasamos el markdown recuperado, incluso si vino por fetch separado
        onComplete({ ...data, markdown: md });
    }
}

/**
 * Procesa un nuevo archivo de grabación
 */
async function processNewRecording(audioBlob, nombre, email, modo, onJobStarted, onJobCompleted, onError) {
    const result = await uploadAudio(audioBlob, nombre, modo, email);

    if (!result.success) {
        hideOverlay();
        alert(result.error);
        setStatusText("Error: " + result.error);
        if (onError) onError(result.error);
        return;
    }

    if (result.jobId) {
        if (onJobStarted) onJobStarted();
        startJobPolling(result.jobId, onJobCompleted, onError);
    }
}

export {
    handleJobCompletion,
    processNewRecording, startJobPolling
};

