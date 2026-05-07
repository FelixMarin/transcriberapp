/**
 * Lógica de autenticación OAuth2 para la página de login
 * TranscriberApp
 * 
 * El flujo OAuth2 se maneja completamente a través del backend
 * para evitar problemas de CORS.
 * 
 * Flujo:
 * 1. Frontend llama a POST /api/auth/oauth2/start
 * 2. Backend genera la URL de autorización y la devuelve
 * 3. Frontend redirige al usuario a esa URL
 * 4. El usuario se autentica en el servidor OAuth2
 * 5. El servidor OAuth2 redirige de vuelta a /oauth/callback
 * 6. Backend maneja el callback y crea la sesión
 */

// Esta configuración se mantiene por compatibilidad pero no se utiliza
const OAUTH2_CONFIG = {
    _deprecated: true
};

/**
 * Genera un code_verifier válido para PKCE (43-128 caracteres)
 */
function generateCodeVerifier() {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return btoa(String.fromCharCode.apply(null, array))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=/g, '');
}

/**
 * Genera un code_challenge desde un code_verifier usando SHA-256
 */
async function generateCodeChallenge(verifier) {
    const encoder = new TextEncoder();
    const data = encoder.encode(verifier);
    const digest = await crypto.subtle.digest('SHA-256', data);
    return btoa(String.fromCharCode.apply(null, new Uint8Array(digest)))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=/g, '');
}

/**
 * Inicia el flujo OAuth2
 * Llama al backend para obtener la URL de autorización
 */
async function startOAuth2Flow() {
    const btn = document.getElementById('oauth-login-btn');
    btn.disabled = true;
    btn.textContent = 'Preparando autenticación...';
    
    try {
        // DEBUG: Log para verificar que se ejecuta el código nuevo
        console.log('=== START_OAUTH2FLOW EJECUTANDO (CÓDIGO NUEVO) ===');
        
        // El flujo OAuth2 se maneja completamente en el backend para evitar problemas de CORS
        // Primero pedimos al backend que prepare la sesión y nos dé la URL de autorización
        const response = await fetch('/api/auth/oauth2/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        console.log('Response status:', response.status);
        const data = await response.json();
        console.log('Response data:', data);
        
        if (!data.success) {
            throw new Error(data.error || 'Error al iniciar sesión');
        }
        
        // El backend nos devuelve la URL de autorización completa
        btn.textContent = 'Redirigiendo...';
        console.log('Authorization URL:', data.authorization_url);
        window.location.href = data.authorization_url;
        
    } catch (error) {
        console.error('=== ERROR EN START_OAUTH2FLOW ===');
        console.error('Error:', error);
        btn.disabled = false;
        btn.textContent = 'Iniciar sesión';
        showError('Error al iniciar OAuth2: ' + error.message);
    }
}

/**
 * Muestra un mensaje de error en la página de login
 * @param {string} message - Mensaje de error a mostrar
 */
function showError(message) {
    // Limpiar mensaje si contiene HTML (errores HTTP raw)
    const containsHtml = message.includes("<!DOCTYPE") || message.includes("<html");
    if (containsHtml) {
        if (message.includes("502")) {
            message = "El servidor de autenticación está temporalmente indisponible. Por favor, inténtalo de nuevo en unos minutos.";
        } else if (message.includes("503")) {
            message = "Servicio de autenticación temporalmente no disponible. Por favor, inténtalo más tarde.";
        } else if (message.includes("504")) {
            message = "Tiempo de espera agotado con el servidor de autenticación. Inténtalo de nuevo.";
        } else if (message.includes("Failed to fetch") || message.includes("NetworkError")) {
            message = "No se pudo conectar con el servidor de autenticación. Verifica tu conexión a internet.";
        } else {
            message = "Error de conexión. Por favor, inténtalo más tarde.";
        }
    }
    
    const container = document.getElementById('login-container');
    container.innerHTML = 
        '<h2>Transcriber<span>App</span></h2>' +
        '<p class="error-msg">' + message + '</p>' +
        '<button type="button" id="retry-btn" class="oauth-btn">Volver a intentar</button>';
    
    document.getElementById('retry-btn').addEventListener('click', () => {
        window.location.href = '/login';
    });
}

/**
 * Canjea el código de autorización por un token de acceso
 * @param {string} code - Código de autorización recibido del servidor OAuth2
 * @param {string} codeVerifier - Code verifier generado durante el inicio del flujo
 * @returns {Promise<object>} - Token de acceso y otros datos
 */
async function exchangeCodeForToken(code, codeVerifier) {
    console.log('Fetching /api/auth/exchange-token');
    const tokenResponse = await fetch('/api/auth/exchange-token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
            code: code,
            code_verifier: codeVerifier
        })
    });
    
    console.log('Response status:', tokenResponse.status);
    console.log('Response headers:', Object.fromEntries(tokenResponse.headers.entries()));
    
    if (!tokenResponse.ok) {
        const status = tokenResponse.status;
        let errorMessage;
        
        // Intentar obtener detalle del JSON
        const contentType = tokenResponse.headers.get("content-type") || "";
        if (contentType.includes("application/json")) {
            try {
                const data = await tokenResponse.json();
                errorMessage = data.error || data.message || "";
            } catch (e) {
                errorMessage = "";
            }
        }
        
        if (!errorMessage) {
            switch (status) {
                case 502:
                    errorMessage = "El servidor de autenticación está temporalmente indisponible. Por favor, inténtalo de nuevo en unos minutos.";
                    break;
                case 503:
                    errorMessage = "Servicio de autenticación temporalmente no disponible. Por favor, inténtalo más tarde.";
                    break;
                case 504:
                    errorMessage = "Tiempo de espera agotado. Inténtalo de nuevo.";
                    break;
                case 500:
                    errorMessage = "Error interno del servidor. Por favor, inténtalo más tarde.";
                    break;
                default:
                    errorMessage = "Error en la autenticación. Por favor, inténtalo de nuevo.";
            }
        }
        
        console.error('Error response:', errorMessage);
        throw new Error(errorMessage);
    }
    
    const loginSuccess = tokenResponse.headers.get('X-Login-Success');
    console.log('Login success header:', loginSuccess);
    
    const data = await tokenResponse.json();
    console.log('Response data:', data);
    return data;
}

/**
 * Obtiene información del usuario usando el token de acceso
 * @param {string} accessToken - Token de acceso
 * @returns {Promise<object|null>} - Información del usuario
 */
async function getUserInfo(accessToken) {
    const response = await fetch('/api/auth/userinfo', {
        headers: {
            'Authorization': 'Bearer ' + accessToken
        }
    });
    
    if (response.ok) {
        return response.json();
    }
    return null;
}

/**
 * Maneja el callback de OAuth2 cuando la página se carga con parámetros
 * Verifica si hay un código de autorización o error en la URL
 */
function handleOAuthCallback() {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const error = params.get('error');
    const state = params.get('state');
    const errorDescription = params.get('error_description');
    
    if (error) {
        showError(error + (errorDescription ? ': ' + errorDescription : ''));
        return;
    }
    
    if (code) {
        // Extraer code_verifier del state codificado
        let codeVerifier = null;
        let originalState = null;
        
        if (state) {
            try {
                let paddedState = state.replace(/-/g, '+').replace(/_/g, '/');
                const padding = 4 - paddedState.length % 4;
                if (padding !== 4) {
                    paddedState += '='.repeat(padding);
                }
                
                const stateData = JSON.parse(atob(paddedState));
                originalState = stateData.s;
                codeVerifier = stateData.v;
            } catch (e) {
                originalState = state;
                codeVerifier = sessionStorage.getItem('oauth_code_verifier');
            }
        }
        
        // Verificar state para prevenir CSRF
        const savedState = sessionStorage.getItem('oauth_state');
        if (originalState && savedState && originalState !== savedState) {
            showError('State mismatch - posible ataque CSRF');
            return;
        }
        
        if (!codeVerifier) {
            codeVerifier = sessionStorage.getItem('oauth_code_verifier');
        }
        
        if (!codeVerifier) {
            showError('Code verifier no encontrado. Intenta de nuevo.');
            return;
        }
        
        // Mostrar estado de carga
        const container = document.getElementById('login-container');
        container.innerHTML = '<div class="loading"><h2>Completando autenticación...</h2><p>Por favor espera</p></div>';
        
        console.log('Exchanging code for token:', { code: code.substring(0, 20), codeVerifier: codeVerifier ? codeVerifier.substring(0, 20) : 'null' });
        
        // Intercambiar código por token
        exchangeCodeForToken(code, codeVerifier)
            .then(async (tokens) => {
                console.log('Tokens received:', tokens);
                
                if (!tokens.access_token) {
                    console.error('No access_token in response:', tokens);
                    showError('No se recibió access_token. Response: ' + JSON.stringify(tokens));
                    return;
                }
                
                // Guardar tokens en localStorage
                localStorage.setItem('access_token', tokens.access_token);
                if (tokens.refresh_token) {
                    localStorage.setItem('refresh_token', tokens.refresh_token);
                }
                
                // Limpiar sessionStorage
                sessionStorage.removeItem('oauth_code_verifier');
                sessionStorage.removeItem('oauth_state');
                
                // Redirigir a página principal
                console.log('Redirecting to /');
                window.location.href = '/';
            })
            .catch((err) => {
                console.error('Error:', err);
                // Limpiar mensaje si contiene HTML
                let message = err.message || "Error desconocido";
                const containsHtml = message.includes("<!DOCTYPE") || message.includes("<html");
                if (containsHtml) {
                    if (message.includes("502")) {
                        message = "El servidor de autenticación está temporalmente indisponible. Por favor, inténtalo de nuevo en unos minutos.";
                    } else if (message.includes("503")) {
                        message = "Servicio de autenticación temporalmente no disponible. Por favor, inténtalo más tarde.";
                    } else if (message.includes("504")) {
                        message = "Tiempo de espera agotado. Inténtalo de nuevo.";
                    } else if (message.includes("Failed to fetch") || message.includes("NetworkError")) {
                        message = "No se pudo conectar con el servidor de autenticación. Verifica tu conexión a internet.";
                    } else {
                        message = "Error de conexión. Por favor, inténtalo más tarde.";
                    }
                }
                showError('Error al completar autenticación: ' + message);
            });
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Manejar callback de OAuth2 si hay parámetros en la URL
    handleOAuthCallback();
    
    // Event listener para el botón de login
    const loginBtn = document.getElementById('oauth-login-btn');
    if (loginBtn) {
        loginBtn.addEventListener('click', startOAuth2Flow);
    }
});

// Exportar funciones para testing (si es necesario)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        generateCodeVerifier,
        generateCodeChallenge,
        startOAuth2Flow,
        showError,
        exchangeCodeForToken,
        getUserInfo,
        handleOAuthCallback
    };
}
