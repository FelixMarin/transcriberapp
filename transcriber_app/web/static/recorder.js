let mediaRecorder;
let audioChunks = [];

const recordBtn = document.getElementById("recordBtn");
const stopBtn = document.getElementById("stopBtn");
const sendBtn = document.getElementById("sendBtn");
const deleteBtn = document.getElementById("deleteBtn");
const statusText = document.getElementById("status");
const preview = document.getElementById("preview");
const output = document.getElementById("output");

recordBtn.onclick = async () => {
    audioChunks = [];

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

    mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunks, { type: "audio/mp3" });
        const url = URL.createObjectURL(blob);
        preview.src = url;
        preview.style.display = "block";
        sendBtn.disabled = false;
        deleteBtn.disabled = false;
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

sendBtn.onclick = async () => {
    const nombre = document.getElementById("nombre").value.trim();
    const email = document.getElementById("email").value.trim();
    const modo = document.getElementById("modo").value;

    if (!nombre || !email) {
        alert("Debes indicar nombre y email.");
        return;
    }

    const blob = new Blob(audioChunks, { type: "audio/mp3" });
    const formData = new FormData();
    formData.append("audio", blob, `${nombre}.mp3`);
    formData.append("nombre", nombre);
    formData.append("modo", modo);
    formData.append("email", email);

    output.textContent = "Enviando audio y lanzando procesamiento…";

    const res = await fetch("/api/upload-audio", {
        method: "POST",
        body: formData
    });

    const data = await res.json();
    output.textContent = JSON.stringify(data, null, 2);
};

deleteBtn.onclick = () => {
    audioChunks = [];
    preview.src = "";
    preview.style.display = "none";
    sendBtn.disabled = true;
    deleteBtn.disabled = true;
    statusText.textContent = "Grabación borrada.";
};

