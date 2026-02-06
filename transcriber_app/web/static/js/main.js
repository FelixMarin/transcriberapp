/**
 * Módulo principal - Inicialización y orquestación
 * Coordina todos los módulos y configura event listeners
 */

import { elements, validateElements } from "./modules/domElements.js";
import {
    handleSendAudio,
    setupBeforeUnloadHandler,
    setupChatHandlers,
    setupCollapsibleHandlers,
    setupFileHandlers,
    setupFormHandlers,
    setupHistoryHandlers,
    setupModalHandlers,
    setupPrintHandler,
    setupRecordingHandlers
} from "./modules/eventHandlers.js";
import { updateRecordingButtonsState } from "./modules/ui.js";

/**
 * Inicializa toda la aplicación
 */
function init() {
    validateElements();

    if (elements.nameWarning) elements.nameWarning.hidden = false;
    if (elements.chatToggle) elements.chatToggle.disabled = true;

    // Initializar estado de botones de grabación (sin audio al inicio)
    updateRecordingButtonsState(false);

    // Configurar todos los event listeners
    setupFormHandlers();
    setupRecordingHandlers();
    setupFileHandlers();
    setupChatHandlers();
    setupHistoryHandlers();
    setupPrintHandler();
    setupBeforeUnloadHandler();
    setupModalHandlers();
    setupCollapsibleHandlers();

    // Asignar manejador principal de envío de audio
    if (elements.sendBtn) {
        elements.sendBtn.onclick = handleSendAudio;
    }

    console.log("✅ Aplicación iniciada correctamente");
}

// Esperar a que el DOM esté listo
document.addEventListener("DOMContentLoaded", init);
