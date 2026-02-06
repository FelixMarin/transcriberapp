/**
 * Módulo de almacenamiento de historial (IndexedDB)
 * Gestiona la persistencia de transcripciones en la base de datos del navegador
 */

const DB_NAME = "TranscriberHistory";
const STORE_NAME = "transcripciones";

/**
 * Abre o crea la base de datos IndexedDB
 */
function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, 1);

        request.onupgradeneeded = () => {
            const db = request.result;
            db.createObjectStore(STORE_NAME, { keyPath: "id" });
        };

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

/**
 * Guarda una transcripción en la base de datos
 */
async function saveTranscription(record) {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, "readwrite");
    const store = tx.objectStore(STORE_NAME);

    return new Promise((resolve, reject) => {
        const req = store.put(record);
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);

        // Opcional: manejar completado de transacción
        tx.oncomplete = () => console.log("Transacción completada");
        tx.onerror = () => console.error("Error en transacción:", tx.error);
    });
}

/**
 * Obtiene todas las transcripciones
 */
async function getAllTranscriptions() {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, "readonly");
    const store = tx.objectStore(STORE_NAME);

    return new Promise(resolve => {
        const req = store.getAll();
        req.onsuccess = () => resolve(req.result);
    });
}

/**
 * Obtiene una transcripción por ID
 */
async function getTranscriptionById(id) {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, "readonly");
    const store = tx.objectStore(STORE_NAME);

    return new Promise(resolve => {
        const req = store.get(id);
        req.onsuccess = () => resolve(req.result);
    });
}

/**
 * Obtiene la última transcripción por nombre
 */
async function getLatestTranscriptionByName(name) {
    const all = await getAllTranscriptions();
    const matches = all.filter(t => t.nombre === name);

    if (matches.length === 0) return null;

    // Ordenar por fecha descendente y devolver la primera
    return matches.sort((a, b) => new Date(b.fecha) - new Date(a.fecha))[0];
}

/**
 * Actualiza el historial de chat de una sesión
 */
async function updateChatHistory(id, chatHistory) {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, "readwrite");
    const store = tx.objectStore(STORE_NAME);

    const record = await new Promise(resolve => {
        const req = store.get(id);
        req.onsuccess = () => resolve(req.result);
    });

    if (record) {
        record.chat = chatHistory;
        return new Promise((resolve, reject) => {
            const req = store.put(record);
            req.onsuccess = () => resolve(req.result);
            req.onerror = () => reject(req.error);
        });
    }
}

/**
 * Elimina una transcripción de la base de datos
 */
async function deleteTranscription(id) {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, "readwrite");
    const store = tx.objectStore(STORE_NAME);

    return new Promise((resolve, reject) => {
        const req = store.delete(id);
        req.onsuccess = () => resolve(true);
        req.onerror = () => reject(req.error);
    });
}

export {
    deleteTranscription, getAllTranscriptions,
    getLatestTranscriptionByName,
    getTranscriptionById,
    saveTranscription,
    updateChatHistory
};

