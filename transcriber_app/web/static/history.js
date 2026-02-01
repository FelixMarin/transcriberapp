// transcriber_app/web/static/history.js
const DB_NAME = "TranscriberHistory";
const STORE_NAME = "transcripciones";

function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, 1);

        request.onupgradeneeded = () => {
            const db = request.result;
            // 🔥 Clave primaria: id
            db.createObjectStore(STORE_NAME, { keyPath: "id" });
        };

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

export async function saveTranscription(record) {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).put(record);
    return tx.complete;
}

export async function getAllTranscriptions() {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, "readonly");
    const store = tx.objectStore(STORE_NAME);

    return new Promise(resolve => {
        const req = store.getAll();
        req.onsuccess = () => resolve(req.result);
    });
}

export async function getTranscriptionById(id) {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, "readonly");
    const store = tx.objectStore(STORE_NAME);

    return new Promise(resolve => {
        const req = store.get(id);
        req.onsuccess = () => resolve(req.result);
    });
}
