/**
 * Módulo de gestión de elementos DOM
 * Centraliza todas las referencias a elementos del HTML
 */

let cachedElements = null;

/**
 * Función para inicializar elementos del DOM
 * Se ejecuta de forma lazy cuando se necesita
 */
function initializeElements() {
    if (cachedElements) return cachedElements;

    cachedElements = {
        // Botones principales
        recordBtn: document.getElementById("recordBtn"),
        stopBtn: document.getElementById("stopBtn"),
        sendBtn: document.getElementById("sendBtn"),
        deleteBtn: document.getElementById("deleteBtn"),
        downloadBtn: document.getElementById("downloadBtn"),
        uploadBtn: document.getElementById("uploadBtn"),

        // Elementos de estado y preview
        statusText: document.getElementById("status"),
        preview: document.getElementById("preview"),
        fileInput: document.getElementById("fileInput"),

        // Elementos del chat
        chatToggle: document.getElementById("chatToggle"),
        chatPanel: document.getElementById("chatPanel"),
        chatClose: document.getElementById("chatClose"),
        chatMessages: document.getElementById("chatMessages"),
        chatInput: document.getElementById("chatInput"),
        chatSend: document.getElementById("chatSend"),

        // Elementos del formulario
        nombre: document.getElementById("nombre"),
        email: document.getElementById("email"),
        modo: document.getElementById("modo"),

        // Elementos de información y warning
        nameWarning: document.getElementById("name-warning"),
        sessionLabel: document.getElementById("sessionLabel"),

        // Elementos de resultados
        transcripcionTexto: document.getElementById("transcripcionTexto"),
        mdResult: document.getElementById("mdResult"),

        // Elementos de UI
        overlayLoading: document.getElementById("overlayLoading"),
        btnImprimirPDF: document.getElementById("btnImprimirPDF"),
        historyToggle: document.getElementById("historyToggle"),
        historyPanel: document.getElementById("historyPanel"),
        historyList: document.getElementById("historyList"),
        multiResults: document.getElementById("multiResults"),
        historyClose: document.getElementById("historyClose"),

        // Elementos colapsables
        transcriptionTitle: document.getElementById("transcriptionTitle"),
        resultTitle: document.getElementById("resultTitle"),
        transcriptionContent: document.getElementById("transcriptionContent"),
        resultContent: document.getElementById("resultContent")
    };

    return cachedElements;
}

/**
 * Getter para acceder a los elementos inicializados
 */
const elements = new Proxy({}, {
    get: (target, prop) => {
        const els = initializeElements();
        return els[prop];
    }
});

/**
 * Valida que todos los elementos necesarios existan en el DOM
 */
function validateElements() {
    const missingElements = [];
    for (const [key, element] of Object.entries(elements)) {
        if (!element) {
            missingElements.push(key);
        }
    }

    if (missingElements.length > 0) {
        console.warn("Elementos DOM no encontrados:", missingElements);
    }
}

/**
 * Obtiene referencias a elementos del modal
 */
function getModalElements() {
    return {
        modal: document.getElementById("modalNuevaSesion"),
        cancelBtn: document.getElementById("modalCancelar"),
        confirmBtn: document.getElementById("modalConfirmar"),
        btnNuevaSesion: document.getElementById("btnNuevaSesion")
    };
}

/**
 * Obtiene referencias a secciones ocultas
 */
function getSectionElements() {
    return {
        resultSection: document.getElementById("result"),
        transcripcionSection: document.getElementById("transcripcion")
    };
}

export { elements, getModalElements, getSectionElements, validateElements };

