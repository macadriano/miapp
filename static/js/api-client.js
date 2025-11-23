/**
 * Cliente API Reutilizable para WayGPS
 * Maneja todas las comunicaciones con el backend Django
 */

class ApiClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl || WAYGPS_CONFIG.API_BASE_URL;
    }

    /**
     * Realiza una petición GET
     * @param {string} endpoint - Endpoint de la API
     * @returns {Promise} - Respuesta de la API
     */
    async get(endpoint) {
        try {
            debugLog(`GET request to: ${this.baseUrl}${endpoint}`);
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status}`);
            }

            const data = await response.json();
            debugLog(`GET response:`, data);
            return data;
        } catch (error) {
            console.error(`Error in GET ${endpoint}:`, error);
            throw error;
        }
    }

    /**
     * Realiza una petición POST
     * @param {string} endpoint - Endpoint de la API
     * @param {object} data - Datos a enviar
     * @returns {Promise} - Respuesta de la API
     */
    async post(endpoint, data) {
        try {
            debugLog(`POST request to: ${this.baseUrl}${endpoint}`, data);
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status}`);
            }

            const responseData = await response.json();
            debugLog(`POST response:`, responseData);
            return responseData;
        } catch (error) {
            console.error(`Error in POST ${endpoint}:`, error);
            throw error;
        }
    }

    /**
     * Realiza una petición PUT
     * @param {string} endpoint - Endpoint de la API
     * @param {object} data - Datos a actualizar
     * @returns {Promise} - Respuesta de la API
     */
    async put(endpoint, data) {
        try {
            debugLog(`PUT request to: ${this.baseUrl}${endpoint}`, data);
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status}`);
            }

            const responseData = await response.json();
            debugLog(`PUT response:`, responseData);
            return responseData;
        } catch (error) {
            console.error(`Error in PUT ${endpoint}:`, error);
            throw error;
        }
    }

    /**
     * Realiza una petición PATCH
     * @param {string} endpoint - Endpoint de la API
     * @param {object} data - Datos parciales a actualizar
     * @returns {Promise} - Respuesta de la API
     */
    async patch(endpoint, data) {
        try {
            debugLog(`PATCH request to: ${this.baseUrl}${endpoint}`, data);
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status}`);
            }

            const responseData = await response.json();
            debugLog(`PATCH response:`, responseData);
            return responseData;
        } catch (error) {
            console.error(`Error in PATCH ${endpoint}:`, error);
            throw error;
        }
    }

    /**
     * Realiza una petición DELETE
     * @param {string} endpoint - Endpoint de la API
     * @returns {Promise} - Respuesta de la API
     */
    async delete(endpoint) {
        try {
            debugLog(`DELETE request to: ${this.baseUrl}${endpoint}`);
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error(`HTTP Error: ${response.status}`);
            }

            debugLog(`DELETE successful`);
            return { success: true };
        } catch (error) {
            console.error(`Error in DELETE ${endpoint}:`, error);
            throw error;
        }
    }

    /**
     * Métodos específicos para móviles
     */
    async getMoviles() {
        return this.get('/moviles/api/moviles/');
    }

    async getMovil(id) {
        return this.get(`/moviles/api/moviles/${id}/`);
    }

    async createMovil(data) {
        return this.post('/moviles/api/moviles/', data);
    }

    async updateMovil(id, data) {
        return this.put(`/moviles/api/moviles/${id}/`, data);
    }

    async patchMovil(id, data) {
        return this.patch(`/moviles/api/moviles/${id}/`, data);
    }

    async deleteMovil(id) {
        return this.delete(`/moviles/api/moviles/${id}/`);
    }

    /**
     * Métodos para futuras entidades (conductores, viajes, etc.)
     */
    
    // Conductores
    async getConductores() {
        return this.get('/conductores/');
    }

    async createConductor(data) {
        return this.post('/conductores/', data);
    }

    // Viajes
    async getViajes() {
        return this.get('/viajes/');
    }

    async createViaje(data) {
        return this.post('/viajes/', data);
    }
}

// Crear instancia global del cliente API
window.apiClient = new ApiClient();

// Exportar para uso en módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ApiClient;
}

