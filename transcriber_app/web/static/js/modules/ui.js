/**
 * Módulo de UI/UX
 * Funciones para manipular la interfaz visual
 */

import { elements, getSectionElements } from "./domElements.js";

/**
 * Muestra el overlay de carga (deprecado - mantenido para compatibilidad)
 */
function showOverlay() {
    if (elements.overlayLoading) {
        elements.overlayLoading.classList.remove("hidden");
    }
}

/**
 * Oculta el overlay de carga (deprecado - mantenido para compatibilidad)
 */
function hideOverlay() {
    if (elements.overlayLoading) {
        elements.overlayLoading.classList.add("hidden");
    }
}

/**
 * Muestra la barra de progreso
 */
function showProgressBar() {
    const container = document.getElementById("progressContainer");
    if (container) {
        container.classList.remove("hidden");
        setProgressBar(0);
    }
}

/**
 * Oculta la barra de progreso
 */
function hideProgressBar() {
    const container = document.getElementById("progressContainer");
    if (container) {
        container.classList.add("hidden");
    }
}

/**
 * Muestra el botón de cancelar subida
 */
function showCancelButton() {
    const btn = document.getElementById("cancelUploadBtn");
    if (btn) {
        btn.classList.remove("hidden");
        btn.disabled = false;
    }
}

/**
 * Oculta el botón de cancelar subida
 */
function hideCancelButton() {
    const btn = document.getElementById("cancelUploadBtn");
    if (btn) {
        btn.classList.add("hidden");
        btn.disabled = true;
    }
}

/**
 * Actualiza la barra de progreso
 * @param {number} percentage - Porcentaje de progreso (0-100)
 */
function setProgressBar(percentage) {
    const clampedPercentage = Math.min(100, Math.max(0, percentage));

    const progressBar = document.getElementById("progressBar");
    if (progressBar) {
        progressBar.style.width = `${clampedPercentage}%`;
    }

    const progressText = document.getElementById("progressText");
    if (progressText) {
        progressText.textContent = `${Math.round(clampedPercentage)}%`;
    }

    const progressContainer = document.getElementById("progressContainer");
    if (progressContainer) {
        progressContainer.setAttribute('aria-valuenow', clampedPercentage);
    }
}

/**
 * Limpia transcripciones y resultados
 */
function clearTranscriptionAndResults() {
    if (elements.transcripcionTexto) elements.transcripcionTexto.innerHTML = "";
    if (elements.resultContent) elements.resultContent.innerHTML = "";
}

/**
 * Deshabilita grabación con tooltip
 */
function disableRecordingWithTooltip() {
    if (elements.recordBtn) {
        elements.recordBtn.disabled = true;
        elements.recordBtn.title = "Audio cargado — grabación deshabilitada";
    }
}

/**
 * Habilita grabación y limpia tooltip
 */
function enableRecordingAndClearTooltip() {
    if (elements.recordBtn) {
        elements.recordBtn.disabled = false;
        elements.recordBtn.title = "";
    }
}

/**
 * Actualiza el estado del botón de envío
 */
function updateSendButtonState(hayAudio, nombre, email, modo, processedModes = []) {
    let puedeEnviar = hayAudio &&
        nombre.length > 0 &&
        email.length > 0 &&
        modo.length > 0;

    // 🔥 Bloqueo si el modo ya ha sido procesado
    if (processedModes.includes(modo)) {
        puedeEnviar = false;
    }

    if (elements.sendBtn) {
        elements.sendBtn.disabled = !puedeEnviar;
        elements.sendBtn.classList.toggle("disabled", !puedeEnviar);
    }
}

/**
 * Actualiza el estado del botón de nueva sesión
 */
function updateResetButtonState(hasName, hasEmail, hasMd, hasTranscript, hasAudio, hasChat) {
    const btn = document.getElementById("btnNuevaSesion");
    if (!btn) return;

    const shouldEnable = hasName || hasEmail || hasMd || hasTranscript || hasAudio || hasChat;
    btn.disabled = !shouldEnable;
}

/**
 * Cambia el estado visual del botón de grabación
 */
function setRecordingButtonState(isRecording) {
    if (elements.recordBtn) {
        if (isRecording) {
            elements.recordBtn.classList.add("recording");
        } else {
            elements.recordBtn.classList.remove("recording");
        }
    }
}

/**
 * Muestra un mensaje de estado
 */
function setStatusText(text) {
    if (elements.statusText) {
        elements.statusText.textContent = text;
    }
}

/**
 * Actualiza el estado de botones de grabación/carga según si hay audio
 * @param {boolean} hayAudio - Si hay audio cargado
 */
function updateRecordingButtonsState(hayAudio) {
    // REGLAS REFINADAS:
    // Con audio: grabar ❌, parar ❌, borrar ✅, descargar ✅, cargar ✅
    // Sin audio: grabar ✅, cargar ✅, parar ❌, borrar ❌, descargar ❌

    if (elements.recordBtn) {
        elements.recordBtn.disabled = hayAudio;
        elements.recordBtn.title = hayAudio ? "Audio cargado — grabación deshabilitada" : "";
    }

    if (elements.stopBtn) {
        elements.stopBtn.disabled = true; // El botón parar solo debe estar activo mientras se graba (manejado en startRecording)
    }

    if (elements.deleteBtn) {
        elements.deleteBtn.disabled = !hayAudio;
    }

    if (elements.downloadBtn) {
        elements.downloadBtn.disabled = !hayAudio;
    }

    if (elements.uploadBtn) {
        elements.uploadBtn.disabled = false; // Siempre se puede cargar un audio nuevo (sustituye al actual)
    }
}

/**
 * Alterna visibilidad de sección de resultados y la expande
 */
function toggleResultSection(visible) {
    const { resultSection } = getSectionElements();
    if (resultSection) {
        resultSection.hidden = !visible;
        if (visible) expandSection(resultSection);
    }
}

/**
 * Alterna visibilidad de sección de transcripción y la expande
 */
function toggleTranscriptionSection(visible) {
    const { transcripcionSection } = getSectionElements();
    if (transcripcionSection) {
        transcripcionSection.hidden = !visible;
        if (visible) expandSection(transcripcionSection);
    }
}

/**
 * Helper para expandir una sección colapsable programáticamente
 */
function expandSection(sectionElement) {
    const toggle = sectionElement.querySelector(".collapsible-toggle");
    const content = sectionElement.querySelector(".collapsible-content");

    if (toggle) {
        toggle.setAttribute("aria-expanded", "true");
        const arrow = toggle.querySelector(".arrow");
        if (arrow) arrow.textContent = "▼";
    }

    if (content) {
        content.hidden = false;
    }
}

/**
 * Muestra el botón de imprimir PDF
 */
function showPrintButton() {
    if (elements.btnImprimirPDF) {
        elements.btnImprimirPDF.style.display = "inline-block";
    }
}

export {
    clearTranscriptionAndResults,
    disableRecordingWithTooltip,
    enableRecordingAndClearTooltip,
    hideOverlay,
    hideCancelButton,
    hideProgressBar,
    setProgressBar,
    setRecordingButtonState,
    setStatusText,
    showCancelButton,
    showOverlay,
    showProgressBar,
    showPrintButton,
    toggleResultSection,
    toggleTranscriptionSection,
    updateRecordingButtonsState,
    updateResetButtonState,
    updateSendButtonState
};

