/**
 * Módulo de historial
 * Gestiona el panel lateral de historial de transcripciones
 */

import { addProcessedMode, getProcessedModes, resetProcessedModes, setCurrentSessionId, setLastRecordingBlob } from "./appState.js";
import { addMessage, clearChatHistory } from "./chat.js";
import { elements } from "./domElements.js";
import { getFormValues, setFormName, validateSessionName } from "./form.js";
import { getAllTranscriptions, getTranscriptionById } from "./historyStorage.js";
import { clearTranscriptionAndResults, updateRecordingButtonsState, updateSendButtonState } from "./ui.js";
import { parseMarkdown, reconstructBlob } from "./utils.js";

/**
 * Alterna la visibilidad del panel de historial
 */
async function toggleHistoryPanel() {
    if (!elements.historyPanel) return;

    const isOpening = !elements.historyPanel.classList.contains("open");
    elements.historyPanel.classList.toggle("open");
    document.body.classList.toggle("history-open", isOpening);

    if (isOpening) {
        await loadHistoryItems();
    }
}

/**
 * Carga la lista de items del historial
 */
async function loadHistoryItems() {
    if (!elements.historyList) return;

    elements.historyList.innerHTML = "";
    try {
        const items = await getAllTranscriptions();
        items
            .sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
            .forEach(item => {
                const li = document.createElement("li");
                li.className = "history-item flex justify-between items-center p-2 hover:bg-gray-100 cursor-pointer rounded mb-1";
                li.style = "display: flex; justify-content: space-between; align-items: center; padding: 8px; cursor: pointer; border-radius: 4px; border-bottom: 1px solid #eee;";

                const textSpan = document.createElement("span");
                const fecha = new Date(item.fecha).toLocaleString();
                textSpan.textContent = `${item.nombre} (${fecha})`;
                textSpan.style = "flex-grow: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;";
                textSpan.onclick = () => loadTranscriptionFromHistory(item.id);

                const deleteBtn = document.createElement("button");
                deleteBtn.innerHTML = "🗑️";
                deleteBtn.title = "Eliminar transcripción";
                deleteBtn.className = "btn-delete-history ml-2 opacity-50 hover:opacity-100";
                deleteBtn.style = "background: none; border: none; cursor: pointer; padding: 4px; font-size: 1.1em;";
                deleteBtn.onclick = (e) => {
                    e.stopPropagation();
                    handleDeleteItem(item.id, item.nombre);
                };

                li.appendChild(textSpan);
                li.appendChild(deleteBtn);

                li.tabIndex = 0;
                li.onkeypress = (e) => {
                    if (e.key === "Enter" || e.key === " ") {
                        loadTranscriptionFromHistory(item.id);
                    }
                };
                elements.historyList.appendChild(li);
            });

    } catch (error) {
        console.error("Error cargando historial:", error);
        if (elements.historyList) {
            elements.historyList.innerHTML = "<li>Error cargando historial</li>";
        }
    }
}

/**
 * Maneja la eliminación de un item del historial
 */
async function handleDeleteItem(id, nombre) {
    if (!confirm(`¿Estás seguro de que quieres eliminar la transcripción "${nombre}"? Esta acción no se puede deshacer.`)) {
        return;
    }

    try {
        await deleteTranscription(id);
        console.log(`[HISTORY] Item eliminado: ${id}`);

        // Si es la sesión actual, limpiar la UI (opcional pero recomendado)
        // Podríamos importar getCurrentSessionId aquí si quisiéramos ser más finos.

        await loadHistoryItems(); // Refrescar lista
    } catch (error) {
        console.error("Error eliminando item:", error);
        alert("No se pudo eliminar el item del historial.");
    }
}

/**
 * Carga una transcripción desde el historial
 */
async function loadTranscriptionFromHistory(id) {
    try {
        const item = await getTranscriptionById(id);
        if (!item) {
            alert("No se encontró la transcripción.");
            return;
        }

        // Limpiar todo lo anterior
        clearTranscriptionAndResults();

        // Resetear modos procesados y cargar los del historial
        resetProcessedModes();
        setCurrentSessionId(id);

        const modesDelHistorial = Object.keys(item.resumenes || {});
        modesDelHistorial.forEach(modo => addProcessedMode(modo));

        // Rellenar nombre
        setFormName(item.nombre);

        // Limpiar chat y restaurar si existe
        clearChatHistory();
        if (elements.chatMessages) elements.chatMessages.innerHTML = "";
        if (item.chat && Array.isArray(item.chat)) {
            item.chat.forEach(msg => {
                addMessage(msg.content, msg.role === "user" ? "user" : "ai");
            });
        }

        // Transcripciones: una o varias
        if (elements.transcripcionTexto) {
            const transcripcionSection = document.getElementById("transcripcion");
            if (transcripcionSection) transcripcionSection.hidden = false;

            if (Array.isArray(item.transcripcion)) {
                renderMultipleTranscriptions(item.transcripcion);
            } else {
                elements.transcripcionTexto.innerHTML = parseMarkdown(item.transcripcion || "");
            }
        }

        // Limpiar y preparar contenedor de resultados
        if (elements.resultContent) {
            elements.resultContent.innerHTML = "";
            const resultSection = document.getElementById("result");
            if (resultSection) {
                resultSection.hidden = false;
                // Auto-expandir
                const toggle = resultSection.querySelector(".collapsible-toggle");
                if (toggle) toggle.setAttribute("aria-expanded", "true");
            }
        }

        // Cargar todos los resúmenes disponibles
        if (item.resumenes) {
            // Ordenar: primero default si existe, luego el resto
            const modes = Object.keys(item.resumenes).sort((a, b) => {
                if (a === 'default') return -1;
                if (b === 'default') return 1;
                return a.localeCompare(b);
            });

            modes.forEach(mode => {
                addResultBox(mode, item.resumenes[mode]);
            });
        }

        // Cargar grabación si existe
        if (item.grabacion) {
            const blob = reconstructBlob(item.grabacion);
            if (blob && elements.preview) {
                setLastRecordingBlob(blob);
                const url = URL.createObjectURL(blob);
                elements.preview.src = url;
                elements.preview.hidden = false;
            }
            updateRecordingButtonsState(true);  // Hay audio
        } else {
            updateRecordingButtonsState(false);  // No hay audio
        }

        validateSessionName(item.nombre);
        if (elements.chatToggle) elements.chatToggle.disabled = false;

        // 🔥 Actualizar estado del botón Enviar con los modos del historial
        const { nombre, email, modo } = getFormValues();
        const hayAudio = !!item.grabacion;

        updateSendButtonState(
            hayAudio,
            nombre,
            email,
            modo,
            getProcessedModes()
        );
    } catch (error) {
        console.error("Error cargando transcripción del historial:", error);
        alert("Error al cargar la transcripción del historial.");
    }
}

/**
 * Renderiza múltiples transcripciones en colapsables
 */
function renderMultipleTranscriptions(transcriptionsArray) {
    if (!elements.transcripcionTexto) return;

    elements.transcripcionTexto.innerHTML = "";

    transcriptionsArray.forEach((md, index) => {
        const wrapper = document.createElement("div");
        wrapper.className = "collapsible-block";

        const toggle = document.createElement("button");
        toggle.className = "collapsible-toggle";
        toggle.innerHTML = `Transcripción ${index + 1} <span class="arrow">▶</span>`;
        toggle.setAttribute("aria-expanded", "false");

        const content = document.createElement("div");
        content.className = "collapsible-content";
        content.hidden = true;
        content.innerHTML = parseMarkdown(md);

        toggle.onclick = () => {
            const expanded = toggle.getAttribute("aria-expanded") === "true";
            toggle.setAttribute("aria-expanded", expanded ? "false" : "true");
            content.hidden = expanded;
            toggle.querySelector(".arrow").textContent = expanded ? "▶" : "▼";
        };

        wrapper.appendChild(toggle);
        wrapper.appendChild(content);
        elements.transcripcionTexto.appendChild(wrapper);
    });
}

/**
 * Añade una caja de resultado (resumen)
 */
/**
 * Añade una caja de resultado al contenedor principal
 */
function addResultBox(mode, content) {
    if (!elements.resultContent) return;

    // Asegurar que la sección padre (#result) sea visible y esté expandida
    const resultSection = document.getElementById("result");
    if (resultSection) {
        resultSection.hidden = false;
        const toggle = resultSection.querySelector(".collapsible-toggle");
        if (toggle) {
            toggle.setAttribute("aria-expanded", "true");
            const arrow = toggle.querySelector(".arrow");
            if (arrow) arrow.textContent = "▼";
        }
    }

    // Crear ID único para evitar colisiones
    const uniqueId = `result-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const contentId = `content-${uniqueId}`;

    const html = `
    <div class="result-box mb-4 pb-4 border-b" id="${uniqueId}">
        <div class="result-header flex justify-between items-center mb-2" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <button class="collapsible-toggle mode-toggle" aria-expanded="true" aria-controls="${contentId}" style="background: none; border: none; font-weight: bold; cursor: pointer; display: flex; align-items: center; gap: 5px; padding: 0; text-transform: uppercase; font-size: 1.1em; color: #444;">
                <span class="arrow">▼</span> ${mode}
            </button>
            <button class="btn btn-sm btn-print-item" aria-label="Imprimir ${mode}" style="padding: 4px 8px; font-size: 0.9em; cursor: pointer;">
                🖨️ PDF
            </button>
        </div>
        <div id="${contentId}" class="collapsible-content markdown-body" style="margin-top: 10px;">
            ${parseMarkdown(content)}
        </div>
    </div>
    `;

    elements.resultContent.insertAdjacentHTML("beforeend", html);

    const container = document.getElementById(uniqueId);
    if (container) {
        // Asignar evento al botón de imprimir
        const printBtn = container.querySelector(".btn-print-item");
        if (printBtn) {
            printBtn.onclick = (e) => {
                e.stopPropagation(); // Evitar que el clic se propague al toggle si estuvieran anidados
                printResultContent(mode, content);
            };
        }

        // Asignar evento de colapso al título
        const toggleBtn = container.querySelector(".mode-toggle");
        const contentDiv = document.getElementById(contentId);

        if (toggleBtn && contentDiv) {
            toggleBtn.onclick = () => {
                const isExpanded = toggleBtn.getAttribute("aria-expanded") === "true";
                toggleBtn.setAttribute("aria-expanded", !isExpanded);
                contentDiv.hidden = isExpanded;
                const arrow = toggleBtn.querySelector(".arrow");
                if (arrow) arrow.textContent = isExpanded ? "▶" : "▼";
            };
        }
    }
}

/**
 * Imprime un contenido específico
 */
function printResultContent(mode, content) {
    const ventana = window.open("", "_blank");
    ventana.document.write(`
        <html>
            <head>
                <title>Resultado: ${mode}</title>
                <style>
                    body { font-family: sans-serif; padding: 20px; }
                    h1, h2, h3 { color: #333; }
                    p, li { line-height: 1.6; }
                    img { max-width: 100%; }
                    pre { background: #f4f4f4; padding: 10px; border-radius: 5px; }
                </style>
            </head>
            <body>
                <h1>Resultado: ${mode.toUpperCase()}</h1>
                ${parseMarkdown(content)}
            </body>
        </html>
    `);
    ventana.document.close();
    setTimeout(() => ventana.print(), 500);
}

export {
    addResultBox, loadHistoryItems,
    loadTranscriptionFromHistory,
    renderMultipleTranscriptions, toggleHistoryPanel
};

