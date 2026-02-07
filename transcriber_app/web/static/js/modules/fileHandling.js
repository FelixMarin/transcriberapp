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
    const extension = lastRecordingBlob.type.split("/")[1]?.split(";")[0] || "webm";
    a.download = `${nombre}.${extension}`;
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
    if (elements.previewContainer) {
        elements.previewContainer.hidden = true;
    }
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
    if (!blob || !elements.preview || !elements.previewContainer) return;

    const url = URL.createObjectURL(blob);

    // 1. Mostrar contenedor principal
    elements.previewContainer.removeAttribute("hidden");
    elements.previewContainer.hidden = false;
    elements.previewContainer.style.display = "block";

    // 2. Refrescar elemento de audio (recrear source para forzar al motor del navegador)
    elements.preview.innerHTML = "";
    const source = document.createElement("source");
    source.src = url;
    source.type = blob.type;
    elements.preview.appendChild(source);

    elements.preview.load();
    elements.preview.controls = true;
    elements.preview.removeAttribute("hidden");
    elements.preview.hidden = false;

    // 3. Información de depuración (útil para el usuario móvil)
    if (elements.debugArea) {
        elements.debugArea.removeAttribute("hidden");
        elements.debugArea.hidden = false;
        elements.debugArea.textContent = `Blob: ${blob.size} bytes | Type: ${blob.type}\nURL: ${url.substring(0, 50)}...`;
    }

    console.log("📺 Preview de audio actualizado (Robust):", url, `(${blob.type}, ${blob.size} bytes)`);
}

/**
 * Limpia la preview de audio
 */
function clearAudioPreview() {
    if (elements.previewContainer) {
        elements.previewContainer.hidden = true;
    }
    if (elements.preview) {
        elements.preview.src = "";
        elements.preview.hidden = true;
    }
}

export {
    clearAudioPreview, deleteRecording, displayAudioPreview, downloadRecording, handleFileUpload, triggerFileInput
};

