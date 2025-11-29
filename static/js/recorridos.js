/**
 * JavaScript para la interfaz de Recorridos GPS
 */

// Variables globales
let map;
let recorridoLayer;
let marcadoresLayer;
let posicionActualLayer;
let openstreetLayer;
let satelliteLayer;
let hybridLayer;
let hybridLabelsLayer;
let datosRecorrido = [];
let estadisticasRecorrido = null;
let isPlaying = false;
let currentIndex = 0;
let playbackInterval = null;
let velocidadReproduccion = 1;
let currentViewMode = 'list'; // 'list' o 'map'
let paginationInfo = null; // Información de paginación
let timelineMeta = {
    total: 0,
    selectedIndex: 1,
    currentPageStart: 1,
    currentPageEnd: 1,
    labels: {
        start: null,
        middle: null,
        end: null
    }
};
let highlightedTimelineRow = null;

const PAGE_SIZE_DEFAULT = 50;

// Zona API
const ZONAS_API_URL = '/zonas/api/zonas/';
const MOVILES_SIMPLE_URL = '/moviles/api/moviles/?simple=true';
let movilesCache = null;

// Obtener CSRF token
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

function buildZonaHeaders() {
    const headers = auth && typeof auth.getHeaders === 'function'
        ? auth.getHeaders()
        : { 'Content-Type': 'application/json' };

    const csrftoken = getCookie('csrftoken');
    if (csrftoken) {
        headers['X-CSRFToken'] = csrftoken;
    }
    // Asegurar JSON
    headers['Content-Type'] = 'application/json';
    return headers;
}

// Configuración del mapa
const MAP_CENTER = [-34.6037, -58.3816]; // Buenos Aires
const MAP_ZOOM = 10;

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    try {
        await loadMoviles();
        initializeMap();
        setupEventListeners();
        setupNaNMonitor(); // Activar monitor NaN
        setDefaultDates();
        
        // Cargar preferencia de vista guardada
        currentViewMode = localStorage.getItem('recorridos-view-mode') || 'list';
        if (document.getElementById(`view-${currentViewMode}`)) {
            document.getElementById(`view-${currentViewMode}`).checked = true;
        }
        cambiarVista(currentViewMode);
    } catch (error) {
        console.error('Error inicializando la aplicación:', error);
        showMessage('Error inicializando la aplicación', 'error');
    }
}

// Cargar lista de móviles
async function loadMoviles(force = false) {
    try {
        if (movilesCache && !force) {
            renderMovilesSelect(movilesCache);
            return;
        }

        const headers = typeof auth !== 'undefined' && auth.getHeaders ? auth.getHeaders() : { 'Content-Type': 'application/json' };
        const response = await fetch(MOVILES_SIMPLE_URL, { headers });

        if (!response.ok) {
            throw new Error('Error cargando móviles');
        }

        const moviles = await response.json();
        movilesCache = moviles;
        renderMovilesSelect(moviles);
    } catch (error) {
        console.error('Error cargando móviles:', error);
        showMessage('Error cargando la lista de móviles', 'error');
    }
}

function renderMovilesSelect(moviles = []) {
    const select = document.getElementById('movil-select');
    if (!select) return;

    select.innerHTML = '<option value="">Seleccionar móvil...</option>';

    moviles.forEach(movil => {
        const option = document.createElement('option');
        option.value = movil.id;
        option.textContent = movil.display || `${movil.patente || movil.alias || 'Sin identificación'}`;
        select.appendChild(option);
    });
}

// Inicializar mapa
let mapInitialized = false;

function initializeMap() {
    // Verificar que el elemento del mapa existe
    const mapElement = document.getElementById('map');
    if (!mapElement) {
        console.error('Elemento #map no encontrado');
        return;
    }
    
    // Si el mapa ya está inicializado, no hacer nada
    if (mapInitialized && map) {
        return;
    }
    
    // Esperar un momento para que el DOM esté completamente renderizado
    setTimeout(() => {
        try {
            const mapResult = initializeNormalizedMap('map', {
                lat: MAP_CENTER[0],
                lon: MAP_CENTER[1],
                zoom: MAP_ZOOM,
                showZonesControl: true,
                showLayerControl: true
            });
            
            map = mapResult.map;
            window.mapResultRecorridos = mapResult; // Guardar referencia global para acceso desde otras funciones
            mapInitialized = true;
            
            // Mantener referencias a las capas para compatibilidad
            openstreetLayer = mapResult.layers.street;
            satelliteLayer = mapResult.layers.satellite;
            hybridLayer = mapResult.layers.hybrid;
            hybridLabelsLayer = mapResult.layers.labels;
            
            // Capas para el recorrido
            recorridoLayer = L.layerGroup().addTo(map);
            marcadoresLayer = L.layerGroup().addTo(map);
            posicionActualLayer = L.layerGroup().addTo(map);
            
            console.log('Mapa inicializado correctamente');
            
            // Si el mapa está visible, invalidar el tamaño inmediatamente
            const mapView = document.getElementById('recorridos-map-view');
            if (mapView && mapView.style.display !== 'none') {
                setTimeout(() => {
                    if (map) {
                        map.invalidateSize();
                        // Asegurar que el mapa ocupe todo el contenedor
                        const mapContainer = map.getContainer();
                        mapContainer.style.height = '540px';
                        mapContainer.style.width = '100%';
                        mapContainer.style.opacity = '1';
                    }
                }, 100);
            }
        } catch (error) {
            console.error('Error inicializando el mapa:', error);
        }
    }, 200);
}

// Monitor global para detectar NaN:NaN en la interfaz
function setupNaNMonitor() {
    // Observar cambios en los elementos de tiempo
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList' || mutation.type === 'characterData') {
                const target = mutation.target;
                if (target.textContent && target.textContent.includes('NaN')) {
                    console.error('🚨 NAN DETECTADO EN INTERFAZ:', {
                        elemento: target,
                        texto: target.textContent,
                        id: target.id,
                        className: target.className,
                        stack: new Error().stack
                    });
                }
            }
        });
    });
    
    // Observar cambios en elementos de tiempo
    const tiempoActual = document.getElementById('tiempo-actual');
    const tiempoTotal = document.getElementById('tiempo-total');
    
    if (tiempoActual) {
        observer.observe(tiempoActual, { 
            childList: true, 
            characterData: true, 
            subtree: true 
        });
    }
    
    if (tiempoTotal) {
        observer.observe(tiempoTotal, { 
            childList: true, 
            characterData: true, 
            subtree: true 
        });
    }
    
    console.log('🔍 Monitor NaN activado para elementos de tiempo');
}

// Configurar event listeners
function setupEventListeners() {
    // Formulario de filtros
    document.getElementById('filtros-form').addEventListener('submit', function(e) {
        e.preventDefault();
        buscarRecorrido();
    });
    
    // Manejar colapso lateral de filtros
    const filtrosPanel = document.getElementById('filtros-panel');
    const contenidoPrincipal = document.getElementById('contenido-principal');
    const filtrosToggleIcon = document.getElementById('filtros-toggle-icon');
    const btnMostrarFiltros = document.getElementById('btn-mostrar-filtros');
    
    if (filtrosPanel && filtrosToggleIcon) {
        // Toggle del panel lateral
        document.getElementById('toggle-filtros').addEventListener('click', function() {
            if (filtrosPanel.classList.contains('colapsado')) {
                // Mostrar panel
                filtrosPanel.classList.remove('colapsado');
                contenidoPrincipal.classList.remove('expandido');
                filtrosToggleIcon.className = 'bi bi-chevron-left';
            } else {
                // Ocultar panel
                filtrosPanel.classList.add('colapsado');
                contenidoPrincipal.classList.add('expandido');
                filtrosToggleIcon.className = 'bi bi-chevron-right';
            }
        });
        
        // Botón flotante para mostrar filtros
        if (btnMostrarFiltros) {
            btnMostrarFiltros.addEventListener('click', function() {
                filtrosPanel.classList.remove('colapsado');
                contenidoPrincipal.classList.remove('expandido');
                filtrosToggleIcon.className = 'bi bi-chevron-left';
            });
        }
    }
    
    // Controles de reproducción
    document.getElementById('velocidad-reproduccion').addEventListener('change', cambiarVelocidadReproduccion);
    
    // Botones de compartir a WhatsApp
    document.getElementById('btn-compartir-whatsapp').addEventListener('click', function() {
        compartirAWhatsApp('lista');
    });
    
    document.getElementById('btn-compartir-whatsapp-mapa').addEventListener('click', function() {
        compartirAWhatsApp('mapa');
    });
    
    // Barra de progreso
    document.querySelector('.progress').addEventListener('click', function(e) {
        const rect = this.getBoundingClientRect();
        const percent = (e.clientX - rect.left) / rect.width;
        const newIndex = Math.floor(percent * (datosRecorrido.length - 1));
        saltarAPosicion(newIndex);
    });
    
    // Event listeners para el toggle de vista
    document.querySelectorAll('input[name="view-mode"]').forEach(radio => {
        radio.addEventListener('change', function() {
            currentViewMode = this.value;
            localStorage.setItem('recorridos-view-mode', currentViewMode);
            cambiarVista(currentViewMode);
        });
    });

    // Botones para crear zona del recorrido (polilínea) en ambas vistas
    const botonesZonaRecorrido = document.querySelectorAll('.btn-zona-recorrido');
    botonesZonaRecorrido.forEach(btn => {
        btn.addEventListener('click', abrirModalZonaRecorrido);
    });

    const timelineRange = document.getElementById('timeline-range');
    if (timelineRange) {
        timelineRange.addEventListener('input', (e) => actualizarTimelinePreview(parseInt(e.target.value)));
        timelineRange.addEventListener('change', (e) => manejarTimelineChange(parseInt(e.target.value)));
    }
}

// Establecer fechas por defecto
function setDefaultDates() {
    const now = new Date();
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    
    document.getElementById('fecha-desde').value = formatDateTimeLocal(yesterday);
    document.getElementById('fecha-hasta').value = formatDateTimeLocal(now);
}

// Formatear fecha para input datetime-local
function formatDateTimeLocal(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

// Buscar recorrido
async function buscarRecorrido() {
    const formData = new FormData(document.getElementById('filtros-form'));
    const movilId = formData.get('movil-select');
    const fechaDesde = formData.get('fecha-desde');
    const fechaHasta = formData.get('fecha-hasta');
    
    if (!movilId || !fechaDesde || !fechaHasta) {
        showMessage('Por favor complete todos los campos requeridos', 'warning');
        return;
    }
    
    timelineMeta = {
        total: 0,
        selectedIndex: 1,
        currentPageStart: 1,
        currentPageEnd: 1,
        labels: {
            start: null,
            middle: null,
            end: null
        }
    };
    
    showLoading(true);
    
    try {
        // Obtener datos del recorrido con filtros
        const params = new URLSearchParams({
            movil_id: movilId,
            fecha_desde: fechaDesde,
            fecha_hasta: fechaHasta
        });
        
        // Agregar filtros de velocidad
        const velocidadMin = document.getElementById('velocidad-min').value;
        const velocidadMax = document.getElementById('velocidad-max').value;
        if (velocidadMin) params.append('velocidad_min', velocidadMin);
        if (velocidadMax) params.append('velocidad_max', velocidadMax);
        
        // Agregar filtros de estado del vehículo
        const soloDetenciones = document.getElementById('solo-detenciones').checked;
        const soloMovimiento = document.getElementById('solo-movimiento').checked;
        const soloEncendido = document.getElementById('ignicion-encendida').checked;
        
        if (soloDetenciones) params.append('solo_detenciones', 'true');
        if (soloMovimiento) params.append('solo_movimiento', 'true');
        if (soloEncendido) params.append('ignicion_encendida', 'true');
        
        // Si es vista de mapa, agregar parámetro para obtener todos los registros
        if (currentViewMode === 'map') {
            params.append('vista_mapa', 'true');
            console.log('🗺️ Enviando parámetro vista_mapa=true al backend');
        }
        
        console.log('Filtros aplicados:', {
            soloDetenciones,
            soloMovimiento,
            soloEncendido,
            velocidadMin,
            velocidadMax,
            vistaMapa: currentViewMode === 'map'
        });
        
        console.log('URL de la consulta:', `/api/recorridos/?${params}`);
        
        const response = await fetch(`/api/recorridos/?${params}`, {
            headers: auth.getHeaders()
        });
        
        console.log('Respuesta del servidor:', response.status, response.statusText);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error del servidor:', errorText);
            throw new Error(`Error obteniendo datos del recorrido: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Datos recibidos:', data);
        
        // Si es vista de mapa, los datos vienen directamente como array
        if (currentViewMode === 'map') {
            datosRecorrido = Array.isArray(data) ? data : data.results || [];
            console.log('🗺️ Vista de mapa: cargadas', datosRecorrido.length, 'posiciones');
        } else {
            // Si es vista de lista, los datos vienen paginados
            datosRecorrido = data.results || data;
            console.log('📋 Vista de lista: cargadas', datosRecorrido.length, 'posiciones (página actual)');
        }
        
        // Guardar información de paginación
        if (data.count !== undefined) {
            paginationInfo = {
                total: data.count,
                currentPage: data.current || 1,
                totalPages: Math.ceil(data.count / PAGE_SIZE_DEFAULT), // 50 es el PAGE_SIZE
                pageSize: data.page_size || PAGE_SIZE_DEFAULT,
                hasNext: data.next !== null,
                hasPrevious: data.previous !== null,
                baseUrl: construirBaseUrl(params)
            };
            console.log('Información de paginación:', paginationInfo);
        }
        
        if (datosRecorrido.length === 0) {
            showMessage('No se encontraron posiciones para el período seleccionado', 'warning');
            return;
        }

        timelineMeta.total = paginationInfo ? paginationInfo.total : datosRecorrido.length;
        timelineMeta.selectedIndex = Math.min(timelineMeta.selectedIndex || 1, Math.max(timelineMeta.total, 1));
        await prepararEtiquetasTimeline(datosRecorrido);
        
        // Obtener estadísticas
        await cargarEstadisticas(movilId, fechaDesde, fechaHasta);
        
        // Renderizar según la vista actual
        if (currentViewMode === 'list') {
            renderizarListado();
        } else {
            renderizarRecorrido();
        }
        
        // Inicializar controles de reproducción después de renderizar
        setTimeout(() => {
            actualizarControlesReproduccion();
            // Inicializar tiempo actual en 00:00
            const tiempoActual = document.getElementById('tiempo-actual');
            if (tiempoActual) tiempoActual.textContent = '00:00';
        }, 100);
        
        // Actualizar controles de paginación solo en vista de lista
        if (currentViewMode === 'list') {
            actualizarControlesPaginacion();
        } else {
            // Ocultar controles de paginación en vista de mapa
            const paginationContainer = document.getElementById('pagination-container');
            if (paginationContainer) {
                paginationContainer.innerHTML = '';
            }
        }
        
        // Habilitar botones de exportación
        document.getElementById('btn-export-excel').disabled = false;
        document.getElementById('btn-geocodificar').disabled = false;
        
        showMessage(`Recorrido cargado: ${datosRecorrido.length} posiciones encontradas`, 'success');
        
    } catch (error) {
        console.error('Error buscando recorrido:', error);
        showMessage('Error cargando el recorrido', 'error');
    } finally {
        showLoading(false);
    }
}

// Cargar estadísticas del recorrido
async function cargarEstadisticas(movilId, fechaDesde, fechaHasta) {
    try {
        const params = new URLSearchParams({
            movil_id: movilId,
            fecha_desde: fechaDesde,
            fecha_hasta: fechaHasta
        });
        
        const response = await fetch(`/api/recorridos/estadisticas_recorrido/?${params}`, {
            headers: auth.getHeaders()
        });
        
        if (response.ok) {
            estadisticasRecorrido = await response.json();
            mostrarEstadisticas();
        }
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
    }
}

// Mostrar estadísticas
function mostrarEstadisticas() {
    if (!estadisticasRecorrido) return;
    
    const panel = document.getElementById('estadisticas-panel');
    const content = document.getElementById('estadisticas-content');
    
    content.innerHTML = `
        <div class="movil-info-panel">
            <h6>Información del Móvil</h6>
            <div class="movil-info-item">
                <span class="movil-info-label">Patente:</span>
                <span class="movil-info-value">${estadisticasRecorrido.movil_info?.patente || 'N/A'}</span>
            </div>
            <div class="movil-info-item">
                <span class="movil-info-label">Alias:</span>
                <span class="movil-info-value">${estadisticasRecorrido.movil_info?.alias || 'N/A'}</span>
            </div>
        </div>
        
        <div class="estadisticas-detalladas">
            <h6>Estadísticas del Recorrido</h6>
            <div class="estadisticas-grid">
                <div class="estadistica-card">
                    <div class="estadistica-valor">${estadisticasRecorrido.duracion_minutos.toFixed(0)}</div>
                    <div class="estadistica-etiqueta">Minutos</div>
                </div>
                <div class="estadistica-card">
                    <div class="estadistica-valor">${estadisticasRecorrido.distancia_km.toFixed(2)}</div>
                    <div class="estadistica-etiqueta">Kilómetros</div>
                </div>
                <div class="estadistica-card">
                    <div class="estadistica-valor">${estadisticasRecorrido.velocidad_maxima}</div>
                    <div class="estadistica-etiqueta">Vel. Máx (km/h)</div>
                </div>
                <div class="estadistica-card">
                    <div class="estadistica-valor">${estadisticasRecorrido.velocidad_promedio.toFixed(1)}</div>
                    <div class="estadistica-etiqueta">Vel. Prom (km/h)</div>
                </div>
                <div class="estadistica-card">
                    <div class="estadistica-valor">${estadisticasRecorrido.puntos_gps}</div>
                    <div class="estadistica-etiqueta">Puntos GPS</div>
                </div>
                <div class="estadistica-card">
                    <div class="estadistica-valor">${estadisticasRecorrido.detenciones}</div>
                    <div class="estadistica-etiqueta">Detenciones</div>
                </div>
            </div>
        </div>
    `;
    
    panel.style.display = 'block';
}

// Renderizar recorrido en el mapa
function renderizarRecorrido() {
    console.log('🎯 renderizarRecorrido llamada con', datosRecorrido.length, 'posiciones');
    
    // Verificar que el mapa esté inicializado
    if (!map) {
        console.log('Mapa no inicializado, inicializando...');
        initializeMap();
        // Esperar un momento para que el mapa se inicialice
        setTimeout(() => {
            renderizarRecorrido();
        }, 100);
        return;
    }
    
    // Limpiar capas anteriores
    if (recorridoLayer) recorridoLayer.clearLayers();
    if (marcadoresLayer) marcadoresLayer.clearLayers();
    if (posicionActualLayer) posicionActualLayer.clearLayers();
    
    if (datosRecorrido.length === 0) return;
    
    // Actualizar contador de posiciones en la vista de mapa
    const posicionesCountMapa = document.getElementById('posiciones-count-mapa');
    if (posicionesCountMapa) {
        posicionesCountMapa.textContent = `${datosRecorrido.length} posiciones`;
    }
    
    // Crear línea del recorrido
    const coordenadas = datosRecorrido.map(punto => [punto.lat, punto.lon]);
    const polyline = L.polyline(coordenadas, {
        color: '#0d6efd',
        weight: 3,
        opacity: 0.8
    });
    
    recorridoLayer.addLayer(polyline);
    
    // Ajustar vista del mapa
    if (coordenadas.length > 0) {
        const bounds = L.latLngBounds(coordenadas);
        console.log('Ajustando mapa a bounds:', bounds);
        map.fitBounds(bounds, { padding: [20, 20] });
        console.log('Mapa ajustado. Centro actual:', map.getCenter(), 'Zoom:', map.getZoom());
    }
    
    // Crear marcadores de velocidad
    datosRecorrido.forEach((punto, index) => {
        const color = getColorBySpeed(punto.velocidad);
        const marker = L.circleMarker([punto.lat, punto.lon], {
            radius: getRadiusBySpeed(punto.velocidad),
            fillColor: color,
            color: 'white',
            weight: 2,
            opacity: 0.8,
            fillOpacity: 0.8
        });
        
        // Popup con información del punto
        const popupContent = `
            <div>
                <strong>Punto ${index + 1}</strong><br>
                <strong>Velocidad:</strong> ${punto.velocidad} km/h<br>
                <strong>Hora:</strong> ${new Date(punto.timestamp).toLocaleString()}<br>
                <strong>Satélites:</strong> ${punto.satelites}<br>
                <strong>Encendido:</strong> ${punto.ignicion ? 'Sí' : 'No'}
            </div>
        `;
        
        marker.bindPopup(popupContent);
        marcadoresLayer.addLayer(marker);
    });
    
    // Inicializar reproducción
    currentIndex = 0;
    actualizarTiempo();
    actualizarBarraProgreso();
}

// Obtener color según velocidad
function getColorBySpeed(velocidad) {
    if (velocidad <= 5) return '#dc3545';      // Detenido
    if (velocidad <= 15) return '#fd7e14';     // Muy lento
    if (velocidad <= 30) return '#ffc107';     // Lento
    if (velocidad <= 50) return '#20c997';     // Moderado
    if (velocidad <= 80) return '#198754';     // Rápido
    return '#0d6efd';                          // Muy rápido
}

// Obtener radio según velocidad
function getRadiusBySpeed(velocidad) {
    if (velocidad <= 5) return 4;
    if (velocidad <= 15) return 5;
    if (velocidad <= 30) return 6;
    if (velocidad <= 50) return 7;
    if (velocidad <= 80) return 8;
    return 9;
}

// Controles de reproducción
function togglePlayback() {
    if (isPlaying) {
        pausarReproduccion();
    } else {
        iniciarReproduccion();
    }
}

function iniciarReproduccion() {
    if (datosRecorrido.length === 0) return;
    
    isPlaying = true;
    document.getElementById('btn-play').style.display = 'none';
    document.getElementById('btn-pause').style.display = 'inline-block';
    
    playbackInterval = setInterval(() => {
        if (currentIndex < datosRecorrido.length - 1) {
            currentIndex++;
            actualizarPosicionActual();
            actualizarTiempo();
            actualizarBarraProgreso();
            actualizarTiempoActual(); // Actualizar controles de tiempo
        } else {
            pausarReproduccion();
        }
    }, 1000 / velocidadReproduccion);
}

function pausarReproduccion() {
    isPlaying = false;
    document.getElementById('btn-play').style.display = 'inline-block';
    document.getElementById('btn-pause').style.display = 'none';
    
    if (playbackInterval) {
        clearInterval(playbackInterval);
        playbackInterval = null;
    }
}

function stopPlayback() {
    pausarReproduccion();
    currentIndex = 0;
    actualizarPosicionActual();
    actualizarTiempo();
    actualizarBarraProgreso();
    
    // Resetear controles de tiempo
    const tiempoActual = document.getElementById('tiempo-actual');
    const progressBar = document.getElementById('progress-bar');
    if (tiempoActual) tiempoActual.textContent = '00:00';
    if (progressBar) progressBar.style.width = '0%';
}

function cambiarVelocidadReproduccion() {
    velocidadReproduccion = parseFloat(document.getElementById('velocidad-reproduccion').value);
    
    if (isPlaying) {
        pausarReproduccion();
        iniciarReproduccion();
    }
}

function saltarAPosicion(index) {
    currentIndex = Math.max(0, Math.min(index, datosRecorrido.length - 1));
    actualizarPosicionActual();
    actualizarTiempo();
    actualizarBarraProgreso();
}

// Actualizar posición actual en el mapa
function actualizarPosicionActual() {
    posicionActualLayer.clearLayers();
    
    if (datosRecorrido[currentIndex]) {
        const punto = datosRecorrido[currentIndex];
        const marker = L.marker([punto.lat, punto.lon], {
            icon: L.divIcon({
                className: 'current-position-marker',
                html: '<div class="current-position"></div>',
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            })
        });
        
        posicionActualLayer.addLayer(marker);
        
        // Centrar mapa en la posición actual
        map.setView([punto.lat, punto.lon], map.getZoom());
    }
}

// Actualizar tiempo mostrado
function actualizarTiempo() {
    if (datosRecorrido.length === 0) return;
    
    console.log('🔍 actualizarTiempo: INICIANDO', { currentIndex, totalPosiciones: datosRecorrido.length });
    
    try {
        // Usar fec_gps en lugar de timestamp
        const posicionActual = datosRecorrido[currentIndex];
        const posicionInicio = datosRecorrido[0];
        const posicionFin = datosRecorrido[datosRecorrido.length - 1];
        
        // Obtener fechas de los campos correctos
        const fechaActual = posicionActual.fec_gps || posicionActual.timestamp;
        const fechaInicio = posicionInicio.fec_gps || posicionInicio.timestamp;
        const fechaFin = posicionFin.fec_gps || posicionFin.timestamp;
        
        console.log('🔍 actualizarTiempo: Fechas obtenidas:', {
            fechaActual,
            fechaInicio,
            fechaFin
        });
        
        const tiempoActual = new Date(fechaActual);
        const tiempoInicio = new Date(fechaInicio);
        const tiempoFin = new Date(fechaFin);
        
        console.log('🔍 actualizarTiempo: Objetos Date creados:', {
            tiempoActual,
            tiempoInicio,
            tiempoFin,
            actualValid: !isNaN(tiempoActual.getTime()),
            inicioValid: !isNaN(tiempoInicio.getTime()),
            finValid: !isNaN(tiempoFin.getTime())
        });
        
        // Verificar que las fechas sean válidas
        if (isNaN(tiempoActual.getTime()) || isNaN(tiempoInicio.getTime()) || isNaN(tiempoFin.getTime())) {
            console.error('❌ actualizarTiempo: Fechas inválidas');
            return;
        }
        
        const duracion = tiempoFin - tiempoInicio;
        const tiempoTranscurrido = tiempoActual - tiempoInicio;
        
        console.log('🔍 actualizarTiempo: Cálculos:', {
            duracion,
            tiempoTranscurrido,
            duracionFormateada: formatTime(duracion),
            tiempoFormateado: formatTime(tiempoTranscurrido)
        });
        
        // Actualizar elementos solo si los cálculos son válidos
        if (!isNaN(duracion) && !isNaN(tiempoTranscurrido)) {
            const tiempoActualElement = document.getElementById('tiempo-actual');
            const tiempoTotalElement = document.getElementById('tiempo-total');
            
            if (tiempoActualElement) {
                tiempoActualElement.textContent = formatTime(tiempoTranscurrido);
            }
            if (tiempoTotalElement) {
                tiempoTotalElement.textContent = formatTime(duracion);
            }
            
            console.log('✅ actualizarTiempo: Tiempos actualizados correctamente');
        } else {
            console.error('❌ actualizarTiempo: Cálculos inválidos');
        }
    } catch (error) {
        console.error('❌ actualizarTiempo: Error:', error);
    }
}

// Actualizar barra de progreso
function actualizarBarraProgreso() {
    if (datosRecorrido.length === 0) return;
    
    const porcentaje = (currentIndex / (datosRecorrido.length - 1)) * 100;
    document.getElementById('progress-bar').style.width = `${porcentaje}%`;
}

// Formatear tiempo en mm:ss
function formatTime(milliseconds) {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// Limpiar filtros
function limpiarFiltros() {
    document.getElementById('filtros-form').reset();
    setDefaultDates();
    
    // Limpiar mapa
    recorridoLayer.clearLayers();
    marcadoresLayer.clearLayers();
    posicionActualLayer.clearLayers();
    
    // Limpiar datos
    datosRecorrido = [];
    estadisticasRecorrido = null;
    currentIndex = 0;
    
    // Ocultar panel de estadísticas
    document.getElementById('estadisticas-panel').style.display = 'none';
    
    // Resetear controles de reproducción
    stopPlayback();
    actualizarTiempo();
    actualizarBarraProgreso();
    
    // Limpiar listado
    renderizarListado();
    
    // Deshabilitar botones de exportación
    document.getElementById('btn-export-excel').disabled = true;
    document.getElementById('btn-geocodificar').disabled = true;
    
    showMessage('Filtros limpiados', 'info');
}

// Mostrar mensaje
function showMessage(message, type = 'info') {
    const alertClass = `alert-${type}`;
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Insertar mensaje al inicio del contenido
    const container = document.querySelector('.container-fluid');
    container.insertAdjacentHTML('afterbegin', alertHtml);
    
    // Auto-remover después de 5 segundos
    setTimeout(() => {
        const alert = container.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

// Mostrar/ocultar loading
function showLoading(show) {
    document.getElementById('loading-overlay').style.display = show ? 'flex' : 'none';
}

// Inicializar comportamiento del modal de zona desde posición
document.addEventListener('DOMContentLoaded', () => {
    const formZonaPos = document.getElementById('formZonaDesdePosicion');
    const tipoPuntoRadio = document.getElementById('zonaPosicionTipoPunto');
    const tipoCirculoRadio = document.getElementById('zonaPosicionTipoCirculo');
    const radioGroup = document.getElementById('zonaPosicionRadioGroup');

    if (tipoPuntoRadio && tipoCirculoRadio && radioGroup) {
        const toggleRadioGroup = () => {
            radioGroup.style.display = tipoCirculoRadio.checked ? 'block' : 'none';
        };
        tipoPuntoRadio.addEventListener('change', toggleRadioGroup);
        tipoCirculoRadio.addEventListener('change', toggleRadioGroup);
        toggleRadioGroup();
    }

    if (formZonaPos) {
        formZonaPos.addEventListener('submit', handleZonaDesdePosicionSubmit);
    }

    const formZonaRecorrido = document.getElementById('formZonaRecorrido');
    if (formZonaRecorrido) {
        formZonaRecorrido.addEventListener('submit', handleZonaRecorridoSubmit);
    }
});

// Manejar submit del modal de zona desde posición
async function handleZonaDesdePosicionSubmit(event) {
    event.preventDefault();

    const lat = parseFloat(document.getElementById('zonaPosicionLat').value);
    const lon = parseFloat(document.getElementById('zonaPosicionLon').value);
    const nombre = document.getElementById('zonaPosicionNombre').value.trim();
    const descripcion = document.getElementById('zonaPosicionDescripcion').value.trim();
    const tipo = document.querySelector('input[name="zonaPosicionTipo"]:checked')?.value || 'punto';
    const radio = parseInt(document.getElementById('zonaPosicionRadio').value || '0', 10);

    if (!nombre) {
        showMessage('Ingresá un nombre para la zona.', 'warning');
        document.getElementById('zonaPosicionNombre').focus();
        return;
    }

    if (Number.isNaN(lat) || Number.isNaN(lon)) {
        showMessage('Las coordenadas no son válidas.', 'warning');
        return;
    }

    const payload = {
        nombre,
        descripcion,
        tipo,
        color: '#0d6efd',
        opacidad: 0.5,
        visible: true
    };

    if (tipo === 'circulo') {
        if (Number.isNaN(radio) || radio <= 0) {
            showMessage('El radio debe ser un número positivo.', 'warning');
            return;
        }
        payload.radio_metros = radio;
        payload.centro_geojson_input = {
            type: 'Point',
            coordinates: [lon, lat]
        };
    } else {
        payload.geom_geojson_input = {
            type: 'Point',
            coordinates: [lon, lat]
        };
    }

    try {
        const headers = buildZonaHeaders();
        const response = await fetch(ZONAS_API_URL, {
            method: 'POST',
            headers,
            body: JSON.stringify(payload),
            credentials: 'same-origin'
        });

        if (!response.ok) {
            let errorMsg = `Error HTTP: ${response.status}`;
            try {
                const errorData = await response.json();
                errorMsg = errorData.error || errorData.detail || errorMsg;
                console.error('Error al crear zona desde posición (modal):', errorData);
            } catch (e) {
                console.error('Error al parsear respuesta de zona (modal):', e);
            }
            throw new Error(errorMsg);
        }

        showMessage('Zona creada correctamente desde la posición seleccionada.', 'success');

        const modalEl = document.getElementById('modalZonaDesdePosicion');
        if (modalEl) {
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
        }
    } catch (error) {
        console.error('Error creando zona desde posición (modal):', error);
        showMessage(`No se pudo crear la zona: ${error.message}`, 'danger');
    }
}

// Manejar submit del modal de zona del recorrido (polilínea)
async function handleZonaRecorridoSubmit(event) {
    event.preventDefault();

    const nombre = document.getElementById('zonaRecorridoNombre').value;
    const descripcion = document.getElementById('zonaRecorridoDescripcion').value;

    if (!nombre || !nombre.trim()) {
        showMessage('Ingresá un nombre para la zona del recorrido.', 'warning');
        document.getElementById('zonaRecorridoNombre').focus();
        return;
    }

    await crearZonaPolilineaDesdeRecorrido(nombre, descripcion);

    const modalEl = document.getElementById('modalZonaRecorrido');
    if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
    }
}

// Crear zona tipo punto desde una posición específica del recorrido
async function crearZonaDesdePosicion(index) {
    if (!datosRecorrido || !datosRecorrido.length) {
        showMessage('Primero cargá un recorrido para crear una zona.', 'warning');
        return;
    }

    const punto = datosRecorrido[index];
    if (!punto || !punto.lat || !punto.lon) {
        showMessage('No hay coordenadas válidas para esta posición.', 'warning');
        return;
    }

    const lat = parseFloat(punto.lat);
    const lon = parseFloat(punto.lon);
    if (Number.isNaN(lat) || Number.isNaN(lon)) {
        showMessage('Las coordenadas de la posición no son válidas.', 'warning');
        return;
    }

    const movilSelect = document.getElementById('movil-select');
    const movilTexto = movilSelect && movilSelect.value
        ? movilSelect.options[movilSelect.selectedIndex].textContent
        : 'Recorrido';

    const fecha = new Date(punto.fec_gps || punto.timestamp);
    const fechaTexto = isNaN(fecha.getTime()) ? '' : fecha.toLocaleString();

    const nombreSugerido = `Zona posición ${index + 1} - ${movilTexto}`;
    const descripcionSugerida = `Generada desde posición ${index + 1} del recorrido${fechaTexto ? ` (${fechaTexto})` : ''}.`;

    // Rellenar y mostrar el modal
    const modalEl = document.getElementById('modalZonaDesdePosicion');
    const nombreInput = document.getElementById('zonaPosicionNombre');
    const descripcionInput = document.getElementById('zonaPosicionDescripcion');
    const latInput = document.getElementById('zonaPosicionLat');
    const lonInput = document.getElementById('zonaPosicionLon');
    const tipoPuntoRadio = document.getElementById('zonaPosicionTipoPunto');
    const tipoCirculoRadio = document.getElementById('zonaPosicionTipoCirculo');
    const radioGroup = document.getElementById('zonaPosicionRadioGroup');
    const radioInput = document.getElementById('zonaPosicionRadio');

    if (!modalEl || !nombreInput || !descripcionInput || !latInput || !lonInput || !tipoPuntoRadio || !tipoCirculoRadio || !radioGroup || !radioInput) {
        console.error('No se encontraron elementos del modal de zona desde posición.');
        return;
    }

    latInput.value = lat;
    lonInput.value = lon;
    nombreInput.value = nombreSugerido;
    descripcionInput.value = descripcionSugerida;
    tipoPuntoRadio.checked = true;
    tipoCirculoRadio.checked = false;
    radioGroup.style.display = 'none';
    radioInput.value = 100;

    const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
    modal.show();
}

// Abrir modal para crear zona polilínea del recorrido
function abrirModalZonaRecorrido() {
    if (!datosRecorrido || !datosRecorrido.length) {
        showMessage('Primero cargá un recorrido para crear la zona del recorrido.', 'warning');
        return;
    }

    const movilSelect = document.getElementById('movil-select');
    const movilTexto = movilSelect && movilSelect.value
        ? movilSelect.options[movilSelect.selectedIndex].textContent
        : 'Recorrido';

    const fechaDesdeInput = document.getElementById('fecha-desde');
    const fechaHastaInput = document.getElementById('fecha-hasta');
    const fechaDesde = fechaDesdeInput && fechaDesdeInput.value ? fechaDesdeInput.value : '';
    const fechaHasta = fechaHastaInput && fechaHastaInput.value ? fechaHastaInput.value : '';

    const nombreSugerido = `Zona recorrido - ${movilTexto}`;
    const rangoTexto = fechaDesde && fechaHasta ? ` (${fechaDesde} a ${fechaHasta})` : '';
    const descripcionSugerida = `Zona de tipo polilínea generada a partir del recorrido de ${movilTexto}${rangoTexto}.`;

    const nombreInput = document.getElementById('zonaRecorridoNombre');
    const descripcionInput = document.getElementById('zonaRecorridoDescripcion');
    const modalEl = document.getElementById('modalZonaRecorrido');

    if (!nombreInput || !descripcionInput || !modalEl) {
        console.error('No se encontraron elementos del modal de zona de recorrido.');
        return;
    }

    nombreInput.value = nombreSugerido;
    descripcionInput.value = descripcionSugerida;

    const modal = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
    modal.show();
}

// Crear zona tipo polilínea a partir del recorrido completo
async function crearZonaPolilineaDesdeRecorrido(nombreCustom, descripcionCustom) {
    // Necesitamos usar TODAS las posiciones del recorrido, no solo la página actual
    if (!paginationInfo || !paginationInfo.baseUrl || !paginationInfo.total) {
        if (!datosRecorrido || !datosRecorrido.length) {
            showMessage('Primero cargá un recorrido para crear la zona del recorrido.', 'warning');
            return;
        }
    }

    showLoading(true);

    let coordinates = [];
    try {
        if (paginationInfo && paginationInfo.baseUrl && paginationInfo.total) {
            const total = paginationInfo.total;
            const pageSize = paginationInfo.pageSize || PAGE_SIZE_DEFAULT;
            const totalPages = Math.ceil(total / pageSize);

            for (let page = 1; page <= totalPages; page++) {
                const [basePath, queryString] = paginationInfo.baseUrl.split('?');
                const params = new URLSearchParams(queryString || '');
                params.set('page', page);
                const url = `${basePath}?${params.toString()}`;

                const headers = (typeof auth !== 'undefined' && typeof auth.getHeaders === 'function')
                    ? auth.getHeaders()
                    : { 'Content-Type': 'application/json' };

                const resp = await fetch(url, { headers });
                if (!resp.ok) throw new Error(`Error cargando página ${page} del recorrido`);
                const data = await resp.json();
                const resultados = data.results || data;

                resultados.forEach(p => {
                    const lat = parseFloat(p.lat);
                    const lon = parseFloat(p.lon);
                    if (!Number.isNaN(lat) && !Number.isNaN(lon)) {
                        coordinates.push([lon, lat]);
                    }
                });
            }
        } else {
            // Sin paginación: usar los datos actuales
            if (!datosRecorrido || !datosRecorrido.length) {
                showMessage('Primero cargá un recorrido para crear la zona del recorrido.', 'warning');
                showLoading(false);
                return;
            }
            coordinates = datosRecorrido
                .map(p => {
                    const lat = parseFloat(p.lat);
                    const lon = parseFloat(p.lon);
                    if (Number.isNaN(lat) || Number.isNaN(lon)) return null;
                    return [lon, lat];
                })
                .filter(Boolean);
        }
    } catch (error) {
        console.error('Error obteniendo todas las posiciones del recorrido:', error);
        showMessage('No se pudieron obtener todas las posiciones del recorrido para crear la zona.', 'danger');
        showLoading(false);
        return;
    }

    if (coordinates.length < 2) {
        showMessage('No hay suficientes puntos válidos para crear una polilínea.', 'warning');
        showLoading(false);
        return;
    }

    const movilSelect = document.getElementById('movil-select');
    const movilTexto = movilSelect && movilSelect.value
        ? movilSelect.options[movilSelect.selectedIndex].textContent
        : 'Recorrido';

    const fechaDesdeInput = document.getElementById('fecha-desde');
    const fechaHastaInput = document.getElementById('fecha-hasta');
    const fechaDesde = fechaDesdeInput && fechaDesdeInput.value ? fechaDesdeInput.value : '';
    const fechaHasta = fechaHastaInput && fechaHastaInput.value ? fechaHastaInput.value : '';

    const nombreDefault = `Zona recorrido - ${movilTexto}`;
    const rangoTexto = fechaDesde && fechaHasta ? ` (${fechaDesde} a ${fechaHasta})` : '';
    const descripcionDefault = `Zona de tipo polilínea generada a partir del recorrido de ${movilTexto}${rangoTexto}.`;

    const nombre = nombreCustom && nombreCustom.trim() ? nombreCustom.trim() : nombreDefault;
    const descripcion = descripcionCustom && descripcionCustom.trim() ? descripcionCustom.trim() : descripcionDefault;

    const payload = {
        nombre,
        descripcion,
        tipo: 'polilinea',
        color: '#ff6600',
        opacidad: 0.6,
        visible: true,
        geom_geojson_input: {
            type: 'LineString',
            coordinates
        }
    };

    try {
        const headers = buildZonaHeaders();
        const response = await fetch(ZONAS_API_URL, {
            method: 'POST',
            headers,
            body: JSON.stringify(payload),
            credentials: 'same-origin'
        });

        if (!response.ok) {
            let errorMsg = `Error HTTP: ${response.status}`;
            try {
                const errorData = await response.json();
                errorMsg = errorData.error || errorData.detail || errorMsg;
                console.error('Error al crear zona polilínea:', errorData);
            } catch (e) {
                console.error('Error al parsear respuesta de zona polilínea:', e);
            }
            throw new Error(errorMsg);
        }

        showMessage('Zona del recorrido (polilínea) creada correctamente.', 'success');
    } catch (error) {
        console.error('Error creando zona del recorrido:', error);
        showMessage(`No se pudo crear la zona del recorrido: ${error.message}`, 'danger');
    } finally {
        showLoading(false);
    }
}

// Cambiar vista entre listado y mapa
function cambiarVista(mode) {
    const listView = document.getElementById('recorridos-list-view');
    const mapView = document.getElementById('recorridos-map-view');
    
    if (mode === 'list') {
        if (listView) listView.style.display = 'block';
        if (mapView) mapView.style.display = 'none';
    } else {
        if (listView) listView.style.display = 'none';
        if (mapView) mapView.style.display = 'block';
        
        // Asegurar que el mapa esté inicializado
        if (!mapInitialized) {
            initializeMap();
        }
        
        // Cuando se cambia a la vista de mapa, invalidar el tamaño para que los controles se muestren correctamente
        if (map) {
            // Esperar a que el elemento sea visible antes de invalidar
            setTimeout(() => {
                if (map) {
                    map.invalidateSize();
                    // Usar la función updateControls del mapa normalizado si está disponible
                    if (window.mapResultRecorridos && window.mapResultRecorridos.updateControls) {
                        window.mapResultRecorridos.updateControls();
                    }
                }
            }, 300);
        }
    }
    
    currentViewMode = mode;
    
    // Si hay datos cargados, recargar con la vista correcta
    if (datosRecorrido.length > 0) {
        if (mode === 'map') {
            // Para vista de mapa, SIEMPRE recargar datos para obtener todos los registros
            console.log('Cambiando a vista de mapa - recargando datos completos');
            buscarRecorrido();
        } else {
            // Para vista de lista, recargar datos con paginación
            buscarRecorrido();
        }
    } else {
        // Si no hay datos, limpiar contadores
        const posicionesCountMapa = document.getElementById('posiciones-count-mapa');
        if (posicionesCountMapa) {
            posicionesCountMapa.textContent = '0 posiciones';
        }
    }
}

// Renderizar listado de posiciones
function renderizarListado() {
    const tbody = document.getElementById('posiciones-table-body');
    const totalPosiciones = document.getElementById('total-posiciones');
    const posicionesCount = document.getElementById('posiciones-count');
    if (highlightedTimelineRow) {
        highlightedTimelineRow.classList.remove('timeline-row-highlight');
        highlightedTimelineRow = null;
    }
    
    if (datosRecorrido.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center text-muted py-4">
                    <i class="bi bi-search me-2"></i>
                    Seleccione un móvil y rango de fechas para ver las posiciones
                </td>
            </tr>
        `;
        totalPosiciones.textContent = '0';
        posicionesCount.textContent = '0 posiciones';
        timelineMeta.total = 0;
        timelineMeta.currentPageStart = 1;
        timelineMeta.currentPageEnd = 1;
        timelineMeta.selectedIndex = 1;
        timelineMeta.labels = { start: null, middle: null, end: null };
        highlightedTimelineRow = null;
        actualizarControlesTimeline();
        return;
    }
    
    tbody.innerHTML = '';
    
            // Calcular el número de inicio basado en la página actual
            let numeroInicio = 1;
            
            if (paginationInfo) {
                // Usar información real de paginación
                const paginaActual = paginationInfo.currentPage || 1;
                const registrosPorPagina = paginationInfo.pageSize || PAGE_SIZE_DEFAULT;
                numeroInicio = (paginaActual - 1) * registrosPorPagina + 1;
                
                console.log(`Página ${paginaActual} de ${paginationInfo.totalPages}: registros ${numeroInicio} a ${numeroInicio + datosRecorrido.length - 1} de ${paginationInfo.total} total`);
            } else {
                // Si no hay paginación, empezar desde 1
                numeroInicio = 1;
                console.log('Sin paginación: registros 1 a', datosRecorrido.length);
            }
            
            datosRecorrido.forEach((posicion, index) => {
                const fecha = new Date(posicion.fec_gps || posicion.timestamp);
                const lat = parseFloat(posicion.lat) || 0;
                const lon = parseFloat(posicion.lon) || 0;
                const coordenadas = `${lat.toFixed(6)}, ${lon.toFixed(6)}`;
                const velocidad = parseInt(posicion.velocidad) || 0;
                const rumbo = parseInt(posicion.rumbo) || 0;
                const estado = posicion.ign_on ? 'Encendido' : 'Apagado';
                const satelites = parseInt(posicion.sats) || 0;
                
                const row = document.createElement('tr');
                const posicionAbsoluta = numeroInicio + index;
                row.dataset.positionIndex = posicionAbsoluta;
                row.innerHTML = `
                    <td>${numeroInicio + index}</td>
            <td>${fecha.toLocaleString()}</td>
            <td>
                <small class="text-muted">${coordenadas}</small>
                <br>
                <button class="btn btn-sm btn-outline-primary" onclick="copiarCoordenadas('${coordenadas}')">
                    <i class="bi bi-clipboard"></i>
                </button>
            </td>
            <td>
                <span class="direccion-texto">${posicion.direccion || 'Sin geocodificar'}</span>
                <br>
                <button class="btn btn-sm btn-outline-info" onclick="geocodificarPosicion(${index})">
                    <i class="bi bi-geo-alt"></i>
                </button>
            </td>
            <td>
                <span class="badge ${getBadgeClassBySpeed(velocidad)}">
                    ${velocidad} km/h
                </span>
            </td>
            <td>
                <span class="rumbo-indicator" style="transform: rotate(${rumbo}deg);">→</span>
                ${rumbo}°
            </td>
            <td>
                <span class="badge ${estado === 'Encendido' ? 'bg-success' : 'bg-secondary'}">
                    ${estado}
                </span>
            </td>
            <td>
                <span class="badge ${getBadgeClassBySatellites(satelites)}">
                    ${satelites}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="verEnMapa(${index})">
                    <i class="bi bi-map"></i>
                </button>
                <button class="btn btn-sm btn-outline-secondary" onclick="verDetalles(${index})">
                    <i class="bi bi-info-circle"></i>
                </button>
                <button class="btn btn-sm btn-outline-success" onclick="crearZonaDesdePosicion(${index})" title="Crear zona desde esta posición">
                    <i class="bi bi-bullseye"></i>
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
    
    // Mostrar el total real de registros, no solo los de la página actual
    const totalReal = paginationInfo ? paginationInfo.total : datosRecorrido.length;
    totalPosiciones.textContent = `${totalReal}`;
    posicionesCount.textContent = `${totalReal} posiciones`;

    timelineMeta.total = totalReal;
    timelineMeta.currentPageStart = numeroInicio;
    timelineMeta.currentPageEnd = numeroInicio + datosRecorrido.length - 1;
    timelineMeta.selectedIndex = Math.min(Math.max(timelineMeta.selectedIndex || numeroInicio, 1), totalReal);

    actualizarControlesTimeline();
    resaltarFilaTimeline(timelineMeta.selectedIndex);
}

// Obtener clase de badge según velocidad
function getBadgeClassBySpeed(velocidad) {
    if (velocidad <= 5) return 'bg-danger';
    if (velocidad <= 15) return 'bg-warning';
    if (velocidad <= 30) return 'bg-info';
    if (velocidad <= 50) return 'bg-primary';
    if (velocidad <= 80) return 'bg-success';
    return 'bg-dark';
}

// Obtener clase de badge según satélites
function getBadgeClassBySatellites(satelites) {
    if (satelites >= 8) return 'bg-success';
    if (satelites >= 6) return 'bg-info';
    if (satelites >= 4) return 'bg-warning';
    return 'bg-danger';
}

function actualizarControlesTimeline() {
    const range = document.getElementById('timeline-range');
    const startLabel = document.getElementById('timeline-start-label');
    const middleLabel = document.getElementById('timeline-middle-label');
    const endLabel = document.getElementById('timeline-end-label');

    if (!range || !startLabel || !middleLabel || !endLabel) {
        return;
    }

    if (!timelineMeta.total || timelineMeta.total <= 0) {
        range.disabled = true;
        range.value = 0;
        startLabel.textContent = 'Inicio';
        middleLabel.textContent = 'Mitad';
        endLabel.textContent = 'Fin';
        return;
    }

    const valorSeleccionado = Math.min(Math.max(timelineMeta.selectedIndex || 1, 1), timelineMeta.total);
    range.disabled = timelineMeta.total <= 1;
    range.min = 1;
    range.max = timelineMeta.total;
    range.value = valorSeleccionado;

    startLabel.textContent = timelineMeta.labels.start || '--';
    middleLabel.textContent = timelineMeta.labels.middle || '--';
    endLabel.textContent = timelineMeta.labels.end || '--';
}

function formatearEtiquetaTimeline(posicion) {
    if (!posicion) return '--';
    const fecha = new Date(posicion.fec_gps || posicion.timestamp);
    return fecha.toLocaleString('es-AR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function actualizarTimelinePreview(valor) {
    // Reservado para posibles futuros tooltips
}

function manejarTimelineChange(valor) {
    valor = parseInt(valor, 10);
    if (Number.isNaN(valor)) return;
    timelineMeta.selectedIndex = valor;
    resaltarFilaTimeline(valor);
}

function obtenerPosicionActualPorIndice(indiceAbsoluto) {
    if (!timelineMeta.currentPageStart) return null;
    const localIndex = indiceAbsoluto - timelineMeta.currentPageStart;
    if (localIndex < 0 || localIndex >= datosRecorrido.length) return null;
    return datosRecorrido[localIndex];
}

async function resaltarFilaTimeline(indiceAbsoluto) {
    const fila = document.querySelector(`[data-position-index="${indiceAbsoluto}"]`);
    if (!fila) {
        await cargarPaginaPorIndice(indiceAbsoluto);
        const nuevaFila = document.querySelector(`[data-position-index="${indiceAbsoluto}"]`);
        if (!nuevaFila) return;
        return resaltarFilaTimeline(indiceAbsoluto);
    }
    if (highlightedTimelineRow) {
        highlightedTimelineRow.classList.remove('timeline-row-highlight');
    }
    fila.classList.add('timeline-row-highlight');
    highlightedTimelineRow = fila;
}

async function cargarPaginaPorIndice(indiceAbsoluto) {
    if (!paginationInfo) return;
    const registrosPorPagina = paginationInfo.pageSize || PAGE_SIZE_DEFAULT;
    const paginaDestino = Math.ceil(indiceAbsoluto / registrosPorPagina);
    if (paginaDestino === paginationInfo.currentPage) return;

    const urlBase = paginationInfo.baseUrl;
    if (!urlBase) return;

    const [basePath, queryString] = urlBase.split('?');
    const params = new URLSearchParams(queryString || '');
    params.set('page', paginaDestino);
    const nuevaUrl = `${basePath}?${params.toString()}`;

    showLoading(true);
    try {
        const response = await fetch(nuevaUrl, { headers: auth.getHeaders() });
        if (!response.ok) throw new Error('Error cargando página');
        const data = await response.json();
        datosRecorrido = data.results || [];
        paginationInfo.currentPage = paginaDestino;
        renderizarListado();
    } catch (error) {
        console.error('Error al cargar página desde timeline:', error);
    } finally {
        showLoading(false);
    }
}

async function prepararEtiquetasTimeline(datosPaginaActual) {
    if (!paginationInfo) {
        timelineMeta.labels = { start: null, middle: null, end: null };
        actualizarEtiquetasTimeline();
        return;
    }

    if (!timelineMeta.labels) {
        timelineMeta.labels = { start: null, middle: null, end: null };
    }

    const total = paginationInfo.total || datosPaginaActual.length || 0;
    timelineMeta.total = total;

    if (total === 0) {
        actualizarEtiquetasTimeline();
        return;
    }

    const pageSize = paginationInfo.pageSize || datosPaginaActual.length || 1;
    const paginaActual = paginationInfo.currentPage || 1;
    const inicioPagina = (paginaActual - 1) * pageSize + 1;
    const finPagina = inicioPagina + datosPaginaActual.length - 1;

    if (!timelineMeta.labels.start && inicioPagina === 1 && datosPaginaActual.length) {
        timelineMeta.labels.start = formatearEtiquetaTimeline(datosPaginaActual[0]);
    }

    if (!timelineMeta.labels.end && finPagina === total && datosPaginaActual.length) {
        timelineMeta.labels.end = formatearEtiquetaTimeline(datosPaginaActual[datosPaginaActual.length - 1]);
    }

    if (!timelineMeta.labels.start) {
        const registroInicial = await obtenerRegistroGlobalPorIndice(1);
        if (registroInicial) {
            timelineMeta.labels.start = formatearEtiquetaTimeline(registroInicial);
        }
    }

    if (!timelineMeta.labels.end) {
        const registroFinal = await obtenerRegistroGlobalPorIndice(total);
        if (registroFinal) {
            timelineMeta.labels.end = formatearEtiquetaTimeline(registroFinal);
        }
    }

    if (!timelineMeta.labels.middle && total > 1) {
        const indiceMedio = Math.ceil(total / 2);
        const registroMedio = await obtenerRegistroGlobalPorIndice(indiceMedio);
        if (registroMedio) {
            timelineMeta.labels.middle = formatearEtiquetaTimeline(registroMedio);
        }
    }

    actualizarEtiquetasTimeline();
}

function actualizarEtiquetasTimeline() {
    const startLabel = document.getElementById('timeline-start-label');
    const middleLabel = document.getElementById('timeline-middle-label');
    const endLabel = document.getElementById('timeline-end-label');

    if (!startLabel || !middleLabel || !endLabel) return;

    startLabel.textContent = timelineMeta.labels?.start || '--';
    middleLabel.textContent = timelineMeta.labels?.middle || '--';
    endLabel.textContent = timelineMeta.labels?.end || '--';
}

async function obtenerRegistroGlobalPorIndice(indice) {
    if (!paginationInfo || !paginationInfo.baseUrl) return null;
    const total = paginationInfo.total || 0;
    if (indice < 1 || indice > total) return null;

    if (timelineMeta.currentPageStart &&
        indice >= timelineMeta.currentPageStart &&
        indice <= timelineMeta.currentPageEnd) {
        return obtenerPosicionActualPorIndice(indice);
    }

    const pageSize = paginationInfo.pageSize || PAGE_SIZE_DEFAULT;
    const pagina = Math.ceil(indice / pageSize);
    const localIndex = (indice - 1) % pageSize;

    const [basePath, queryString] = paginationInfo.baseUrl.split('?');
    const params = new URLSearchParams(queryString || '');
    params.set('page', pagina);
    const url = `${basePath}?${params.toString()}`;

    try {
        const headers = (typeof auth !== 'undefined' && typeof auth.getHeaders === 'function')
            ? auth.getHeaders()
            : { 'Content-Type': 'application/json' };
        const response = await fetch(url, { headers });
        if (!response.ok) return null;
        const data = await response.json();
        const resultados = data.results || data;
        return resultados[localIndex] || null;
    } catch (error) {
        console.error('Error obteniendo registro global:', error);
        return null;
    }
}

function construirBaseUrl(params) {
    const baseParams = new URLSearchParams(params);
    baseParams.delete('page');
    const query = baseParams.toString();
    return query ? `/api/recorridos/?${query}` : '/api/recorridos/';
}
// Copiar coordenadas al portapapeles
function copiarCoordenadas(coordenadas) {
    navigator.clipboard.writeText(coordenadas).then(() => {
        showMessage('Coordenadas copiadas al portapapeles', 'success');
    });
}

// Geocodificar posición individual
async function geocodificarPosicion(index) {
    const posicion = datosRecorrido[index];
    if (!posicion) return;
    
    // Verificar si ya tiene dirección geocodificada
    const tieneDireccion = posicion.direccion && 
                          posicion.direccion.trim() !== '' && 
                          posicion.direccion !== 'Sin geocodificar' &&
                          !posicion.direccion.startsWith('Coordenadas:');
    
    if (tieneDireccion) {
        showMessage('Esta posición ya está geocodificada', 'info');
        return;
    }
    
    try {
        showMessage('Geocodificando posición...', 'info');
        
        const response = await fetch('/api/recorridos/geocodificar_posicion/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...auth.getHeaders()
            },
            body: JSON.stringify({
                lat: parseFloat(posicion.lat),
                lon: parseFloat(posicion.lon),
                posicion_id: posicion.id
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            posicion.direccion = data.direccion;
            
            // Actualizar la fila en el listado
            const row = document.querySelector(`#posiciones-table-body tr:nth-child(${index + 1})`);
            if (row) {
                const direccionCell = row.querySelector('.direccion-texto');
                if (direccionCell) {
                    direccionCell.textContent = data.direccion;
                }
            }
            
            showMessage('Posición geocodificada correctamente', 'success');
        } else {
            throw new Error('Error en la geocodificación');
        }
    } catch (error) {
        console.error('Error geocodificando posición:', error);
        showMessage('Error geocodificando la posición', 'error');
    }
}

// Variables para control de geocodificación masiva
let geocodificacionEnProgreso = false;
let geocodificacionCancelada = false;

// Geocodificar todas las posiciones
async function geocodificarPosiciones() {
    if (datosRecorrido.length === 0) return;
    
    // Prevenir múltiples ejecuciones
    if (geocodificacionEnProgreso) {
        showMessage('⚠️ Ya hay una geocodificación en progreso. Espere a que termine.', 'warning');
        return;
    }
    
    // Obtener el total real de registros
    const totalRegistros = paginationInfo ? paginationInfo.total : datosRecorrido.length;
    
    // Mostrar popup personalizado de confirmación
    const confirmacion = await mostrarConfirmacionGeocodificacion(totalRegistros);
    if (!confirmacion) {
        return;
    }
    
    try {
        // Marcar como en progreso
        geocodificacionEnProgreso = true;
        geocodificacionCancelada = false;
        
        // Mostrar indicador de progreso más contundente
        showMessage(`🚀 Iniciando geocodificación masiva de ${totalRegistros} posiciones...`, 'info');
        
        // Deshabilitar botones durante el proceso y agregar botón de cancelar
        const btnGeocodificar = document.getElementById('btn-geocodificar');
        const btnExportExcel = document.getElementById('btn-export-excel');
        if (btnGeocodificar) {
            btnGeocodificar.disabled = true;
            btnGeocodificar.innerHTML = '<i class="bi bi-hourglass-split"></i> Procesando...';
        }
        if (btnExportExcel) {
            btnExportExcel.disabled = true;
        }
        
        // Agregar botón de cancelar
        agregarBotonCancelar();
        
        // Obtener TODAS las posiciones del recorrido, no solo las de la página actual
        let todasLasPosiciones = [];
        
        if (paginationInfo && paginationInfo.total > datosRecorrido.length) {
            // Si hay paginación, obtener todas las posiciones
            console.log(`Obteniendo todas las ${paginationInfo.total} posiciones para geocodificación...`);
            
            // Obtener todas las páginas
            for (let pagina = 1; pagina <= paginationInfo.totalPages; pagina++) {
                // Verificar si fue cancelado
                if (geocodificacionCancelada) {
                    console.log('Geocodificación cancelada por el usuario');
                    throw new Error('Geocodificación cancelada por el usuario');
                }
                
                const url = `/api/recorridos/?movil_id=${document.getElementById('movil-select').value}&fecha_desde=${document.getElementById('fecha-desde').value}&fecha_hasta=${document.getElementById('fecha-hasta').value}&page=${pagina}`;
                
                const response = await fetch(url, {
                    headers: auth.getHeaders()
                });
                
                if (response.ok) {
                    const data = await response.json();
                    todasLasPosiciones = todasLasPosiciones.concat(data.results || data);
                    console.log(`Página ${pagina}: ${data.results ? data.results.length : data.length} posiciones`);
                }
            }
        } else {
            // Si no hay paginación, usar los datos actuales
            todasLasPosiciones = datosRecorrido;
        }
        
        // Filtrar solo las posiciones que NO tienen dirección geocodificada
        const posicionesSinGeocodificar = todasLasPosiciones.filter(posicion => {
            const tieneDireccion = posicion.direccion && 
                                 posicion.direccion.trim() !== '' && 
                                 posicion.direccion !== 'Sin geocodificar' &&
                                 !posicion.direccion.startsWith('Coordenadas:');
            return !tieneDireccion;
        });
        
        const posicionesYaGeocodificadas = todasLasPosiciones.length - posicionesSinGeocodificar.length;
        
        console.log(`📊 Análisis de posiciones:`);
        console.log(`   Total: ${todasLasPosiciones.length}`);
        console.log(`   Ya geocodificadas: ${posicionesYaGeocodificadas}`);
        console.log(`   Sin geocodificar: ${posicionesSinGeocodificar.length}`);
        
        // Si todas ya están geocodificadas, no hacer nada
        if (posicionesSinGeocodificar.length === 0) {
            showMessage('✅ Todas las posiciones ya están geocodificadas. No hay nada que procesar.', 'success');
            return;
        }
        
        // Actualizar el mensaje de progreso con información más precisa
        showMessage(`🚀 Procesando ${posicionesSinGeocodificar.length} posiciones sin geocodificar (${posicionesYaGeocodificadas} ya estaban geocodificadas)...`, 'info');
        
        console.log(`Total de posiciones a geocodificar: ${posicionesSinGeocodificar.length}`);
        
        const response = await fetch('/api/recorridos/geocodificar_recorrido/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...auth.getHeaders()
            },
            body: JSON.stringify({
                posiciones: posicionesSinGeocodificar.map(p => ({ id: p.id, lat: p.lat, lon: p.lon }))
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            console.log('Respuesta de geocodificación masiva:', data);
            
            // Mostrar resultado detallado
            if (data.geocodificadas > 0) {
                showMessage(`✅ Geocodificación completada: ${data.geocodificadas} de ${data.total} posiciones procesadas exitosamente`, 'success');
                
                // Recargar los datos para mostrar las direcciones actualizadas
                setTimeout(() => {
                    buscarRecorrido();
                }, 1000);
            } else {
                showMessage('⚠️ No se pudieron geocodificar las posiciones. Verifique la conexión a internet.', 'warning');
            }
        } else {
            const errorData = await response.json();
            console.error('Error del servidor:', errorData);
            throw new Error(`Error del servidor: ${errorData.error || 'Error desconocido'}`);
        }
    } catch (error) {
        console.error('Error geocodificando posiciones:', error);
        if (geocodificacionCancelada) {
            showMessage('⏹️ Geocodificación cancelada por el usuario', 'warning');
        } else {
            showMessage(`❌ Error geocodificando las posiciones: ${error.message}`, 'error');
        }
    } finally {
        // Restablecer estado
        geocodificacionEnProgreso = false;
        geocodificacionCancelada = false;
        
        // Restablecer botones
        console.log('Restableciendo botones después de geocodificación...');
        const btnGeocodificar = document.getElementById('btn-geocodificar');
        const btnExportExcel = document.getElementById('btn-export-excel');
        
        if (btnGeocodificar) {
            btnGeocodificar.disabled = false;
            btnGeocodificar.innerHTML = '<i class="bi bi-geo-alt"></i> Geocodificar';
            console.log('✅ Botón geocodificar restablecido');
        } else {
            console.error('❌ No se encontró el botón geocodificar');
        }
        
        if (btnExportExcel) {
            btnExportExcel.disabled = false;
            console.log('✅ Botón exportar restablecido');
        } else {
            console.error('❌ No se encontró el botón exportar');
        }
        
        // Remover botón de cancelar
        removerBotonCancelar();
    }
}

// Exportar a Excel
async function exportarExcel() {
    const movilSelect = document.getElementById('movil-select');
    const fechaDesde = document.getElementById('fecha-desde');
    const fechaHasta = document.getElementById('fecha-hasta');
    const btnExportExcel = document.getElementById('btn-export-excel');
    const btnGeocodificar = document.getElementById('btn-geocodificar');

    if (!movilSelect?.value) {
        showMessage('Seleccioná un móvil antes de exportar.', 'warning');
        return;
    }
    if (!fechaDesde?.value || !fechaHasta?.value) {
        showMessage('Indicá el rango de fechas para exportar.', 'warning');
        return;
    }
    
    try {
        showMessage('Generando archivo Excel...', 'info');
        if (btnExportExcel) {
            btnExportExcel.disabled = true;
            btnExportExcel.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generando...';
        }
        if (btnGeocodificar) btnGeocodificar.disabled = true;
        
        const queryParams = new URLSearchParams({
            movil_id: movilSelect.value,
            fecha_desde: fechaDesde.value,
            fecha_hasta: fechaHasta.value,
        });
        const response = await fetch(`/api/recorridos/exportar_excel/?${queryParams.toString()}`, {
            method: 'GET',
                    headers: auth.getHeaders()
                });
                
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || 'Error del servidor');
        }
        

        const contentType = response.headers.get('content-type') || '';
        if (!contentType.includes('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')) {
            const errorText = await response.text();
            throw new Error(errorText || 'El servidor no devolvió un archivo Excel válido');
        }

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
        const movilText = movilSelect.options[movilSelect.selectedIndex].textContent || 'movil';
        a.download = `recorrido_${movilText.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.xlsx`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showMessage('Archivo Excel descargado exitosamente', 'success');
    } catch (error) {
        console.error('Error exportando a Excel:', error);
        showMessage(`Error generando archivo Excel: ${error.message}`, 'error');
    } finally {
        if (btnExportExcel) {
            btnExportExcel.disabled = false;
            btnExportExcel.innerHTML = '<i class="bi bi-file-earmark-excel"></i> Exportar Excel';
        }
        if (btnGeocodificar) btnGeocodificar.disabled = false;
    }
}

// Ver posición en el mapa
function verEnMapa(index) {
    // Cambiar a vista de mapa
    document.getElementById('view-map').checked = true;
    currentViewMode = 'map';
    localStorage.setItem('recorridos-view-mode', 'map');
    cambiarVista('map');
    
    // Centrar en la posición
    const posicion = datosRecorrido[index];
    if (posicion && map) {
        map.setView([posicion.lat, posicion.lon], 15);
        
        // Destacar la posición
        posicionActualLayer.clearLayers();
        const marker = L.marker([posicion.lat, posicion.lon], {
            icon: L.divIcon({
                className: 'highlighted-position-marker',
                html: '<div class="highlighted-position"></div>',
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            })
        });
        posicionActualLayer.addLayer(marker);
    }
}

// Ver detalles de posición
function verDetalles(index) {
    const posicion = datosRecorrido[index];
    if (!posicion) return;
    
    const fecha = new Date(posicion.timestamp);
    
    const detalles = `
        <div class="position-details">
            <h6>Detalles de la Posición</h6>
            <table class="table table-sm">
                <tr><td><strong>Fecha/Hora:</strong></td><td>${fecha.toLocaleString()}</td></tr>
                <tr><td><strong>Coordenadas:</strong></td><td>${posicion.lat}, ${posicion.lon}</td></tr>
                <tr><td><strong>Dirección:</strong></td><td>${posicion.direccion || 'Sin geocodificar'}</td></tr>
                <tr><td><strong>Velocidad:</strong></td><td>${posicion.velocidad} km/h</td></tr>
                <tr><td><strong>Rumbo:</strong></td><td>${posicion.rumbo}°</td></tr>
                <tr><td><strong>Altitud:</strong></td><td>${posicion.altitud} m</td></tr>
                <tr><td><strong>Satélites:</strong></td><td>${posicion.satelites}</td></tr>
                <tr><td><strong>Encendido:</strong></td><td>${posicion.ignicion ? 'Sí' : 'No'}</td></tr>
                <tr><td><strong>Calidad:</strong></td><td>${posicion.calidad}</td></tr>
            </table>
        </div>
    `;
    
    // Mostrar en modal o alert
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Detalles de Posición #${index + 1}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    ${detalles}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    modal.addEventListener('hidden.bs.modal', () => {
        document.body.removeChild(modal);
    });
}

// Logout
async function logout() {
    const confirmed = await notify.confirm({
        message: '¿Está seguro que desea cerrar sesión?',
        confirmText: 'Cerrar sesión'
    });
    if (!confirmed) return;
    auth.logout();
}

// Función para agregar botón de cancelar
function agregarBotonCancelar() {
    // Remover botón existente si existe
    removerBotonCancelar();
    
    // Crear botón de cancelar
    const btnCancelar = document.createElement('button');
    btnCancelar.id = 'btn-cancelar-geocodificacion';
    btnCancelar.className = 'btn btn-danger btn-sm ms-2';
    btnCancelar.innerHTML = '<i class="bi bi-x-circle"></i> Cancelar';
    btnCancelar.onclick = cancelarGeocodificacion;
    
    // Agregar al contenedor de botones
    const btnGeocodificar = document.getElementById('btn-geocodificar');
    if (btnGeocodificar && btnGeocodificar.parentNode) {
        btnGeocodificar.parentNode.appendChild(btnCancelar);
    }
}

// Función para remover botón de cancelar
function removerBotonCancelar() {
    const btnCancelar = document.getElementById('btn-cancelar-geocodificacion');
    if (btnCancelar) {
        btnCancelar.remove();
    }
}

// Función para cancelar geocodificación
async function cancelarGeocodificacion() {
    const confirmed = await notify.confirm({
        message: '¿Cancelar la geocodificación en progreso?',
        confirmText: 'Cancelar proceso'
    });
    if (!confirmed) return;
    geocodificacionCancelada = true;
    showMessage('⏹️ Cancelando geocodificación...', 'warning');
}

// Función para mostrar popup personalizado de confirmación
function mostrarConfirmacionGeocodificacion(totalRegistros) {
    return new Promise((resolve) => {
        // Crear el modal personalizado
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'modal-confirmacion-geocodificacion';
        modal.setAttribute('data-bs-backdrop', 'static');
        modal.setAttribute('data-bs-keyboard', 'false');
        
        const tiempoEstimado = Math.ceil(totalRegistros / 10);
        const esMuchosRegistros = totalRegistros > 100;
        
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header ${esMuchosRegistros ? 'bg-warning' : 'bg-primary'} text-white">
                        <h5 class="modal-title">
                            <i class="bi bi-geo-alt-fill me-2"></i>
                            Confirmar Geocodificación Masiva
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="text-center mb-4">
                            <i class="bi bi-geo-alt-fill text-primary" style="font-size: 3rem;"></i>
                        </div>
                        
                        <div class="alert ${esMuchosRegistros ? 'alert-warning' : 'alert-info'}">
                            <h6 class="alert-heading">
                                <i class="bi bi-info-circle me-2"></i>
                                Información del Proceso
                            </h6>
                            <p class="mb-2">
                                <strong>Posiciones a procesar:</strong> ${totalRegistros}
                            </p>
                            <p class="mb-2">
                                <strong>Tiempo estimado:</strong> ${tiempoEstimado} minutos
                            </p>
                            <p class="mb-0">
                                <strong>Proceso:</strong> El sistema verificará automáticamente cuáles posiciones ya están geocodificadas y solo procesará las que necesiten geocodificación.
                            </p>
                        </div>
                        
                        ${esMuchosRegistros ? `
                            <div class="alert alert-danger">
                                <h6 class="alert-heading">
                                    <i class="bi bi-exclamation-triangle me-2"></i>
                                    Advertencia Importante
                                </h6>
                                <ul class="mb-0">
                                    <li>Este proceso puede tomar <strong>${tiempoEstimado} minutos o más</strong></li>
                                    <li>Se procesarán las posiciones una por una para evitar sobrecargar el servicio</li>
                                    <li>Puede cancelar el proceso en cualquier momento</li>
                                    <li>Se optimizará automáticamente para no procesar posiciones ya geocodificadas</li>
                                </ul>
                            </div>
                        ` : ''}
                        
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="confirmar-proceso">
                            <label class="form-check-label" for="confirmar-proceso">
                                Entiendo que este proceso puede tomar tiempo y deseo continuar
                            </label>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="bi bi-x-circle me-1"></i>
                            Cancelar
                        </button>
                        <button type="button" class="btn btn-primary" id="btn-confirmar-geocodificacion">
                            <i class="bi bi-geo-alt me-1"></i>
                            Iniciar Geocodificación
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Agregar al DOM
        document.body.appendChild(modal);
        
        // Mostrar el modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Manejar eventos
        const btnConfirmar = modal.querySelector('#btn-confirmar-geocodificacion');
        const checkbox = modal.querySelector('#confirmar-proceso');
        
        // Habilitar/deshabilitar botón según checkbox
        checkbox.addEventListener('change', () => {
            btnConfirmar.disabled = !checkbox.checked;
        });
        
        // Inicialmente deshabilitado
        btnConfirmar.disabled = true;
        
        // Manejar confirmación
        btnConfirmar.addEventListener('click', () => {
            if (checkbox.checked) {
                bsModal.hide();
                resolve(true);
            }
        });
        
        // Manejar cancelación
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
            resolve(false);
        });
    });
}

// Función para actualizar el tiempo actual durante la reproducción
function actualizarTiempoActual() {
    const tiempoActual = document.getElementById('tiempo-actual');
    const progressBar = document.getElementById('progress-bar');
    
    if (!tiempoActual || !progressBar || datosRecorrido.length === 0) {
        console.log('🔍 actualizarTiempoActual: Elementos no encontrados o sin datos');
        return;
    }
    
    // Calcular el progreso basado en la posición actual
    const progreso = currentIndex / (datosRecorrido.length - 1);
    const porcentaje = Math.round(progreso * 100);
    
    console.log('🔍 actualizarTiempoActual:', {
        currentIndex,
        totalPosiciones: datosRecorrido.length,
        progreso,
        porcentaje
    });
    
    // Actualizar barra de progreso
    progressBar.style.width = `${porcentaje}%`;
    
    // Calcular tiempo transcurrido basado en la posición actual
    if (currentIndex < datosRecorrido.length) {
        const posicionActual = datosRecorrido[currentIndex];
        const primeraPosicion = datosRecorrido[0];
        
        if (posicionActual && primeraPosicion) {
            try {
                let inicio, actual;
                let fechaInicioStr, fechaActualStr;
                
                // Obtener fecha de inicio
                if (primeraPosicion.fec_gps) {
                    fechaInicioStr = primeraPosicion.fec_gps;
                } else if (primeraPosicion.timestamp) {
                    fechaInicioStr = primeraPosicion.timestamp;
                } else {
                    console.warn('🔍 actualizarTiempoActual: No se encontró fecha de inicio');
                    return;
                }
                
                // Obtener fecha actual
                if (posicionActual.fec_gps) {
                    fechaActualStr = posicionActual.fec_gps;
                } else if (posicionActual.timestamp) {
                    fechaActualStr = posicionActual.timestamp;
                } else {
                    console.warn('🔍 actualizarTiempoActual: No se encontró fecha actual');
                    return;
                }
                
                console.log('🔍 actualizarTiempoActual - Fechas:', {
                    fechaInicioStr,
                    fechaActualStr,
                    tipoInicio: typeof fechaInicioStr,
                    tipoActual: typeof fechaActualStr
                });
                
                // Crear objetos Date
                inicio = new Date(fechaInicioStr);
                actual = new Date(fechaActualStr);
                
                console.log('🔍 actualizarTiempoActual - Objetos Date:', {
                    inicio,
                    actual,
                    inicioValid: !isNaN(inicio.getTime()),
                    actualValid: !isNaN(actual.getTime())
                });
                
                if (!isNaN(inicio.getTime()) && !isNaN(actual.getTime())) {
                    const tiempoTranscurrido = actual - inicio;
                    const minutos = Math.floor(tiempoTranscurrido / 60000);
                    const segundos = Math.floor((tiempoTranscurrido % 60000) / 1000);
                    const tiempoFormateado = `${minutos.toString().padStart(2, '0')}:${segundos.toString().padStart(2, '0')}`;
                    
                    // Verificar que no haya NaN en el resultado
                    if (isNaN(minutos) || isNaN(segundos)) {
                        console.error('❌ NAN DETECTADO en tiempo actual:', {
                            tiempoTranscurrido,
                            minutos,
                            segundos,
                            tiempoFormateado
                        });
                        tiempoActual.textContent = 'Error';
                    } else {
                        tiempoActual.textContent = tiempoFormateado;
                        console.log('✅ Tiempo actual actualizado:', tiempoFormateado);
                    }
                } else {
                    console.error('❌ actualizarTiempoActual: Fechas inválidas');
                    tiempoActual.textContent = 'Error';
                }
            } catch (error) {
                console.error('❌ Error calculando tiempo actual:', error);
                tiempoActual.textContent = 'Error';
            }
        }
    }
}

// Función para actualizar controles de reproducción
function actualizarControlesReproduccion() {
    console.log('🔍 actualizarControlesReproduccion: INICIANDO');
    
    const tiempoActual = document.getElementById('tiempo-actual');
    const tiempoTotal = document.getElementById('tiempo-total');
    const progressBar = document.getElementById('progress-bar');
    
    console.log('🔍 actualizarControlesReproduccion: Elementos encontrados:', {
        tiempoActual: !!tiempoActual,
        tiempoTotal: !!tiempoTotal,
        progressBar: !!progressBar
    });
    
    // Inicializar con valores por defecto
    if (tiempoActual) tiempoActual.textContent = '00:00';
    if (tiempoTotal) tiempoTotal.textContent = '00:00';
    if (progressBar) progressBar.style.width = '0%';
    
    console.log('🔍 actualizarControlesReproduccion: Valores inicializados');
    
    if (datosRecorrido.length === 0) {
        console.log('No hay datos de recorrido para calcular duración');
        return;
    }
    
    // Calcular duración total del recorrido
    const primeraPosicion = datosRecorrido[0];
    const ultimaPosicion = datosRecorrido[datosRecorrido.length - 1];
    
    console.log('🔍 DEBUG - Datos de posiciones:', {
        totalPosiciones: datosRecorrido.length,
        primeraPosicion: {
            id: primeraPosicion?.id,
            fec_gps: primeraPosicion?.fec_gps,
            timestamp: primeraPosicion?.timestamp,
            tipo_fec_gps: typeof primeraPosicion?.fec_gps,
            tipo_timestamp: typeof primeraPosicion?.timestamp
        },
        ultimaPosicion: {
            id: ultimaPosicion?.id,
            fec_gps: ultimaPosicion?.fec_gps,
            timestamp: ultimaPosicion?.timestamp,
            tipo_fec_gps: typeof ultimaPosicion?.fec_gps,
            tipo_timestamp: typeof ultimaPosicion?.timestamp
        }
    });
    
    if (primeraPosicion && ultimaPosicion) {
        try {
            // Intentar obtener las fechas de diferentes campos posibles
            let inicio, fin;
            let fechaInicioStr, fechaFinStr;
            
            // Obtener string de fecha de inicio
            if (primeraPosicion.fec_gps) {
                fechaInicioStr = primeraPosicion.fec_gps;
            } else if (primeraPosicion.timestamp) {
                fechaInicioStr = primeraPosicion.timestamp;
            } else {
                console.error('❌ No se encontró campo de fecha en la primera posición');
                if (tiempoTotal) tiempoTotal.textContent = 'Error';
                return;
            }
            
            // Obtener string de fecha de fin
            if (ultimaPosicion.fec_gps) {
                fechaFinStr = ultimaPosicion.fec_gps;
            } else if (ultimaPosicion.timestamp) {
                fechaFinStr = ultimaPosicion.timestamp;
            } else {
                console.error('❌ No se encontró campo de fecha en la última posición');
                if (tiempoTotal) tiempoTotal.textContent = 'Error';
                return;
            }
            
            console.log('🔍 DEBUG - Strings de fecha:', {
                fechaInicioStr,
                fechaFinStr,
                tipoInicio: typeof fechaInicioStr,
                tipoFin: typeof fechaFinStr
            });
            
            // Crear objetos Date
            inicio = new Date(fechaInicioStr);
            fin = new Date(fechaFinStr);
            
            console.log('🔍 DEBUG - Objetos Date creados:', {
                inicio,
                fin,
                inicioTime: inicio.getTime(),
                finTime: fin.getTime(),
                inicioValid: !isNaN(inicio.getTime()),
                finValid: !isNaN(fin.getTime())
            });
            
            // Verificar que las fechas sean válidas
            if (isNaN(inicio.getTime()) || isNaN(fin.getTime())) {
                console.error('❌ Fechas inválidas:', {
                    inicioValid: !isNaN(inicio.getTime()),
                    finValid: !isNaN(fin.getTime()),
                    inicioString: fechaInicioStr,
                    finString: fechaFinStr
                });
                if (tiempoTotal) tiempoTotal.textContent = 'Error';
                return;
            }
            
            const duracionTotal = fin - inicio;
            console.log('🔍 DEBUG - Duración calculada:', {
                duracionTotal,
                duracionMinutos: Math.floor(duracionTotal / 60000),
                duracionSegundos: Math.floor(duracionTotal / 1000)
            });
            
            // Verificar que la duración sea válida
            if (duracionTotal > 0) {
                // Actualizar tiempo total
                if (tiempoTotal) {
                    const minutos = Math.floor(duracionTotal / 60000);
                    const segundos = Math.floor((duracionTotal % 60000) / 1000);
                    const tiempoFormateado = `${minutos.toString().padStart(2, '0')}:${segundos.toString().padStart(2, '0')}`;
                    
                    // Verificar que no haya NaN en el resultado
                    if (isNaN(minutos) || isNaN(segundos)) {
                        console.error('❌ NAN DETECTADO en tiempo total:', {
                            duracionTotal,
                            minutos,
                            segundos,
                            tiempoFormateado,
                            fechaInicioStr,
                            fechaFinStr,
                            inicio,
                            fin
                        });
                        tiempoTotal.textContent = 'Error';
                    } else {
                        console.log('🔍 actualizarControlesReproduccion: ANTES de actualizar tiempo total:', {
                            tiempoTotalElement: tiempoTotal,
                            tiempoFormateado,
                            minutos,
                            segundos
                        });
                        tiempoTotal.textContent = tiempoFormateado;
                        console.log('✅ Tiempo total actualizado:', tiempoFormateado);
                        console.log('🔍 actualizarControlesReproduccion: DESPUÉS de actualizar tiempo total:', {
                            tiempoTotalTextContent: tiempoTotal.textContent
                        });
                    }
                }
            } else {
                console.warn('⚠️ Duración total inválida o cero:', duracionTotal);
                if (tiempoTotal) tiempoTotal.textContent = '00:00';
            }
        } catch (error) {
            console.error('❌ Error calculando duración del recorrido:', error);
            if (tiempoTotal) tiempoTotal.textContent = 'Error';
        }
    } else {
        console.error('❌ No hay suficientes posiciones para calcular duración');
        if (tiempoTotal) tiempoTotal.textContent = 'Error';
    }
    
    console.log('🔍 actualizarControlesReproduccion: FINALIZANDO');
}

// Función para actualizar controles de paginación
function actualizarControlesPaginacion() {
    const paginationContainer = document.getElementById('pagination-container');
    if (!paginationContainer || !paginationInfo) return;
    
    let paginationHTML = '';
    
    // Botón Anterior
    if (paginationInfo.hasPrevious) {
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="cambiarPagina(${paginationInfo.currentPage - 1})">
                    <i class="bi bi-chevron-left"></i> Anterior
                </a>
            </li>
        `;
    } else {
        paginationHTML += `
            <li class="page-item disabled">
                <span class="page-link">
                    <i class="bi bi-chevron-left"></i> Anterior
                </span>
            </li>
        `;
    }
    
    // Números de página
    const startPage = Math.max(1, paginationInfo.currentPage - 2);
    const endPage = Math.min(paginationInfo.totalPages, paginationInfo.currentPage + 2);
    
    if (startPage > 1) {
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="cambiarPagina(1)">1</a></li>`;
        if (startPage > 2) {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        if (i === paginationInfo.currentPage) {
            paginationHTML += `
                <li class="page-item active">
                    <span class="page-link">${i}</span>
                </li>
            `;
        } else {
            paginationHTML += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="cambiarPagina(${i})">${i}</a>
                </li>
            `;
        }
    }
    
    if (endPage < paginationInfo.totalPages) {
        if (endPage < paginationInfo.totalPages - 1) {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="cambiarPagina(${paginationInfo.totalPages})">${paginationInfo.totalPages}</a></li>`;
    }
    
    // Botón Siguiente
    if (paginationInfo.hasNext) {
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="cambiarPagina(${paginationInfo.currentPage + 1})">
                    Siguiente <i class="bi bi-chevron-right"></i>
                </a>
            </li>
        `;
    } else {
        paginationHTML += `
            <li class="page-item disabled">
                <span class="page-link">
                    Siguiente <i class="bi bi-chevron-right"></i>
                </span>
            </li>
        `;
    }
    
    paginationContainer.innerHTML = `
        <nav aria-label="Paginación de recorridos">
            <ul class="pagination justify-content-center">
                ${paginationHTML}
            </ul>
        </nav>
        <div class="text-center text-muted">
            Página ${paginationInfo.currentPage} de ${paginationInfo.totalPages} 
            (${paginationInfo.total} posiciones en total)
        </div>
    `;
}

// Función para cambiar de página
async function cambiarPagina(pageUrlOrNumber) {
    try {
        // Validar que hay datos de paginación
        if (!paginationInfo) {
            showMessage('No hay información de paginación disponible', 'warning');
            return;
        }
        
        // Si es un número, validar que esté en el rango correcto
        if (typeof pageUrlOrNumber === 'number') {
            if (pageUrlOrNumber < 1 || pageUrlOrNumber > paginationInfo.totalPages) {
                showMessage(`Página inválida. Debe estar entre 1 y ${paginationInfo.totalPages}`, 'warning');
                return;
            }
            
            // Si es la página actual, no hacer nada
            if (pageUrlOrNumber === paginationInfo.currentPage) {
                showMessage('Ya estás en esta página', 'info');
                return;
            }
        }
        
        showMessage('Cargando página...', 'info');
        
        let url;
        
        // Si es un número, construir la URL
        if (typeof pageUrlOrNumber === 'number') {
            const movilId = document.getElementById('movil-select').value;
            const fechaDesde = document.getElementById('fecha-desde').value;
            const fechaHasta = document.getElementById('fecha-hasta').value;
            
            const params = new URLSearchParams({
                movil_id: movilId,
                fecha_desde: fechaDesde,
                fecha_hasta: fechaHasta,
                page: pageUrlOrNumber
            });
            
            url = `/api/recorridos/?${params}`;
        } else {
            // Si es una URL completa, usarla directamente
            url = pageUrlOrNumber;
        }
        
        console.log('Cargando página:', url);
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...auth.getHeaders()
            }
        });
        
        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Datos recibidos:', data);
        
        datosRecorrido = data.results || data;
        
        // Actualizar información de paginación
        if (data.count !== undefined) {
            // Extraer número de página de la URL actual
            const currentPage = extractPageFromUrl(url) || 1;
            
            paginationInfo = {
                total: data.count,
                currentPage: currentPage,
                totalPages: Math.ceil(data.count / PAGE_SIZE_DEFAULT),
                hasNext: data.next !== null,
                hasPrevious: data.previous !== null,
                nextUrl: data.next,
                previousUrl: data.previous,
                pageSize: data.page_size || PAGE_SIZE_DEFAULT
            };
            
            console.log('Información de paginación actualizada:', paginationInfo);
        }
        
        // Renderizar según la vista actual
        if (currentViewMode === 'list') {
            renderizarListado();
        } else {
            renderizarRecorrido();
        }
        
        // Actualizar controles de paginación
        actualizarControlesPaginacion();
        
        showMessage(`Página ${paginationInfo ? paginationInfo.currentPage : 1} cargada: ${datosRecorrido.length} posiciones`, 'success');
        
    } catch (error) {
        console.error('Error cambiando página:', error);
        showMessage('Error cargando la página', 'error');
    }
}

// Función auxiliar para extraer el número de página de una URL
function extractPageFromUrl(url) {
    try {
        const urlObj = new URL(url, window.location.origin);
        const pageParam = urlObj.searchParams.get('page');
        return pageParam ? parseInt(pageParam) : 1;
    } catch (error) {
        console.error('Error extrayendo página de URL:', error);
        return 1;
    }
}

// Función para detectar si es dispositivo móvil
function esDispositivoMovil() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// Función para compartir a WhatsApp
function compartirAWhatsApp(vista) {
    if (datosRecorrido.length === 0) {
        notify.info('No hay datos de recorrido para compartir');
        return;
    }
    
    // Detectar si es dispositivo móvil
    const esMovil = esDispositivoMovil();
    
    if (!esMovil) {
        // En desktop, mostrar opciones de compartir
        mostrarOpcionesCompartir(vista);
        return;
    }
    
    // En móvil, compartir directamente
    const mensaje = generarMensajeWhatsApp(vista);
    const urlWhatsApp = `https://wa.me/?text=${encodeURIComponent(mensaje)}`;
    
    // Abrir WhatsApp
    window.open(urlWhatsApp, '_blank');
}

// Función para mostrar opciones de compartir en desktop
function mostrarOpcionesCompartir(vista) {
    const opciones = `
        <div class="modal fade" id="modalCompartir" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-whatsapp me-2"></i>
                            Compartir en WhatsApp
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">Tipo de compartir:</label>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="tipoCompartir" id="ubicacionActual" value="actual" checked>
                                <label class="form-check-label" for="ubicacionActual">
                                    Ubicación actual (última posición)
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="tipoCompartir" id="resumenRecorrido" value="resumen">
                                <label class="form-check-label" for="resumenRecorrido">
                                    Resumen del recorrido
                                </label>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label for="mensajePersonalizado" class="form-label">Mensaje personalizado (opcional):</label>
                            <textarea class="form-control" id="mensajePersonalizado" rows="3" 
                                placeholder="Agregar un mensaje personalizado..."></textarea>
                        </div>
                        <div class="alert alert-info">
                            <i class="bi bi-info-circle me-2"></i>
                            <strong>Nota:</strong> En dispositivos móviles, esta opción se abre directamente en WhatsApp.
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn btn-success" id="btnCompartirConfirmar">
                            <i class="bi bi-whatsapp me-1"></i>
                            Compartir
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remover modal existente si existe
    const modalExistente = document.getElementById('modalCompartir');
    if (modalExistente) {
        modalExistente.remove();
    }
    
    // Agregar modal al DOM
    document.body.insertAdjacentHTML('beforeend', opciones);
    
    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('modalCompartir'));
    modal.show();
    
    // Event listener para el botón de confirmar
    document.getElementById('btnCompartirConfirmar').addEventListener('click', function() {
        const tipoCompartir = document.querySelector('input[name="tipoCompartir"]:checked').value;
        const mensajePersonalizado = document.getElementById('mensajePersonalizado').value;
        
        const mensaje = generarMensajeWhatsApp(vista, tipoCompartir, mensajePersonalizado);
        const urlWhatsApp = `https://wa.me/?text=${encodeURIComponent(mensaje)}`;
        
        // Abrir WhatsApp
        window.open(urlWhatsApp, '_blank');
        
        // Cerrar modal
        modal.hide();
    });
}

// Función para generar mensaje de WhatsApp
function generarMensajeWhatsApp(vista, tipoCompartir = 'actual', mensajePersonalizado = '') {
    const fechaActual = new Date().toLocaleString('es-AR');
    
    // Obtener información del móvil desde el dropdown
    const movilSelect = document.getElementById('movil-select');
    const movilInfo = movilSelect ? movilSelect.options[movilSelect.selectedIndex] : null;
    const patente = movilInfo ? movilInfo.text.split(' - ')[0] : 'N/A';
    const alias = movilInfo ? movilInfo.text.split(' - ')[1] : 'Sin alias';
    
    let mensaje = `*Seguimiento GPS* - ${fechaActual}\n`;
    mensaje += `*Vehículo:* ${patente}${alias !== 'Sin alias' ? ` (${alias})` : ''}\n\n`;
    
    if (mensajePersonalizado) {
        mensaje += `${mensajePersonalizado}\n\n`;
    }
    
         if (tipoCompartir === 'actual') {
         // Ubicación actual (última posición)
         const ultimaPosicion = datosRecorrido[datosRecorrido.length - 1];
         if (ultimaPosicion) {
             mensaje += `*Ubicación Actual:*\n`;
             mensaje += `• Coordenadas: ${ultimaPosicion.lat}, ${ultimaPosicion.lon}\n`;
             if (ultimaPosicion.direccion) {
                 mensaje += `• Dirección: ${ultimaPosicion.direccion}\n`;
             }
             mensaje += `• Hora: ${new Date(ultimaPosicion.fec_gps || ultimaPosicion.timestamp).toLocaleString('es-AR')}\n`;
             mensaje += `• Velocidad: ${ultimaPosicion.velocidad || 0} km/h\n`;
             mensaje += `• Satélites: ${ultimaPosicion.sats || 0}\n\n`;
             
             // Agregar enlace de Google Maps
             mensaje += `Ver en Google Maps:\n`;
             mensaje += `https://www.google.com/maps?q=${ultimaPosicion.lat},${ultimaPosicion.lon}`;
         }
     } else {
         // Resumen del recorrido
         const primeraPosicion = datosRecorrido[0];
         const ultimaPosicion = datosRecorrido[datosRecorrido.length - 1];
         
         if (primeraPosicion && ultimaPosicion) {
             // Obtener el total real de posiciones desde la información de paginación
             const totalPosiciones = paginationInfo && paginationInfo.total ? paginationInfo.total : datosRecorrido.length;
             
                           mensaje += `*Resumen del Recorrido:*\n`;
              mensaje += `• Inicio: ${new Date(primeraPosicion.fec_gps || primeraPosicion.timestamp).toLocaleString('es-AR')}\n`;
              mensaje += `• Fin: ${new Date(ultimaPosicion.fec_gps || ultimaPosicion.timestamp).toLocaleString('es-AR')}\n`;
              
              // Calcular estadísticas básicas solo si tenemos suficiente datos
              let velocidadMaxima = 0;
              let velocidadPromedio = 0;
              let distanciaRecorrida = 0;
              let detenciones = 0;
              
              if (datosRecorrido.length > 0) {
                  const velocidades = datosRecorrido.map(p => p.velocidad || 0).filter(v => v > 0);
                  if (velocidades.length > 0) {
                      velocidadMaxima = Math.max(...velocidades);
                      velocidadPromedio = velocidades.reduce((a, b) => a + b, 0) / velocidades.length;
                  }
                  
                  // Calcular distancia total recorrida (suma de distancias entre puntos consecutivos)
                  for (let i = 1; i < datosRecorrido.length; i++) {
                      const puntoAnterior = datosRecorrido[i - 1];
                      const puntoActual = datosRecorrido[i];
                      
                      const lat1 = parseFloat(puntoAnterior.lat);
                      const lon1 = parseFloat(puntoAnterior.lon);
                      const lat2 = parseFloat(puntoActual.lat);
                      const lon2 = parseFloat(puntoActual.lon);
                      
                      if (!isNaN(lat1) && !isNaN(lon1) && !isNaN(lat2) && !isNaN(lon2)) {
                          // Fórmula de Haversine para calcular distancia en km
                          const R = 6371; // Radio de la Tierra en km
                          const dLat = (lat2 - lat1) * Math.PI / 180;
                          const dLon = (lon2 - lon1) * Math.PI / 180;
                          const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                                    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                                    Math.sin(dLon/2) * Math.sin(dLon/2);
                          const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
                          const distancia = R * c;
                          distanciaRecorrida += distancia;
                      }
                  }
                  
                  // Contar detenciones (velocidad <= 5 km/h)
                  detenciones = datosRecorrido.filter(p => (p.velocidad || 0) <= 5).length;
              }
              
              mensaje += `• Distancia recorrida: ${distanciaRecorrida.toFixed(2)} km\n`;
              mensaje += `• Detenciones: ${detenciones}\n`;
              mensaje += `• Velocidad máxima: ${velocidadMaxima.toFixed(1)} km/h\n`;
              mensaje += `• Velocidad promedio: ${velocidadPromedio.toFixed(1)} km/h\n`;
              mensaje += `• Total de posiciones: ${totalPosiciones}\n\n`;
             
             // Agregar enlaces de Google Maps para inicio y fin
             mensaje += `*Ubicaciones:*\n`;
             mensaje += `• Inicio: https://www.google.com/maps?q=${primeraPosicion.lat},${primeraPosicion.lon}\n`;
             mensaje += `• Fin: https://www.google.com/maps?q=${ultimaPosicion.lat},${ultimaPosicion.lon}\n`;
         }
     }
    
    return mensaje;
}
