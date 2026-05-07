/**
 * Módulo principal - Inicialización y orquestación
 * Coordina todos los módulos y configura event listeners
 */

const APP_VERSION = window.APP_VERSION;
console.log(window.APP_VERSION)

/**
 * Inicializa toda la aplicación
 */
async function init() {
    // Cargar módulos con cache busting
    const { elements, validateElements } = await import(`./modules/domElements.js?v=${APP_VERSION}`);
    const eventHandlers = await import(`./modules/eventHandlers.js?v=${APP_VERSION}`);
    const { updateRecordingButtonsState } = await import(`./modules/ui.js?v=${APP_VERSION}`);

    // Extraer funciones de eventHandlers
    const {
        handleSendAudio,
        setupBeforeUnloadHandler,
        setupCancelHandler,
        setupChatHandlers,
        setupCollapsibleHandlers,
        setupFileHandlers,
        setupFormHandlers,
        setupHistoryHandlers,
        setupModalHandlers,
        setupPrintHandler,
        setupRecordingHandlers
    } = eventHandlers;

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
    setupCancelHandler();
    setupCollapsibleHandlers();

    // Asignar manejador principal de envío de audio
    if (elements.sendBtn) {
        elements.sendBtn.onclick = handleSendAudio;
    }

    console.log("✅ Aplicación iniciada correctamente");
}

// Esperar a que el DOM esté listo
document.addEventListener("DOMContentLoaded", init);
