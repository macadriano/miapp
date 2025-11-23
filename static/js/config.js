// Configuración de WayGPS Frontend
// Modifica estos valores según tu configuración

const CONFIG = {
    // URL base de tu API Django
    API_BASE_URL: window.location.origin || 'http://127.0.0.1:8000',
    
    // Endpoint específico para móviles
    MOVILES_ENDPOINT: '/moviles/api/moviles/',
    
    // URL del frontend de móviles
    MOVILES_FRONTEND_URL: '/moviles/dashboard/',
    
    // Configuración de actualización automática (en milisegundos)
    AUTO_REFRESH_INTERVAL: 30000, // 30 segundos
    
    // Configuración del mapa
    MAP: {
        // Coordenadas por defecto (Buenos Aires, Argentina)
        DEFAULT_LAT: -34.6037,
        DEFAULT_LON: -58.3816,
        DEFAULT_ZOOM: 10,
        
        // Proveedor de mapas
        TILE_PROVIDER: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        ATTRIBUTION: '© OpenStreetMap contributors'
    },
    
    // Configuración de estados
    STATUS: {
        // Tiempo en minutos para considerar un móvil como "en línea"
        ONLINE_THRESHOLD_MINUTES: 15,
        
        // Colores para los estados
        ONLINE_COLOR: 'green',
        OFFLINE_COLOR: 'red',
        
        // Colores para encendido
        IGNITION_ON_COLOR: '#d4edda',
        IGNITION_OFF_COLOR: '#f8d7da'
    },
    
    // Configuración de la interfaz
    UI: {
        // Tiempo de mostrar alertas (en milisegundos)
        ALERT_DURATION: 5000,
        
        // Elementos por página en la tabla
        ITEMS_PER_PAGE: 50,
        
        // Animaciones
        ENABLE_ANIMATIONS: true,
        
        // Tema
        THEME: 'light' // 'light' o 'dark'
    },
    
    // Configuración de campos del formulario
    FORM: {
        // Campos requeridos para crear un móvil
        REQUIRED_FIELDS: ['patente'],
        
        // Validaciones personalizadas
        VALIDATIONS: {
            PATENTE_MIN_LENGTH: 3,
            PATENTE_MAX_LENGTH: 10,
            VIN_LENGTH: 17,
            ANIO_MIN: 1900,
            ANIO_MAX: 2030
        }
    },
    
    // Configuración de reportes
    REPORTS: {
        // Tipos de reportes disponibles
        AVAILABLE_REPORTS: [
            'ubicacion_actual',
            'historial_rutas',
            'consumo_combustible',
            'tiempos_parada',
            'velocidades_exceso'
        ],
        
        // Períodos por defecto
        DEFAULT_PERIODS: [
            'hoy',
            'ayer',
            'ultima_semana',
            'ultimo_mes',
            'personalizado'
        ]
    },
    
    // Configuración de notificaciones
    NOTIFICATIONS: {
        // Habilitar notificaciones del navegador
        ENABLE_BROWSER_NOTIFICATIONS: false,
        
        // Tipos de notificaciones
        TYPES: {
            MÓVIL_CONECTADO: 'success',
            MÓVIL_DESCONECTADO: 'warning',
            VELOCIDAD_EXCESO: 'danger',
            BATERÍA_BAJA: 'warning'
        }
    },
    
    // Configuración de desarrollo
    DEBUG: {
        // Mostrar logs en consola
        ENABLE_CONSOLE_LOGS: true,
        
        // Mostrar información de debug en la interfaz
        SHOW_DEBUG_INFO: false,
        
        // Simular datos (para desarrollo sin API)
        MOCK_DATA: false
    }
};

// Función para obtener la URL completa de la API
function getApiUrl(endpoint = '') {
    return CONFIG.API_BASE_URL + CONFIG.MOVILES_ENDPOINT + endpoint;
}

// Función para verificar si estamos en modo debug
function isDebugMode() {
    return CONFIG.DEBUG.ENABLE_CONSOLE_LOGS;
}

// Función para log condicional
function debugLog(message, data = null) {
    if (isDebugMode()) {
        console.log(`[WayGPS] ${message}`, data || '');
    }
}

// Función para obtener configuración específica
function getConfig(path) {
    return path.split('.').reduce((obj, key) => obj && obj[key], CONFIG);
}

// Exportar configuración para uso global
window.WAYGPS_CONFIG = CONFIG;
window.getApiUrl = getApiUrl;
window.debugLog = debugLog;
window.getConfig = getConfig;

