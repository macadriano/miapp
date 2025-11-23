# Deploy CRUD de Zonas

Guía para reproducir el módulo de Zonas en otros entornos (testing/preproducción/producción). Incluye dependencias, migraciones, assets y verificación funcional.

---

## 1. Requisitos previos

1. **Código fuente**: asegúrese de que `zonas/`, `static/js/zonas.js`, `static/css/zonas.css`, `templates/zonas/index.html` y modificaciones en `wayproject/settings.py`, `wayproject/urls.py`, `templates/partials/sidebar.html` estén incluidos en el paquete/branch a desplegar.
2. **PostgreSQL + PostGIS**: verificar que (a) la extensión `postgis` esté disponible en la base, y (b) el usuario de la app tenga permisos para ejecutar `CREATE EXTENSION IF NOT EXISTS postgis;`.
3. **Variables de entorno**: no se crean nuevas, pero la app debe usar el engine `django.contrib.gis.db.backends.postgis` (ya configurado).
4. **Dependencias Python**: no se agregaron librerías adicionales (Leaflet y Leaflet.draw son CDN en el frontend).

---

## 2. Migraciones

> **Nota**: si el entorno ya tiene PostGIS habilitado, la migración simplemente saltará la extensión.

1. Con el entorno virtual activo y el código actualizado, ejecutar:

```bash
python manage.py migrate zonas
```

2. Confirmar que la tabla `zonas_zona` se creó y contiene índices GIST; por ejemplo:

```sql
\d zonas_zona;
```

Esperar columnas `geom`, `centro`, `radio_metros` y los índices:
- `zonas_zona_tipo_*`
- `zonas_zona_geom_*` (GIST)

---

## 3. Archivos estáticos

Si el servidor usa `collectstatic`, ejecutar nuevamente tras subir los cambios:

```bash
python manage.py collectstatic
```

Esto publicará `static/js/zonas.js` y `static/css/zonas.css`. Asegurarse de limpiar cache en CDN/proxy si aplica.

---

## 4. Reinicio de servicios

Según la arquitectura:

```bash
# Ejemplo gunicorn
sudo systemctl restart waygps.service

# o con docker-compose
docker compose restart web
```

Verificar logs para asegurar que no hay errores de importación en `zonas`.

---

## 5. Pruebas funcionales

1. Autenticarse en la plataforma y visitar `/zonas/`.
2. Crear una zona de cada tipo:
   - Punto
   - Círculo (verificar que se exige centro+radio)
   - Polígono
   - Polilínea
3. Confirmar que:
   - El mapa muestra las geometrías con color y opacidad configurados.
   - El CRUD responde en `/zonas/api/zonas/` (GET/POST/PUT/DELETE).
   - El menú lateral incluye “Zonas” y navega correctamente.
4. Validar permisos: sólo usuarios autenticados deben acceder. Si hay control adicional por perfiles, aplicarlo en `ZonaViewSet.permission_classes`.

---

## 6. Checklist rápido

- [ ] Código actualizado (nuevos directorios + modificaciones).
- [ ] Migración `zonas/0001_initial.py` aplicada.
- [ ] `collectstatic` (si corresponde).
- [ ] Servicios reiniciados (gunicorn/uWSGI/Daphne/etc.).
- [ ] CRUD validado en interfaz y API.
- [ ] Documentación interna actualizada (enlace a este archivo).

---

## 7. Rollback

Si fuera necesario revertir:
1. Eliminar el menú o redirección hacia `/zonas/`.
2. Opcional: `python manage.py migrate zonas zero` (solo si se desea borrar la tabla; asegura respaldo antes).
3. Deployear versión anterior del código.
4. Reiniciar servicios.

---

## 8. Contacto / Mantenimiento

El módulo fue diseñado para extenderse fácilmente (p. ej., asociar zonas a móviles o crear alertas). Para evolutivos:
- Añadir permisos específicos (CustomPermission).
- Integrar con otras apps (e.g., asociar `Zona` a `Movil`).
- Implementar exportación/importación GeoJSON.

Mantener este documento actualizado con cualquier cambio estructural futuro. 

