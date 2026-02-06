/**
 * Módulo de utilidades
 * Funciones auxiliares reutilizables
 */

/**
 * Genera un ID único basado en un nombre y fecha
 */
async function generateId(nombre, fecha) {
    const encoder = new TextEncoder();
    const data = encoder.encode(nombre + fecha);
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
}

/**
 * Formatea texto como HTML escapando caracteres especiales
 */
function formatAsHTML(text) {
    if (!text) return "";
    const escaped = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    const withBreaks = escaped.replace(/\n/g, "<br>");
    return withBreaks
        .replace(/•\s/g, "•&nbsp;")
        .replace(/^\d+\.\s/gm, match => `<strong>${match}</strong>`);
}

/**
 * Parsea markdown a HTML
 * Usa la librería 'marked' si está disponible
 */
function parseMarkdown(markdown) {
    if (!markdown) return "";
    try {
        // Intentar encontrar marked en el ámbito global o window
        const m = (typeof marked !== 'undefined') ? marked : (window.marked || null);

        if (m && (typeof m === 'function' || m.parse)) {
            const parseFn = m.parse || m;
            return parseFn(markdown);
        } else {
            console.warn("marked no está disponible, usando parseador básico");
            // Fallback muy básico para títulos si falla marked
            return markdown
                .replace(/^# (.*$)/gm, '<h1>$1</h1>')
                .replace(/^## (.*$)/gm, '<h2>$1</h2>')
                .replace(/^### (.*$)/gm, '<h3>$1</h3>')
                .replace(/\n/g, '<br>');
        }
    } catch (error) {
        console.error("Error parseando markdown:", error);
        return markdown.replace(/\n/g, '<br>');
    }
}

/**
 * Normaliza texto: minúsculas y sin acentos
 */
function normalizeText(text) {
    return text.toLowerCase();
}

/**
 * Valida un email
 */
function isValidEmail(email) {
    return email.includes("@") && email.includes(".");
}

/**
 * Valida un nombre (mínimo 5 caracteres)
 */
function isValidName(name) {
    return name.trim().length >= 5;
}

/**
 * Obtiene mensaje de estado según el código del servidor
 */
function getStatusMessage(status) {
    const messages = {
        processing: "Procesando audio…",
        running: "Procesando audio…",
        done: "Transcripción enviada por email.",
        error: "Error durante el procesamiento.",
        bad_audio: "Audio de mala calidad detectado."
    };
    return messages[status] || "Estado desconocido.";
}

/**
 * Reconstrúye un Blob desde diferentes formatos de almacenamiento
 */
function reconstructBlob(stored) {
    if (!stored) return null;

    // Caso 1: ya es un Blob
    if (stored instanceof Blob) return stored;

    // Caso 2: viene como ArrayBuffer o Uint8Array
    if (stored.data) {
        return new Blob([new Uint8Array(stored.data)], { type: stored.type || "audio/mp3" });
    }

    // Caso 3: viene como objeto serializado por IndexedDB
    if (stored.arrayBuffer) {
        return new Blob([new Uint8Array(stored.arrayBuffer)], { type: stored.type || "audio/mp3" });
    }

    console.warn("Formato de grabación desconocido:", stored);
    return null;
}

export {
    formatAsHTML, generateId, getStatusMessage, isValidEmail,
    isValidName, normalizeText, parseMarkdown, reconstructBlob
};

