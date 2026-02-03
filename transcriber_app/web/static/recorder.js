import { getAllTranscriptions, getTranscriptionById, saveTranscription } from "./history.js";

let mediaRecorder;
let audioChunks = [];
let lastRecordingBlob = null;
let lastRecordingName = null;
let hasTranscript = false;
let lastRecordingDuration = null;
let chatHistory = [];
let ultimoModoProcesado = null;


// Cache de elementos DOM - ACTUALIZADO para coincidir con el nuevo HTML
const elements = {
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

    // Elementos colapsables (nuevos selectores)
    transcriptionTitle: document.getElementById("transcriptionTitle"),
    resultTitle: document.getElementById("resultTitle"),
    transcriptionContent: document.getElementById("transcriptionContent"),
    resultContent: document.getElementById("resultContent")
};

elements.modo.addEventListener("change", () => {
    const modoActual = elements.modo.value;

    if (modoActual === ultimoModoProcesado) {
        elements.sendBtn.disabled = true;
    } else {
        elements.sendBtn.disabled = false;
    }
});

// Verificar que todos los elementos existen
function validateElements() {
    const missingElements = [];
    for (const [key, element] of Object.entries(elements)) {
        if (!element) {
            missingElements.push(key);
        }
    }

    if (missingElements.length > 0) {
        console.warn("Elementos DOM no encontrados:", missingElements);
        // No es crítico si algunos elementos opcionales no existen
        // Solo mostrar warning para depuración
    }
}

// -----------------------------
// Funciones de utilidad
// -----------------------------
function showOverlay() {
    if (elements.overlayLoading) {
        elements.overlayLoading.classList.remove("hidden");
    }
}

function hideOverlay() {
    if (elements.overlayLoading) {
        elements.overlayLoading.classList.add("hidden");
    }
}

async function generateId(nombre, fecha) {
    const encoder = new TextEncoder();
    const data = encoder.encode(nombre + fecha);
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
}

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

// Función segura para parsear markdown
function parseMarkdown(markdown) {
    if (!markdown) return "";
    try {
        // Verificar si marked está disponible
        if (typeof marked !== 'undefined' && marked.parse) {
            return marked.parse(markdown);
        } else {
            console.warn("marked no está disponible, usando texto plano");
            return `<pre>${markdown}</pre>`;
        }
    } catch (error) {
        console.error("Error parseando markdown:", error);
        return `<pre>${markdown}</pre>`;
    }
}

function clearTranscriptionAndResults() {
    if (elements.transcripcionTexto) elements.transcripcionTexto.innerHTML = "";
    if (elements.mdResult) elements.mdResult.innerHTML = "";
    if (elements.multiResults) elements.multiResults.innerHTML = "";
}

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

// -----------------------------
// Manejo de estado del formulario
// -----------------------------
function validateForm() {
    const nombre = elements.nombre?.value?.trim() || "";
    const email = elements.email?.value?.trim() || "";
    const modo = elements.modo?.value || "";
    const emailValido = email.includes("@") && email.includes(".");

    const todoCorrecto = lastRecordingBlob && nombre.length > 0 && emailValido && modo.length > 0;
    if (elements.sendBtn) {
        elements.sendBtn.disabled = !todoCorrecto;
    }
}

function updateSendButtonState() {
    const nombre = elements.nombre?.value?.trim() || "";
    const email = elements.email?.value?.trim() || "";
    const modo = elements.modo?.value?.trim() || "";
    const transcripcion = elements.transcripcionTexto?.textContent?.trim() || "";
    const resultado = elements.mdResult?.textContent?.trim() || "";
    const hayAudio = !!lastRecordingBlob;

    const puedeEnviar = hayAudio &&
        nombre.length > 0 &&
        email.length > 0 &&
        modo.length > 0 &&
        transcripcion.length === 0 &&
        resultado.length === 0;

    if (elements.sendBtn) {
        elements.sendBtn.disabled = !puedeEnviar;
        elements.sendBtn.classList.toggle("disabled", !puedeEnviar);
    }
}

// -----------------------------
// Manejo de sesión
// -----------------------------
function validateSessionName(nombre) {
    if (!nombre && elements.nombre) {
        nombre = elements.nombre.value;
    }

    const trimmed = nombre.trim();
    const isValid = trimmed.length >= 5;   // 🔥 Validación correcta

    // Guardar solo si es válido
    if (isValid) {
        localStorage.setItem("nombreSesion", trimmed);
    }

    // Actualizar etiqueta de sesión
    if (elements.sessionLabel) {
        elements.sessionLabel.textContent = isValid ? trimmed : "Sin sesión";

        if (isValid) {
            elements.sessionLabel.classList.add("session-active");
            elements.sessionLabel.title = "Sesión activa: " + trimmed;
        } else {
            elements.sessionLabel.classList.remove("session-active");
            elements.sessionLabel.title = "No hay sesión activa";
        }
    }

    // Actualizar estado de botones según validez
    if (elements.recordBtn) elements.recordBtn.disabled = !isValid;
    if (elements.stopBtn) elements.stopBtn.disabled = true;
    if (elements.deleteBtn) elements.deleteBtn.disabled = true;
    if (elements.downloadBtn) elements.downloadBtn.disabled = true;
    if (elements.sendBtn) elements.sendBtn.disabled = !isValid;

    // Mostrar/ocultar warning
    if (elements.nameWarning) {
        elements.nameWarning.hidden = isValid;
    }

    return isValid;
}

// -----------------------------
// Grabación de audio
// -----------------------------
function setupRecordingHandlers() {
    if (!elements.recordBtn || !elements.stopBtn) return;

    elements.recordBtn.onclick = async () => {
        audioChunks = [];
        lastRecordingBlob = null;

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
            mediaRecorder.onstop = handleRecordingStop;

            mediaRecorder.start();
            if (elements.statusText) elements.statusText.textContent = "Grabando…";
            elements.recordBtn.disabled = true;
            elements.stopBtn.disabled = false;

            // Añadir clase de animación
            elements.recordBtn.classList.add("recording");
        } catch (error) {
            console.error("Error al acceder al micrófono:", error);
            alert("No se pudo acceder al micrófono. Verifica los permisos.");
        }
    };

    elements.stopBtn.onclick = () => {
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
            if (elements.statusText) elements.statusText.textContent = "Grabación finalizada.";
            if (elements.recordBtn) {
                elements.recordBtn.disabled = false;
                elements.recordBtn.classList.remove("recording");
            }
            if (elements.stopBtn) elements.stopBtn.disabled = true;
        }
    };
}

function handleRecordingStop() {
    lastRecordingBlob = new Blob(audioChunks, { type: "audio/mp3" });

    const audioTmp = new Audio();
    audioTmp.src = URL.createObjectURL(lastRecordingBlob);
    audioTmp.onloadedmetadata = () => {
        lastRecordingDuration = audioTmp.duration;
    };

    updateSendButtonState();

    const url = URL.createObjectURL(lastRecordingBlob);
    if (elements.preview) {
        elements.preview.src = url;
        elements.preview.hidden = false;
    }

    if (elements.recordBtn) elements.recordBtn.disabled = true;

    validateForm();
    if (elements.deleteBtn) elements.deleteBtn.disabled = false;
    if (elements.downloadBtn) elements.downloadBtn.disabled = false;
}

// -----------------------------
// Manejo de archivos de audio
// -----------------------------
function setupFileHandlers() {
    if (elements.downloadBtn) {
        elements.downloadBtn.onclick = () => {
            if (!lastRecordingBlob) return;

            const nombre = elements.nombre?.value?.trim() || "grabacion";
            const url = URL.createObjectURL(lastRecordingBlob);

            const a = document.createElement("a");
            a.href = url;
            a.download = `${nombre}.mp3`;
            a.click();

            URL.revokeObjectURL(url);
        };
    }

    if (elements.deleteBtn) {
        elements.deleteBtn.onclick = () => {
            if (!lastRecordingBlob) {
                if (elements.statusText) elements.statusText.textContent = "No hay grabación que borrar.";
                return;
            }

            if (!confirm("¿Seguro que quieres borrar la grabación? Esta acción no se puede deshacer.")) {
                return;
            }

            audioChunks = [];
            lastRecordingBlob = null;

            enableRecordingAndClearTooltip();

            if (elements.preview) {
                elements.preview.src = "";
                elements.preview.hidden = true;
            }

            if (elements.sendBtn) elements.sendBtn.disabled = true;
            if (elements.deleteBtn) elements.deleteBtn.disabled = true;
            if (elements.downloadBtn) elements.downloadBtn.disabled = true;
            if (elements.recordBtn) elements.recordBtn.disabled = false;

            if (elements.statusText) elements.statusText.textContent = "Grabación borrada.";
            validateForm();
        };
    }

    if (elements.uploadBtn) {
        elements.uploadBtn.onclick = () => elements.fileInput?.click();
    }

    if (elements.fileInput) {
        elements.fileInput.onchange = async (event) => {
            const file = event.target.files[0];
            if (!file) return;

            lastRecordingBlob = file;

            const url = URL.createObjectURL(file);
            if (elements.preview) {
                elements.preview.src = url;
                elements.preview.hidden = false;
            }

            validateForm();
            if (elements.deleteBtn) elements.deleteBtn.disabled = false;
            if (elements.downloadBtn) elements.downloadBtn.disabled = false;
            if (elements.recordBtn) elements.recordBtn.disabled = true;

            disableRecordingWithTooltip();

            if (elements.statusText) elements.statusText.textContent = `Grabación cargada: ${file.name}`;
        };
    }
}

// -----------------------------
// Envío de audio y procesamiento
// -----------------------------
async function sendAudio() {
    const nombre = elements.nombre?.value?.trim() || "";
    const email = elements.email?.value?.trim() || "";
    const modo = elements.modo?.value || "";

    if (!nombre || !email) {
        alert("Debes indicar nombre y email.");
        return;
    }

    // CASO 1: Ya existe transcripción → reutilizar
    if (hasTranscript && lastRecordingName === nombre) {
        await processExistingTranscription(nombre, modo);
        return;
    }

    // CASO 2: Primera vez → enviar audio
    await processNewRecording(nombre, email, modo);
}

async function processExistingTranscription(nombre, modo) {
    const formData = new FormData();
    formData.append("nombre", nombre);
    formData.append("modo", modo);

    showOverlay();

    try {
        const res = await fetch("/api/process-existing", {
            method: "POST",
            body: formData
        });

        const data = await res.json();

        if (data.status === "done") {
            addResultBox(data.mode || modo, data.content || "");
        } else {
            alert("Error procesando la transcripción existente.");
        }
    } catch (err) {
        console.error("Error:", err);
        alert("Error procesando la transcripción existente.");
    } finally {
        hideOverlay();
    }
}

async function processNewRecording(nombre, email, modo) {
    if (!lastRecordingBlob) {
        alert("No hay grabación disponible.");
        return;
    }

    const formData = new FormData();
    formData.append("audio", lastRecordingBlob, `${nombre}.mp3`);
    formData.append("nombre", nombre);
    formData.append("modo", modo);
    formData.append("email", email);

    if (elements.statusText) elements.statusText.textContent = "Procesando audio…";

    showOverlay();

    try {
        console.log("Enviando audio al servidor...");

        const response = await fetch("/api/upload-audio", {
            method: "POST",
            body: formData
            // Nota: NO añadir headers cuando usas FormData
            // El navegador los establecerá automáticamente con el boundary correcto
        });

        console.log("Respuesta recibida, status:", response.status);

        if (!response.ok) {
            // Si el servidor responde con un error HTTP
            const errorText = await response.text();
            console.error("Error del servidor:", response.status, errorText);
            throw new Error(`Error del servidor: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        console.log("Datos recibidos:", data);

        if (data.job_id) {
            lastRecordingName = nombre;
            hasTranscript = true;
            startJobPolling(data.job_id);
        } else if (data.error) {
            throw new Error(data.error);
        } else {
            throw new Error("Respuesta del servidor inválida");
        }
    } catch (err) {
        console.error("Error completo al enviar audio:", err);

        // Mensaje de error más específico
        let errorMessage = "Error al enviar el audio.";

        if (err.name === "TypeError" && err.message.includes("fetch")) {
            errorMessage = "No se pudo conectar con el servidor. Verifica que el servidor esté en ejecución.";
        } else if (err.message.includes("Failed to fetch")) {
            errorMessage = "Error de red. Verifica tu conexión a internet.";
        } else if (err.message.includes("CORS")) {
            errorMessage = "Error de permisos CORS. Contacta al administrador.";
        } else {
            errorMessage = err.message;
        }

        alert(errorMessage);

        if (elements.statusText) {
            elements.statusText.textContent = "Error: " + errorMessage;
        }
    } finally {
        hideOverlay();
    }
}

// -----------------------------
// Polling del estado del job
// -----------------------------
async function startJobPolling(jobId) {
    const checkStatus = async () => {
        try {
            const res = await fetch(`/api/status/${jobId}`);
            const data = await res.json();

            if (elements.statusText) elements.statusText.textContent = getStatusMessage(data.status);

            if (data.status === "processing" || data.status === "running") {
                setTimeout(checkStatus, 3000);
                return;
            }

            if (data.status === "bad_audio") {
                hideOverlay();
                alert("La grabación tiene mala calidad y no se ha podido transcribir.");
                return;
            }

            if (data.status === "done") {
                hasTranscript = true;
                lastRecordingName = elements.nombre?.value?.trim() || "";
                await handleJobCompletion(data);
            }

            hideOverlay();
        } catch (error) {
            console.error("Error en polling:", error);
            hideOverlay();
        }
    };

    checkStatus();
}

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

async function handleJobCompletion(data) {
    // Intentar obtener markdown de la respuesta
    const md = data.markdown || data.resultado || data.md || data.resultado_md;

    if (md && elements.mdResult) {
        elements.mdResult.innerHTML = parseMarkdown(md);
        const resultSection = document.getElementById("result");
        if (resultSection) resultSection.hidden = false;
        if (elements.btnImprimirPDF) elements.btnImprimirPDF.style.display = "inline-block";
    } else {
        // Si no viene en la respuesta, cargar desde archivos
        await loadFromFiles();
    }

    // Cargar transcripción original
    await loadTranscriptionOriginal();

    // Guardar en historial si tenemos ambos
    await saveToHistoryIfComplete();

    updateSendButtonState();
}

async function loadFromFiles() {
    const nombre = normalizeText(elements.nombre?.value?.trim() || "");
    const modo = normalizeText(elements.modo?.value || "");
    const archivoMd = `${nombre}_${modo}.md`;

    try {
        const resMd = await fetch(`/api/resultados/${archivoMd}`);
        if (resMd.ok) {
            const markdown = await resMd.text();
            if (elements.mdResult) {
                elements.mdResult.innerHTML = parseMarkdown(markdown);
                const resultSection = document.getElementById("result");
                if (resultSection) resultSection.hidden = false;
                if (elements.btnImprimirPDF) elements.btnImprimirPDF.style.display = "inline-block";
            }

            ultimoModoProcesado = modo;
            elements.sendBtn.disabled = true;
            elements.recordBtn.disabled = true;

            return markdown;
        }

        disableRecordingWithTooltip();

    } catch (e) {
        console.error("Error cargando markdown:", e);
    }
    return null;
}

async function loadTranscriptionOriginal() {
    const nombre = normalizeText(elements.nombre?.value?.trim() || "");
    const archivoTxt = `${nombre}.txt`;

    try {
        const resTxt = await fetch(`/api/transcripciones/${archivoTxt}`);
        if (resTxt.ok) {
            const texto = await resTxt.text();
            if (elements.transcripcionTexto) {
                elements.transcripcionTexto.innerHTML = parseMarkdown(texto);
                const transcripcionSection = document.getElementById("transcripcion");
                if (transcripcionSection) transcripcionSection.hidden = false;
            }
            return texto;
        }
    } catch (e) {
        console.error("Error cargando transcripción:", e);
    }
    return null;
}

function normalizeText(text) {
    return text.toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "");
}

async function saveToHistoryIfComplete() {
    const markdown = elements.mdResult?.textContent?.trim() || "";
    const texto = elements.transcripcionTexto?.textContent?.trim() || "";

    if (markdown && texto) {
        const nombre = elements.nombre?.value?.trim() || "";
        const modo = elements.modo?.value || "";
        const fecha = new Date().toISOString();
        const id = await generateId(nombre, fecha);

        await saveTranscription({
            id,
            nombre,
            fecha,
            duracion: lastRecordingDuration,
            grabacion: lastRecordingBlob || null,
            // 🔥 ahora siempre guardamos como array (aunque sea una sola)
            transcripcion: [texto],
            resumenes: { [modo]: markdown }
        });
    }
}

// -----------------------------
// Chat y panel lateral
// -----------------------------
function setupChatHandlers() {
    if (!elements.chatToggle || !elements.chatPanel) return;

    elements.chatToggle.onclick = () => {
        const isOpening = !elements.chatPanel.classList.contains("open");
        elements.chatPanel.classList.toggle("open");
        elements.chatToggle.classList.toggle("hidden");
        document.body.classList.toggle("chat-open", isOpening);
    };

    if (elements.chatClose) {
        elements.chatClose.onclick = () => {
            elements.chatPanel.classList.remove("open");
            elements.chatToggle.classList.remove("hidden");
            document.body.classList.remove("chat-open");
        };
    }

    if (elements.chatSend) {
        elements.chatSend.onclick = sendChatMessage;
    }

    if (elements.chatInput) {
        elements.chatInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") sendChatMessage();
        });
    }
}

async function sendChatMessage() {
    const msg = elements.chatInput?.value?.trim() || "";
    if (!msg) return;

    addMessage(msg, "user");
    if (elements.chatInput) elements.chatInput.value = "";
    chatHistory.push({ role: "user", content: msg });

    const aiMsg = addMessage("", "ai", true);
    showOverlay();

    try {
        let textoFinal = "";
        for await (const parcial of enviarPreguntaStreaming(msg)) {
            hideOverlay();
            if (aiMsg) aiMsg.innerHTML = formatAsHTML(parcial);
            textoFinal = parcial;
        }
        chatHistory.push({ role: "assistant", content: textoFinal });
    } catch (e) {
        if (aiMsg) aiMsg.innerHTML = formatAsHTML("Error al procesar la respuesta.");
        console.error("Error en chat:", e);
    } finally {
        hideOverlay();
    }
}

function addMessage(text, sender = "user", returnNode = false) {
    if (!elements.chatMessages) return null;

    const div = document.createElement("div");
    div.className = sender === "user" ? "msg-user" : "msg-ai";
    div.innerHTML = formatAsHTML(text);
    elements.chatMessages.appendChild(div);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    return returnNode ? div : null;
}

async function* enviarPreguntaStreaming(pregunta) {
    const transcripcion = elements.transcripcionTexto?.textContent?.trim() || "";
    const resumen = elements.mdResult?.textContent?.trim() || "";
    const modo = elements.modo?.value || "";

    const payload = {
        message: `Transcripción original:\n${transcripcion}\n\nResultado procesado:\n${resumen}\n\nMi pregunta es:\n${pregunta}`,
        mode: modo
    };

    const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");

    let buffer = "";
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value);
        yield buffer;
    }
}

// -----------------------------
// Historial
// -----------------------------
function setupHistoryHandlers() {
    if (!elements.historyToggle || !elements.historyPanel) return;

    elements.historyToggle.onclick = toggleHistoryPanel;

    if (elements.historyClose) {
        elements.historyClose.onclick = toggleHistoryPanel;
    }

    // Configurar colapsables
    document.querySelectorAll(".collapsible-toggle").forEach(button => {
        button.addEventListener("click", toggleCollapsible);
    });
}

function toggleCollapsible() {
    const isExpanded = this.getAttribute("aria-expanded") === "true";
    const contentId = this.getAttribute("aria-controls");
    const content = document.getElementById(contentId);
    const arrow = this.querySelector(".arrow");

    if (content && arrow) {
        if (isExpanded) {
            content.hidden = true;
            this.setAttribute("aria-expanded", "false");
            arrow.textContent = "▶";
        } else {
            content.hidden = false;
            this.setAttribute("aria-expanded", "true");
            arrow.textContent = "▼";
        }
    }
}

async function toggleHistoryPanel() {
    if (!elements.historyPanel) return;

    const isOpening = !elements.historyPanel.classList.contains("open");

    // Alternar clase en el panel
    elements.historyPanel.classList.toggle("open");

    // Alternar clase en el body
    document.body.classList.toggle("history-open", isOpening);

    // Si se está abriendo, cargar el historial
    if (isOpening) {
        await loadHistoryItems();
    }
}

async function loadHistoryItems() {
    if (!elements.historyList) return;

    elements.historyList.innerHTML = "";
    try {
        const items = await getAllTranscriptions();
        items
            .sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
            .forEach(item => {
                const li = document.createElement("li");
                const fecha = new Date(item.fecha).toLocaleString();
                li.textContent = `${item.nombre} (${fecha})`;
                li.tabIndex = 0;
                li.onclick = () => loadTranscriptionFromHistory(item.id);
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

async function loadTranscriptionFromHistory(id) {
    try {
        const item = await getTranscriptionById(id);
        if (!item) {
            alert("No se encontró la transcripción.");
            return;
        }

        // 🔥 Limpiar todo lo anterior
        clearTranscriptionAndResults();

        // Rellenar nombre
        if (elements.nombre) elements.nombre.value = item.nombre;

        // 🔥 Transcripciones: una o varias
        if (elements.transcripcionTexto) {
            const transcripcionSection = document.getElementById("transcripcion");
            if (transcripcionSection) transcripcionSection.hidden = false;

            if (Array.isArray(item.transcripcion)) {
                renderMultipleTranscriptions(item.transcripcion);
            } else {
                elements.transcripcionTexto.innerHTML = parseMarkdown(item.transcripcion || "");
            }
        }

        // 🔥 Resúmenes guardados (multiResults)
        if (elements.multiResults) {
            elements.multiResults.innerHTML = "";
            elements.multiResults.hidden = false;
            for (const modo in item.resumenes) {
                addResultBox(modo, item.resumenes[modo]);
            }
        }

        // 🔥 Resultado principal según modo actual (si coincide)
        const modoActual = elements.modo?.value || "";
        if (modoActual && item.resumenes && item.resumenes[modoActual] && elements.mdResult) {
            elements.mdResult.innerHTML = parseMarkdown(item.resumenes[modoActual]);
            const resultSection = document.getElementById("result");
            if (resultSection) resultSection.hidden = false;
            if (elements.btnImprimirPDF) elements.btnImprimirPDF.style.display = "inline-block";
        }

        // Cargar grabación si existe
        if (item.grabacion && elements.preview) {
            const url = URL.createObjectURL(item.grabacion);
            elements.preview.src = url;
            elements.preview.hidden = false;
            disableRecordingWithTooltip();
        } else {
            enableRecordingAndClearTooltip();
        }

        lastRecordingName = item.nombre;
        hasTranscript = true;

        // Actualizar sesión
        validateSessionName(item.nombre);
    } catch (error) {
        console.error("Error cargando transcripción del historial:", error);
        alert("Error al cargar la transcripción del historial.");
    }
}

function addResultBox(mode, content) {
    if (!elements.multiResults) return;

    const html = `
    <details class="result-box" open>
        <summary>${mode.toUpperCase()}</summary>
        <div class="markdown-body">${parseMarkdown(content)}</div>
    </details>
    `;
    elements.multiResults.insertAdjacentHTML("beforeend", html);
}

// -----------------------------
// Impresión PDF
// -----------------------------
function setupPrintHandler() {
    if (!elements.btnImprimirPDF) return;

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

// -----------------------------
// Protección contra cerrar/refrescar
// -----------------------------
function setupBeforeUnloadHandler() {
    window.addEventListener("beforeunload", (e) => {
        if (lastRecordingBlob) {
            e.preventDefault();
            e.returnValue = "Estas seguro? Puedes perder la grabación.";
        }
    });
}

// -----------------------------
// Inicialización
// -----------------------------
function init() {
    // Validar que todos los elementos existen
    validateElements();

    // Configurar event listeners del formulario
    if (elements.nombre) {
        elements.nombre.addEventListener("input", () => {
            validateSessionName(elements.nombre.value);
            validateForm();
            updateSendButtonState();
        });
    }

    if (elements.email) {
        elements.email.addEventListener("input", () => {
            validateForm();
            updateSendButtonState();
        });
    }

    if (elements.modo) {
        elements.modo.addEventListener("change", () => {
            validateForm();
            updateSendButtonState();
        });
    }

    // Restaurar sesión guardada
    const nombreGuardado = localStorage.getItem("nombreSesion");
    if (nombreGuardado && elements.nombre) {
        elements.nombre.value = nombreGuardado;
        validateSessionName(nombreGuardado);
    } else {
        // Asegurarse de que el label muestre "Sin sesión" correctamente
        validateSessionName("");
    }

    // Configurar manejadores
    setupRecordingHandlers();
    setupFileHandlers();
    setupChatHandlers();
    setupHistoryHandlers();
    setupPrintHandler();
    setupBeforeUnloadHandler();

    // Configurar botón de enviar
    if (elements.sendBtn) {
        elements.sendBtn.onclick = sendAudio;
    }

    // Inicializar colapsables
    if (elements.transcriptionTitle) {
        const transcriptionButton = elements.transcriptionTitle.querySelector(".collapsible-toggle");
        if (transcriptionButton) {
            transcriptionButton.addEventListener("click", toggleCollapsible);
        }
    }

    if (elements.resultTitle) {
        const resultButton = elements.resultTitle.querySelector(".collapsible-toggle");
        if (resultButton) {
            resultButton.addEventListener("click", toggleCollapsible);
        }
    }
}

function disableRecordingWithTooltip() {
    if (elements.recordBtn) {
        elements.recordBtn.disabled = true;
        elements.recordBtn.title = "Audio cargado — grabación deshabilitada";
    }
}

function enableRecordingAndClearTooltip() {
    if (elements.recordBtn) {
        elements.recordBtn.disabled = false;
        elements.recordBtn.title = "";
    }
}

// Iniciar la aplicación
document.addEventListener("DOMContentLoaded", init);