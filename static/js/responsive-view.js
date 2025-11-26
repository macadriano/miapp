// Lógica de vista responsive automática para Móviles y Equipos
// Este archivo maneja el cambio automático entre vista de lista (PC) y tarjetas (móvil)

(function () {
    'use strict';

    // Esperar a que el DOM esté listo
    document.addEventListener('DOMContentLoaded', function () {
        console.log('Inicializando vista responsive automática');

        // Función para manejar el cambio de vista
        function handleResponsiveView() {
            const isMobile = window.innerWidth < 768;
            const newMode = isMobile ? 'cards' : 'list';

            // Solo cambiar si currentViewMode está definido (significa que estamos en móviles o equipos)
            if (typeof currentViewMode !== 'undefined' && currentViewMode !== newMode) {
                console.log(`Cambiando vista de ${currentViewMode} a ${newMode}`);
                currentViewMode = newMode;

                // Llamar a cambiarVista si existe
                if (typeof cambiarVista === 'function') {
                    cambiarVista(currentViewMode);
                }
            }
        }

        // Ejecutar al cargar
        setTimeout(handleResponsiveView, 500);

        // Ejecutar al redimensionar
        let resizeTimer;
        window.addEventListener('resize', function () {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(handleResponsiveView, 250);
        });

        console.log('Vista responsive automática configurada');
    });
})();
