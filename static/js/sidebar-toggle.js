/**
 * Script común para manejar el toggle del sidebar con icono dinámico
 * Se puede usar en todas las páginas que tengan el botón sidebarToggle
 */

document.addEventListener('DOMContentLoaded', function() {
    const wrapper = document.getElementById('appWrapper');
    const toggle = document.getElementById('sidebarToggle');
    
    if (!wrapper || !toggle) return;
    
    const storedState = localStorage.getItem('sidebarCollapsed');
    
    // Restaurar estado guardado
    if (storedState === 'true') {
        wrapper.classList.add('collapsed');
    }
    
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
    
    // Configurar evento de click
    toggle.addEventListener('click', function() {
        wrapper.classList.toggle('collapsed');
        localStorage.setItem('sidebarCollapsed', wrapper.classList.contains('collapsed') ? 'true' : 'false');
        // Actualizar icono después del toggle
        updateSidebarIcon();
    });
    
    // Marcar link activo según la página actual
    const currentPage = document.body.dataset.page;
    if (currentPage) {
        const activeLink = document.querySelector(`.sidebar-nav a[data-page="${currentPage}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }
    }
});

