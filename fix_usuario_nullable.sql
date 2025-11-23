-- Script SQL para corregir la columna usuario_id en ConversacionSofia
-- Ejecuta este script directamente en PostgreSQL

ALTER TABLE agenteIA_conversacionsofia ALTER COLUMN usuario_id DROP NOT NULL;


