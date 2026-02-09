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
    if (!cachedElements) {
        cachedElements = {};
    }

    const selectors = {
        // Botones principales
        recordBtn: "recordBtn",
        stopBtn: "stopBtn",
        sendBtn: "sendBtn",
        deleteBtn: "deleteBtn",
        downloadBtn: "downloadBtn",
        uploadBtn: "uploadBtn",

        // Elementos de estado y preview
        statusText: "status",
        previewContainer: "previewContainer",
        fileInput: "fileInput",

        // Elementos del chat
        chatToggle: "chatToggle",
        chatPanel: "chatPanel",
        chatClose: "chatClose",
        chatMessages: "chatMessages",
        chatInput: "chatInput",
        chatSend: "chatSend",

        // Elementos del formulario
        nombre: "nombre",
        email: "email",
        modo: "modo",

        // Elementos de información y warning
        nameWarning: "name-warning",
        sessionLabel: "sessionLabel",

        // Elementos de resultados
        transcripcionTexto: "transcripcionTexto",
        mdResult: "mdResult",

        // Elementos de UI
        overlayLoading: "overlayLoading",
        btnImprimirPDF: "btnImprimirPDF",
        historyToggle: "historyToggle",
        historyPanel: "historyPanel",
        historyList: "historyList",
        multiResults: "multiResults",
        historyClose: "historyClose",

        // Elementos colapsables
        transcriptionTitle: "transcriptionTitle",
        resultTitle: "resultTitle",
        transcriptionContent: "transcriptionContent",
        resultContent: "resultContent"
    };

    // Solo buscar elementos que no hayan sido encontrados previamente con éxito
    for (const [key, id] of Object.entries(selectors)) {
        if (!cachedElements[key]) {
            cachedElements[key] = document.getElementById(id);
        }
    }

    return cachedElements;
}

/**
 * Getter para acceder a los elementos inicializados
 */
const elements = new Proxy({}, {
    get: (target, prop) => {
        if (prop === "preview") {
            return document.getElementById("preview");
        }
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

