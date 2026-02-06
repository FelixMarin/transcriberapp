/**
 * Módulo de gestión de formulario
 * Validación y manejo del formulario principal
 */

import { elements } from "./domElements.js";
import { isValidEmail, isValidName } from "./utils.js";

/**
 * Valida el formulario completo
 */
function validateForm(lastRecordingBlob) {
    const nombre = elements.nombre?.value?.trim() || "";
    const email = elements.email?.value?.trim() || "";
    const modo = elements.modo?.value || "";
    const emailValido = isValidEmail(email);

    const todoCorrecto = lastRecordingBlob && nombre.length > 0 && emailValido && modo.length > 0;
    if (elements.sendBtn) {
        elements.sendBtn.disabled = !todoCorrecto;
    }
}

/**
 * Valida el nombre de la sesión
 */
function validateSessionName(nombre) {
    if (!nombre && elements.nombre) {
        nombre = elements.nombre.value;
    }

    const trimmed = nombre.trim();
    const isValid = isValidName(trimmed);
    const btnNuevaSesion = document.getElementById("btnNuevaSesion");

    // Actualizar etiqueta de sesión
    if (elements.sessionLabel) {
        elements.sessionLabel.textContent = isValid ? trimmed : "Sin sesión";

        if (elements.nameWarning) {
            elements.nameWarning.hidden = isValid;
        }

        if (isValid) {
            elements.sessionLabel.classList.add("session-active");
            elements.sessionLabel.title = "Sesión activa: " + trimmed;
            if (btnNuevaSesion) btnNuevaSesion.disabled = false;
        } else {
            elements.sessionLabel.classList.remove("session-active");
            elements.sessionLabel.title = "No hay sesión activa";
            if (btnNuevaSesion) btnNuevaSesion.disabled = true;
        }
    }

    return isValid;
}

/**
 * Obtiene los valores actuales del formulario
 */
function getFormValues() {
    return {
        nombre: elements.nombre?.value?.trim() || "",
        email: elements.email?.value?.trim() || "",
        modo: elements.modo?.value || ""
    };
}

/**
 * Limpia todos los campos del formulario
 */
function clearFormFields() {
    if (elements.nombre) elements.nombre.value = "";
    if (elements.email) elements.email.value = "";
    if (elements.chatInput) elements.chatInput.value = "";
}

/**
 * Establece el nombre en el formulario
 */
function setFormName(nombre) {
    if (elements.nombre) {
        elements.nombre.value = nombre;
    }
}

/**
 * Obtiene el nombre actual del formulario
 */
function getFormName() {
    return elements.nombre?.value?.trim() || "";
}

/**
 * Obtiene el modo actual del formulario
 */
function getFormMode() {
    return elements.modo?.value || "";
}

export {
    clearFormFields, getFormMode, getFormName, getFormValues, setFormName, validateForm,
    validateSessionName
};

