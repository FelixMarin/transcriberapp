/**
 * Módulo de grabación de audio
 * Gestión del micrófono y grabación de audio
 */

import { elements } from "./domElements.js";
import { setRecordingButtonState, setStatusText } from "./ui.js";

let mediaRecorder;
let audioChunks = [];

/**
 * Inicia una nueva grabación de audio
 */
async function startRecording() {
    audioChunks = [];

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

        mediaRecorder.start();
        setStatusText("Grabando…");

        if (elements.recordBtn) {
            elements.recordBtn.disabled = true;
            elements.recordBtn.title = "Grabación en curso";
            setRecordingButtonState(true);
        }
        if (elements.stopBtn) elements.stopBtn.disabled = false;
        if (elements.uploadBtn) elements.uploadBtn.disabled = true;
        if (elements.deleteBtn) elements.deleteBtn.disabled = true;
        if (elements.downloadBtn) elements.downloadBtn.disabled = true;

    } catch (error) {
        console.error("Error al acceder al micrófono:", error);
        alert("No se pudo acceder al micrófono. Verifica los permisos.");
    }
}

/**
 * Detiene la grabación actual
 */
function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        setStatusText("Grabación finalizada.");

        if (elements.recordBtn) {
            setRecordingButtonState(false);
        }
        if (elements.stopBtn) elements.stopBtn.disabled = true;
    }
}

/**
 * Obtiene el Blob del audio grabado
 */
function getRecordingBlob() {
    if (audioChunks.length === 0) return null;
    return new Blob(audioChunks, { type: "audio/mp3" });
}

/**
 * Limpia los chunks de audio
 */
function clearAudioChunks() {
    audioChunks = [];
}

/**
 * Obtiene la duración de un blob de audio
 */
async function getAudioDuration(blob) {
    return new Promise((resolve) => {
        const audio = new Audio();
        audio.src = URL.createObjectURL(blob);
        audio.onloadedmetadata = () => {
            resolve(audio.duration);
        };
        audio.onerror = () => {
            resolve(null);
        };
    });
}

export {
    clearAudioChunks,
    getAudioDuration, getRecordingBlob, startRecording,
    stopRecording
};

