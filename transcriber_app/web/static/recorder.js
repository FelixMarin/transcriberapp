let mediaRecorder;
let audioChunks = [];
let lastRecordingBlob = null; // Para saber si hay grabación pendiente

const recordBtn = document.getElementById("recordBtn");
const stopBtn = document.getElementById("stopBtn");
const sendBtn = document.getElementById("sendBtn");
const deleteBtn = document.getElementById("deleteBtn");
const downloadBtn = document.getElementById("downloadBtn");
const statusText = document.getElementById("status");
const preview = document.getElementById("preview");
const output = document.getElementById("output");

document.getElementById("nombre").oninput = validateForm;
document.getElementById("email").oninput = validateForm;
document.getElementById("modo").onchange = validateForm;

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
// Enviar audio
// -----------------------------
sendBtn.onclick = async () => {
    const nombre = document.getElementById("nombre").value.trim();
    const email = document.getElementById("email").value.trim();
    const modo = document.getElementById("modo").value;

    if (!nombre || !email) {
        alert("Debes indicar nombre y email.");
        return;
    }

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

    const res = await fetch("/api/upload-audio", {
        method: "POST",
        body: formData
    });

    const data = await res.json();
    output.textContent = JSON.stringify(data, null, 2);

    if (data.job_id) {
        startJobPolling(data.job_id);
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

const uploadBtn = document.getElementById("uploadBtn");
const fileInput = document.getElementById("fileInput");

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
