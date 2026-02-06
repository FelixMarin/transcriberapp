/**
 * Módulo de chat
 * Gestiona el panel de chat y mensajes
 */

import { chatStream } from "./api.js";
import { getCurrentSessionId } from "./appState.js";
import { elements } from "./domElements.js";
import { closeHistoryPanel } from "./history.js";
import { updateChatHistory } from "./historyStorage.js";
import { hideOverlay, showOverlay } from "./ui.js";
import { formatAsHTML, parseMarkdown } from "./utils.js";

let chatHistory = [];

/**
 * Persiste el historial de chat actual en IndexedDB
 */
async function persistChat() {
    const sessionId = getCurrentSessionId();
    if (sessionId && chatHistory.length > 0) {
        try {
            await updateChatHistory(sessionId, chatHistory);
            console.log("[CHAT] Historial persistido para sesión:", sessionId);
        } catch (e) {
            console.error("[CHAT] Error persistiendo historial:", e);
        }
    }
}

/**
 * Añade un mensaje al chat
 */
function addMessage(text, sender = "user", returnNode = false) {
    if (!elements.chatMessages) return null;

    const div = document.createElement("div");
    div.className = sender === "user" ? "msg-user" : "msg-ai";
    div.innerHTML = formatAsHTML(text);
    elements.chatMessages.appendChild(div);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

    return returnNode ? div : null;
}

/**
 * Recopila todos los resultados procesados en un formato estructurado para la IA
 */
function gatherAllResultsContext() {
    if (!elements.resultContent) return "";

    const resultBoxes = elements.resultContent.querySelectorAll(".result-box");
    let context = "";

    resultBoxes.forEach(box => {
        const modeBtn = box.querySelector(".mode-toggle");
        const contentDiv = box.querySelector(".collapsible-content");

        if (modeBtn && contentDiv) {
            const modeName = modeBtn.textContent.replace(/[▼▶]/g, "").trim();
            const contentText = contentDiv.textContent.trim();

            context += `--- ANÁLISIS MODO: ${modeName} ---\n`;
            context += `${contentText}\n`;
            context += `-----------------------------------\n\n`;
        }
    });

    return context;
}

/**
 * Envía un mensaje de chat
 */
async function sendMessage() {
    const msg = elements.chatInput?.value?.trim() || "";
    if (!msg) return;

    const nombre = document.getElementById("nombre")?.value?.trim() || "";
    const transcripcion = elements.transcripcionTexto?.textContent?.trim() || "";

    // Obtener contexto estructurado de todos los resultados
    const resumen = gatherAllResultsContext();
    const modo = document.getElementById("modo")?.value || "";

    // Validar que hay contenido (mínimo la transcripción o algún resumen)
    if (!transcripcion && !resumen) {
        alert("No hay transcripción ni resumen disponible para chatear.");
        return;
    }

    addMessage(msg, "user");
    if (elements.chatInput) elements.chatInput.value = "";
    chatHistory.push({ role: "user", content: msg });
    persistChat(); // Guardar mensaje del usuario

    const aiMsg = addMessage("", "ai", true);
    showOverlay();

    try {
        let textoFinal = "";
        let isFirstChunk = true;

        for await (const parcial of chatStream(msg, modo, transcripcion, resumen)) {
            if (isFirstChunk) {
                hideOverlay();
                isFirstChunk = false;
            }

            textoFinal += parcial;

            // Mostrar texto en vivo sin parsear markdown
            if (aiMsg) aiMsg.innerHTML = `<pre style="white-space: pre-wrap; word-wrap: break-word; font-family: inherit;">${textoFinal}</pre>`;
        }

        // Cuando termina el streaming → renderizamos markdown completo
        if (aiMsg) aiMsg.innerHTML = parseMarkdown(textoFinal);
        chatHistory.push({ role: "assistant", content: textoFinal });
        persistChat(); // Guardar respuesta completa de la IA

    } catch (e) {
        hideOverlay();
        if (aiMsg) aiMsg.innerHTML = formatAsHTML("Error al procesar la respuesta.");
        console.error("Error en chat:", e);
    }
}

/**
 * Limpia el historial de chat
 */
function clearChatHistory() {
    chatHistory = [];
}

/**
 * Obtiene el historial de chat
 */
function getChatHistory() {
    return chatHistory;
}

/**
 * Abre/cierra el panel de chat
 */
function toggleChatPanel() {
    if (!elements.chatPanel || !elements.chatToggle) return;

    const isOpening = !elements.chatPanel.classList.contains("open");

    if (isOpening) {
        // Cerrar historial si se va a abrir el chat
        closeHistoryPanel();
    }

    elements.chatPanel.classList.toggle("open");
    elements.chatToggle.classList.toggle("hidden");
    document.body.classList.toggle("chat-open", isOpening);
}

/**
 * Cierra el panel de chat
 */
function closeChatPanel() {
    if (elements.chatPanel) {
        elements.chatPanel.classList.remove("open");
    }
    if (elements.chatToggle) {
        elements.chatToggle.classList.remove("hidden");
    }
    document.body.classList.remove("chat-open");
}

export {
    addMessage, clearChatHistory, closeChatPanel, getChatHistory, sendMessage, toggleChatPanel
};

