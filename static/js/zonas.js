let map;
let drawnItems;
let drawControl;
let currentGeometry = null;
let currentCentro = null;
let zonasData = [];
let zonaLayers = new Map();
let zonesLayerGroup;
let searchMarker = null;
let selectedSearchLocation = null;
let voiceRecognition = null;
let voiceActive = false;
let searchDebounce = null;
let lastSearchResults = [];
let selectFirstResultPending = false;
let currentTipoSeleccionado = null;
let currentZonasViewMode = window.innerWidth < 768 ? 'cards' : 'list'; // 'cards', 'list', o 'map'
let movilesData = [];
let movilesLayerGroup = null;
let movilesMarkers = [];

document.addEventListener('DOMContentLoaded', async () => {
    await auth.verificar();
    initMap();
    bindFormEvents();
    setupSearchControls();
    setupViewToggle();
    setupModalHandlers();
    await loadZonas();
    // Los móviles se cargarán cuando se active el overlay en el control de capas
});

function initMap() {
    // Usar función normalizada para inicializar el mapa con selector de tipo y control de zonas integrado
    const mapResult = initializeNormalizedMap('zonasMap', {
        lat: -34.6037,
        lon: -58.3816,
        zoom: 11,
        showZonesControl: true, // Mostrar control de zonas integrado en el selector de tipo de mapa
        showLayerControl: true
    });
    
    map = mapResult.map;
    
    // Usar el zonesLayerGroup del mapa normalizado
    zonesLayerGroup = mapResult.getZonesLayer();
    
    // Crear capa de grupo para móviles
    movilesLayerGroup = L.layerGroup();
    
    // Agregar móviles como overlay en el control de capas
    if (mapResult.layerControl) {
        const movilesOverlayName = '🚗 Móviles';
        mapResult.layerControl.addOverlay(movilesLayerGroup, movilesOverlayName);
        
        // Escuchar cambios en el control de capas para mostrar/ocultar móviles
        map.on('overlayadd', function(e) {
            console.log('[Zonas] Overlay agregado:', e.name);
            if (e.name === movilesOverlayName || e.layer === movilesLayerGroup) {
                console.log('[Zonas] Activando carga de móviles...');
                loadMoviles();
            }
        });
        
        map.on('overlayremove', function(e) {
            console.log('[Zonas] Overlay removido:', e.name);
            if (e.name === movilesOverlayName || e.layer === movilesLayerGroup) {
                console.log('[Zonas] Ocultando móviles...');
                clearMovilesMarkers();
            }
        });
        
        // También escuchar directamente cambios en el control
        setTimeout(() => {
            const controlContainer = mapResult.layerControl.getContainer();
            if (controlContainer) {
                const checkboxes = controlContainer.querySelectorAll('input[type="checkbox"]');
                checkboxes.forEach(checkbox => {
                    const label = checkbox.closest('label');
                    if (label && label.textContent.includes('Móviles')) {
                        checkbox.addEventListener('change', function() {
                            if (this.checked) {
                                console.log('[Zonas] Checkbox de móviles activado');
                                loadMoviles();
                            } else {
                                console.log('[Zonas] Checkbox de móviles desactivado');
                                clearMovilesMarkers();
                            }
                        });
                    }
                });
            }
        }, 500);
    }
    
    // Guardar referencia global para acceso desde otras funciones
    window.mapResult = mapResult;
    
    // Sincronizar con nuestro sistema de renderizado de zonas
    // Sobrescribir la función renderZones del mapa normalizado para usar nuestra lógica
    const originalRenderZones = mapResult.renderZones;
    mapResult.renderZones = function() {
        // Primero ejecutar la lógica del mapa normalizado
        originalRenderZones.call(this);
        // Luego ejecutar nuestra lógica personalizada para agregar event handlers (click para editar)
        renderZonasMap();
    };
    
    // No cargar zonas automáticamente desde el mapa normalizado
    // porque nosotros las cargamos con nuestra propia función loadZonas()
    // que tiene más lógica (tabla, etc.)
    // Las zonas se cargarán cuando se llame a loadZonas() en el DOMContentLoaded
    
    drawnItems = new L.FeatureGroup().addTo(map);

    refreshDrawControl();

    map.on(L.Draw.Event.CREATED, onShapeCreated);
}

function refreshDrawControl() {
    if (!map) return;
    if (drawControl) {
        map.removeControl(drawControl);
    }

    // Mostrar todas las herramientas de dibujo disponibles
    const baseOptions = {
        polygon: {
            allowIntersection: false,
            showArea: true,
            drawError: {
                color: '#e74c3c',
                message: '<strong>Error:</strong> El polígono no puede autointersectarse.'
            },
            shapeOptions: {
                color: '#ff0000',
                weight: 2
            }
        },
        polyline: {
            shapeOptions: {
                color: '#0d6efd',
                weight: 3
            }
        },
        marker: true,
        circle: {
            shapeOptions: {
                color: '#ff0000',
                weight: 2
            }
        },
        rectangle: false,
        circlemarker: false
    };

    drawControl = new L.Control.Draw({
        edit: {
            featureGroup: drawnItems,
            edit: false
        },
        draw: baseOptions
    });
    map.addControl(drawControl);
    
    // Detectar cuando el usuario hace clic en un icono de la barra de herramientas
    setTimeout(() => {
        const toolbar = document.querySelector('.leaflet-draw-toolbar');
        if (toolbar) {
            // Usar delegación de eventos para capturar clics en los botones
            toolbar.addEventListener('click', (e) => {
                const button = e.target.closest('a');
                if (button && (
                    button.classList.contains('leaflet-draw-draw-marker') || 
                    button.classList.contains('leaflet-draw-draw-circle') ||
                    button.classList.contains('leaflet-draw-draw-polygon') ||
                    button.classList.contains('leaflet-draw-draw-polyline')
                )) {
                    // Detener el titileo cuando el usuario selecciona una herramienta
                    removeTipoSelectHighlight();
                }
            });
        }
    }, 200);
}

function onShapeCreated(event) {
    drawnItems.clearLayers();
    const layer = event.layer;
    drawnItems.addLayer(layer);

    const feature = layer.toGeoJSON();
    currentGeometry = feature?.geometry || null;
    currentCentro = null;

    let tipoDetectado = '';
    const tipoSelectModal = document.getElementById('tipo');
    const tipoActual = tipoSelectModal?.value || '';

    if (layer instanceof L.Circle) {
        tipoDetectado = 'circulo';
        const latLng = layer.getLatLng();
        const radio = Math.round(layer.getRadius());
        currentCentro = {
            type: 'Point',
            coordinates: [latLng.lng, latLng.lat]
        };
        if (currentGeometry) {
            currentGeometry = feature.geometry;
        }
    } else if (layer instanceof L.Marker) {
        tipoDetectado = 'punto';
        currentCentro = currentGeometry;
    } else if (layer instanceof L.Polygon || layer instanceof L.Polyline) {
        // Determinar si es polígono o polilínea
        const coords = feature.geometry.coordinates;
        if (coords && coords[0] && coords[0].length >= 3 && 
            coords[0][0][0] === coords[0][coords[0].length - 1][0] &&
            coords[0][0][1] === coords[0][coords[0].length - 1][1]) {
            // Es cerrado, es un polígono
            tipoDetectado = 'poligono';
        } else {
            // Es abierto, es una polilínea
            tipoDetectado = 'polilinea';
        }
    }

    // Usar el tipo del formulario si existe, sino usar el detectado
    const tipoFinal = tipoActual || tipoDetectado || '';
    currentTipoSeleccionado = tipoFinal;

    // Actualizar el selector del modal con los valores detectados
    if (tipoSelectModal && tipoFinal) {
        tipoSelectModal.value = tipoFinal;
    }
    
    // Remover la animación de títilado rojo ya que se detectó/dibujó el tipo
    removeTipoSelectHighlight();

    const radioGroup = document.getElementById('radioGroup');
    if (tipoFinal === 'circulo') {
        if (layer instanceof L.Circle) {
            const radio = Math.round(layer.getRadius());
            const radioInput = document.getElementById('radio_metros');
            if (radioInput) {
                radioInput.value = radio;
            }
        }
        if (radioGroup) {
            radioGroup.style.display = 'block';
        }
    } else {
        if (radioGroup) {
            radioGroup.style.display = 'none';
        }
    }

    // Abrir el modal automáticamente después de dibujar
    const modalElement = document.getElementById('zonaFormModal');
    if (modalElement) {
        const modal = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
        modal.show();
    }
}

async function loadZonas() {
    try {
        const response = await fetch('/zonas/api/zonas/', {
            headers: auth.getHeaders()
        });
        if (!response.ok) throw new Error('No se pudieron obtener las zonas');

        const data = await response.json();
        zonasData = Array.isArray(data) ? data : data.results || [];

        renderZonasTable();
        renderZonasMap();
        
        // Aplicar la vista actual según el modo seleccionado
        const mapViewRadio = document.querySelector('input[name="view-mode"][value="map"]');
        const listViewRadio = document.querySelector('input[name="view-mode"][value="list"]');
        const cardsViewRadio = document.querySelector('input[name="view-mode"][value="cards"]');
        
        // Determinar qué vista está seleccionada
        let selectedView = 'map'; // Por defecto
        if (mapViewRadio && mapViewRadio.checked) selectedView = 'map';
        else if (listViewRadio && listViewRadio.checked) selectedView = 'list';
        else if (cardsViewRadio && cardsViewRadio.checked) selectedView = 'cards';
        
        // En móviles, si no está en mapa, usar tarjetas
        const isMobile = window.innerWidth < 768;
        if (isMobile && selectedView !== 'map') {
            if (cardsViewRadio) {
                cardsViewRadio.checked = true;
                cambiarVistaZonas('cards');
            }
        } else {
            // En desktop, respetar la selección del usuario
            cambiarVistaZonas(selectedView);
        }
        
        // Sincronizar con el mapa normalizado si está disponible
        if (window.mapResult && window.mapResult.setZonesData) {
            // Actualizar los datos del mapa normalizado con nuestros datos
            window.mapResult.setZonesData(zonasData);
        }
    } catch (error) {
        console.error(error);
        showToast('Error cargando zonas', 'danger');
    }
}

function renderZonasTable() {
    const tbody = document.getElementById('zonasTableBody');
    const cardsContainer = document.getElementById('zonasCardsContainer');
    const countBadge = document.getElementById('zonasCount');
    const countBadgeList = document.getElementById('zonasCountList');

    const countText = `${zonasData.length} zonas`;
    if (countBadge) {
        countBadge.textContent = countText;
    }
    if (countBadgeList) {
        countBadgeList.textContent = countText;
    }

    if (!zonasData.length) {
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">No hay zonas registradas.</td></tr>`;
        }
        if (cardsContainer) {
            cardsContainer.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="bi bi-bounding-box-circles fs-1 text-muted"></i>
                    <h5 class="text-muted mt-3">No hay zonas registradas</h5>
                </div>
            `;
        }
        return;
    }

    // Renderizar según el modo de vista actual
    // En desktop, si está en modo 'list', mostrar lista; si está en 'cards', mostrar tarjetas
    // En móviles, si está en modo 'cards', mostrar tarjetas; si está en 'list', mostrar lista
    const isMobile = window.innerWidth < 768;
    console.log('[renderZonasTable] currentZonasViewMode:', currentZonasViewMode, 'isMobile:', isMobile);
    
    if (currentZonasViewMode === 'cards' && cardsContainer) {
        console.log('[renderZonasTable] Renderizando tarjetas');
        renderZonasCards(cardsContainer);
    } else if (currentZonasViewMode === 'list' && tbody) {
        console.log('[renderZonasTable] Renderizando lista');
        renderZonasList(tbody);
    } else if (cardsContainer && isMobile) {
        // Fallback: si es móvil y no hay modo definido, usar tarjetas
        console.log('[renderZonasTable] Fallback: renderizando tarjetas (móvil)');
        renderZonasCards(cardsContainer);
    } else if (tbody) {
        // Fallback: si es desktop, usar lista
        console.log('[renderZonasTable] Fallback: renderizando lista (desktop)');
        renderZonasList(tbody);
    }
}

function renderZonasCards(container) {
    container.innerHTML = zonasData.map(zona => {
        const tipoBadge = zona.tipo === 'punto' ? 'bg-primary' : 
                         zona.tipo === 'circulo' ? 'bg-info' : 
                         zona.tipo === 'poligono' ? 'bg-success' : 'bg-secondary';
        
        return `
            <div class="col-12 col-md-6 col-lg-4">
                <div class="card h-100 shadow-sm">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0 text-truncate" title="${zona.nombre}">${zona.nombre}</h6>
                        <span class="badge ${tipoBadge} text-uppercase">${zona.tipo}</span>
                    </div>
                    <div class="card-body">
                        ${zona.descripcion ? `<p class="card-text text-muted small">${zona.descripcion}</p>` : ''}
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <small class="text-muted">Visible:</small>
                            <span class="badge ${zona.visible ? 'bg-success' : 'bg-secondary'}">
                                ${zona.visible ? 'Sí' : 'No'}
                            </span>
                        </div>
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">Actualizado:</small>
                            <small class="text-muted">${new Date(zona.actualizado_en).toLocaleDateString()}</small>
                        </div>
                    </div>
                    <div class="card-footer bg-transparent border-top-0">
                        <div class="btn-group w-100" role="group">
                            <button class="btn btn-sm btn-outline-primary" onclick="editZona(${zona.id})" title="Editar">
                                <i class="bi bi-pencil-square"></i> Editar
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteZona(${zona.id})" title="Eliminar">
                                <i class="bi bi-trash"></i> Eliminar
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function renderZonasList(tbody) {
        tbody.innerHTML = zonasData.map(zona => `
            <tr>
                <td>
                    <span class="fw-semibold">${zona.nombre}</span><br>
                    <small class="text-muted">${zona.descripcion || ''}</small>
                </td>
                <td><span class="badge bg-light text-dark text-uppercase">${zona.tipo}</span></td>
                <td>${zona.visible ? '<span class="text-success">Sí</span>' : '<span class="text-muted">No</span>'}</td>
                <td>${new Date(zona.actualizado_en).toLocaleString()}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editZona(${zona.id})">
                        <i class="bi bi-pencil-square"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteZona(${zona.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
}

function renderZonasMap() {
    zonaLayers.forEach(layer => zonesLayerGroup.removeLayer(layer));
    zonaLayers.clear();

    zonasData.forEach(zona => {
        let layer;
        const color = zona.color || '#ff0000';
        const style = {
            color,
            weight: 2,
            opacity: 1,
            fillColor: color,
            fillOpacity: zona.opacidad ?? 0.5
        };

        if (!zona.visible) {
            style.opacity = 0.3;
            style.fillOpacity = 0.1;
        }

        if (zona.tipo === 'circulo' && zona.centro_geojson && zona.radio_metros) {
            const [lng, lat] = zona.centro_geojson.coordinates;
            layer = L.circle([lat, lng], { radius: zona.radio_metros, ...style });
        } else {
            layer = L.geoJSON(zona.geom_geojson, { style });
        }

        layer.bindPopup(`<strong>${zona.nombre}</strong><br>${zona.descripcion || ''}`);
        layer.on('click', () => editZona(zona.id));
        layer.addTo(zonesLayerGroup);
        zonaLayers.set(zona.id, layer);
    });
}

function bindFormEvents() {
    // Selector del modal (para edición)
    const tipoSelect = document.getElementById('tipo');
    if (tipoSelect) {
        tipoSelect.addEventListener('change', (e) => {
            currentTipoSeleccionado = e.target.value || null;
            
            currentGeometry = null;
            currentCentro = null;
            const radioGroup = document.getElementById('radioGroup');
            if (radioGroup) {
                radioGroup.style.display = e.target.value === 'circulo' ? 'block' : 'none';
            }
            refreshDrawControl();
        });
    }

    const clearBtn = document.getElementById('clearDrawingBtn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            drawnItems.clearLayers();
            currentGeometry = null;
            currentCentro = null;
            showToast('Dibujo limpiado. Seleccioná un tipo y dibujá nuevamente.', 'info');
        });
    }

    const fitBoundsBtn = document.getElementById('fitBoundsBtn');
    if (fitBoundsBtn) {
        fitBoundsBtn.addEventListener('click', () => {
            if (zonesLayerGroup && zonesLayerGroup.getLayers().length) {
                map.fitBounds(zonesLayerGroup.getBounds(), { padding: [20, 20] });
            } else if (drawnItems && drawnItems.getLayers().length) {
                map.fitBounds(drawnItems.getBounds(), { padding: [20, 20] });
            } else if (map) {
                map.setView(MAP_CENTER, MAP_ZOOM);
            }
        });
    }

    const resetBtn = document.getElementById('resetFormBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetForm);
    }

    const form = document.getElementById('zonaForm');
    if (form) {
        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            await submitZonaForm();
        });
    }
}

function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : null;
}

function buildAuthHeaders() {
    return auth.getHeaders ? auth.getHeaders() : {'Content-Type': 'application/json'};
}

async function submitZonaForm() {
    const id = document.getElementById('zonaId').value;
    const tipoInput = document.getElementById('tipo');
    const tipoValue = tipoInput ? tipoInput.value : null;
    const payload = {
        nombre: document.getElementById('nombre').value,
        descripcion: document.getElementById('descripcion').value,
        tipo: tipoValue || currentTipoSeleccionado || '',
        color: document.getElementById('color').value,
        opacidad: parseFloat(document.getElementById('opacidad').value || 0.5),
        visible: document.getElementById('visible').checked,
    };

    if (!payload.tipo) {
        showToast('Seleccioná un tipo de zona.', 'warning');
        return;
    }
    
    // Actualizar el input de tipo si se usó currentTipoSeleccionado
    if (!tipoValue && currentTipoSeleccionado && tipoInput) {
        tipoInput.value = currentTipoSeleccionado;
    }

    if (!currentGeometry && !id) {
        showToast('Dibujá la zona en el mapa antes de guardar.', 'warning');
        return;
    }

    if (currentGeometry) {
        payload.geom_geojson_input = currentGeometry;
    }

    if (payload.tipo === 'circulo') {
        payload.radio_metros = parseInt(document.getElementById('radio_metros').value || '0', 10);
        if (currentCentro) {
            payload.centro_geojson_input = currentCentro;
        }
    } else {
        payload.radio_metros = null;
    }

    const method = id ? 'PUT' : 'POST';
    const url = id ? `/zonas/api/zonas/${id}/` : '/zonas/api/zonas/';

    try {
        const headers = {
            ...buildAuthHeaders(),
            'X-CSRFToken': getCsrfToken() || ''
        };

        const response = await fetch(url, {
            method,
            headers,
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'No se pudo guardar la zona');
        }

        showToast('Zona guardada correctamente', 'success');
        resetForm();
        await loadZonas();
        
        // Cerrar modal si está abierto
        const modalElement = document.getElementById('zonaFormModal');
        if (modalElement) {
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) {
                modal.hide();
            }
        }
    } catch (error) {
        console.error(error);
        showToast(error.message || 'Error guardando la zona', 'danger');
    }
}

function resetForm() {
    const form = document.getElementById('zonaForm');
    if (form) {
        form.reset();
    }
    const zonaId = document.getElementById('zonaId');
    if (zonaId) {
        zonaId.value = '';
    }
    
    const radioGroup = document.getElementById('radioGroup');
    if (radioGroup) {
        radioGroup.style.display = 'none';
    }
    const color = document.getElementById('color');
    if (color) {
        color.value = '#FF0000';
    }
    const opacidad = document.getElementById('opacidad');
    if (opacidad) {
        opacidad.value = 0.5;
    }
    const visible = document.getElementById('visible');
    if (visible) {
        visible.checked = true;
    }
    if (drawnItems) {
        drawnItems.clearLayers();
    }
    currentGeometry = null;
    currentCentro = null;
    currentTipoSeleccionado = null;
    refreshDrawControl();
    hideQuickActions();
    hideSuggestions();
    if (searchMarker && map) {
        map.removeLayer(searchMarker);
        searchMarker = null;
    }
    const searchInput = document.getElementById('zonaSearchInput');
    if (searchInput) {
        searchInput.value = '';
    }
    // Remover animación de títilado rojo al resetear
    removeTipoSelectHighlight();
}

function editZona(id) {
    const zona = zonasData.find(z => z.id === id);
    if (!zona) return;

    document.getElementById('zonaId').value = zona.id;
    document.getElementById('nombre').value = zona.nombre;
    document.getElementById('descripcion').value = zona.descripcion || '';
    document.getElementById('tipo').value = zona.tipo;
    currentTipoSeleccionado = zona.tipo;
    document.getElementById('color').value = zona.color || '#FF0000';
    document.getElementById('opacidad').value = zona.opacidad || 0.5;
    document.getElementById('visible').checked = zona.visible;
    document.getElementById('radioGroup').style.display = zona.tipo === 'circulo' ? 'block' : 'none';
    document.getElementById('radio_metros').value = zona.radio_metros || '';

    refreshDrawControl();

    drawnItems.clearLayers();
    if (zona.tipo === 'circulo' && zona.centro_geojson) {
        const [lng, lat] = zona.centro_geojson.coordinates;
        const marker = L.circle([lat, lng], { radius: zona.radio_metros || 100 });
        drawnItems.addLayer(marker);
    } else if (zona.geom_geojson) {
        const layer = L.geoJSON(zona.geom_geojson);
        layer.eachLayer(l => drawnItems.addLayer(l));
    }

    currentGeometry = zona.geom_geojson;
    currentCentro = zona.centro_geojson;

    const layer = zonaLayers.get(zona.id);
    if (layer && map) {
        map.fitBounds(layer.getBounds(), { padding: [20, 20] });
        layer.openPopup();
    }
    
    // Abrir modal y cambiar a vista de mapa
    const modal = bootstrap.Modal.getInstance(document.getElementById('zonaFormModal')) || new bootstrap.Modal(document.getElementById('zonaFormModal'));
    modal.show();
    
    // Cambiar a vista de mapa si estamos en lista
    const mapViewRadio = document.querySelector('input[name="view-mode"][value="map"]');
    if (mapViewRadio && !mapViewRadio.checked) {
        mapViewRadio.checked = true;
        mapViewRadio.dispatchEvent(new Event('change'));
    }
}

async function deleteZona(id) {
    const confirmed = await notify.confirm({
        message: '¿Eliminar zona seleccionada?',
        confirmText: 'Eliminar',
        cancelText: 'Cancelar'
    });
    if (!confirmed) return;
    try {
        const headers = {
            ...buildAuthHeaders(),
            'X-CSRFToken': getCsrfToken() || ''
        };
        const response = await fetch(`/zonas/api/zonas/${id}/`, {
            method: 'DELETE',
            headers,
            credentials: 'same-origin'
        });
        if (!response.ok) throw new Error('No se pudo eliminar la zona');
        showToast('Zona eliminada', 'success');
        await loadZonas();
        resetForm();
    } catch (error) {
        console.error(error);
        showToast('Error eliminando zona', 'danger');
    }
}

function showToast(message, variant = 'info') {
    let container = document.getElementById('zonasToastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'zonasToastContainer';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }

    const alert = document.createElement('div');
    alert.className = `alert alert-${variant}`;
    alert.role = 'alert';
    alert.textContent = message;

    container.appendChild(alert);

    setTimeout(() => {
        alert.remove();
    }, 3200);
}

window.editZona = editZona;
window.deleteZona = deleteZona;

// === BÚSQUEDA Y ACCIONES RÁPIDAS ===
function setupSearchControls() {
    const input = document.getElementById('zonaSearchInput');
    const clearBtn = document.getElementById('zonaSearchClear');
    const suggestionsEl = document.getElementById('zonaSearchSuggestions');
    const micBtn = document.getElementById('voiceSearchBtn');

    if (!input) {
        console.warn('[Zonas] No se encontró el campo de búsqueda.');
        return;
    }

    console.log('[Zonas] Controles de búsqueda inicializados.');

    input.addEventListener('input', () => {
        const value = input.value.trim();
        if (value.length < 3) {
            hideSuggestions();
            const statusEl = document.getElementById('zonaSearchStatus');
            if (statusEl) statusEl.textContent = value.length ? 'Ingresá al menos 3 letras.' : '';
            return;
        }
        if (searchDebounce) clearTimeout(searchDebounce);
        searchDebounce = setTimeout(() => fetchAutocomplete(value), 250);
    });
    
    input.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            const value = input.value.trim();
            if (value.length >= 3) {
                selectFirstResultPending = true;
                fetchAutocomplete(value);
            } else {
                const statusEl = document.getElementById('zonaSearchStatus');
                if (statusEl) statusEl.textContent = 'Ingresá al menos 3 letras.';
            }
        }
    });

    clearBtn?.addEventListener('click', () => {
        input.value = '';
        hideSuggestions();
        if (searchMarker) {
            map.removeLayer(searchMarker);
            searchMarker = null;
        }
        selectedSearchLocation = null;
    });

    micBtn?.addEventListener('click', handleVoiceSearch);
    
    document.addEventListener('click', (event) => {
        if (!suggestionsEl?.contains(event.target) && event.target !== input) {
            hideSuggestions();
        }
    });
}

async function fetchAutocomplete(query) {
    const suggestionsEl = document.getElementById('zonaSearchSuggestions');
    const statusEl = document.getElementById('zonaSearchStatus');
    suggestionsEl.innerHTML = '';
    suggestionsEl.classList.remove('active');
    statusEl.textContent = 'Buscando...';

    try {
        const headers = auth.getHeaders ? auth.getHeaders() : {'Content-Type': 'application/json'};
        headers['Accept'] = 'application/json';
        console.log('[Zonas] Buscando direcciones:', query);
        const response = await fetch(`/zonas/api/geocode/autocomplete/?q=${encodeURIComponent(query)}`, {
            headers,
            credentials: 'same-origin'
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        console.log('[Zonas] Resultados recibidos:', data);
        lastSearchResults = data.results || [];
        renderSuggestions(lastSearchResults);
        statusEl.textContent = `${lastSearchResults.length} resultados`;
        if (selectFirstResultPending && lastSearchResults.length) {
            selectFirstResult(lastSearchResults[0]);
        }
        selectFirstResultPending = false;
    } catch (error) {
        console.error('[Zonas] Error en la búsqueda:', error);
        statusEl.textContent = 'No se pudo completar la búsqueda';
        showToast('No se pudo completar la búsqueda. Revisá la consola para más detalles.', 'danger');
    }
}

function renderSuggestions(results) {
    const suggestionsEl = document.getElementById('zonaSearchSuggestions');
    if (!suggestionsEl) return;
    if (!results.length) {
        suggestionsEl.classList.remove('active');
        suggestionsEl.innerHTML = '';
        return;
    }
    suggestionsEl.classList.add('active');
    suggestionsEl.innerHTML = results.map((item, index) => `
        <div class="search-suggestion-item" data-index="${index}">
            <strong>${item.label || 'Sin nombre'}</strong>
            <small>${item.address_formatted || ''}</small>
        </div>
    `).join('');

    suggestionsEl.querySelectorAll('.search-suggestion-item').forEach(el => {
        el.addEventListener('click', () => {
            const idx = Number(el.dataset.index);
            selectSuggestion(results[idx]);
        });
    });
}

function hideSuggestions() {
    const suggestionsEl = document.getElementById('zonaSearchSuggestions');
    const statusEl = document.getElementById('zonaSearchStatus');
    if (suggestionsEl) {
        suggestionsEl.classList.remove('active');
        suggestionsEl.innerHTML = '';
    }
    if (statusEl) statusEl.textContent = '';
}

function selectSuggestion(place) {
    selectFirstResultPending = false;
    hideSuggestions();
    if (!place || !place.coordinates) return;
    selectedSearchLocation = place;
    const lat = place.coordinates.lat;
    const lon = place.coordinates.lon;

    if (searchMarker) {
        map.removeLayer(searchMarker);
    }

    searchMarker = L.marker([lat, lon], {icon: L.icon({
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41]
    })}).addTo(map);

    searchMarker.bindPopup(`<div class="fw-semibold">${place.label}</div><small>${place.address_formatted || ''}</small>`).openPopup();
    map.flyTo([lat, lon], 17);
    // No mostrar acciones rápidas - el usuario puede elegir el tipo en el modal y dibujar
}

function selectFirstResult(place) {
    const input = document.getElementById('zonaSearchInput');
    if (input && place && place.label) {
        input.value = place.label;
    }
    selectSuggestion(place);
    // No mostrar acciones rápidas
}

function hideQuickActions() {
    // Función simplificada - solo limpia selectedSearchLocation si es necesario
    // Mantenida para compatibilidad con código existente
    selectedSearchLocation = null;
}

function handleVoiceSearch() {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
        showToast('La búsqueda por voz no está disponible en este navegador.', 'warning');
        return;
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!voiceRecognition) {
        voiceRecognition = new SpeechRecognition();
        voiceRecognition.lang = 'es-AR';
        voiceRecognition.interimResults = false;
        voiceRecognition.maxAlternatives = 1;
    }

    if (voiceActive) {
        voiceRecognition.stop();
        voiceActive = false;
        return;
    }

    voiceRecognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        document.getElementById('zonaSearchInput').value = transcript;
        fetchAutocomplete(transcript);
    };
    voiceRecognition.onerror = (event) => {
        voiceActive = false;
        console.error('[Zonas] Error en reconocimiento de voz:', event.error);
        showToast(`No se pudo capturar la voz (${event.error || 'error desconocido'}).`, 'warning');
    };
    voiceRecognition.onend = () => {
        voiceActive = false;
    };

    voiceActive = true;
    voiceRecognition.start();
    showToast('Escuchando... hablá cerca del micrófono.', 'info');
}

// Configurar toggle Mapa/Lista/Tarjetas
function setupViewToggle() {
    const viewModeRadios = document.querySelectorAll('input[name="view-mode"]');
    viewModeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            const viewMode = this.value;
            cambiarVistaZonas(viewMode);
        });
    });
    
    // Inicializar vista responsive
    function initResponsiveView() {
        const isMobile = window.innerWidth < 768;
        const mapViewRadio = document.querySelector('input[name="view-mode"][value="map"]');
        const listViewRadio = document.querySelector('input[name="view-mode"][value="list"]');
        const cardsViewRadio = document.querySelector('input[name="view-mode"][value="cards"]');
        
        if (isMobile) {
            // En móviles, cambiar automáticamente a modo tarjetas si no está en mapa
            if (mapViewRadio && !mapViewRadio.checked && currentZonasViewMode !== 'cards') {
                // Si no está en mapa, cambiar a tarjetas
                if (cardsViewRadio) {
                    cardsViewRadio.checked = true;
                    cambiarVistaZonas('cards');
                }
            }
        } else {
            // En desktop, asegurar que si está en modo tarjetas, cambie a lista
            if (currentZonasViewMode === 'cards' && listViewRadio) {
                listViewRadio.checked = true;
                cambiarVistaZonas('list');
            } else if (mapViewRadio && mapViewRadio.checked) {
                // Si está en mapa, mantenerlo
                cambiarVistaZonas('map');
            } else if (listViewRadio && listViewRadio.checked) {
                // Si está en lista, asegurar que se muestre
                cambiarVistaZonas('list');
            }
        }
    }
    
    // Ejecutar al cargar y al redimensionar
    setTimeout(initResponsiveView, 100);
    window.addEventListener('resize', function() {
        clearTimeout(window.zonasResizeTimer);
        window.zonasResizeTimer = setTimeout(initResponsiveView, 250);
    });
    
    // Cargar preferencia guardada (solo si no es móvil)
    const isMobile = window.innerWidth < 768;
    if (!isMobile) {
        const savedViewMode = localStorage.getItem('zonas-view-mode') || 'map';
        const savedRadio = document.querySelector(`input[name="view-mode"][value="${savedViewMode}"]`);
        if (savedRadio) {
            savedRadio.checked = true;
            savedRadio.dispatchEvent(new Event('change'));
        }
    }
}

function cambiarVistaZonas(viewMode) {
    console.log('[cambiarVistaZonas] Cambiando a modo:', viewMode, 'ancho:', window.innerWidth);
    currentZonasViewMode = viewMode;
            const mapView = document.getElementById('zonas-map-view');
            const listView = document.getElementById('zonas-list-view');
    const cardsView = document.getElementById('zonas-cards-view');
    
    // Ocultar todas las vistas
    if (mapView) mapView.style.display = 'none';
    if (listView) listView.style.display = 'none';
    if (cardsView) cardsView.style.display = 'none';
    
    // Mostrar la vista seleccionada
            if (viewMode === 'map') {
                if (mapView) mapView.style.display = 'block';
                // Asegurar que el mapa se redibuje correctamente
                if (map) {
                    setTimeout(() => {
                        map.invalidateSize();
                    }, 100);
                }
            } else if (viewMode === 'list') {
        if (listView) {
            listView.style.display = 'block';
            console.log('[cambiarVistaZonas] Vista de lista mostrada');
        }
        // Renderizar lista si hay datos - forzar modo lista
        if (zonasData.length > 0) {
            // Asegurar que se renderice como lista
            const tbody = document.getElementById('zonasTableBody');
            if (tbody) {
                renderZonasList(tbody);
            } else {
                renderZonasTable();
            }
        }
    } else if (viewMode === 'cards') {
        if (cardsView) {
            cardsView.style.display = 'block';
            console.log('[cambiarVistaZonas] Vista de tarjetas mostrada');
        }
        // Renderizar tarjetas si hay datos - forzar modo tarjetas
        if (zonasData.length > 0) {
            const cardsContainer = document.getElementById('zonasCardsContainer');
            if (cardsContainer) {
                renderZonasCards(cardsContainer);
            } else {
                renderZonasTable();
            }
        }
    }
    
    // Guardar preferencia (solo si no es móvil)
    if (window.innerWidth >= 768) {
            localStorage.setItem('zonas-view-mode', viewMode);
    }
}

// ========================================
// FUNCIONES PARA MÓVILES EN EL MAPA
// ========================================

// Verificar si un móvil está en línea (reportó en los últimos 15 minutos)
function isOnlineMovil(movil) {
    const status = movil.status_info || {};
    const fechaRecepcion = status.fecha_recepcion || status.ultima_actualizacion;
    
    if (!fechaRecepcion) return false;

    const ultimaRecepcion = new Date(fechaRecepcion);
    const ahora = new Date();
    const diferenciaMinutos = (ahora - ultimaRecepcion) / (1000 * 60);

    return diferenciaMinutos <= 15;
}

// Crear popup para marcador de móvil
function createMovilPopupZonas(movil) {
    const status = movil.status_info || {};
    const geocode = movil.geocode_info || {};
    const online = isOnlineMovil(movil);
    const estado = online ? 'En línea' : 'Desconectado';
    const encendido = status.ignicion ? 'Encendido' : 'Apagado';

    // Información de domicilio
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

// Limpiar marcadores de móviles
function clearMovilesMarkers() {
    if (movilesLayerGroup) {
        movilesLayerGroup.clearLayers();
    }
    movilesMarkers = [];
}

// Renderizar móviles en el mapa
function renderMoviles() {
    if (!movilesLayerGroup || !map) {
        console.warn('[Zonas] No se puede renderizar móviles: movilesLayerGroup o map no están disponibles');
        return;
    }
    
    console.log('[Zonas] Renderizando móviles, total:', movilesData.length);
    
    // Limpiar marcadores existentes
    clearMovilesMarkers();
    
    // Asegurar que la capa esté en el mapa antes de agregar marcadores
    if (!map.hasLayer(movilesLayerGroup)) {
        movilesLayerGroup.addTo(map);
        console.log('[Zonas] Capa de móviles agregada al mapa');
    }
    
    // Agregar marcadores para cada móvil
    let marcadoresAgregados = 0;
    movilesData.forEach(movil => {
        const status = movil.status_info || {};
        if (status.ultimo_lat && status.ultimo_lon) {
            const online = isOnlineMovil(movil);
            const iconColor = online ? 'green' : 'red';

            // Convertir coordenadas a números
            const lat = parseFloat(status.ultimo_lat);
            const lon = parseFloat(status.ultimo_lon);
            
            // Validar coordenadas
            if (isNaN(lat) || isNaN(lon)) {
                console.warn('[Zonas] Coordenadas inválidas para móvil:', movil.id, lat, lon);
                return;
            }

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
                .addTo(movilesLayerGroup)
                .bindPopup(createMovilPopupZonas(movil));

            movilesMarkers.push(marker);
            marcadoresAgregados++;
        }
    });
    
    console.log(`[Zonas] Móviles renderizados: ${marcadoresAgregados} de ${movilesData.length}`);
}

// Cargar móviles desde la API
async function loadMoviles() {
    try {
        console.log('[Zonas] Iniciando carga de móviles...');
        
        // Obtener headers de autenticación
        let headers = { 'Content-Type': 'application/json' };
        if (typeof auth !== 'undefined' && auth && typeof auth.getHeaders === 'function') {
            headers = auth.getHeaders();
        } else if (typeof window.auth !== 'undefined' && window.auth && typeof window.auth.getHeaders === 'function') {
            headers = window.auth.getHeaders();
        }
        
        // Obtener URL de la API de móviles
        // La URL correcta es /moviles/api/moviles/ según las rutas de Django
        let MOVILES_API_URL;
        if (typeof WAYGPS_CONFIG !== 'undefined' && WAYGPS_CONFIG) {
            // Usar el endpoint configurado si está disponible
            if (WAYGPS_CONFIG.MOVILES_ENDPOINT) {
                MOVILES_API_URL = WAYGPS_CONFIG.MOVILES_ENDPOINT;
            } else if (WAYGPS_CONFIG.API_BASE_URL) {
                MOVILES_API_URL = `${WAYGPS_CONFIG.API_BASE_URL}/moviles/api/moviles/`;
            } else {
                MOVILES_API_URL = '/moviles/api/moviles/';
            }
        } else if (typeof window.WAYGPS_CONFIG !== 'undefined' && window.WAYGPS_CONFIG) {
            if (window.WAYGPS_CONFIG.MOVILES_ENDPOINT) {
                MOVILES_API_URL = window.WAYGPS_CONFIG.MOVILES_ENDPOINT;
            } else if (window.WAYGPS_CONFIG.API_BASE_URL) {
                MOVILES_API_URL = `${window.WAYGPS_CONFIG.API_BASE_URL}/moviles/api/moviles/`;
            } else {
                MOVILES_API_URL = '/moviles/api/moviles/';
            }
        } else {
            // URL por defecto según las rutas de Django
            MOVILES_API_URL = '/moviles/api/moviles/';
        }
        
        console.log('[Zonas] Cargando móviles desde:', MOVILES_API_URL);
        
        const response = await fetch(MOVILES_API_URL, {
            headers: headers,
            credentials: 'same-origin'
        });

        if (!response.ok) {
            console.error('[Zonas] Error al cargar móviles. Status:', response.status);
            const errorText = await response.text();
            console.error('[Zonas] Error response:', errorText);
            return;
        }

        const data = await response.json();
        movilesData = Array.isArray(data) ? data : (data.results || []);
        
        console.log(`[Zonas] Móviles cargados: ${movilesData.length}`);
        
        // Renderizar móviles en el mapa
        renderMoviles();
        
    } catch (error) {
        console.error('[Zonas] Error cargando móviles:', error);
        console.error('[Zonas] Stack trace:', error.stack);
    }
}

// Activar animación de títilado rojo en la barra de herramientas de dibujo
function highlightTipoSelect() {
    // Asegurar que la barra de herramientas esté visible
    if (!drawControl) {
        refreshDrawControl();
    }
    
    // Esperar a que la barra de herramientas se renderice
    setTimeout(() => {
        const toolbar = document.querySelector('.leaflet-draw-toolbar');
        if (toolbar) {
            toolbar.classList.add('tipo-select-highlight');
        } else {
            // Si no se encuentra, intentar nuevamente después de un breve delay
            setTimeout(() => {
                const toolbarRetry = document.querySelector('.leaflet-draw-toolbar');
                if (toolbarRetry) {
                    toolbarRetry.classList.add('tipo-select-highlight');
                }
            }, 300);
        }
    }, 200);
}

// Remover animación de títilado rojo de la barra de herramientas
function removeTipoSelectHighlight() {
    const toolbar = document.querySelector('.leaflet-draw-toolbar');
    if (toolbar) {
        toolbar.classList.remove('tipo-select-highlight');
    }
}

// Configurar handlers del modal
function setupModalHandlers() {
    const modalElement = document.getElementById('zonaFormModal');
    const modal = new bootstrap.Modal(modalElement);
    const btnNuevaZona = document.getElementById('btnNuevaZona');
    const saveZonaBtn = document.getElementById('saveZonaBtn');
    
    // Abrir modal para nueva zona - NO abrir modal, solo activar animación
    if (btnNuevaZona) {
        btnNuevaZona.addEventListener('click', () => {
            resetForm();
            // NO abrir el modal, solo activar la animación de títilado rojo en el selector del mapa
            highlightTipoSelect();
            // Cambiar a vista de mapa si estamos en lista
            const mapViewRadio = document.querySelector('input[name="view-mode"][value="map"]');
            if (mapViewRadio && !mapViewRadio.checked) {
                mapViewRadio.checked = true;
                mapViewRadio.dispatchEvent(new Event('change'));
            }
        });
    }
    
    // Guardar desde el modal
    if (saveZonaBtn) {
        saveZonaBtn.addEventListener('click', async () => {
            await submitZonaForm();
            // Cerrar modal si se guardó correctamente
            const zonaId = document.getElementById('zonaId').value;
            if (zonaId || currentGeometry) {
                // Solo cerrar si hay algo que guardar
                // El submitZonaForm mostrará un toast si hay error
            }
        });
    }
    
    // Limpiar formulario cuando se cierra el modal
    if (modalElement) {
        modalElement.addEventListener('hidden.bs.modal', () => {
            resetForm();
            removeTipoSelectHighlight(); // Asegurar que se remueva la animación
        });
        
        // Cuando se abre el modal desde onShapeCreated (después de dibujar)
        modalElement.addEventListener('shown.bs.modal', () => {
            // Asegurar que la animación esté desactivada cuando se abre el modal después de dibujar
            removeTipoSelectHighlight();
        });
    }
}

