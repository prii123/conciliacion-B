// Configuración dinámica de la URL base
// En producción, usar rutas relativas para evitar problemas de CORS
// En desarrollo local, especificar el puerto
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : window.location.origin;

// Hacer disponible globalmente
window.API_BASE_URL = API_BASE_URL;

// Para compatibilidad con código antiguo
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { API_BASE_URL };
}