# Problema con la Vista Responsive

## Diagnóstico

El problema es que hay **código conflictivo** en `moviles.js` que está intentando hacer lo mismo de dos maneras diferentes:

1. Una implementación con `initializeViewMode()` y `ocultarBotonesVista()` 
2. Mi implementación con `handleViewMode()`

Esto causa que ambas compitan y no funcione correctamente.

## Solución Simple

He creado un archivo nuevo: `static/js/responsive-view.js` que maneja SOLO la lógica de cambio automático de vista.

### Pasos para implementar:

1. **Restaurar el archivo moviles.js a su estado limpio:**
   ```powershell
   git checkout HEAD -- static/js/moviles.js
   ```

2. **Agregar el script responsive-view.js al HTML:**
   
   Editar `templates/moviles/index.html` y buscar la línea:
   ```html
   <script src="{% static 'js/moviles.js' %}"></script>
   ```
   
   Agregar justo debajo:
   ```html
   <script src="{% static 'js/responsive-view.js' %}"></script>
   ```

3. **Hacer lo mismo para equipos:**
   
   Editar `templates/equipos/index.html` y agregar el mismo script después de `equipos.js`

## Cómo funciona

El archivo `responsive-view.js` es muy simple:
- Detecta si la pantalla es menor a 768px (móvil)
- Si es móvil, cambia a vista "cards"
- Si es PC, cambia a vista "list"
- Se ejecuta automáticamente al cargar y al redimensionar

## Alternativa más simple

Si prefieres, puedo simplemente agregar estas 3 líneas al final de `moviles.js`:

```javascript
// Auto-cambio de vista según tamaño de pantalla
window.addEventListener('resize', () => {
    const newMode = window.innerWidth < 768 ? 'cards' : 'list';
    if (typeof currentViewMode !== 'undefined' && currentViewMode !== newMode) {
        currentViewMode = newMode;
        if (typeof cambiarVista === 'function') cambiarVista(newMode);
    }
});
```

¿Cuál prefieres?
