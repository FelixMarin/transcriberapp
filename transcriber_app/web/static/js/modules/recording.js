/**
 * Módulo de grabación de audio
 * Gestión del micrófono y grabación de audio
 */

import { elements } from "./domElements.js";
import { setRecordingButtonState, setStatusText } from "./ui.js";

let mediaRecorder;
let audioChunks = [];
let recordedMimeType = "audio/mp3"; // Default fallback

/**
 * Inicia una nueva grabación de audio
 */
async function startRecording() {
    audioChunks = [];

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        // Detectar si es móvil (especialmente Android) para priorizar formatos más seguros
        const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
        const isAndroid = /Android/i.test(navigator.userAgent);

        // Detectar MIME type compatible
        const mimeTypes = isAndroid
            ? ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/aac"] // Android prefiere WebM
            : ["audio/mp4", "audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/aac"];

        recordedMimeType = mimeTypes.find(type => MediaRecorder.isTypeSupported(type)) || "audio/webm";
        console.log("🧩 MIME type seleccionado:", recordedMimeType, isMobile ? "(Mobile context)" : "(Desktop context)");

        mediaRecorder = new MediaRecorder(stream, { mimeType: recordedMimeType });

        mediaRecorder.ondataavailable = e => {
            if (e.data && e.data.size > 0) {
                audioChunks.push(e.data);
                console.log(`📦 Chunk recibido: ${e.data.size} bytes`);
            } else {
                console.warn("⚠️ Chunk de audio vacío recibido");
            }
        };

        // Iniciar grabación con chunks periódicos (1s) para mejorar estabilidad en móviles
        mediaRecorder.start(1000);
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
 * Detiene la grabación actual y espera a que el MediaRecorder termine
 * @returns {Promise<void>}
 */
async function stopRecording() {
    if (!mediaRecorder || mediaRecorder.state !== "recording") return;

    return new Promise((resolve) => {
        mediaRecorder.onstop = () => {
            console.log("⏹️ MediaRecorder detenido y chunks finalizados");
            setStatusText("Grabación finalizada.");
            if (elements.recordBtn) setRecordingButtonState(false);
            if (elements.stopBtn) elements.stopBtn.disabled = true;
            resolve();
        };

        mediaRecorder.stop();
        console.log("⏹️ Grabación detenida");
    });
}

/**
 * Obtiene el Blob del audio grabado
 */
function getRecordingBlob() {
    if (audioChunks.length === 0) {
        console.warn("⚠️ No hay chunks de audio para crear el blob");
        return null;
    }
    const blob = new Blob(audioChunks, { type: recordedMimeType });
    console.log(`📊 Blob final generado: ${blob.size} bytes (${blob.type})`);

    if (blob.size === 0) {
        console.error("❌ ERROR CRÍTICO: El blob de grabación está vacío. Posible incompatibilidad de hardware con el MIME type.");
        alert("Error: La grabación está vacía. Intenta recargar la página o usar otro navegador.");
    }

    return blob;
}

/**
 * Limpia los chunks de audio
 */
function clearAudioChunks() {
    audioChunks = [];
}

/**
 * Obtiene la duración de un blob de audio con timeout
 */
async function getAudioDuration(blob) {
    if (!blob) return null;

    return new Promise((resolve) => {
        const audio = new Audio();
        const url = URL.createObjectURL(blob);

        // Timeout de seguridad por si el navegador no puede procesar el blob
        const timeout = setTimeout(() => {
            console.warn("⏱️ Timeout cargando metadatos de audio");
            URL.revokeObjectURL(url);
            resolve(null);
        }, 2000);

        audio.src = url;
        audio.onloadedmetadata = () => {
            clearTimeout(timeout);
            const duration = audio.duration;
            URL.revokeObjectURL(url);
            resolve(duration);
        };
        audio.onerror = () => {
            clearTimeout(timeout);
            console.error("❌ Error cargando el audio para duración");
            URL.revokeObjectURL(url);
            resolve(null);
        };
    });
}

export {
    clearAudioChunks,
    getAudioDuration, getRecordingBlob, startRecording,
    stopRecording
};

