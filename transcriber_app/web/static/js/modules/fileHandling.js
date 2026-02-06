/**
 * Módulo de manejo de archivos de audio
 * Descarga, carga y eliminación de archivos
 */

import { elements } from "./domElements.js";
import { getFormName, validateForm } from "./form.js";
import { disableRecordingWithTooltip, enableRecordingAndClearTooltip, setStatusText } from "./ui.js";

/**
 * Descarga la grabación actual como archivo MP3
 */
function downloadRecording(lastRecordingBlob) {
    if (!lastRecordingBlob) return;

    const nombre = getFormName() || "grabacion";
    const url = URL.createObjectURL(lastRecordingBlob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `${nombre}.mp3`;
    a.click();

    URL.revokeObjectURL(url);
}

/**
 * Elimina la grabación actual
 */
function deleteRecording(callback) {
    if (!callback) {
        console.error("Callback requerido para deleteRecording");
        return;
    }

    if (!confirm("¿Seguro que quieres borrar la grabación? Esta acción no se puede deshacer.")) {
        return;
    }

    // Limpiar UI
    if (elements.preview) {
        elements.preview.src = "";
        elements.preview.hidden = true;
    }

    if (elements.sendBtn) elements.sendBtn.disabled = true;
    if (elements.deleteBtn) elements.deleteBtn.disabled = true;
    if (elements.downloadBtn) elements.downloadBtn.disabled = true;
    if (elements.recordBtn) elements.recordBtn.disabled = false;

    setStatusText("Grabación borrada.");

    enableRecordingAndClearTooltip();

    // Llamar callback para que limpie el estado
    callback();
}

/**
 * Abre el selector de archivos
 */
function triggerFileInput() {
    elements.fileInput?.click();
}

/**
 * Procesa un archivo seleccionado
 */
function handleFileUpload(file, callback) {
    if (!file || !callback) return;

    const url = URL.createObjectURL(file);
    if (elements.preview) {
        elements.preview.src = url;
        elements.preview.hidden = false;
    }

    validateForm(file);
    if (elements.deleteBtn) elements.deleteBtn.disabled = false;
    if (elements.downloadBtn) elements.downloadBtn.disabled = false;
    if (elements.recordBtn) elements.recordBtn.disabled = true;

    disableRecordingWithTooltip();
    setStatusText(`Grabación cargada: ${file.name}`);

    callback(file);
}

/**
 * Prepara la preview de audio
 */
function displayAudioPreview(blob) {
    if (!blob || !elements.preview) return;

    const url = URL.createObjectURL(blob);
    elements.preview.src = url;
    elements.preview.hidden = false;
}

/**
 * Limpia la preview de audio
 */
function clearAudioPreview() {
    if (elements.preview) {
        elements.preview.src = "";
        elements.preview.hidden = true;
    }
}

export {
    clearAudioPreview, deleteRecording, displayAudioPreview, downloadRecording, handleFileUpload, triggerFileInput
};

