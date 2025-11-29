/**
 * Funciones comunes para mapas en WayGPS
 * Proporciona inicialización normalizada de mapas con selector de tipo y control de zonas
 */

/**
 * Inicializa un mapa con capas base normalizadas y control de zonas
 * @param {string} mapId - ID del elemento HTML del mapa
 * @param {Object} options - Opciones de configuración
 * @param {number} options.lat - Latitud inicial (default: -34.6037)
 * @param {number} options.lon - Longitud inicial (default: -58.3816)
 * @param {number} options.zoom - Zoom inicial (default: 11)
 * @param {boolean} options.showZonesControl - Mostrar control de zonas (default: true)
 * @param {boolean} options.showLayerControl - Mostrar control de capas (default: true)
 * @returns {Object} - Objeto con el mapa, capas, y funciones de control
 */
function initializeNormalizedMap(mapId, options = {}) {
    // Obtener configuración de manera segura, con valores por defecto
    let mapConfig = {};
    if (typeof WAYGPS_CONFIG !== 'undefined' && WAYGPS_CONFIG && WAYGPS_CONFIG.MAP) {
        mapConfig = WAYGPS_CONFIG.MAP;
    } else if (typeof window.WAYGPS_CONFIG !== 'undefined' && window.WAYGPS_CONFIG && window.WAYGPS_CONFIG.MAP) {
        mapConfig = window.WAYGPS_CONFIG.MAP;
    }
    
    const lat = options.lat || mapConfig.DEFAULT_LAT || -34.6037;
    const lon = options.lon || mapConfig.DEFAULT_LON || -58.3816;
    const zoom = options.zoom || mapConfig.DEFAULT_ZOOM || 11;
    const showZonesControl = options.showZonesControl !== false;
    const showLayerControl = options.showLayerControl !== false;

    // Verificar que el elemento existe y es visible
    const mapElement = document.getElementById(mapId);
    if (!mapElement) {
        console.error(`Elemento #${mapId} no encontrado para inicializar el mapa.`);
        return { map: null, layers: {} };
    }
    
    // Crear mapa
    const map = L.map(mapId, {
        preferCanvas: false // Asegurar que los controles se rendericen correctamente
    }).setView([lat, lon], zoom);

    // Capa de calles (OpenStreetMap)
    const streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    });

    // Capa satelital (Esri World Imagery)
    const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: '© Esri',
        maxZoom: 19
    });

    // Capa híbrida (satélite + etiquetas)
    const hybridLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: '© Esri',
        maxZoom: 19
    });

    const labelsLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}.png', {
        attribution: '© CartoDB',
        maxZoom: 19
    });

    // Agregar capa por defecto
    streetLayer.addTo(map);

    // Capas base normalizadas
    const baseLayers = {
        "🗺️ Calles": streetLayer,
        "🛰️ Satélite": satelliteLayer,
        "🌍 Híbrido": L.layerGroup([hybridLayer, labelsLayer])
    };

    // Capa de zonas
    const zonesLayerGroup = L.layerGroup();
    let zonesVisible = false;
    let zonesData = [];

    // Control de capas (selector de tipo de mapa) con zonas integradas
    let layerControl = null;
    if (showLayerControl) {
        // Si se muestra el control de zonas, agregarlo como overlay en el control de capas
        const overlays = showZonesControl ? {
            "📍 Zonas": zonesLayerGroup
        } : {};
        
        layerControl = L.control.layers(baseLayers, overlays).addTo(map);
        
        // Si hay zonas, inicializar como visible por defecto y agregar al mapa
        if (showZonesControl) {
            // Inicializar zonas como visibles por defecto
            zonesVisible = true;
            zonesLayerGroup.addTo(map);
            
            // Marcar el checkbox como activado en el control de capas
            // Esperar un momento para que el control se renderice
            setTimeout(() => {
                const controlContainer = layerControl.getContainer();
                if (controlContainer) {
                    const checkbox = controlContainer.querySelector('input[type="checkbox"]');
                    if (checkbox) {
                        checkbox.checked = true;
                    }
                }
            }, 100);
            
            // Escuchar cambios en el control de capas para sincronizar el estado
            map.on('overlayadd', function(e) {
                if (e.name === '📍 Zonas') {
                    zonesVisible = true;
                    renderZones(); // Re-renderizar cuando se activa
                }
            });
            
            map.on('overlayremove', function(e) {
                if (e.name === '📍 Zonas') {
                    zonesVisible = false;
                    zonesLayerGroup.clearLayers(); // Limpiar cuando se desactiva
                }
            });
        }
    }

    /**
     * Carga y muestra las zonas en el mapa
     */
    async function loadZones() {
        try {
            // Obtener headers de autenticación si están disponibles
            let headers = { 'Content-Type': 'application/json' };
            if (typeof auth !== 'undefined' && auth && typeof auth.getHeaders === 'function') {
                headers = auth.getHeaders();
            } else if (typeof window.auth !== 'undefined' && window.auth && typeof window.auth.getHeaders === 'function') {
                headers = window.auth.getHeaders();
            }
            
            const response = await fetch('/zonas/api/zonas/', {
                headers: headers,
                credentials: 'same-origin'
            });

            if (!response.ok) {
                console.warn('No se pudieron cargar las zonas. Status:', response.status);
                return [];
            }

            const data = await response.json();
            zonesData = Array.isArray(data) ? data : data.results || [];
            
            console.log(`Zonas cargadas: ${zonesData.length}`);
            
            // Renderizar zonas solo si están visibles
            if (zonesVisible) {
                renderZones();
            }
            
            // Retornar los datos para que puedan ser usados externamente
            return zonesData;
        } catch (error) {
            console.error('Error cargando zonas:', error);
            return [];
        }
    }

    /**
     * Renderiza las zonas en el mapa
     */
    function renderZones() {
        // Limpiar zonas existentes
        zonesLayerGroup.clearLayers();

        // Si las zonas están ocultas en el control, no renderizar ninguna
        if (!zonesVisible) {
            return;
        }

        zonesData.forEach(zona => {
            let layer;
            const color = zona.color || '#ff0000';
            const style = {
                color,
                weight: 2,
                opacity: zona.visible ? 1 : 0.3,
                fillColor: color,
                fillOpacity: zona.visible ? (zona.opacidad ?? 0.5) : 0.1
            };

            if (zona.tipo === 'circulo' && zona.centro_geojson && zona.radio_metros) {
                const [lng, lat] = zona.centro_geojson.coordinates;
                layer = L.circle([lat, lng], { radius: zona.radio_metros, ...style });
            } else if (zona.geom_geojson) {
                layer = L.geoJSON(zona.geom_geojson, { style });
            } else {
                return; // No hay geometría válida
            }

            layer.bindPopup(`<strong>${zona.nombre}</strong><br>${zona.descripcion || ''}`);
            layer.addTo(zonesLayerGroup);
        });

        // El control de capas de Leaflet maneja automáticamente agregar/remover la capa
        // Solo necesitamos asegurarnos de que esté en el mapa si está visible
        if (layerControl && showZonesControl) {
            // El control de capas ya maneja esto automáticamente
            // Solo asegurarnos de que la capa esté agregada si está visible
            if (zonesVisible && !map.hasLayer(zonesLayerGroup)) {
                zonesLayerGroup.addTo(map);
            }
        } else {
            // Si no hay control de capas, manejar manualmente
            if (zonesVisible) {
                if (!map.hasLayer(zonesLayerGroup)) {
                    zonesLayerGroup.addTo(map);
                }
            } else {
                if (map.hasLayer(zonesLayerGroup)) {
                    map.removeLayer(zonesLayerGroup);
                }
            }
        }
    }

    /**
     * Muestra/oculta las zonas
     */
    function toggleZones(show) {
        zonesVisible = show !== undefined ? show : !zonesVisible;
        renderZones();
        
        // Sincronizar con el control de capas si existe
        if (layerControl && showZonesControl) {
            if (zonesVisible) {
                if (!map.hasLayer(zonesLayerGroup)) {
                    zonesLayerGroup.addTo(map);
                }
            } else {
                if (map.hasLayer(zonesLayerGroup)) {
                    map.removeLayer(zonesLayerGroup);
                }
            }
        }
    }

    // Cargar zonas al inicializar
    if (showZonesControl) {
        loadZones();
    }

    /**
     * Actualiza los datos de zonas desde una fuente externa
     */
    function setZonesData(newZonesData) {
        zonesData = newZonesData || [];
        renderZones();
    }

    /**
     * Función para forzar actualización de controles cuando el mapa se hace visible
     */
    function updateControls() {
        if (map) {
            map.invalidateSize();
            // Forzar actualización de todos los controles
            if (layerControl) {
                // Los controles de Leaflet se actualizan automáticamente con invalidateSize
                // pero podemos forzar una actualización adicional
                setTimeout(() => {
                    map.invalidateSize();
                }, 50);
            }
        }
    }

    return {
        map,
        layers: {
            street: streetLayer,
            satellite: satelliteLayer,
            hybrid: hybridLayer,
            labels: labelsLayer,
            zones: zonesLayerGroup
        },
        baseLayers,
        layerControl,
        toggleZones,
        loadZones,
        renderZones,
        setZonesData,
        updateControls,
        getZonesData: () => zonesData,
        getZonesLayer: () => zonesLayerGroup
    };
}

