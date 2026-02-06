/**
 * Configuración para testing de módulos
 * Exporta funciones de test helpers
 */

/**
 * Mock de fetch para testing
 */
export function mockFetch(mockData) {
    return jest.fn(() =>
        Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockData),
            text: () => Promise.resolve(JSON.stringify(mockData)),
            status: 200
        })
    );
}

/**
 * Mock de elementos DOM
 */
export function createMockElements() {
    return {
        recordBtn: { click: jest.fn(), disabled: false, classList: { add: jest.fn(), remove: jest.fn(), toggle: jest.fn() } },
        stopBtn: { click: jest.fn(), disabled: false },
        sendBtn: { click: jest.fn(), disabled: false, classList: { add: jest.fn(), remove: jest.fn(), toggle: jest.fn() } },
        deleteBtn: { click: jest.fn(), disabled: false },
        downloadBtn: { click: jest.fn(), disabled: false },
        uploadBtn: { click: jest.fn(), disabled: false },
        statusText: { textContent: "" },
        preview: { src: "", hidden: true },
        fileInput: { click: jest.fn() },
        nombre: { value: "test", addEventListener: jest.fn() },
        email: { value: "test@test.com", addEventListener: jest.fn() },
        modo: { value: "tecnico", addEventListener: jest.fn(), value: "tecnico" },
        chatToggle: { click: jest.fn(), disabled: false, classList: { toggle: jest.fn(), remove: jest.fn() } },
        chatPanel: { classList: { toggle: jest.fn(), remove: jest.fn(), add: jest.fn() } },
        chatMessages: { appendChild: jest.fn(), scrollTop: 0, scrollHeight: 100 },
        chatInput: { value: "", addEventListener: jest.fn() },
        chatSend: { click: jest.fn(), addEventListener: jest.fn() },
        mdResult: { innerHTML: "", textContent: "" },
        transcripcionTexto: { innerHTML: "", textContent: "" },
        multiResults: { innerHTML: "", insertAdjacentHTML: jest.fn() },
        overlayLoading: { classList: { add: jest.fn(), remove: jest.fn() } },
        btnImprimirPDF: { click: jest.fn(), style: { display: "" } },
        historyToggle: { click: jest.fn(), disabled: false },
        historyPanel: { classList: { toggle: jest.fn(), add: jest.fn(), remove: jest.fn() } },
        historyList: { innerHTML: "", appendChild: jest.fn() },
        historyClose: { click: jest.fn() },
        nameWarning: { hidden: false },
        sessionLabel: { textContent: "Sin sesión", classList: { add: jest.fn(), remove: jest.fn() } }
    };
}

/**
 * Mock de mediaRecorder
 */
export function createMockMediaRecorder() {
    return {
        start: jest.fn(),
        stop: jest.fn(),
        state: "recording",
        ondataavailable: null,
        onstop: null
    };
}

/**
 * Mock de AudioContext
 */
export function createMockAudioContext() {
    return {
        createMediaStreamAudioSourceNode: jest.fn(),
        createAnalyser: jest.fn(() => ({
            connect: jest.fn(),
            getByteFrequencyData: jest.fn()
        }))
    };
}

/**
 * Espera un tiempo determinado
 */
export function waitFor(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Crea un blob de prueba
 */
export function createTestBlob() {
    const data = new Uint8Array([1, 2, 3, 4, 5]);
    return new Blob([data], { type: "audio/mp3" });
}

/**
 * Simula respuesta del servidor
 */
export function createMockServerResponse(data) {
    return {
        ok: true,
        json: () => Promise.resolve(data),
        text: () => Promise.resolve(JSON.stringify(data)),
        status: 200,
        headers: new Map()
    };
}

/**
 * Limpia mocks después de test
 */
export function cleanupMocks() {
    jest.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
}
