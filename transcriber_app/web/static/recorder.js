let mediaRecorder;
let audioChunks = [];
let lastRecordingBlob = null; // Para saber si hay grabación pendiente
let lastRecordingName = null;
let hasTranscript = false;

const recordBtn = document.getElementById("recordBtn");
const stopBtn = document.getElementById("stopBtn");
const sendBtn = document.getElementById("sendBtn");
const deleteBtn = document.getElementById("deleteBtn");
const downloadBtn = document.getElementById("downloadBtn");
const statusText = document.getElementById("status");
const preview = document.getElementById("preview");
const output = document.getElementById("output");
const uploadBtn = document.getElementById("uploadBtn");
const fileInput = document.getElementById("fileInput");
const chatToggle = document.getElementById("chatToggle");
const chatPanel = document.getElementById("chatPanel");
const chatClose = document.getElementById("chatClose");

document.getElementById("nombre").oninput = validateForm;
document.getElementById("email").oninput = validateForm;
document.getElementById("modo").onchange = validateForm;

let chatHistory = [];

document.getElementById("nombre").addEventListener("input", updateSendButtonState);
document.getElementById("email").addEventListener("input", updateSendButtonState);
document.getElementById("modo").addEventListener("change", updateSendButtonState);

// -----------------------------
// Protección contra cerrar/refrescar
// -----------------------------
window.addEventListener("beforeunload", (e) => {
    if (lastRecordingBlob) {
        e.preventDefault();
        e.returnValue = "Estas seguro? Puedes perder la grabación.";
    }
});

function validateForm() {
    const nombre = document.getElementById("nombre").value.trim();
    const email = document.getElementById("email").value.trim();
    const modo = document.getElementById("modo").value;

    const emailValido = email.includes("@") && email.includes(".");

    const todoCorrecto =
        lastRecordingBlob &&
        nombre.length > 0 &&
        emailValido &&
        modo.length > 0;

    sendBtn.disabled = !todoCorrecto;
}

// -----------------------------
// Polling del estado del job
// -----------------------------
function startJobPolling(jobId) {
    const mensajes = {
        processing: "Procesando audio…",
        running: "Procesando audio…",
        done: "Transcripción enviada por email.",
        error: "Error durante el procesamiento.",
        unknown: "Job no encontrado."
    };

    const checkStatus = async () => {
        const res = await fetch(`/api/status/${jobId}`);
        const data = await res.json();

        output.textContent = JSON.stringify(data, null, 2);
        statusText.textContent = mensajes[data.status] || "Estado desconocido.";

        if (data.status === "processing" || data.status === "running") {
            setTimeout(checkStatus, 3000);
            return;
        }

        // 🔥 NUEVO: manejar mala calidad
        if (data.status === "bad_audio") {
            hideOverlay();
            alert("La grabación tiene mala calidad y no se ha podido transcribir.");
            return;
        }

        // 🔥 NUEVO: marcar que ya existe transcripción
        if (data.status === "done") {
            hasTranscript = true;
            lastRecordingName = document.getElementById("nombre").value.trim();
        }

        hideOverlay();

        // --- resto de tu código tal cual ---
        if (data.markdown || data.resultado || data.md) {
            const md = data.markdown || data.resultado || data.md;
            document.getElementById("mdResult").innerHTML = marked.parse(md);
        } else {
            const md = data.resultado_md || data.markdown || data.resultado || data.md;
            if (md) {
                document.getElementById("mdResult").innerHTML = marked.parse(md);
            } else {
                // Normalizar nombre y modo (sin tildes)
                const nombre = document.getElementById("nombre").value.trim()
                    .toLowerCase()
                    .normalize("NFD")
                    .replace(/[\u0300-\u036f]/g, "");

                const modo = document.getElementById("modo").value
                    .toLowerCase()
                    .normalize("NFD")
                    .replace(/[\u0300-\u036f]/g, "");

                const archivoMd = `${nombre}_${modo}.md`;
                const archivoTxt = `${nombre}.txt`;

                // Cargar MARKDOWN
                try {
                    const resMd = await fetch(`/api/resultados/${archivoMd}`);
                    if (resMd.ok) {
                        const markdown = await resMd.text();
                        document.getElementById("mdResult").innerHTML = marked.parse(markdown);
                        document.getElementById("result").style.display = "block";
                        document.getElementById("btnImprimirPDF").style.display = "inline-block";
                        updateSendButtonState();
                    } else {
                        document.getElementById("btnImprimirPDF").style.display = "none";
                        document.getElementById("mdResult").innerHTML =
                            "<p>No se pudo cargar el Markdown generado.</p>";
                    }
                } catch (e) {
                    document.getElementById("btnImprimirPDF").style.display = "none";
                    document.getElementById("mdResult").innerHTML =
                        "<p>Error al intentar cargar el Markdown.</p>";
                }

                // Cargar TRANSCRIPCIÓN ORIGINAL
                try {
                    const resTxt = await fetch(`/api/transcripciones/${archivoTxt}`);
                    if (resTxt.ok) {
                        const texto = await resTxt.text();
                        document.getElementById("transcripcionTexto").textContent = texto;
                        document.getElementById("transcripcion").style.display = "block";
                        updateSendButtonState();
                    } else {
                        document.getElementById("transcripcionTexto").textContent =
                            "No se pudo cargar la transcripción original.";
                    }
                } catch (e) {
                    document.getElementById("transcripcionTexto").textContent =
                        "Error al cargar la transcripción original.";
                }

                chatPanel.classList.remove("open");
                chatHistory = [];
                chatMessages.innerHTML = "";
                updateSendButtonState();
            }
        }
    };

    checkStatus();
}

// -----------------------------
// Grabación
// -----------------------------
recordBtn.onclick = async () => {
    audioChunks = [];
    lastRecordingBlob = null;

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

    mediaRecorder.onstop = () => {
        lastRecordingBlob = new Blob(audioChunks, { type: "audio/mp3" });
        updateSendButtonState();

        const url = URL.createObjectURL(lastRecordingBlob);
        preview.src = url;
        preview.style.display = "block";

        validateForm();
        deleteBtn.disabled = false;
        downloadBtn.disabled = false;
    };

    mediaRecorder.start();
    statusText.textContent = "Grabando…";
    recordBtn.disabled = true;
    stopBtn.disabled = false;
};

stopBtn.onclick = () => {
    mediaRecorder.stop();
    statusText.textContent = "Grabación finalizada.";
    recordBtn.disabled = false;
    stopBtn.disabled = true;
};

// -----------------------------
// Descargar grabación
// -----------------------------
downloadBtn.onclick = () => {
    if (!lastRecordingBlob) return;

    const nombre = document.getElementById("nombre").value.trim() || "grabacion";
    const url = URL.createObjectURL(lastRecordingBlob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `${nombre}.mp3`;
    a.click();

    URL.revokeObjectURL(url);
};

// -----------------------------
// Enviar audio o reutilizar transcripción
// -----------------------------
sendBtn.onclick = async () => {
    const nombre = document.getElementById("nombre").value.trim();
    const email = document.getElementById("email").value.trim();
    const modo = document.getElementById("modo").value;

    if (!nombre || !email) {
        alert("Debes indicar nombre y email.");
        return;
    }

    // -----------------------------------------
    // CASO 1: YA EXISTE TRANSCRIPCIÓN → NO reenviar audio
    // -----------------------------------------
    if (hasTranscript && lastRecordingName === nombre) {

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
                addResultBox(data.mode, data.content);
            } else {
                alert("Error procesando la transcripción existente.");
            }

        } catch (err) {
            console.error("Error:", err);
            alert("Error procesando la transcripción existente.");
        } finally {
            hideOverlay();
        }

        return;
    }

    // -----------------------------------------
    // CASO 2: PRIMERA VEZ → enviar audio
    // -----------------------------------------
    const blob = lastRecordingBlob;
    if (!blob) {
        alert("No hay grabación disponible.");
        return;
    }

    const formData = new FormData();
    formData.append("audio", blob, `${nombre}.mp3`);
    formData.append("nombre", nombre);
    formData.append("modo", modo);
    formData.append("email", email);

    output.textContent = "Enviando audio y lanzando procesamiento…";
    statusText.textContent = "Procesando audio…";

    showOverlay();

    try {
        const res = await fetch("/api/upload-audio", {
            method: "POST",
            body: formData
        });

        const data = await res.json();
        output.textContent = JSON.stringify(data, null, 2);

        if (data.job_id) {
            lastRecordingName = nombre;
            hasTranscript = true;
            startJobPolling(data.job_id);
        }

    } catch (err) {
        console.error("Error al enviar audio:", err);
        alert("Error al enviar el audio o iniciar el procesamiento.");
    }
};

// -----------------------------
// Borrar grabación
// -----------------------------
deleteBtn.onclick = () => {
    if (!lastRecordingBlob) {
        statusText.textContent = "No hay grabación que borrar.";
        return;
    }

    const confirmar = confirm("¿Seguro que quieres borrar la grabación? Esta acción no se puede deshacer.");

    if (!confirmar) {
        return;
    }

    audioChunks = [];
    lastRecordingBlob = null;

    preview.src = "";
    preview.style.display = "none";

    sendBtn.disabled = true;
    deleteBtn.disabled = true;
    downloadBtn.disabled = true;

    statusText.textContent = "Grabación borrada.";
    validateForm();
};

// -----------------------------
// Cargar grabación desde archivo
// -----------------------------
uploadBtn.onclick = () => {
    fileInput.click();
};

fileInput.onchange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Guardamos la grabación cargada como si fuera una grabación hecha
    lastRecordingBlob = file;

    const url = URL.createObjectURL(file);
    preview.src = url;
    preview.style.display = "block";

    validateForm();
    deleteBtn.disabled = false;
    downloadBtn.disabled = false;

    statusText.textContent = `Grabación cargada: ${file.name}`;
};

document.querySelectorAll(".collapsible").forEach(header => {
    header.addEventListener("click", () => {
        const content = header.nextElementSibling;
        const isOpen = header.classList.contains("open");

        if (isOpen) {
            content.style.display = "none";
            header.classList.remove("open");
            header.querySelector(".arrow").textContent = "▶";
        } else {
            content.style.display = "block";
            header.classList.add("open");
            header.querySelector(".arrow").textContent = "▼";
        }
    });
});

// -----------------------------
// Panel lateral del chat
// -----------------------------
chatToggle.onclick = () => {
    chatPanel.classList.add("open");
    chatToggle.classList.add("hidden");
};

chatClose.onclick = () => {
    chatPanel.classList.remove("open");
    chatToggle.classList.remove("hidden");
};

const chatMessages = document.getElementById("chatMessages");
const chatInput = document.getElementById("chatInput");
const chatSend = document.getElementById("chatSend");

function addMessage(text, sender = "user", returnNode = false) {
    const div = document.createElement("div");
    div.className = sender === "user" ? "msg-user" : "msg-ai";
    div.innerHTML = formatAsHTML(text);
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return returnNode ? div : null;
}

async function enviarPreguntaAlModelo(pregunta) {
    const transcripcion = document.getElementById("transcripcionTexto").textContent;
    const resumen = document.getElementById("mdResult").textContent;

    const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            transcripcion,
            resumen,
            pregunta,
            historial: chatHistory
        })
    });

    const data = await res.json();
    return data.respuesta;
}

chatSend.onclick = async () => {
    const msg = chatInput.value.trim();
    if (!msg) return;

    addMessage(msg, "user");
    chatInput.value = "";

    chatHistory.push({ role: "user", content: msg });

    const aiMsg = addMessage("", "ai", true);

    showOverlay();

    try {
        let textoFinal = "";

        for await (const parcial of enviarPreguntaStreaming(msg)) {
            hideOverlay();
            let texto = parcial;

            // Intentar extraer el campo "response"
            try {
                const json = JSON.parse(parcial);
                if (json.response) {
                    texto = json.response;
                }
            } catch (e) {
                // Si no es JSON válido, dejamos el texto tal cual
            }

            aiMsg.innerHTML = formatAsHTML(texto);

            textoFinal = parcial;
        }

        chatHistory.push({ role: "assistant", content: textoFinal });

    } catch (e) {
        aiMsg.innerHTML = formatAsHTML("Error al procesar la respuesta.");
    } finally {
        hideOverlay();
    }
};

// -----------------------------
// Overlay + spinner
// -----------------------------

function showOverlay() {
    document.getElementById("overlayLoading").classList.remove("hidden");
}

function hideOverlay() {
    document.getElementById("overlayLoading").classList.add("hidden");
}


// -----------------------------
// Botón Procesar activado/desactivado
// -----------------------------
function updateSendButtonState() {
    const nombre = document.getElementById("nombre").value.trim();
    const email = document.getElementById("email").value.trim();
    const modo = document.getElementById("modo").value.trim();

    const transcripcion = document.getElementById("transcripcionTexto").textContent.trim();
    const resultado = document.getElementById("mdResult").textContent.trim();

    const hayAudio = !!lastRecordingBlob;

    const puedeEnviar =
        hayAudio &&
        nombre.length > 0 &&
        email.length > 0 &&
        modo.length > 0 &&
        transcripcion.length === 0 &&
        resultado.length === 0;

    sendBtn.disabled = !puedeEnviar;
    sendBtn.classList.toggle("disabled", !puedeEnviar);
}

// -----------------------------
// Streaming de la respuesta del modelo
// -----------------------------
async function enviarPreguntaStreaming(pregunta) {
    const transcripcion = document.getElementById("transcripcionTexto").textContent.trim();
    const resumen = document.getElementById("mdResult").textContent.trim();
    const modo = document.getElementById("modo").value;

    const payload = {
        message: `
Transcripción original:
${transcripcion}

Resultado procesado:
${resumen}

Mi pregunta es:
${pregunta}
        `.trim(),
        mode: modo
    };

    const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");

    return {
        async *[Symbol.asyncIterator]() {
            let buffer = "";
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value);
                yield buffer;
            }
        }
    };
}

// -----------------------------
// Formatear texto como HTML
// -----------------------------
function formatAsHTML(text) {
    // Escapar HTML básico
    const escaped = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // Convertir saltos de línea en <br>
    const withBreaks = escaped.replace(/\n/g, "<br>");

    // Convertir listas numeradas y con viñetas en <ul>/<ol>
    const formatted = withBreaks
        .replace(/•\s/g, "•&nbsp;") // viñetas
        .replace(/^\d+\.\s/gm, match => `<strong>${match}</strong>`); // numeradas

    return formatted;
}

// -----------------------------
// Imprimir PDF
// -----------------------------
document.getElementById("btnImprimirPDF").onclick = () => {
    const contenido = document.getElementById("mdResult").innerHTML;

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

// -----------------------------
// Validar nombre de grabación único
// -----------------------------
async function validateName(name) {
    const warning = document.getElementById("name-warning");

    if (!name.trim()) {
        warning.style.display = "none";
        return;
    }

    try {
        const res = await fetch(`/check-name?name=${encodeURIComponent(name)}`);
        const data = await res.json();

        if (data.exists) {
            warning.textContent = "⚠ Ya existe una grabación con ese nombre";
            warning.style.display = "block";
        } else {
            warning.style.display = "none";
        }
    } catch (err) {
        console.error("Error comprobando nombre:", err);
    }
}

function addResultBox(mode, content) {
    const container = document.getElementById("multiResults");

    const html = `
    <details class="result-box" open>
        <summary>${mode.toUpperCase()}</summary>
        <div class="markdown-body">${marked.parse(content)}</div>
    </details>
    `;

    container.insertAdjacentHTML("beforeend", html);
}

