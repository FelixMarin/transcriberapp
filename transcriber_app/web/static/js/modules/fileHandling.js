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
        elements.previewContainer.style.display = "none";
    }
    if (elements.preview) {
        elements.preview.src = "";
        elements.preview.style.display = "none";
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

    displayAudioPreview(file);

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
    if (!blob) return;

    // Búsqueda directa para evitar condiciones de carrera en móviles
    const container = document.getElementById("previewContainer");

    if (!container) {
        console.error("❌ previewContainer no encontrado");
        return;
    }

    const url = URL.createObjectURL(blob);

    // 1. Mostrar contenedor principal (CSS-only approach for better desktop/mobile compatibility)
    container.style.display = "block";
    container.style.opacity = "1";
    container.style.visibility = "visible";

    // 2. REEMPLAZO TOTAL DEL NODO (Forzar render en Chrome Android y asegurar visibilidad en Desktop)
    const oldAudio = document.getElementById("preview");
    if (oldAudio) {
        oldAudio.remove();
    }

    const newAudio = document.createElement("audio");
    newAudio.id = "preview";
    newAudio.controls = true;
    newAudio.preload = "auto";
    newAudio.className = "audio-preview";
    newAudio.style.display = "block"; // Asegurar que el elemento audio sea tratado como bloque
    newAudio.ariaLabel = "Previsualización del audio grabado";

    const source = document.createElement("source");
    source.src = url;
    source.type = blob.type;
    newAudio.appendChild(source);

    container.appendChild(newAudio);

    newAudio.load();

    console.log("📺 Preview de audio listo:", url);
}

/**
 * Limpia la preview de audio
 */
function clearAudioPreview() {
    if (elements.previewContainer) {
        elements.previewContainer.style.display = "none";
    }
    if (elements.preview) {
        elements.preview.src = "";
        elements.preview.style.display = "none";
    }
}

export {
    clearAudioPreview, deleteRecording, displayAudioPreview, downloadRecording, handleFileUpload, triggerFileInput
};

