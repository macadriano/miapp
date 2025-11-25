# Documentación de la última modificación

## Contexto
En la aplicación **WayGPS** se ha actualizado la forma en que se presentan los móviles y equipos en pantalla, pasando de una vista estática con un toggle manual a una **vista responsiva automática** que muestra:

- **Tarjetas (cards)** cuando el usuario accede desde un dispositivo móvil.
- **Lista (list)** cuando se visualiza desde un escritorio.

Esta lógica se aplica tanto a la sección **"Móviles"** como a la sección **"Equipos"**.

## Cambios clave en el código

1. **Variable global `currentViewMode`**
   ```javascript
   let currentViewMode = 'cards'; // 'cards' o 'list'
   ```
   - Almacena el modo de vista activo.

2. **Función `handleViewMode()`**
   ```javascript
   function handleViewMode() {
       const isMobile = window.innerWidth < 768;
       const newMode = isMobile ? 'cards' : 'list';
       if (currentViewMode !== newMode) {
           currentViewMode = newMode;
           cambiarVista(currentViewMode);
       }
   }
   ```
   - Detecta el ancho de la ventana y decide el modo.
   - Se ejecuta al iniciar la app y en cada evento `resize`.

3. **Función `cambiarVista(mode)`**
   ```javascript
   function cambiarVista(mode) {
       const cardsView = document.getElementById('moviles-cards-view');
       const listView = document.getElementById('moviles-list-view');
       if (mode === 'cards') {
           if (cardsView) cardsView.style.display = 'block';
           if (listView) listView.style.display = 'none';
       } else {
           if (cardsView) cardsView.style.display = 'none';
           if (listView) listView.style.display = 'block';
       }
       renderizarMoviles();
   }
   ```
   - Muestra/oculta los contenedores correspondientes y vuelve a renderizar.

4. **Renderizado centralizado en `renderizarMoviles()`**
   ```javascript
   function renderizarMoviles() {
       if (currentViewMode === 'cards') {
           renderizarTarjetas();
       } else {
           renderizarLista();
       }
       actualizarContadorMoviles();
   }
   ```
   - Delegado a `renderizarTarjetas()` o `renderizarLista()` según el modo.

5. **Eliminación del toggle manual**
   - Se removió cualquier botón o control que permitiera al usuario cambiar la vista manualmente; ahora la lógica es automática y basada en el ancho de pantalla.

## Impacto en la UI
- **Móviles**: Los usuarios móviles ven tarjetas con información resumida y botones de acción; los usuarios de escritorio ven una tabla tradicional.
- **Equipos**: Se aplicó la misma lógica (el código está en `equipos.js` con funciones análogas a `handleViewMode`, `cambiarVista`, etc.).
- La experiencia es más fluida y coherente con los principios de diseño responsivo.

## Cómo probar
1. Abrir la aplicación en un navegador de escritorio.
   - Verás la vista de **lista**.
2. Redimensionar la ventana a menos de 768 px de ancho o abrir en un móvil.
   - La vista cambia automáticamente a **tarjetas**.
3. Recargar la página para confirmar que la lógica se ejecuta al iniciar (`initializeApp`).

## Comentarios futuros
- Si se requiere un toggle manual opcional, se puede re‑introducir un botón que invoque `cambiarVista('cards')` o `cambiarVista('list')`.
- La constante `768` está hard‑codeada; considerar extraerla a una variable de configuración.
