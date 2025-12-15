/**
 * MÓDULO DE AUTENTICACIÓN
 * Maneja el token JWT usando cookies y las peticiones autenticadas
 */

const Auth = {
    TOKEN_KEY: 'token',
    // TOKEN_KEY: 'access_token',

    /**
     * Obtiene el token de las cookies
     */
    getToken() {
        const name = this.TOKEN_KEY + "=";
        const decodedCookie = decodeURIComponent(document.cookie);
        const cookieArray = decodedCookie.split(';');
        
        for (let i = 0; i < cookieArray.length; i++) {
            let cookie = cookieArray[i].trim();
            if (cookie.indexOf(name) === 0) {
                return cookie.substring(name.length, cookie.length);
            }
        }
        return null;
    },

    /**
     * Guarda el token en cookies
     * @param {string} token - Token JWT
     * @param {number} expirationMinutes - Minutos de expiración (default: 30)
     */
    setToken(token, expirationMinutes = 30) {
        const d = new Date();
        d.setTime(d.getTime() + (expirationMinutes * 60 * 1000));
        const expires = "expires=" + d.toUTCString();
        document.cookie = `${this.TOKEN_KEY}=${token};${expires};path=/;SameSite=Lax`;
    },

    /**
     * Elimina el token de las cookies
     */
    removeToken() {
        document.cookie = `${this.TOKEN_KEY}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
    },

    /**
     * Verifica si el usuario está autenticado
     */
    isAuthenticated() {
        return !!this.getToken();
    },

    /**
     * Obtiene los headers con autenticación
     */
    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        return headers;
    },

    /**
     * Realiza logout
     */
    logout() {
        this.removeToken();
        window.location.href = '/login';
    },

    /**
     * Verifica si la respuesta es un error 401 (no autorizado)
     */
    handleUnauthorized(response) {
        if (response.status === 401) {
            this.removeToken();
            alert('Su sesión ha expirado. Por favor inicie sesión nuevamente.');
            window.location.href = '/login';
            return true;
        }
        return false;
    },

    /**
     * Fetch wrapper que incluye automáticamente el token
     */
    async fetch(url, options = {}) {
        // Preparar headers con autenticación
        const token = this.getToken();
        const headers = {
            ...(options.headers || {})
        };

        // Agregar token si existe
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // Si el body no es FormData, agregar Content-Type
        if (options.body && !(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
        } else if (options.body instanceof FormData) {
            // Para FormData, NO agregar Content-Type para que el navegador lo configure automáticamente
            // No hacer nada, dejar que el navegador maneje el boundary
        }

        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(url, config);

            // Verificar si es 401
            if (this.handleUnauthorized(response)) {
                throw new Error('No autorizado');
            }

            return response;
        } catch (error) {
            // Error en fetch autenticado
            throw error;
        }
    },

    /**
     * GET request autenticado
     */
    async get(url) {
        const response = await this.fetch(url, {
            method: 'GET'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error en la petición');
        }
        
        return await response.json();
    },

    /**
     * POST request autenticado
     */
    async post(url, data) {
        const body = data instanceof FormData ? data : JSON.stringify(data);
        
        const response = await this.fetch(url, {
            method: 'POST',
            body
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error en la petición');
        }
        
        return await response.json();
    },

    /**
     * PUT request autenticado
     */
    async put(url, data) {
        const response = await this.fetch(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error en la petición');
        }
        
        return await response.json();
    },

    /**
     * DELETE request autenticado
     */
    async delete(url) {
        const response = await this.fetch(url, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error en la petición');
        }
        
        return await response.json();
    },

    /**
     * Obtiene la información del usuario actual
     */
    async getCurrentUser() {
        try {
            // Asegurarse de que API_BASE_URL esté definido
            const baseUrl = window.API_BASE_URL || 'http://localhost:8000';
            //
            
            const response = await fetch(`${baseUrl}/api/auth/me`, {
                credentials: 'include',
                headers: this.getAuthHeaders()
            });
            
            //
            
            // Si es 401, el token expiró o es inválido
            if (response.status === 401) {
                //
                this.removeToken();
                return null;
            }
            
            if (!response.ok) {
                //
                throw new Error('No se pudo obtener el usuario');
            }
            
            const userData = await response.json();
            //
            return userData;
        } catch (error) {
            //
            return null;
        }
    }
};

// Exportar para uso global
window.Auth = Auth;
