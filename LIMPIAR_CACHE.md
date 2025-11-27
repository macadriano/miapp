# Instrucciones para limpiar caché y ver cambios

## Pasos para asegurar que se vean los cambios:

1. **Detener el servidor Django** (Ctrl+C en la terminal donde corre)

2. **Limpiar caché de Python:**
   ```powershell
   Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force
   ```

3. **Limpiar archivos estáticos compilados:**
   ```powershell
   python manage.py collectstatic --noinput --clear
   ```

4. **Limpiar caché del navegador:**
   - Presiona `Ctrl + Shift + Delete`
   - O presiona `Ctrl + F5` para recarga forzada
   - O abre en modo incógnito (Ctrl + Shift + N)

5. **Reiniciar el servidor Django:**
   ```powershell
   python manage.py runserver
   ```

6. **Verificar que estás en el archivo correcto:**
   - Deberías ver el título: "⚠️⚠️⚠️ ARCHIVO CORRECTO - WayGPS Móviles ⚠️⚠️⚠️"
   - Deberías ver el mensaje rojo/amarillo en la página
   - Deberías ver "⚠️ MÓVILES - ARCHIVO CORRECTO ⚠️" en el header

## Si aún no ves los cambios:

1. Verifica que el archivo `templates/moviles/index.html` tenga el mensaje grotesco
2. Verifica que no haya otro template con el mismo nombre
3. Reinicia completamente el servidor (cerrar y abrir de nuevo)
4. Verifica que no estés usando un proxy o CDN que cachee

