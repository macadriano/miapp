// Inicialización específica para la página de móviles
// Este archivo se carga después de moviles.js

// Verificar autenticación al cargar la página
document.addEventListener('DOMContentLoaded', async function () {
    // Configurar sidebar toggle
    const wrapper = document.getElementById('appWrapper');
    const toggle = document.getElementById('sidebarToggle');
    const storedState = localStorage.getItem('sidebarCollapsed');

    if (wrapper && storedState === 'true') {
        wrapper.classList.add('collapsed');
    }

    if (toggle && wrapper) {
        // Función para actualizar el icono según el estado del sidebar
        function updateSidebarIcon() {
            const icon = toggle.querySelector('i');
            if (icon) {
                if (wrapper.classList.contains('collapsed')) {
                    // Sidebar colapsado: mostrar chevron-right para expandir
                    icon.className = 'bi bi-chevron-right';
                } else {
                    // Sidebar expandido: mostrar chevron-left para colapsar
                    icon.className = 'bi bi-chevron-left';
                }
            }
        }
        
        // Actualizar icono al cargar según el estado guardado
        updateSidebarIcon();
        
        toggle.addEventListener('click', function () {
            wrapper.classList.toggle('collapsed');
            localStorage.setItem('sidebarCollapsed', wrapper.classList.contains('collapsed') ? 'true' : 'false');
            // Actualizar icono después del toggle
            updateSidebarIcon();
        });
    }

    const currentPage = document.body.dataset.page;
    const activeLink = document.querySelector(`.sidebar-nav a[data-page="${currentPage}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }

    // Mostrar info del usuario si existe token
    if (typeof auth !== 'undefined' && auth && auth.getToken) {
        try {
            if (auth.getToken()) {
                auth.mostrarInfo();
            } else {
                const userNameElement = document.getElementById('userName');
                if (userNameElement) {
                    userNameElement.textContent = 'No autenticado';
                }
            }
        } catch(e) {
            console.warn('Error al obtener token:', e);
        }
    } else {
        const userNameElement = document.getElementById('userName');
        if (userNameElement) {
            userNameElement.textContent = 'No autenticado';
        }
    }

    // Configurar opciones de logout (botón en footer y opción en menú simplificado)
    function setupLogout(element) {
        if (!element) return;
        element.addEventListener('click', function (e) {
            e.preventDefault();
            console.log('Opción de logout clickeada');
            if (typeof auth !== 'undefined' && auth && typeof auth.logout === 'function') {
                auth.logout();
            } else {
                console.error('auth.logout no está disponible');
            }
        });
    }

    const logoutBtn = document.getElementById('logoutBtn');
    const sidebarLogoutLink = document.getElementById('sidebarLogoutLink');
    setupLogout(logoutBtn);
    setupLogout(sidebarLogoutLink);
});

// Funciones para gestión de fotos
function abrirCamara() {
    const input = document.getElementById('file-input');
    if (input) {
        input.setAttribute('capture', 'camera');
        input.click();
    }
}

function subirFoto() {
    const input = document.getElementById('file-input');
    if (input) {
        input.removeAttribute('capture');
        input.click();
    }
}

function procesarFotos(files) {
    console.log('Procesando fotos:', files);
    // Aquí se implementará la lógica para subir las fotos
    if (files) {
        for (let file of files) {
            console.log('Archivo:', file.name, 'Tipo:', file.type, 'Tamaño:', file.size);
        }
    }
}

function nuevaObservacion() {
    const modalElement = document.getElementById('modalObservacion');
    if (modalElement && typeof bootstrap !== 'undefined') {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    }
}

function guardarObservacion() {
    console.log('Guardando observación...');
    // Aquí se implementará la lógica para guardar la observación
    const modalElement = document.getElementById('modalObservacion');
    if (modalElement && typeof bootstrap !== 'undefined') {
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
        }
    }
}

