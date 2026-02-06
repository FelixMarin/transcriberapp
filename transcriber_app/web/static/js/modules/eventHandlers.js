/**
 * Módulo de manejadores de eventos
 * Contiene toda la lógica de handlers de audio, formulario, archivos, etc.
 */

import {
    addProcessedMode,
    getHasTranscript,
    getLastRecordingBlob,
    getLastRecordingDuration,
    getLastRecordingName,
    getProcessedModes,
    resetAllState,
    setHasTranscript,
    setLastRecordingBlob,
    setLastRecordingDuration,
    setLastRecordingName
} from "./appState.js";

import {
    processExistingTranscription
} from "./api.js";
import {
    processNewRecording
} from "./audioProcessing.js";
import {
    clearChatHistory,
    closeChatPanel,
    getChatHistory,
    sendMessage,
    toggleChatPanel
} from "./chat.js";
import { elements, getModalElements } from "./domElements.js";
import {
    deleteRecording,
    displayAudioPreview,
    downloadRecording,
    handleFileUpload,
    triggerFileInput
} from "./fileHandling.js";
import { clearFormFields, getFormName, getFormValues, validateForm, validateSessionName } from "./form.js";
import { addResultBox, toggleHistoryPanel } from "./history.js";
import { getLatestTranscriptionByName, saveTranscription } from "./historyStorage.js";
import {
    clearAudioChunks,
    getAudioDuration,
    getRecordingBlob,
    startRecording,
    stopRecording
} from "./recording.js";
import {
    clearTranscriptionAndResults,
    setStatusText,
    updateRecordingButtonsState,
    updateResetButtonState,
    updateSendButtonState
} from "./ui.js";
import { generateId } from "./utils.js";

/**
 * Guarda en historial si está completo
 */
async function saveToHistoryIfComplete(providedMarkdown, providedMode) {
    // Prioridad: Argumentos > DOM > Vacío
    const markdown = providedMarkdown || elements.mdResult?.textContent?.trim() || "";
    // NOTA: Si leemos del DOM (textContent), perdemos formato Markdown. 
    // Lo ideal es que siempre venga 'providedMarkdown'.

    const texto = elements.transcripcionTexto?.textContent?.trim() || "";
    // Para la transcripción original, es aceptable leer del DOM si no ha cambiado, 
    // aunque idealmente deberíamos tenerla en memoria.

    console.log("[SAVE] Intentando guardar. MD length:", markdown.length, "Txt length:", texto.length);

    if (markdown && texto) {
        const nombre = getFormName();
        const modo = providedMode || elements.modo?.value || "default";
        const fecha = new Date().toISOString();

        console.log("[SAVE] Guardando para:", nombre, "Modo:", modo);

        // 1. Buscar si ya existe una sesión con este nombre
        const existingRecord = await getLatestTranscriptionByName(nombre);

        let recordToSave;

        if (existingRecord) {
            console.log("[SAVE] Fusión: Encontrado registro previo. ID:", existingRecord.id, "Modos actuales:", Object.keys(existingRecord.resumenes || {}));

            // FUSIÓN: Mantener ID y otros datos, actualizar resúmenes
            recordToSave = {
                ...existingRecord,
                fecha: fecha, // Actualizamos fecha a la última modificación
                resumenes: {
                    ...(existingRecord.resumenes || {}),
                    [modo]: markdown
                },
                transcripcion: existingRecord.transcripcion || [texto] // Preservar transcripción original si existe
            };

            // IMPORTANTE: Si la transcripción original estaba vacía en el registro, intentamos usar 'texto'
            if (!recordToSave.transcripcion || recordToSave.transcripcion.length === 0 || !recordToSave.transcripcion[0]) {
                if (texto) recordToSave.transcripcion = [texto];
            }

        } else {
            console.log("[SAVE] Nuevo: No se encontró registro previo para", nombre);
            // COMPORTAMIENTO NUEVO: Crear desde cero
            const id = await generateId(nombre, fecha);
            recordToSave = {
                id,
                nombre,
                fecha,
                duracion: getLastRecordingDuration(),
                grabacion: getLastRecordingBlob() || null,
                transcripcion: [texto],
                resumenes: { [modo]: markdown }
            };
        }

        try {
            await saveTranscription(recordToSave);
            setCurrentSessionId(recordToSave.id);
            console.log("[SAVE] Guardado exitoso en IndexedDB. ID:", recordToSave.id);
        } catch (e) {
            console.error("[SAVE] Error al guardar en DB:", e);
        }
    } else {
        console.warn("[SAVE] No se pudo guardar: faltan datos (MD o Texto)");
    }
}

/**
 * Reinicia la interfaz
 */
function resetUI() {
    clearFormFields();
    clearTranscriptionAndResults();

    if (elements.nameWarning) elements.nameWarning.hidden = false;
    if (elements.sessionLabel) {
        elements.sessionLabel.textContent = "Sin sesión";
        elements.sessionLabel.classList.remove("session-active");
    }

    document.getElementById("result")?.setAttribute("hidden", true);
    document.getElementById("transcripcion")?.setAttribute("hidden", true);
    document.getElementById("btnNuevaSesion").disabled = true;

    if (elements.preview) {
        elements.preview.src = "";
        elements.preview.hidden = true;
    }

    if (elements.chatToggle) elements.chatToggle.disabled = true;

    clearChatHistory();
    updateRecordingButtonsState(false);  // Sin audio
    resetAllState();
}

/**
 * Maneja el envío de audio
 */
async function handleSendAudio() {
    const { nombre, email, modo } = getFormValues();

    if (!nombre || !email) {
        alert("Debes indicar nombre y email.");
        return;
    }

    // CASO 1: Ya existe transcripción → reutilizar
    if (getHasTranscript() && getLastRecordingName() === nombre) {
        // Intentar obtener el texto de la transcripción actual para mandarlo al back (si ya no hay archivos)
        const currentTranscript = elements.transcripcionTexto?.innerText || "";
        const result = await processExistingTranscription(nombre, modo, currentTranscript);

        if (result.success) {
            // Actualizar UI principal
            // Actualizar UI principal
            // (La visibilidad ahora se gestiona dentro de addResultBox)

            // Añadir a la lista de resultados múltiples
            addResultBox(result.mode, result.content);
            addProcessedMode(result.mode);

            updateSendButtonState(
                !!getLastRecordingBlob(),
                ...Object.values(getFormValues()),
                getProcessedModes()
            );

            // Guardar en historial (fusión)
            // Pasamos explícitamente contenido y modo
            await saveToHistoryIfComplete(result.content, result.mode);

            // Auto-scroll a resultados
            setTimeout(() => {
                const resultSection = document.getElementById("result");
                if (resultSection) {
                    resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 100);

        } else {
            alert(result.error);
        }
        return;
    }

    // CASO 2: Primera vez → enviar audio
    await processNewRecording(
        getLastRecordingBlob(),
        nombre,
        email,
        modo,
        async () => {
            setLastRecordingName(nombre);
            setHasTranscript(true);
            addProcessedMode(modo);
            updateSendButtonState(
                !!getLastRecordingBlob(),
                ...Object.values(getFormValues()),
                getProcessedModes()
            );
        },
        async (data) => {
            // onJobCompleted: save to history after processing
            // 'data' ahora trae 'markdown' asegurado por el fix en audioProcessing.js
            const mdContent = data?.markdown || data?.resultado || "";
            const currentMode = elements.modo?.value || "default";

            // Renderizar inmediatamente
            addResultBox(currentMode, mdContent);
            addProcessedMode(currentMode);

            await saveToHistoryIfComplete(mdContent, currentMode);

            // Auto-scroll a resultados
            setTimeout(() => {
                const resultSection = document.getElementById("result");
                if (resultSection) {
                    resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 100);
        }
    );
}

/**
 * Configura event listeners del modal
 */
function setupModalHandlers() {
    const { modal, cancelBtn, confirmBtn, btnNuevaSesion } = getModalElements();

    if (cancelBtn) {
        cancelBtn.addEventListener("click", () => {
            modal.classList.add("hidden");
        });
    }

    if (confirmBtn) {
        confirmBtn.addEventListener("click", async () => {
            modal.classList.add("hidden");
            await saveToHistoryIfComplete();
            resetUI();
            elements.historyPanel?.classList.remove("open");
            document.body.classList.remove("history-open");
        });
    }

    if (btnNuevaSesion) {
        btnNuevaSesion.onclick = () => {
            clearFormFields();
            setStatusText("");
            document.getElementById("modalNuevaSesion")?.classList.remove("hidden");
            if (elements.preview) {
                elements.preview.src = "";
                elements.preview.hidden = true;
            }
        };
    }
}

/**
 * Configura event listeners del formulario
 */
function setupFormHandlers() {
    if (elements.nombre) {
        elements.nombre.addEventListener("input", () => {
            validateSessionName(elements.nombre.value);
            validateForm(getLastRecordingBlob());
            updateSendButtonState(
                !!getLastRecordingBlob(),
                ...Object.values(getFormValues()),
                getProcessedModes()
            );
            updateResetButtonState(
                getFormName().length > 0,
                elements.email?.value?.length > 0,
                elements.mdResult?.innerHTML?.trim().length > 0,
                elements.transcripcionTexto?.innerHTML?.trim().length > 0,
                !!getLastRecordingBlob(),
                getChatHistory().length > 0
            );
        });
    }

    if (elements.email) {
        elements.email.addEventListener("input", () => {
            validateForm(getLastRecordingBlob());
            updateSendButtonState(
                !!getLastRecordingBlob(),
                ...Object.values(getFormValues()),
                getProcessedModes()
            );
            updateResetButtonState(
                getFormName().length > 0,
                elements.email?.value?.length > 0,
                elements.mdResult?.innerHTML?.trim().length > 0,
                elements.transcripcionTexto?.innerHTML?.trim().length > 0,
                !!getLastRecordingBlob(),
                getChatHistory().length > 0
            );
        });
    }

    if (elements.modo) {
        elements.modo.addEventListener("change", () => {
            updateSendButtonState(
                !!getLastRecordingBlob(),
                ...Object.values(getFormValues()),
                getProcessedModes()
            );
        });
    }
}

/**
 * Configura event listeners de grabación
 */
function setupRecordingHandlers() {
    if (elements.recordBtn) {
        elements.recordBtn.onclick = startRecording;
    }

    if (elements.stopBtn) {
        elements.stopBtn.onclick = async () => {
            stopRecording();
            const blob = getRecordingBlob();
            if (blob) {
                setLastRecordingBlob(blob);
                setLastRecordingDuration(await getAudioDuration(blob));
                displayAudioPreview(blob);
                validateForm(blob);
                updateRecordingButtonsState(true);  // Hay audio ahora
                updateSendButtonState(
                    !!getLastRecordingBlob(),
                    ...Object.values(getFormValues()),
                    getProcessedModes()
                );
            }
        };
    }
}

/**
 * Configura event listeners de archivos
 */
function setupFileHandlers() {
    if (elements.downloadBtn) {
        elements.downloadBtn.onclick = () => downloadRecording(getLastRecordingBlob());
    }

    if (elements.deleteBtn) {
        elements.deleteBtn.onclick = () => {
            deleteRecording(() => {
                setLastRecordingBlob(null);
                clearAudioChunks();
                validateForm(null);
                updateRecordingButtonsState(false);  // No hay audio ahora
            });
        };
    }

    if (elements.uploadBtn) {
        elements.uploadBtn.onclick = triggerFileInput;
    }

    if (elements.fileInput) {
        elements.fileInput.onchange = async (event) => {
            const file = event.target.files[0];
            if (!file) return;

            handleFileUpload(file, (uploadedFile) => {
                setLastRecordingBlob(uploadedFile);
                validateForm(uploadedFile);
                updateRecordingButtonsState(true);  // Hay audio ahora
                updateSendButtonState(
                    !!getLastRecordingBlob(),
                    ...Object.values(getFormValues()),
                    getProcessedModes()
                );
            });
        };
    }
}

/**
 * Configura event listeners del chat
 */
function setupChatHandlers() {
    if (elements.chatToggle) {
        elements.chatToggle.onclick = toggleChatPanel;
    }

    if (elements.chatClose) {
        elements.chatClose.onclick = closeChatPanel;
    }

    if (elements.chatSend) {
        elements.chatSend.onclick = sendMessage;
    }

    if (elements.chatInput) {
        // Auto-redimensionar al escribir
        elements.chatInput.addEventListener("input", () => {
            elements.chatInput.style.height = "auto";
            elements.chatInput.style.height = (elements.chatInput.scrollHeight) + "px";
        });

        // Manejar Enter para enviar y Shift+Enter para salto de línea
        elements.chatInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();

                // Resetear altura después de enviar
                setTimeout(() => {
                    elements.chatInput.style.height = "auto";
                }, 0);
            }
        });
    }
}

/**
 * Configura event listeners del historial
 */
function setupHistoryHandlers() {
    if (elements.historyToggle) {
        elements.historyToggle.onclick = toggleHistoryPanel;
    }

    if (elements.historyClose) {
        elements.historyClose.onclick = toggleHistoryPanel;
    }
}

/**
 * Configura el botón de imprimir PDF
 */
function setupPrintHandler() {
    if (elements.btnImprimirPDF) {
        elements.btnImprimirPDF.onclick = () => {
            const contenido = elements.mdResult?.innerHTML || "";
            const ventana = window.open("", "_blank");
            ventana.document.write(`
                <html>
                    <head>
                        <title>Resumen Técnico</title>
                        <style>
                            body { font-family: sans-serif; padding: 20px; }
                            h1, h2, h3 { color: #333; }
                            p, li { line-height: 1.6; }
                        </style>
                    </head>
                    <body>${contenido}</body>
                </html>
            `);
            ventana.document.close();
            ventana.print();
        };
    }
}

/**
 * Protege contra cerrar/refrescar con datos no guardados
 */
function setupBeforeUnloadHandler() {
    window.addEventListener("beforeunload", (e) => {
        if (getLastRecordingBlob()) {
            e.preventDefault();
            e.returnValue = "¿Estás seguro? Puedes perder la grabación.";
        }
    });
}

/**
 * Configura event listeners para secciones colapsables
 */
function setupCollapsibleHandlers() {
    document.querySelectorAll(".collapsible-toggle").forEach(button => {
        button.addEventListener("click", () => {
            const isExpanded = button.getAttribute("aria-expanded") === "true";
            const targetId = button.getAttribute("aria-controls");

            // Alternar estado del botón
            button.setAttribute("aria-expanded", !isExpanded);

            // Alternar flecha
            const arrow = button.querySelector(".arrow");
            if (arrow) {
                arrow.textContent = isExpanded ? "▶" : "▼";
            }

            // Alternar contenido
            if (targetId) {
                const content = document.getElementById(targetId);
                if (content) {
                    content.hidden = isExpanded;
                }
            } else {
                // Fallback: buscar el siguiente elemento hermano si no tiene aria-controls
                const next = button.parentElement.nextElementSibling;
                if (next && next.classList.contains("collapsible-content")) {
                    next.hidden = isExpanded;
                }
            }
        });
    });
}

export {
    handleSendAudio, resetUI, saveToHistoryIfComplete, setupBeforeUnloadHandler, setupChatHandlers, setupCollapsibleHandlers, setupFileHandlers, setupFormHandlers, setupHistoryHandlers, setupModalHandlers, setupPrintHandler, setupRecordingHandlers
};

