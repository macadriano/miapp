// Configuración de la API (se inicializará después de cargar config.js)
let API_BASE_URL;
let MOVILES_API_URL;

// Variables globales
let movilesData = [];
let filteredMovilesData = [];
let mapaPrincipal = null;
let mapaDashboard = null;
let markers = [];
let currentSection = null;
// Se inicializará automáticamente según el dispositivo al cargar
let currentViewMode = window.innerWidth < 768 ? 'cards' : 'list';
let zonaDesdeMovilModal = null;
let zonaMovilSeleccionado = null;

// Función para obtener CSRF token de las cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Inicialización cuando se carga la página
document.addEventListener('DOMContentLoaded', function () {
    console.log('WayGPS Frontend iniciado');
    initializeApp();

    const defaultSection = document.body?.dataset?.defaultSection || 'moviles';
    const menu = document.getElementById('moviles-menu');
    const defaultLink = menu ? menu.querySelector(`.nav-link[data-section="${defaultSection}"]`) : null;

    if (defaultLink) {
        showSection(defaultSection, defaultLink);
    } else {
        const targetSection = document.getElementById(`${defaultSection}-section`);
        if (targetSection) {
            targetSection.style.display = 'block';
        }
        currentSection = defaultSection;
    }
});

// Función principal de inicialización
async function initializeApp() {
    try {
        console.log('Iniciando aplicación WayGPS');

        // Inicializar configuración de API
        if (typeof WAYGPS_CONFIG !== 'undefined') {
            API_BASE_URL = WAYGPS_CONFIG.API_BASE_URL;
            MOVILES_API_URL = getApiUrl();
        } else {
            console.error('WAYGPS_CONFIG no está disponible');
            return;
        }

        // La lógica de vista responsive se inicializa automáticamente al final del archivo


        await loadMoviles();
        initializeMaps();
        setupEventListeners();
        setupZonaDesdeMovilModal();
        updateDashboard();
        console.log('Aplicación inicializada correctamente');
    } catch (error) {
        console.error('Error al inicializar la aplicación:', error);
        showAlert('Error al cargar los datos', 'danger');
    }
}

// Cargar datos de móviles desde la API
async function loadMoviles() {
    try {
        console.log('=== INICIANDO CARGA DE MÓVILES ===');
        console.log('MOVILES_API_URL:', MOVILES_API_URL);
        console.log('WAYGPS_CONFIG disponible:', typeof WAYGPS_CONFIG !== 'undefined');
        console.log('getApiUrl disponible:', typeof getApiUrl !== 'undefined');

        showLoading(true);

        // Headers básicos sin autenticación para pruebas
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };

        // Intentar agregar autenticación si está disponible
        if (typeof auth !== 'undefined' && auth && typeof auth.getHeaders === 'function') {
            console.log('Agregando headers de autenticación...');
            const authHeaders = auth.getHeaders();
            Object.assign(headers, authHeaders);
        } else {
            console.log('No se encontró autenticación, usando headers básicos');
        }

        console.log('Headers finales:', headers);
        console.log('Realizando petición a:', MOVILES_API_URL);

        const response = await fetch(MOVILES_API_URL, {
            headers: headers
        });

        console.log('=== RESPUESTA RECIBIDA ===');
        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);
        console.log('Response headers:', Object.fromEntries(response.headers.entries()));

        if (!response.ok) {
            const errorText = await response.text();
            console.error('=== ERROR EN RESPUESTA ===');
            console.error('Status:', response.status);
            console.error('Error text:', errorText);
            throw new Error(`Error HTTP: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        console.log('=== DATOS RECIBIDOS ===');
        console.log('Tipo de datos:', typeof data);
        console.log('Es array:', Array.isArray(data));
        console.log('Tiene results:', data.results !== undefined);
        console.log('Claves del objeto:', Object.keys(data));
        console.log('Datos completos:', data);

        // Verificar si es la respuesta del router (contiene URLs)
        if (data.moviles && typeof data.moviles === 'string' && data.moviles.includes('http')) {
            console.error('=== PROBLEMA DETECTADO ===');
            console.error('Se recibió la respuesta del router en lugar de los datos de móviles');
            console.error('Esto indica un problema con la URL o la configuración del ViewSet');
            throw new Error('Respuesta del router recibida en lugar de datos de móviles');
        }

        // Manejar respuesta paginada o no paginada
        if (data.results && Array.isArray(data.results)) {
            movilesData = data.results;
        } else if (Array.isArray(data)) {
            movilesData = data;
        } else {
            console.error('Formato de respuesta desconocido:', data);
            movilesData = [];
        }
        filteredMovilesData = [...movilesData];
        console.log(`Cargados ${movilesData.length} móviles`);
        console.log('Datos de móviles cargados:', movilesData);
        
        // Asegurar que los botones de vista estén ocultos/eliminados
        if (typeof eliminarBotonesVista === 'function') {
            eliminarBotonesVista();
        }

        // Si no hay datos, usar datos de prueba
        if (movilesData.length === 0) {
            console.log('No hay datos reales, usando datos de prueba');
            movilesData = [
                {
                    id: 1,
                    alias: 'Auto de Prueba 1',
                    patente: 'ABC123',
                    codigo: 'M001',
                    marca: 'Toyota',
                    modelo: 'Corolla',
                    status_info: {
                        estado_conexion: 'conectado',
                        ultima_velocidad_kmh: 45,
                        bateria_pct: 80,
                        ultima_actualizacion: new Date().toISOString()
                    },
                    geocode_info: {
                        direccion_formateada: 'Av. Corrientes 1234, CABA'
                    },
                    fotos_count: 3,
                    observaciones_count: 2
                },
                {
                    id: 2,
                    alias: 'Auto de Prueba 2',
                    patente: 'DEF456',
                    codigo: 'M002',
                    marca: 'Ford',
                    modelo: 'Focus',
                    status_info: {
                        estado_conexion: 'desconectado',
                        ultima_velocidad_kmh: 0,
                        bateria_pct: 25,
                        ultima_actualizacion: new Date(Date.now() - 300000).toISOString()
                    },
                    geocode_info: {
                        direccion_formateada: 'Av. Santa Fe 5678, CABA'
                    },
                    fotos_count: 1,
                    observaciones_count: 0
                }
            ];
        }

        // Renderizar móviles según el modo actual
        renderizarMoviles();

        // Actualizar estadísticas del dashboard
        updateDashboardStats();
        
        // Actualizar dashboard completo
        updateDashboard();

        // Actualizar mapas si están inicializados
        if (mapaPrincipal) {
            updateMapaPrincipal();
        }
        if (mapaDashboard) {
            updateMapaDashboard();
        }

    } catch (error) {
        console.error('=== ERROR EN CARGA DE MÓVILES ===');
        console.error('Error completo:', error);
        console.error('Stack trace:', error.stack);
        showAlert('Error al cargar los datos de móviles', 'danger');
        movilesData = [];
    } finally {
        showLoading(false);
        console.log('=== FINALIZANDO CARGA DE MÓVILES ===');
        console.log('Total móviles cargados:', movilesData.length);
        console.log('Carga de móviles completada');
    }
}

// Mostrar/ocultar indicador de carga
function showLoading(show) {
    const loadingElements = document.querySelectorAll('.loading');
    loadingElements.forEach(el => {
        el.style.display = show ? 'block' : 'none';
    });
}

// Actualizar estadísticas del dashboard
function updateDashboardStats() {
    const totalMoviles = movilesData.length;
    const movilesOnline = movilesData.filter(m => isOnline(m)).length;
    const movilesConIgnicion = movilesData.filter(m => m.ignicion === true).length;

    // Calcular velocidad promedio de móviles en movimiento
    const velocidades = movilesData
        .filter(m => m.ultima_velocidad_kmh && m.ultima_velocidad_kmh > 0)
        .map(m => parseFloat(m.ultima_velocidad_kmh));

    const velocidadPromedio = velocidades.length > 0
        ? (velocidades.reduce((a, b) => a + b, 0) / velocidades.length).toFixed(1)
        : 0;

    const totalMovilesEl = document.getElementById('total-moviles');
    const movilesOnlineEl = document.getElementById('moviles-online');
    const movilesIgnicionEl = document.getElementById('moviles-ignicion');
    const velocidadPromedioEl = document.getElementById('velocidad-promedio');

    if (totalMovilesEl) totalMovilesEl.textContent = totalMoviles;
    if (movilesOnlineEl) movilesOnlineEl.textContent = movilesOnline;
    if (movilesIgnicionEl) movilesIgnicionEl.textContent = movilesConIgnicion;
    if (velocidadPromedioEl) velocidadPromedioEl.textContent = `${velocidadPromedio} km/h`;
}

// Verificar si un móvil está en línea
function isOnline(movil) {
    if (!movil.fecha_recepcion) return false;

    const ultimaRecepcion = new Date(movil.fecha_recepcion);
    const ahora = new Date();
    const diferenciaMinutos = (ahora - ultimaRecepcion) / (1000 * 60);

    return diferenciaMinutos <= WAYGPS_CONFIG.STATUS.ONLINE_THRESHOLD_MINUTES;
}

// Mostrar secciones del menú
function showSection(section, link) {
    // Ocultar todas las secciones
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(sec => sec.style.display = 'none');

    // Mostrar la sección seleccionada
    const sectionElement = document.getElementById(`${section}-section`);
    if (sectionElement) {
        sectionElement.style.display = 'block';
    } else {
        console.warn(`Sección ${section} no encontrada en DOM`);
    }

    // Actualizar menú activo
    const menu = document.getElementById('moviles-menu');
    if (menu) {
        menu.querySelectorAll('.nav-link[data-section]').forEach(navLink => {
            navLink.classList.remove('active');
        });
    }
    if (link && link.classList) {
        link.classList.add('active');
    } else if (menu) {
        const fallbackLink = menu.querySelector(`.nav-link[data-section="${section}"]`);
        if (fallbackLink) {
            fallbackLink.classList.add('active');
        }
    }

    // Actualizar título
    const titles = {
        'dashboard': 'Dashboard',
        'moviles': 'Móviles',
        'mapa': 'Mapa',
        'reportes': 'Reportes'
    };
    const pageTitle = document.getElementById('page-title');
    if (pageTitle && titles[section]) {
        pageTitle.textContent = titles[section];
    }

    currentSection = section;

    // Cerrar menú en móviles después de seleccionar
    const sidebarMenu = document.getElementById('sidebarMenu');
    if (sidebarMenu && window.innerWidth < 768) {
        const bsCollapse = bootstrap.Collapse.getInstance(sidebarMenu);
        if (bsCollapse) {
            bsCollapse.hide();
        }
    }

    // Cargar datos específicos de la sección
    switch (section) {
        case 'moviles':
            updateMovilesTable();
            break;
        case 'mapa':
            if (!mapaPrincipal) {
                initializeMapaPrincipal();
            }
            updateMapaPrincipal();
            break;
    }
}

// Actualizar tabla de móviles (ahora con tarjetas)
function updateMovilesTable() {
    // Mostrar skeleton loading mientras cargan los datos
    showSkeletonLoading();

    // Limpiar contenido después de un breve delay para mostrar el skeleton
    setTimeout(() => {
        // Renderizar según el modo de vista actual
        renderizarMoviles();
    }, 500);
}

// Mostrar skeleton loading
function showSkeletonLoading() {
    const cardsView = document.getElementById('moviles-cards-view');
    const listView = document.getElementById('moviles-list-view');

    if (cardsView) {
        cardsView.innerHTML = '';
        for (let i = 0; i < 6; i++) {
            const skeletonCard = document.createElement('div');
            skeletonCard.className = 'skeleton skeleton-card';
            cardsView.appendChild(skeletonCard);
        }
    }

    if (listView) {
        const tbody = document.getElementById('moviles-table-body');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center py-3"><i class="bi bi-hourglass-split"></i> Cargando...</td></tr>';
        }
    }
}

// Crear tarjeta moderna para un móvil
function createMovilCard(movil) {
    const card = document.createElement('div');
    card.className = 'movil-card';

    // Determinar estado del móvil
    const online = isOnline(movil);
    const status = movil.status_info || {};
    const estadoConexion = status.estado_conexion || (online ? 'conectado' : 'desconectado');

    // Agregar clase de estado
    card.classList.add(estadoConexion);

    // Identificación del móvil
    const identificacion = movil.alias || movil.patente || movil.codigo || 'Sin identificar';

    // Información de posición y domicilio
    const geocode = movil.geocode_info || {};
    const domicilio = geocode.direccion_formateada ||
        (geocode.localidad && geocode.provincia ? `${geocode.localidad}, ${geocode.provincia}` :
            'Sin geocodificación');

    // Información de velocidad y batería
    const velocidad = status.ultima_velocidad_kmh ?
        `${status.ultima_velocidad_kmh} km/h` :
        'Sin datos';

    const bateria = status.bateria_pct ?
        `${status.bateria_pct}%` :
        'N/A';

    // Estado de encendido
    const encendido = status.ignicion ? 'ON' : 'OFF';
    const satelites = status.satelites || 'N/A';

    // Última actualización
    const ultimaActualizacion = status.ultima_actualizacion ?
        new Date(status.ultima_actualizacion) :
        null;

    const tiempoTranscurrido = ultimaActualizacion ?
        getTiempoTranscurrido(ultimaActualizacion) :
        'Sin datos';

    // Contador de fotos y observaciones
    const fotosCount = movil.fotos_count || 0;
    const observacionesCount = movil.observaciones_count || 0;

    card.innerHTML = `
        <div class="movil-header">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h5 class="mb-0">🚗 ${identificacion}</h5>
                    <small class="opacity-75">${movil.patente || 'Sin patente'}</small>
                </div>
                <div class="movil-status-badge status-${estadoConexion}"></div>
            </div>
        </div>
        
        <div class="movil-info">
            <div class="info-row">
                <span class="info-label">📍 Ubicación</span>
                <span class="info-value text-truncate" title="${domicilio}">${domicilio}</span>
            </div>
            
            <div class="info-row">
                <span class="info-label">⚡ Estado</span>
                <span class="info-value">
                    🔋 ${bateria} ⚡ ${encendido} 📡 ${satelites} sat
                </span>
            </div>
            
            <div class="info-row">
                <span class="info-label">🏃 Velocidad</span>
                <span class="info-value">${velocidad}</span>
            </div>
            
            <div class="info-row">
                <span class="info-label">🕐 Última actualización</span>
                <span class="info-value">${tiempoTranscurrido}</span>
            </div>
            
            <div class="info-row">
                <span class="info-label">📊 Información</span>
                <span class="info-value">
                    📷 ${fotosCount} fotos | 📝 ${observacionesCount} obs
                </span>
            </div>
        </div>
        
        <div class="movil-actions">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <button class="btn btn-outline-primary btn-action" onclick="verDetalleMovil(${movil.id})" title="Ver detalles">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-outline-warning btn-action" onclick="editarMovil(${movil.id})" title="Editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-outline-info btn-action" onclick="verEnMapa(${movil.id})" title="Ver en mapa">
                        <i class="bi bi-geo-alt"></i>
                    </button>
                    <button class="btn btn-outline-success btn-action" onclick="compartirMovil(${movil.id})" title="Compartir información">
                        <i class="bi bi-share"></i>
                    </button>
                    <button class="btn btn-outline-secondary btn-action" onclick="abrirModalZonaDesdeMovil(${movil.id})" title="Crear zona desde este móvil">
                        <i class="bi bi-bullseye"></i>
                    </button>
                </div>
                <div>
                    <button class="btn btn-outline-danger btn-action" onclick="eliminarMovil(${movil.id})" title="Eliminar">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `;

    return card;
}

// Función para calcular tiempo transcurrido
function getTiempoTranscurrido(fecha) {
    const ahora = new Date();
    const diferencia = ahora - fecha;

    const minutos = Math.floor(diferencia / (1000 * 60));
    const horas = Math.floor(diferencia / (1000 * 60 * 60));
    const dias = Math.floor(diferencia / (1000 * 60 * 60 * 24));

    if (minutos < 1) {
        return 'Ahora';
    } else if (minutos < 60) {
        return `${minutos} min`;
    } else if (horas < 24) {
        return `${horas}h ${minutos % 60}min`;
    } else {
        return `${dias}d ${horas % 24}h`;
    }
}

// Función para ver móvil en mapa
function verEnMapa(id) {
    const movil = movilesData.find(m => m.id === id);
    if (movil && movil.status_info && movil.status_info.ultimo_lat && movil.status_info.ultimo_lon) {
        // Cambiar a la sección de mapa
        showSection('mapa');

        // Centrar el mapa en la posición del móvil
        if (mapaPrincipal) {
            const lat = parseFloat(movil.status_info.ultimo_lat);
            const lon = parseFloat(movil.status_info.ultimo_lon);
            mapaPrincipal.setView([lat, lon], 15);

            // Mostrar popup del móvil
            setTimeout(() => {
                const marker = markers.find(m => {
                    const position = m.getLatLng();
                    return Math.abs(position.lat - lat) < 0.001 && Math.abs(position.lng - lon) < 0.001;
                });
                if (marker) {
                    marker.openPopup();
                }
            }, 500);
        }
    } else {
        showAlert('No hay información de ubicación disponible para este móvil', 'warning');
    }
}

// Crear fila de tabla para un móvil (mantener para compatibilidad)
function createMovilRow(movil) {
    const tr = document.createElement('tr');

    // Estado (online/offline)
    const online = isOnline(movil);
    const estadoIcon = online ?
        '<i class="bi bi-wifi status-online"></i>' :
        '<i class="bi bi-wifi-off status-offline"></i>';

    // Patente/Alias
    const identificacion = movil.alias || movil.patente || movil.codigo || 'Sin identificar';

    // Última posición (desde status_info)
    const status = movil.status_info || {};
    const posicion = (status.ultimo_lat && status.ultimo_lon) ?
        `${parseFloat(status.ultimo_lat).toFixed(6)}, ${parseFloat(status.ultimo_lon).toFixed(6)}` :
        'Sin datos';

    // Domicilio (desde geocode_info)
    const geocode = movil.geocode_info || {};
    const domicilio = geocode.direccion_formateada ||
        (geocode.localidad && geocode.provincia ? `${geocode.localidad}, ${geocode.provincia}` :
            'Sin geocodificación');

    // Velocidad (desde status_info)
    const velocidad = status.ultima_velocidad_kmh ?
        `${status.ultima_velocidad_kmh} km/h` :
        'Sin datos';

    // Estado de encendido (desde status_info)
    const encendido = status.ignicion === true ?
        '<span class="badge status-ignition-on">Encendido</span>' :
        '<span class="badge status-ignition-off">Apagado</span>';

    // Batería (desde status_info)
    const bateria = status.bateria_pct ?
        `${status.bateria_pct}%` :
        'Sin datos';

    // Última actualización (desde status_info)
    const ultimaActualizacion = status.ultima_actualizacion ?
        new Date(status.ultima_actualizacion).toLocaleString('es-ES') :
        'Sin datos';

    tr.innerHTML = `
        <td>${estadoIcon}</td>
        <td><strong>${identificacion}</strong></td>
        <td>${movil.gps_id || 'Sin ID'}</td>
        <td><small>${posicion}</small></td>
        <td><small title="${geocode.direccion_formateada || 'Sin dirección'}">${domicilio}</small></td>
        <td>${velocidad}</td>
        <td>${encendido}</td>
        <td>${bateria}</td>
        <td><small>${ultimaActualizacion}</small></td>
        <td>
            <button class="btn btn-sm btn-outline-primary" onclick="verDetalleMovil(${movil.id})" title="Ver detalles">
                <i class="bi bi-eye"></i>
            </button>
            <button class="btn btn-sm btn-outline-warning" onclick="editarMovil(${movil.id})" title="Editar">
                <i class="bi bi-pencil"></i>
            </button>
            <button class="btn btn-sm btn-outline-danger" onclick="eliminarMovil(${movil.id})" title="Eliminar">
                <i class="bi bi-trash"></i>
            </button>
        </td>
    `;

    return tr;
}

// Capas de mapa
let baseLayers = {};

// Inicializar mapas
function initializeMaps() {
    // Mapa del dashboard
    if (document.getElementById('mapa-dashboard')) {
        const mapConfig = WAYGPS_CONFIG.MAP;
        const mapResult = initializeNormalizedMap('mapa-dashboard', {
            lat: mapConfig.DEFAULT_LAT,
            lon: mapConfig.DEFAULT_LON,
            zoom: mapConfig.DEFAULT_ZOOM,
            showZonesControl: true,
            showLayerControl: true
        });
        
        mapaDashboard = mapResult.map;
        baseLayers = mapResult.baseLayers;
    }
}

// Inicializar mapa principal
function initializeMapaPrincipal() {
    if (document.getElementById('mapa-principal')) {
        const mapConfig = WAYGPS_CONFIG.MAP;
        const mapResult = initializeNormalizedMap('mapa-principal', {
            lat: mapConfig.DEFAULT_LAT,
            lon: mapConfig.DEFAULT_LON,
            zoom: mapConfig.DEFAULT_ZOOM,
            showZonesControl: true,
            showLayerControl: true
        });
        
        mapaPrincipal = mapResult.map;
    }
}

// Actualizar mapa principal
function updateMapaPrincipal() {
    if (!mapaPrincipal) return;

    // Limpiar marcadores existentes
    markers.forEach(marker => mapaPrincipal.removeLayer(marker));
    markers = [];

    // Agregar marcadores para cada móvil
    movilesData.forEach(movil => {
        const status = movil.status_info || {};
        if (status.ultimo_lat && status.ultimo_lon) {
            const online = isOnline(movil);
            const iconColor = online ? WAYGPS_CONFIG.STATUS.ONLINE_COLOR : WAYGPS_CONFIG.STATUS.OFFLINE_COLOR;

            // Convertir coordenadas a números
            const lat = parseFloat(status.ultimo_lat);
            const lon = parseFloat(status.ultimo_lon);

            // Identificación del móvil
            const label = movil.patente || movil.alias || movil.codigo || 'N/A';

            // Crear ícono personalizado con etiqueta
            const icon = L.divIcon({
                className: 'custom-marker-with-label',
                html: `
                    <div style="text-align: center;">
                        <div style="background-color: ${iconColor}; width: 24px; height: 24px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3); margin: 0 auto;"></div>
                        <div style="
                            background-color: rgba(255,255,255,0.95);
                            color: #333;
                            padding: 2px 6px;
                            border-radius: 3px;
                            font-size: 11px;
                            font-weight: bold;
                            white-space: nowrap;
                            margin-top: 2px;
                            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
                            border: 1px solid ${iconColor};
                        ">${label}</div>
                    </div>
                `,
                iconSize: [80, 45],
                iconAnchor: [40, 45]
            });

            const marker = L.marker([lat, lon], { icon })
                .addTo(mapaPrincipal)
                .bindPopup(createMovilPopup(movil));

            markers.push(marker);
        }
    });

    // Ajustar vista para mostrar todos los marcadores
    if (markers.length > 0) {
        const group = new L.featureGroup(markers);
        mapaPrincipal.fitBounds(group.getBounds().pad(0.1));
    }
}

// Variables para almacenar marcadores del dashboard
let dashboardMarkers = [];

// Actualizar mapa del dashboard
function updateMapaDashboard() {
    if (!mapaDashboard) return;

    // Limpiar marcadores existentes
    dashboardMarkers.forEach(marker => mapaDashboard.removeLayer(marker));
    dashboardMarkers = [];

    // Agregar marcadores para todos los móviles (no solo online)
    movilesData.forEach(movil => {
        const status = movil.status_info || {};
        if (status.ultimo_lat && status.ultimo_lon) {
            // Convertir coordenadas a números
            const lat = parseFloat(status.ultimo_lat);
            const lon = parseFloat(status.ultimo_lon);

            const online = isOnline(movil);
            const iconColor = online ? 'green' : 'red';

            // Identificación del móvil
            const label = movil.patente || movil.alias || movil.codigo || 'N/A';

            const marker = L.marker([lat, lon], {
                icon: L.divIcon({
                    className: 'custom-marker-with-label',
                    html: `
                        <div style="text-align: center;">
                            <div style="background-color: ${iconColor}; width: 18px; height: 18px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3); margin: 0 auto;"></div>
                            <div style="
                                background-color: rgba(255,255,255,0.95);
                                color: #333;
                                padding: 1px 4px;
                                border-radius: 3px;
                                font-size: 10px;
                                font-weight: bold;
                                white-space: nowrap;
                                margin-top: 1px;
                                box-shadow: 0 1px 3px rgba(0,0,0,0.3);
                                border: 1px solid ${iconColor};
                            ">${label}</div>
                        </div>
                    `,
                    iconSize: [70, 38],
                    iconAnchor: [35, 38]
                })
            }).addTo(mapaDashboard).bindPopup(createMovilPopup(movil));

            dashboardMarkers.push(marker);
        }
    });

    // Ajustar vista si hay marcadores
    if (dashboardMarkers.length > 0) {
        const group = new L.featureGroup(dashboardMarkers);
        mapaDashboard.fitBounds(group.getBounds().pad(0.1));
    }
}

// Crear popup para marcador de móvil
function createMovilPopup(movil) {
    const status = movil.status_info || {};
    const geocode = movil.geocode_info || {};
    const online = isOnline(movil);
    const estado = online ? 'En línea' : 'Desconectado';
    const encendido = status.ignicion ? 'Encendido' : 'Apagado';

    // Información de domicilio desde moviles_geocode
    const domicilio = geocode.direccion_formateada ||
        (geocode.localidad && geocode.provincia ? `${geocode.localidad}, ${geocode.provincia}` :
            'Sin geocodificación');

    return `
        <div style="min-width: 250px;">
            <h6><strong>${movil.alias || movil.patente || 'Sin identificar'}</strong></h6>
            <p><strong>Estado:</strong> ${estado}<br>
            <strong>GPS ID:</strong> ${movil.gps_id || 'Sin ID'}<br>
            <strong>Domicilio:</strong> ${domicilio}<br>
            <strong>Velocidad:</strong> ${status.ultima_velocidad_kmh || 0} km/h<br>
            <strong>Encendido:</strong> ${encendido}<br>
            <strong>Batería:</strong> ${status.bateria_pct || 'N/A'}%</p>
            <small><strong>Última actualización:</strong><br>${status.ultima_actualizacion ? new Date(status.ultima_actualizacion).toLocaleString('es-ES') : 'Sin datos'}</small>
        </div>
    `;
}

// Configurar event listeners
function setupEventListeners() {
    // Filtros de búsqueda
    const filtroBusqueda = document.getElementById('filtro-busqueda');
    const filtroEstado = document.getElementById('filtro-estado');
    const filtroEncendido = document.getElementById('filtro-encendido');
    const filtroTipo = document.getElementById('filtro-tipo');

    if (filtroBusqueda) filtroBusqueda.addEventListener('input', aplicarFiltros);
    if (filtroEstado) filtroEstado.addEventListener('change', aplicarFiltros);
    if (filtroEncendido) filtroEncendido.addEventListener('change', aplicarFiltros);
    if (filtroTipo) filtroTipo.addEventListener('change', aplicarFiltros);
}

// Aplicar filtros a las tarjetas
function aplicarFiltros() {
    const filtroBusqueda = document.getElementById('filtro-busqueda');
    const filtroEstado = document.getElementById('filtro-estado');
    const filtroEncendido = document.getElementById('filtro-encendido');
    const filtroTipo = document.getElementById('filtro-tipo');

    if (!filtroBusqueda || !filtroEstado || !filtroEncendido || !filtroTipo) {
        filteredMovilesData = [...movilesData];
        renderizarMoviles();
        return;
    }

    const busqueda = filtroBusqueda.value.toLowerCase();
    const estado = filtroEstado.value;
    const encendido = filtroEncendido.value;
    const tipo = filtroTipo.value;

    filteredMovilesData = movilesData.filter(movil => {
        // Filtro de búsqueda
        const coincideBusqueda = !busqueda ||
            (movil.patente && movil.patente.toLowerCase().includes(busqueda)) ||
            (movil.alias && movil.alias.toLowerCase().includes(busqueda)) ||
            (movil.codigo && movil.codigo.toLowerCase().includes(busqueda));

        // Filtro de estado (usando status_info)
        const status = movil.status_info || {};
        const estadoConexion = status.estado_conexion || (isOnline(movil) ? 'conectado' : 'desconectado');
        const coincideEstado = !estado ||
            (estado === 'conectado' && estadoConexion === 'conectado') ||
            (estado === 'desconectado' && estadoConexion === 'desconectado') ||
            (estado === 'error' && estadoConexion === 'error');

        // Filtro de encendido (usando status_info)
        const coincideEncendido = !encendido ||
            (encendido === 'true' && status.ignicion === true) ||
            (encendido === 'false' && status.ignicion === false);

        // Filtro de tipo
        const coincideTipo = !tipo || movil.tipo_vehiculo === tipo;

        return coincideBusqueda && coincideEstado && coincideEncendido && coincideTipo;
    });

    renderizarMoviles();
}

// Cargar equipos GPS disponibles (sin asignar)
async function cargarEquiposDisponibles({ gpsIdActual = null, movilId = null } = {}) {
    try {
        const headers = auth ? auth.getHeaders() : { 'Content-Type': 'application/json' };
        let url = `${API_BASE_URL}/api/equipos/sin_asignar/`;
        if (movilId) {
            const params = new URLSearchParams({ movil_id: movilId });
            url += `?${params.toString()}`;
        }
        const response = await fetch(url, {
            headers: headers,
            credentials: 'same-origin'
        });

        if (!response.ok) {
            console.error('Error al cargar equipos disponibles');
            return;
        }

        const equipos = await response.json();
        const select = document.getElementById('gps-id');

        // Limpiar opciones excepto la primera (Sin asignar)
        select.innerHTML = '<option value="">Sin asignar</option>';

        // Agregar equipos disponibles
        equipos.forEach(equipo => {
            const option = document.createElement('option');
            option.value = equipo.imei;
            option.textContent = `${equipo.imei} - ${equipo.marca || 'Sin marca'} ${equipo.modelo || ''}`;
            select.appendChild(option);
        });

        // Si hay un GPS asignado actualmente, agregarlo como opción (aunque no esté en la lista)
        if (gpsIdActual && gpsIdActual.trim() !== '') {
            // Verificar si ya existe en el select
            const exists = Array.from(select.options).some(opt => opt.value === gpsIdActual);
            if (!exists) {
                const option = document.createElement('option');
                option.value = gpsIdActual;
                option.textContent = `${gpsIdActual} (Asignado actualmente)`;
                select.appendChild(option);
            }
        }

    } catch (error) {
        console.error('Error al cargar equipos disponibles:', error);
    }
}

// Mostrar formulario de móvil
async function mostrarFormularioMovil(movil = null) {
    const modal = new bootstrap.Modal(document.getElementById('modalMovil'));
    const titulo = document.getElementById('modalMovilTitulo');
    const form = document.getElementById('formMovil');

    // Limpiar formulario
    form.reset();

    // Cargar equipos disponibles
    await cargarEquiposDisponibles({
        gpsIdActual: movil ? movil.gps_id : null,
        movilId: movil ? movil.id : null
    });

    if (movil) {
        // Editar móvil existente
        titulo.textContent = 'Editar Móvil';
        document.getElementById('movil-id').value = movil.id;
        document.getElementById('patente').value = movil.patente || '';
        document.getElementById('alias').value = movil.alias || '';
        document.getElementById('codigo').value = movil.codigo || '';
        document.getElementById('vin').value = movil.vin || '';
        document.getElementById('marca').value = movil.marca || '';
        document.getElementById('modelo').value = movil.modelo || '';
        document.getElementById('anio').value = movil.anio || '';
        document.getElementById('color').value = movil.color || '';
        document.getElementById('tipo-vehiculo').value = movil.tipo_vehiculo || '';
        document.getElementById('gps-id').value = movil.gps_id || '';
        document.getElementById('activo').checked = movil.activo !== false;
    } else {
        // Nuevo móvil
        titulo.textContent = 'Nuevo Móvil';
        document.getElementById('movil-id').value = '';
        document.getElementById('activo').checked = true;
    }

    modal.show();
}

// Guardar móvil
async function guardarMovil() {
    try {
        const form = document.getElementById('formMovil');
        const formData = new FormData(form);
        const movilId = document.getElementById('movil-id').value;

        // Preparar datos, enviando null para campos vacíos
        const data = {
            patente: document.getElementById('patente').value.trim() || null,
            alias: document.getElementById('alias').value.trim() || null,
            codigo: document.getElementById('codigo').value.trim() || null,
            vin: document.getElementById('vin').value.trim() || null,
            marca: document.getElementById('marca').value.trim() || null,
            modelo: document.getElementById('modelo').value.trim() || null,
            anio: document.getElementById('anio').value ? parseInt(document.getElementById('anio').value) : null,
            color: document.getElementById('color').value.trim() || null,
            tipo_vehiculo: document.getElementById('tipo-vehiculo').value || null,
            gps_id: document.getElementById('gps-id').value.trim() || null,
            activo: document.getElementById('activo').checked
        };

        // Obtener headers con autenticación
        const headers = auth ? auth.getHeaders() : { 'Content-Type': 'application/json' };

        // Obtener CSRF token
        const csrftoken = getCookie('csrftoken');
        if (csrftoken) {
            headers['X-CSRFToken'] = csrftoken;
        }

        let response;
        if (movilId) {
            // Actualizar móvil existente
            response = await fetch(`${MOVILES_API_URL}${movilId}/`, {
                method: 'PUT',
                headers: headers,
                body: JSON.stringify(data)
            });
        } else {
            // Crear nuevo móvil
            response = await fetch(MOVILES_API_URL, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(data)
            });
        }

        if (!response.ok) {
            // Intentar obtener el mensaje de error del servidor
            let errorMessage = `Error HTTP: ${response.status}`;
            try {
                const errorData = await response.json();
                console.error('Error del servidor:', errorData);
                console.log('Datos enviados:', data);

                // Construir mensaje de error detallado
                let errores = [];

                // Recorrer todos los errores del servidor
                for (const [campo, mensajes] of Object.entries(errorData)) {
                    if (Array.isArray(mensajes)) {
                        errores.push(`${campo}: ${mensajes.join(', ')}`);
                    } else if (typeof mensajes === 'string') {
                        errores.push(`${campo}: ${mensajes}`);
                    }
                }

                if (errores.length > 0) {
                    errorMessage = errores.join('<br>');
                } else {
                    errorMessage = JSON.stringify(errorData);
                }

            } catch (e) {
                console.error('No se pudo parsear el error:', e);
            }

            showAlert(errorMessage, 'danger', true);  // true para permitir HTML
            return;
        }

        // Recargar datos primero, luego cerrar modal
        await loadMoviles();

        // Cerrar modal
        bootstrap.Modal.getInstance(document.getElementById('modalMovil')).hide();

        // Mostrar mensaje de éxito
        showAlert(movilId ? 'Móvil actualizado correctamente' : 'Móvil creado correctamente', 'success');

    } catch (error) {
        console.error('Error al guardar móvil:', error);
        showAlert('Error al guardar el móvil: ' + error.message, 'danger');
    }
}

// Editar móvil
async function editarMovil(id) {
    try {
        // Obtener datos actualizados del móvil específico desde la API
        const headers = auth ? auth.getHeaders() : { 'Content-Type': 'application/json' };
        const response = await fetch(`${MOVILES_API_URL}${id}/`, {
            headers: headers
        });

        if (response.ok) {
            const movil = await response.json();
            mostrarFormularioMovil(movil);
        } else {
            // Fallback: usar datos locales si falla la petición
            const movil = movilesData.find(m => m.id === id);
            if (movil) {
                mostrarFormularioMovil(movil);
            }
        }
    } catch (error) {
        console.error('Error al obtener datos del móvil:', error);
        // Fallback: usar datos locales
        const movil = movilesData.find(m => m.id === id);
        if (movil) {
            mostrarFormularioMovil(movil);
        }
    }
}

// Ver detalle de móvil
function verDetalleMovil(id) {
    const movil = movilesData.find(m => m.id === id);
    if (movil) {
        // Mostrar detalles en un modal o alert
        const detalles = `
            <strong>${movil.alias || movil.patente || 'Sin identificar'}</strong><br>
            <strong>Patente:</strong> ${movil.patente || 'Sin patente'}<br>
            <strong>GPS ID:</strong> ${movil.gps_id || 'Sin ID'}<br>
            <strong>Marca/Modelo:</strong> ${movil.marca || 'N/A'} ${movil.modelo || ''}<br>
            <strong>Año:</strong> ${movil.anio || 'N/A'}<br>
            <strong>Última posición:</strong> ${movil.ultimo_lat && movil.ultimo_lon ? `${movil.ultimo_lat}, ${movil.ultimo_lon}` : 'Sin datos'}<br>
            <strong>Velocidad:</strong> ${movil.ultima_velocidad_kmh || 0} km/h<br>
            <strong>Encendido:</strong> ${movil.ignicion ? 'Sí' : 'No'}<br>
            <strong>Batería:</strong> ${movil.bateria_pct || 'N/A'}%<br>
            <strong>Última actualización:</strong> ${movil.fecha_recepcion ? new Date(movil.fecha_recepcion).toLocaleString('es-ES') : 'Sin datos'}
        `;

        showAlert(detalles, 'info', true);
    }
}

// Eliminar móvil
async function eliminarMovil(id) {
    const confirmed = await notify.confirm({
        message: '¿Está seguro de que desea eliminar este móvil?',
        confirmText: 'Eliminar',
        cancelText: 'Cancelar'
    });
    if (!confirmed) {
        return;
    }
    try {
            // Obtener headers con autenticación
            const headers = auth ? auth.getHeaders() : { 'Content-Type': 'application/json' };

            // Obtener CSRF token
            const csrftoken = getCookie('csrftoken');
            if (csrftoken) {
                headers['X-CSRFToken'] = csrftoken;
            }

            const response = await fetch(`${MOVILES_API_URL}${id}/`, {
                method: 'DELETE',
                headers: headers
            });

            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }

            await loadMoviles();
            showAlert('Móvil eliminado correctamente', 'success');

        } catch (error) {
            console.error('Error al eliminar móvil:', error);
            showAlert('Error al eliminar el móvil', 'danger');
        }
}

// Actualizar dashboard
function updateDashboard() {
    // Actualizar estadísticas primero
    updateDashboardStats();
    
    // Mostrar móviles recientes
    const movilesRecientes = document.getElementById('moviles-recientes');
    if (!movilesRecientes) {
        return;
    }
    const movilesOrdenados = movilesData
        .sort((a, b) => new Date(b.fecha_recepcion || 0) - new Date(a.fecha_recepcion || 0))
        .slice(0, 5);

    movilesRecientes.innerHTML = '';
    movilesOrdenados.forEach(movil => {
        const div = document.createElement('div');
        div.className = 'd-flex justify-content-between align-items-center mb-2';

        const online = isOnline(movil);
        const estadoIcon = online ?
            '<i class="bi bi-wifi text-success"></i>' :
            '<i class="bi bi-wifi-off text-danger"></i>';

        div.innerHTML = `
            <div>
                <strong>${movil.alias || movil.patente || 'Sin identificar'}</strong><br>
                <small class="text-muted">${movil.fecha_recepcion ? new Date(movil.fecha_recepcion).toLocaleString('es-ES') : 'Sin datos'}</small>
            </div>
            <div>${estadoIcon}</div>
        `;

        movilesRecientes.appendChild(div);
    });
}

// Refrescar datos
async function refreshData() {
    await loadMoviles();
    showAlert('Datos actualizados correctamente', 'success');
}

// Mostrar alertas
function showAlert(message, type = 'info', html = false) {
    // Crear elemento de alerta
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';

    if (html) {
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
    } else {
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
    }

    // Agregar al DOM
    document.body.appendChild(alertDiv);

    // Auto-remover después del tiempo configurado
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, WAYGPS_CONFIG.UI.ALERT_DURATION);
}

// ----- Zonas generadas desde móviles -----
function setupZonaDesdeMovilModal() {
    const modalElement = document.getElementById('zonaDesdeMovilModal');
    const form = document.getElementById('zonaDesdeMovilForm');
    const tipoSelect = document.getElementById('zonaTipoSelect');

    if (!modalElement || !form || !tipoSelect) return;

    zonaDesdeMovilModal = new bootstrap.Modal(modalElement);
    form.addEventListener('submit', handleZonaDesdeMovilSubmit);
    tipoSelect.addEventListener('change', toggleZonaRadioField);
    toggleZonaRadioField();
}

function abrirModalZonaDesdeMovil(id) {
    const movil = movilesData.find(m => m.id === id);
    if (!movil) {
        showAlert('No se encontró el móvil seleccionado.', 'danger');
        return;
    }

    const status = movil.status_info || {};
    if (!status.ultimo_lat || !status.ultimo_lon) {
        showAlert('El móvil no tiene una posición actual disponible.', 'warning');
        return;
    }

    zonaMovilSeleccionado = movil;
    document.getElementById('zonaMovilId').value = movil.id;

    const identificacion = movil.alias || movil.patente || movil.codigo || `ID ${movil.id}`;
    const infoElement = document.getElementById('zonaMovilInfo');
    if (infoElement) infoElement.textContent = identificacion;

    const lat = parseFloat(status.ultimo_lat).toFixed(5);
    const lon = parseFloat(status.ultimo_lon).toFixed(5);
    const fecha = status.ultima_actualizacion ? new Date(status.ultima_actualizacion).toLocaleString() : 'Sin datos';
    const posicionInfo = document.getElementById('zonaMovilPosicionInfo');
    if (posicionInfo) {
        posicionInfo.innerHTML = `📍 Latitud: <strong>${lat}</strong> | Longitud: <strong>${lon}</strong><br><small>Actualizado: ${fecha}</small>`;
    }

    const nombreBase = identificacion.replace(/\s+/g, ' ');
    document.getElementById('zonaNombreInput').value = `${nombreBase} - Zona`;
    document.getElementById('zonaDescripcionInput').value = `Zona generada desde ${identificacion}`;
    document.getElementById('zonaTipoSelect').value = 'punto';
    document.getElementById('zonaRadioInput').value = 200;
    document.getElementById('zonaColorInput').value = '#ff0000';
    document.getElementById('zonaOpacidadInput').value = 0.5;
    document.getElementById('zonaVisibleInput').checked = true;
    toggleZonaRadioField();

    const statusElement = document.getElementById('zonaDesdeMovilStatus');
    if (statusElement) statusElement.textContent = '';

    zonaDesdeMovilModal.show();
}

function toggleZonaRadioField() {
    const tipo = document.getElementById('zonaTipoSelect')?.value;
    const radioGroup = document.getElementById('zonaRadioGroup');
    if (!radioGroup) return;
    radioGroup.style.display = tipo === 'circulo' ? 'block' : 'none';
}

async function handleZonaDesdeMovilSubmit(event) {
    event.preventDefault();
    if (!zonaMovilSeleccionado) {
        showAlert('No hay un móvil seleccionado.', 'danger');
        return;
    }

    const nombre = document.getElementById('zonaNombreInput').value.trim();
    if (!nombre) {
        showAlert('El nombre de la zona es obligatorio.', 'warning');
        return;
    }

    const payload = {
        movil_id: zonaMovilSeleccionado.id,
        nombre,
        descripcion: document.getElementById('zonaDescripcionInput').value.trim(),
        tipo: document.getElementById('zonaTipoSelect').value,
        color: document.getElementById('zonaColorInput').value,
        opacidad: document.getElementById('zonaOpacidadInput').value || 0.5,
        visible: document.getElementById('zonaVisibleInput').checked,
    };

    if (payload.tipo === 'circulo') {
        const radio = parseInt(document.getElementById('zonaRadioInput').value, 10);
        if (Number.isNaN(radio) || radio <= 0) {
            showAlert('Ingresá un radio válido para la zona circular.', 'warning');
            return;
        }
        payload.radio_metros = radio;
    }

    const btn = document.getElementById('zonaCrearBtn');
    const statusElement = document.getElementById('zonaDesdeMovilStatus');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Creando...';
    }
    if (statusElement) statusElement.textContent = 'Creando zona...';

    try {
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') || ''
        };
        if (typeof auth !== 'undefined' && auth && typeof auth.getHeaders === 'function') {
            Object.assign(headers, auth.getHeaders());
        }

        const response = await fetch('/zonas/api/zonas/crear-desde-movil/', {
            method: 'POST',
            headers,
            credentials: 'same-origin',
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMsg = errorData.error || errorData.detail || 'No se pudo crear la zona.';
            throw new Error(errorMsg);
        }

        showAlert('Zona creada correctamente. Podés gestionarla desde el módulo Zonas.', 'success');
        if (statusElement) statusElement.textContent = 'Zona creada correctamente.';
        zonaDesdeMovilModal.hide();
    } catch (error) {
        console.error('Error creando zona:', error);
        const message = error.message || 'Error creando la zona.';
        showAlert(message, 'danger');
        if (statusElement) statusElement.textContent = message;
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-bullseye"></i> Crear zona';
        }
    }
}
// Función para actualizar automáticamente
setInterval(() => {
    if (currentSection === 'dashboard' || currentSection === 'moviles' || currentSection === 'mapa') {
        loadMoviles();
    }
}, WAYGPS_CONFIG.AUTO_REFRESH_INTERVAL);

// ========================================
// FUNCIONES PARA TOGGLE DE VISTA
// ========================================

// Cambiar entre vista de tarjetas y lista
function cambiarVista(mode) {
    console.log('[cambiarVista] Cambiando a modo:', mode);
    const cardsView = document.getElementById('moviles-cards-view');
    const listView = document.getElementById('moviles-list-view');

    if (!cardsView || !listView) {
        console.warn('[cambiarVista] No se encontraron los contenedores de vista');
        return;
    }

    if (mode === 'cards') {
        cardsView.style.display = 'grid'; // Usar 'grid' para que se muestre correctamente
        listView.style.display = 'none';
        console.log('[cambiarVista] Vista cambiada a TARJETAS');
    } else {
        cardsView.style.display = 'none';
        listView.style.display = 'block';
        console.log('[cambiarVista] Vista cambiada a LISTA');
    }

    // Re-renderizar con el modo actual
    if (typeof renderizarMoviles === 'function') {
        renderizarMoviles();
    }
    
    // Asegurar que los botones estén eliminados después de cambiar la vista
    if (typeof eliminarBotonesVista === 'function') {
        setTimeout(eliminarBotonesVista, 50);
    }
}

// Renderizar móviles según el modo de vista actual
function renderizarMoviles() {
    console.log('renderizarMoviles llamado - modo:', currentViewMode, 'datos:', movilesData.length);

    // Asegurar que los botones estén eliminados antes de renderizar
    if (typeof eliminarBotonesVista === 'function') {
        eliminarBotonesVista();
    }

    if (currentViewMode === 'cards') {
        renderizarTarjetas();
    } else {
        renderizarLista();
    }

    // Actualizar contador
    actualizarContadorMoviles();
}

// Renderizar vista de tarjetas
function renderizarTarjetas() {
    const container = document.getElementById('moviles-cards-view');
    if (!container) return;

    container.innerHTML = '';

    if (filteredMovilesData.length === 0) {
        const hayDatos = movilesData.length > 0;
        container.innerHTML = `
            <div class="col-12 text-center py-5">
                <i class="bi bi-${hayDatos ? 'search' : 'car-front'} fs-1 text-muted"></i>
                <h5 class="text-muted mt-3">${hayDatos ? 'No se encontraron móviles' : 'No hay móviles disponibles'}</h5>
                <p class="text-muted">
                    ${hayDatos ? 'Ajustá los filtros o la búsqueda para ver resultados' : 'Crea tu primer móvil para comenzar'}
                </p>
            </div>
        `;
        return;
    }

    filteredMovilesData.forEach(movil => {
        const card = createMovilCard(movil);
        container.appendChild(card);
    });
}

// Renderizar vista de lista
function renderizarLista() {
    console.log('renderizarLista llamado - datos:', filteredMovilesData.length);
    const tbody = document.getElementById('moviles-table-body');
    console.log('tbody encontrado:', !!tbody);
    if (!tbody) {
        console.error('No se encontró moviles-table-body');
        return;
    }

    tbody.innerHTML = '';

    if (filteredMovilesData.length === 0) {
        const hayDatos = movilesData.length > 0;
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center py-5">
                    <i class="bi bi-${hayDatos ? 'search' : 'car-front'} fs-1 text-muted"></i>
                    <h5 class="text-muted mt-3">${hayDatos ? 'No se encontraron móviles' : 'No hay móviles disponibles'}</h5>
                    <p class="text-muted">
                        ${hayDatos ? 'Ajustá los filtros o la búsqueda para ver resultados' : 'Crea tu primer móvil para comenzar'}
                    </p>
                </td>
            </tr>
        `;
        return;
    }

    console.log('Renderizando', filteredMovilesData.length, 'móviles en lista');
    filteredMovilesData.forEach((movil, index) => {
        console.log(`Creando fila ${index + 1} para móvil:`, movil.alias || movil.patente);
        const row = createMovilRow(movil);
        tbody.appendChild(row);
    });
}

// Crear fila de tabla para vista de lista
function createMovilRow(movil) {
    const row = document.createElement('tr');

    // Determinar estado del móvil
    const online = isOnline(movil);
    const status = movil.status_info || {};
    const estadoConexion = status.estado_conexion || (online ? 'conectado' : 'desconectado');

    // Identificación del móvil
    const identificacion = movil.alias || movil.patente || movil.codigo || 'Sin identificar';

    // Información de posición y domicilio
    const geocode = movil.geocode_info || {};
    const domicilio = geocode.direccion_formateada ||
        (geocode.localidad && geocode.provincia ? `${geocode.localidad}, ${geocode.provincia}` :
            'Sin geocodificación');

    // Información de velocidad y batería
    const velocidad = status.ultima_velocidad_kmh ?
        `${status.ultima_velocidad_kmh} km/h` :
        'Sin datos';

    const bateria = status.bateria_pct ?
        `${status.bateria_pct}%` :
        'N/A';

    // Última actualización
    const ultimaActualizacion = status.ultima_actualizacion ?
        new Date(status.ultima_actualizacion) :
        null;

    const tiempoTranscurrido = ultimaActualizacion ?
        getTiempoTranscurrido(ultimaActualizacion) :
        'Sin datos';

    // Contador de fotos y observaciones
    const fotosCount = movil.fotos_count || 0;
    const observacionesCount = movil.observaciones_count || 0;

    row.innerHTML = `
        <td>
            <span class="status-indicator status-${estadoConexion}"></span>
            <span class="badge badge-status bg-${estadoConexion === 'conectado' ? 'success' : estadoConexion === 'desconectado' ? 'danger' : 'warning'}">
                ${estadoConexion === 'conectado' ? 'En línea' : estadoConexion === 'desconectado' ? 'Desconectado' : 'Error'}
            </span>
        </td>
        <td>
            <strong>${identificacion}</strong><br>
            <small class="text-muted">${movil.patente || 'Sin patente'}</small>
        </td>
        <td>
            <span class="text-truncate d-inline-block" style="max-width: 200px;" title="${domicilio}">
                ${domicilio}
            </span>
        </td>
        <td>${velocidad}</td>
        <td>
            ${bateria !== 'N/A' ?
            `<span class="badge bg-${parseInt(bateria) > 50 ? 'success' : parseInt(bateria) > 20 ? 'warning' : 'danger'}">${bateria}</span>` :
            '<span class="text-muted">N/A</span>'
        }
        </td>
        <td>
            <small>${tiempoTranscurrido}</small>
        </td>
        <td>
            <span class="badge bg-info">${fotosCount}</span>
        </td>
        <td>
            <span class="badge bg-secondary">${observacionesCount}</span>
        </td>
        <td>
            <div class="btn-group btn-group-sm" role="group">
                <button class="btn btn-outline-primary" onclick="verDetalleMovil(${movil.id})" title="Ver detalles">
                    <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-outline-warning" onclick="editarMovil(${movil.id})" title="Editar">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-outline-info" onclick="verEnMapa(${movil.id})" title="Ver en mapa">
                    <i class="bi bi-geo-alt"></i>
                </button>
                <button class="btn btn-outline-success" onclick="compartirMovil(${movil.id})" title="Compartir información">
                    <i class="bi bi-share"></i>
                </button>
                <button class="btn btn-outline-secondary" onclick="abrirModalZonaDesdeMovil(${movil.id})" title="Crear zona desde este móvil">
                    <i class="bi bi-bullseye"></i>
                </button>
                <button class="btn btn-outline-danger" onclick="eliminarMovil(${movil.id})" title="Eliminar">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        </td>
    `;

    return row;
}

// Actualizar contador de móviles
function actualizarContadorMoviles() {
    const counter = document.getElementById('moviles-count');
    if (counter) {
        const count = filteredMovilesData.length;
        counter.textContent = `${count} móvil${count !== 1 ? 'es' : ''}`;
    }
}

// Limpiar filtros
function limpiarFiltros() {
    const filtroBusqueda = document.getElementById('filtro-busqueda');
    const filtroEstado = document.getElementById('filtro-estado');
    const filtroEncendido = document.getElementById('filtro-encendido');
    const filtroTipo = document.getElementById('filtro-tipo');

    if (!filtroBusqueda || !filtroEstado || !filtroEncendido || !filtroTipo) {
        return;
    }

    filtroBusqueda.value = '';
    filtroEstado.value = '';
    filtroEncendido.value = '';
    filtroTipo.value = '';

    // Aplicar filtros (que mostrará todos los móviles)
    aplicarFiltros();
}

// ========================================
// FUNCIONES PARA COMPARTIR INFORMACIÓN
// ========================================

// Función principal para compartir información del móvil
function compartirMovil(id) {
    const movil = movilesData.find(m => m.id === id);
    if (!movil) {
        showAlert('No se encontró información del móvil', 'danger');
        return;
    }

    // Detectar si es dispositivo móvil
    const esMovil = esDispositivoMovil();

    if (!esMovil) {
        // En desktop, mostrar opciones de compartir
        mostrarOpcionesCompartirMovil(movil);
        return;
    }

    // En móvil, compartir directamente
    const mensaje = generarMensajeWhatsAppMovil(movil);
    const urlWhatsApp = `https://wa.me/?text=${encodeURIComponent(mensaje)}`;

    // Abrir WhatsApp
    window.open(urlWhatsApp, '_blank');
}

// Función para detectar si es dispositivo móvil
function esDispositivoMovil() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// Función para mostrar opciones de compartir en desktop
function mostrarOpcionesCompartirMovil(movil) {
    const status = movil.status_info || {};
    const geocode = movil.geocode_info || {};
    const identificacion = movil.alias || movil.patente || movil.codigo || 'Sin identificar';

    const opciones = `
        <div class="modal fade" id="modalCompartirMovil" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-whatsapp me-2"></i>
                            Compartir en WhatsApp - ${identificacion}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label for="mensajePersonalizadoMovil" class="form-label">Mensaje personalizado (opcional):</label>
                            <textarea class="form-control" id="mensajePersonalizadoMovil" rows="3" 
                                placeholder="Agregar un mensaje personalizado..."></textarea>
                        </div>
                        <div class="alert alert-info">
                            <i class="bi bi-info-circle me-2"></i>
                            <strong>Nota:</strong> En dispositivos móviles, esta opción se abre directamente en WhatsApp.
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn btn-success" id="btnCompartirMovilConfirmar">
                            <i class="bi bi-whatsapp me-1"></i>
                            Compartir
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remover modal existente si existe
    const modalExistente = document.getElementById('modalCompartirMovil');
    if (modalExistente) {
        modalExistente.remove();
    }

    // Agregar modal al DOM
    document.body.insertAdjacentHTML('beforeend', opciones);

    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('modalCompartirMovil'));
    modal.show();

    // Event listener para el botón de confirmar
    document.getElementById('btnCompartirMovilConfirmar').addEventListener('click', function () {
        const mensajePersonalizado = document.getElementById('mensajePersonalizadoMovil').value;

        const mensaje = generarMensajeWhatsAppMovil(movil, mensajePersonalizado);
        const urlWhatsApp = `https://wa.me/?text=${encodeURIComponent(mensaje)}`;

        // Abrir WhatsApp
        window.open(urlWhatsApp, '_blank');

        // Cerrar modal
        modal.hide();
    });

    // Limpiar modal cuando se cierre
    document.getElementById('modalCompartirMovil').addEventListener('hidden.bs.modal', function () {
        this.remove();
    });
}

// Función para generar mensaje de WhatsApp para móviles
function generarMensajeWhatsAppMovil(movil, mensajePersonalizado = '') {
    const fechaActual = new Date().toLocaleString('es-AR');
    const status = movil.status_info || {};
    const geocode = movil.geocode_info || {};

    const identificacion = movil.alias || movil.patente || movil.codigo || 'Sin identificar';
    const patente = movil.patente || 'Sin patente';
    const domicilio = geocode.direccion_formateada ||
        (geocode.localidad && geocode.provincia ? `${geocode.localidad}, ${geocode.provincia}` :
            'Sin geocodificación');

    const velocidad = status.ultima_velocidad_kmh ? `${status.ultima_velocidad_kmh} km/h` : 'Sin datos';
    const bateria = status.bateria_pct ? `${status.bateria_pct}%` : 'N/A';
    const encendido = status.ignicion ? 'Encendido' : 'Apagado';
    const online = isOnline(movil);
    const estado = online ? 'En línea' : 'Desconectado';

    const ultimaActualizacion = status.ultima_actualizacion ?
        new Date(status.ultima_actualizacion).toLocaleString('es-AR') :
        'Sin datos';

    let mensaje = `*Seguimiento GPS* - ${fechaActual}\n`;
    mensaje += `*Vehículo:* ${patente}${identificacion !== patente ? ` (${identificacion})` : ''}\n\n`;

    if (mensajePersonalizado) {
        mensaje += `${mensajePersonalizado}\n\n`;
    }

    mensaje += `*Ubicación Actual:*\n`;
    mensaje += `• Dirección: ${domicilio}\n`;
    if (status.ultimo_lat && status.ultimo_lon) {
        mensaje += `• Coordenadas: ${status.ultimo_lat}, ${status.ultimo_lon}\n`;
    }
    mensaje += `• Hora: ${ultimaActualizacion}\n`;
    mensaje += `• Velocidad: ${velocidad}\n`;
    mensaje += `• Batería: ${bateria}\n`;
    mensaje += `• Encendido: ${encendido}\n`;
    mensaje += `• Estado: ${estado}\n\n`;

    // Agregar enlace de Google Maps si hay coordenadas
    if (status.ultimo_lat && status.ultimo_lon) {
        mensaje += `Ver en Google Maps:\n`;
        mensaje += `https://www.google.com/maps?q=${status.ultimo_lat},${status.ultimo_lon}\n\n`;
    }

    mensaje += `📱 Información compartida desde WayGPS`;

    return mensaje;
}

window.abrirModalZonaDesdeMovil = abrirModalZonaDesdeMovil;

// ========================================
// LÓGICA DE VISTA RESPONSIVE AUTOMÁTICA
// ========================================
// Cambia automáticamente entre vista de tarjetas (móvil) y lista (PC)
// según el ancho de la pantalla. Los botones de cambio manual están ocultos.

/**
 * Elimina completamente cualquier botón de cambio de vista que pueda aparecer
 */
function eliminarBotonesVista() {
    const selectors = [
        '.view-controls',
        '.view-toggle',
        '#view-cards',
        '#view-list',
        'label[for="view-cards"]',
        'label[for="view-list"]',
        'input[name="view-mode"]',
        'input[type="radio"][name="view-mode"]',
        '.btn-group input[value="cards"]',
        '.btn-group input[value="list"]',
        '.btn-group label[for*="view"]'
    ];

    selectors.forEach(selector => {
        try {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                if (el) {
                    el.remove();
                }
            });
        } catch (e) {
            // Ignorar errores de selectores inválidos
        }
    });

    // Buscar contenedores padre que puedan tener los botones
    const viewControls = document.querySelectorAll('.view-controls, .view-toggle');
    viewControls.forEach(el => {
        el.remove();
    });

    // Buscar cualquier botón o label que contenga "Tarjetas" o "Lista" relacionado con vista
    const allButtons = document.querySelectorAll('button, label, .btn');
    allButtons.forEach(btn => {
        const text = (btn.textContent || btn.innerText || '').trim();
        const parent = btn.closest('.view-controls') || btn.closest('.view-toggle') || btn.closest('.btn-group');
        
        if ((text.includes('Tarjetas') || text.includes('Lista')) && 
            (parent || btn.id === 'view-cards' || btn.id === 'view-list' || 
             btn.getAttribute('for') === 'view-cards' || btn.getAttribute('for') === 'view-list')) {
            if (parent) {
                parent.remove();
            } else {
                btn.remove();
            }
        }
    });
}

/**
 * Detecta si el dispositivo es móvil basándose en el ancho de pantalla
 * @returns {boolean} true si es móvil (< 768px), false si es PC
 */
function isMobileDevice() {
    return window.innerWidth < 768;
}

/**
 * Maneja el cambio automático de vista según el tamaño de pantalla
 * - Móvil (< 768px): Vista de tarjetas
 * - PC (>= 768px): Vista de lista
 */
function handleViewMode() {
    const newMode = isMobileDevice() ? 'cards' : 'list';
    
    if (currentViewMode !== newMode) {
        console.log(`[Vista Responsive] Cambiando de ${currentViewMode} a ${newMode} (ancho: ${window.innerWidth}px)`);
        currentViewMode = newMode;
        cambiarVista(currentViewMode);
    }
}

// Inicializar vista automáticamente al cargar
(function initializeResponsiveView() {
    function initView() {
        // Primero eliminar cualquier botón de vista
        if (typeof eliminarBotonesVista === 'function') {
            eliminarBotonesVista();
        }
        
        // Luego aplicar la vista responsive
        if (typeof isMobileDevice === 'function' && typeof handleViewMode === 'function') {
            handleViewMode();
        }
    }
    
    // Ejecutar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(initView, 150);
        });
    } else {
        // Si el DOM ya está listo, ejecutar inmediatamente
        setTimeout(initView, 150);
    }
    
    // También ejecutar cuando la página esté completamente cargada (por si acaso)
    window.addEventListener('load', function() {
        setTimeout(initView, 300);
    });
    
    // Ejecutar periódicamente para asegurar que los botones no aparezcan (por si se crean dinámicamente)
    setInterval(function() {
        if (typeof eliminarBotonesVista === 'function') {
            eliminarBotonesVista();
        }
    }, 2000); // Cada 2 segundos
})();

// Manejar cambios de tamaño de ventana con debounce
let resizeTimer;
window.addEventListener('resize', function() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(handleViewMode, 250);
});

console.log('WayGPS Frontend cargado - Vista responsive automática activada');


