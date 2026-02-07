/**
 * Módulo de API y comunicación con el servidor
 * Gestiona todas las peticiones fetch al backend
 */

import { hideOverlay, setStatusText, showOverlay } from "./ui.js";
import { normalizeText } from "./utils.js";

/**
 * Procesa una transcripción existente con un nuevo modo
 */
async function processExistingTranscription(nombre, modo, transcription = null) {
    const formData = new FormData();
    formData.append("nombre", nombre);
    formData.append("modo", modo);

    if (transcription) {
        formData.append("transcription", transcription);
    }

    showOverlay();

    try {
        const response = await fetch("/api/process-existing", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (data.status === "done") {
            // Si el backend no devuelve el contenido directamente, lo buscamos
            let mdContent = data.content || data.markdown || data.resultado || "";

            if (!mdContent) {
                console.log("Contenido no recibido en respuesta directa. Fetching explícito...");
                const fetchedMd = await loadMarkdownResult(nombre, modo);
                if (fetchedMd) mdContent = fetchedMd;
            }

            return {
                success: true,
                mode: data.mode || modo,
                content: mdContent
            };
        } else {
            return {
                success: false,
                error: "Error procesando la transcripción existente."
            };
        }
    } catch (err) {
        console.error("Error:", err);
        return {
            success: false,
            error: "Error procesando la transcripción existente."
        };
    } finally {
        hideOverlay();
    }
}

/**
 * Envía un nuevo archivo de audio al servidor
 */
async function uploadAudio(audioBlob, nombre, modo, email) {
    if (!audioBlob) {
        return {
            success: false,
            error: "No hay grabación disponible."
        };
    }

    const formData = new FormData();
    // Determinar extensión según MIME type
    let extension = "webm";
    if (audioBlob.type.includes("mp4") || audioBlob.type.includes("aac")) {
        extension = "m4a";
    } else if (audioBlob.type.includes("ogg")) {
        extension = "ogg";
    }

    formData.append("audio", audioBlob, `${nombre}.${extension}`);
    formData.append("nombre", nombre);
    formData.append("modo", modo);
    formData.append("email", email);

    setStatusText("Procesando audio…");
    showOverlay();

    try {
        console.log("Enviando audio al servidor...");

        const response = await fetch("/api/upload-audio", {
            method: "POST",
            body: formData
        });

        console.log("Respuesta recibida, status:", response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error("Error del servidor:", response.status, errorText);
            throw new Error(`Error del servidor: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        console.log("Datos recibidos:", data);

        if (data.job_id) {
            // NOTA: NO ocultamos el overlay aquí porque empieza el polling
            return {
                success: true,
                jobId: data.job_id
            };
        } else if (data.error) {
            throw new Error(data.error);
        } else {
            throw new Error("Respuesta del servidor inválida");
        }
    } catch (err) {
        console.error("Error completo al enviar audio:", err);
        hideOverlay(); // Ocultar si hay error inicial

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

        return {
            success: false,
            error: errorMessage
        };
    }
}

/**
 * Verifica el estado de un job en el servidor
 */
async function checkJobStatus(jobId) {
    try {
        const res = await fetch(`/api/status/${jobId}`);
        const data = await res.json();
        return data;
    } catch (error) {
        console.error("Error en polling:", error);
        throw error;
    }
}

/**
 * Carga un archivo markdown de resultados
 */
async function loadMarkdownResult(nombre, modo) {
    const normalizedNombre = normalizeText(nombre);
    const normalizedModo = normalizeText(modo);
    const archivoMd = `${normalizedNombre}_${normalizedModo}.md`;

    try {
        const res = await fetch(`/api/resultados/${archivoMd}`);
        if (res.ok) {
            return await res.text();
        }
        return null;
    } catch (e) {
        console.error("Error cargando markdown:", e);
        return null;
    }
}

/**
 * Carga un archivo de transcripción
 */
async function loadTranscriptionFile(nombre) {
    const normalizedNombre = normalizeText(nombre);
    const archivoTxt = `${normalizedNombre}.txt`;

    try {
        const res = await fetch(`/api/transcripciones/${archivoTxt}`);
        if (res.ok) {
            return await res.text();
        }
        return null;
    } catch (e) {
        console.error("Error cargando transcripción:", e);
        return null;
    }
}

/**
 * Stream de chat desde el servidor
 */
async function* chatStream(message, mode, transcripcion, resumen) {
    const payload = {
        message: `Transcripción original:\n${transcripcion}\n\nResultado procesado:\n${resumen}\n\nMi pregunta es:\n${message}`,
        mode: mode
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
        const chunk = decoder.decode(value);
        yield chunk;
    }
}

export {
    chatStream, checkJobStatus,
    loadMarkdownResult,
    loadTranscriptionFile, processExistingTranscription,
    uploadAudio
};

