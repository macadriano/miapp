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

document.addEventListener('DOMContentLoaded', async () => {
    await auth.verificar();
    initMap();
    bindFormEvents();
    setupSearchControls();
    setupViewToggle();
    setupModalHandlers();
    await loadZonas();
});

function initMap() {
    map = L.map('zonasMap').setView([-34.6037, -58.3816], 11);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    drawnItems = new L.FeatureGroup().addTo(map);
    zonesLayerGroup = new L.FeatureGroup().addTo(map);

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
    } catch (error) {
        console.error(error);
        showToast('Error cargando zonas', 'danger');
    }
}

function renderZonasTable() {
    const tbody = document.getElementById('zonasTableBody');
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
        return;
    }

    if (tbody) {
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

// Configurar toggle Mapa/Lista
function setupViewToggle() {
    const viewModeRadios = document.querySelectorAll('input[name="view-mode"]');
    viewModeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            const viewMode = this.value;
            const mapView = document.getElementById('zonas-map-view');
            const listView = document.getElementById('zonas-list-view');
            
            if (viewMode === 'map') {
                if (mapView) mapView.style.display = 'block';
                if (listView) listView.style.display = 'none';
                // Asegurar que el mapa se redibuje correctamente
                if (map) {
                    setTimeout(() => {
                        map.invalidateSize();
                    }, 100);
                }
            } else if (viewMode === 'list') {
                if (mapView) mapView.style.display = 'none';
                if (listView) listView.style.display = 'block';
            }
            
            // Guardar preferencia
            localStorage.setItem('zonas-view-mode', viewMode);
        });
    });
    
    // Cargar preferencia guardada
    const savedViewMode = localStorage.getItem('zonas-view-mode') || 'map';
    const savedRadio = document.querySelector(`input[name="view-mode"][value="${savedViewMode}"]`);
    if (savedRadio) {
        savedRadio.checked = true;
        savedRadio.dispatchEvent(new Event('change'));
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

