INSERT INTO moviles_status (movil_id, ultimo_lat, ultimo_lon, ultima_velocidad_kmh, estado_conexion, fecha_gps, fecha_recepcion, ultima_actualizacion)
VALUES
    ((SELECT id FROM moviles WHERE alias='CAMION3'),  -34.5880, -58.4300, 35.0, 'conectado', NOW(), NOW(), NOW()),
    ((SELECT id FROM moviles WHERE alias='CAMION4'),  -34.6180, -58.4450, 28.0, 'conectado', NOW(), NOW(), NOW()),
    ((SELECT id FROM moviles WHERE alias='CAMION5'),  -34.6330, -58.4560, 45.0, 'conectado', NOW(), NOW(), NOW()),
    ((SELECT id FROM moviles WHERE alias='CAMION6'),  -34.6480, -58.3780, 22.0, 'conectado', NOW(), NOW(), NOW()),
    ((SELECT id FROM moviles WHERE alias='CAMION7'),  -34.6620, -58.3640, 18.0, 'conectado', NOW(), NOW(), NOW()),
    ((SELECT id FROM moviles WHERE alias='CAMION8'),  -34.6990, -58.3920, 32.0, 'conectado', NOW(), NOW(), NOW()),
    ((SELECT id FROM moviles WHERE alias='CAMION9'),  -34.7600, -58.4010, 40.0, 'conectado', NOW(), NOW(), NOW()),
    ((SELECT id FROM moviles WHERE alias='CAMION10'), -34.7200, -58.2520, 27.0, 'conectado', NOW(), NOW(), NOW()),
    ((SELECT id FROM moviles WHERE alias='CAMION11'), -34.4260, -58.5760, 33.0, 'conectado', NOW(), NOW(), NOW()),
    ((SELECT id FROM moviles WHERE alias='CAMION12'), -34.4720, -58.5120, 25.0, 'conectado', NOW(), NOW(), NOW()),
    ((SELECT id FROM moviles WHERE alias='CAMION13'), -34.6530, -58.6190, 30.0, 'conectado', NOW(), NOW(), NOW())
ON CONFLICT (movil_id) DO UPDATE SET
    ultimo_lat = EXCLUDED.ultimo_lat,
    ultimo_lon = EXCLUDED.ultimo_lon,
    ultima_velocidad_kmh = EXCLUDED.ultima_velocidad_kmh,
    estado_conexion = EXCLUDED.estado_conexion,
    fecha_gps = EXCLUDED.fecha_gps,
    fecha_recepcion = EXCLUDED.fecha_recepcion,
    ultima_actualizacion = EXCLUDED.ultima_actualizacion;
