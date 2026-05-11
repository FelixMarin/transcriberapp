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
    disableUploadControls,
    enableUploadControls,
    hideCancelButton,
    hideProgressBar,
    setProgressBar,
    setStatusText,
    showCancelButton,
    showProgressBar,
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

            const displayText = data.message || getStatusMessage(data.status);
            setStatusText(displayText);

            if (data.status === "processing" || data.status === "running") {
                setTimeout(checkStatus, 3000);
                return;
            }

            if (data.status === "bad_audio") {
                hideProgressBar();
                hideCancelButton();
                alert("La grabación tiene mala calidad y no se ha podido transcribir.");
                if (onError) onError("bad_audio");
                return;
            }

            if (data.status === "done") {
                handleJobCompletion(data, onComplete);
            }

            hideProgressBar();
            hideCancelButton();
        } catch (error) {
            console.error("Error en polling:", error);
            hideProgressBar();
            hideCancelButton();
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
    console.log(`[PROCESS NEW] Iniciando procesamiento de grabación:`);
    console.log(`  Nombre: ${nombre}`);
    console.log(`  Modo: ${modo}`);
    console.log(`  Email: ${email}`);
    console.log(`  Tamaño blob: ${(audioBlob.size / 1024 / 1024).toFixed(2)} MB`);

    showProgressBar();
    setProgressBar(0);
    setStatusText("Preparando subida...");
    showCancelButton();
    disableUploadControls();

    let result;
    try {
        result = await uploadAudio(audioBlob, nombre, modo, email);
    } catch (err) {
        // Cancelación u otro error durante la subida
        enableUploadControls(!!audioBlob);
        hideProgressBar();
        hideCancelButton();
        if (err?.name !== "AbortError") {
            setStatusText("Error en la subida.");
            if (onError) onError(err);
        } else {
            setStatusText("Subida cancelada.");
        }
        return;
    }

    if (!result.success) {
        enableUploadControls(!!audioBlob);
        hideProgressBar();
        hideCancelButton();
        alert(result.error);
        setStatusText("Error: " + result.error);
        console.error(`[PROCESS NEW] Falló subida: ${result.error}`);
        if (onError) onError(result.error);
        return;
    }

    if (result.jobId) {
        console.log(`[PROCESS NEW] Subida exitosa. Job ID: ${result.jobId}. Iniciando polling...`);
        setStatusText("Subida completada. Procesando...");
        hideCancelButton();
        // Durante el procesamiento backend los botones de audio se pueden usar (el fichero ya está en el servidor)
        enableUploadControls(!!audioBlob);
        if (onJobStarted) onJobStarted();
        startJobPolling(result.jobId, onJobCompleted, onError);
    }
}

export {
    handleJobCompletion,
    processNewRecording, startJobPolling
};

