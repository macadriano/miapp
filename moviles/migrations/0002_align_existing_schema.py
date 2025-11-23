from django.db import migrations


def rebuild_foreign_keys(apps, schema_editor):
    statements = [
        # moviles_status → moviles (CASCADE)
        """
        ALTER TABLE moviles_status
        DROP CONSTRAINT IF EXISTS moviles_status_movil_id_aa121ac7_fk_moviles_id;
        """,
        """
        ALTER TABLE moviles_status
        ADD CONSTRAINT moviles_status_movil_id_aa121ac7_fk_moviles_id
        FOREIGN KEY (movil_id) REFERENCES moviles (id) ON DELETE CASCADE;
        """,
        # moviles_geocode → moviles (CASCADE)
        """
        ALTER TABLE moviles_geocode
        DROP CONSTRAINT IF EXISTS moviles_geocode_movil_id_b943a547_fk_moviles_id;
        """,
        """
        ALTER TABLE moviles_geocode
        ADD CONSTRAINT moviles_geocode_movil_id_b943a547_fk_moviles_id
        FOREIGN KEY (movil_id) REFERENCES moviles (id) ON DELETE CASCADE;
        """,
        # moviles_fotos → moviles (CASCADE)
        """
        ALTER TABLE moviles_fotos
        DROP CONSTRAINT IF EXISTS moviles_fotos_movil_id_46c304bc_fk_moviles_id;
        """,
        """
        ALTER TABLE moviles_fotos
        ADD CONSTRAINT moviles_fotos_movil_id_46c304bc_fk_moviles_id
        FOREIGN KEY (movil_id) REFERENCES moviles (id) ON DELETE CASCADE;
        """,
        # moviles_observaciones → moviles (CASCADE)
        """
        ALTER TABLE moviles_observaciones
        DROP CONSTRAINT IF EXISTS moviles_observaciones_movil_id_a86c5ef1_fk_moviles_id;
        """,
        """
        ALTER TABLE moviles_observaciones
        ADD CONSTRAINT moviles_observaciones_movil_id_a86c5ef1_fk_moviles_id
        FOREIGN KEY (movil_id) REFERENCES moviles (id) ON DELETE CASCADE;
        """,
        # moviles_notas → moviles (CASCADE)
        """
        ALTER TABLE moviles_notas
        DROP CONSTRAINT IF EXISTS moviles_notas_movil_id_5a5b858a_fk_moviles_id;
        """,
        """
        ALTER TABLE moviles_notas
        ADD CONSTRAINT moviles_notas_movil_id_5a5b858a_fk_moviles_id
        FOREIGN KEY (movil_id) REFERENCES moviles (id) ON DELETE CASCADE;
        """,
        # moviles_observaciones.usuario_asignado → auth_user (SET NULL)
        """
        ALTER TABLE moviles_observaciones
        DROP CONSTRAINT IF EXISTS moviles_observacione_usuario_asignado_id_81328c47_fk_auth_user;
        """,
        """
        ALTER TABLE moviles_observaciones
        ADD CONSTRAINT moviles_observacione_usuario_asignado_id_81328c47_fk_auth_user
        FOREIGN KEY (usuario_asignado_id) REFERENCES auth_user (id) ON DELETE SET NULL;
        """,
        # moviles_observaciones.usuario_creacion → auth_user (SET NULL)
        """
        ALTER TABLE moviles_observaciones
        DROP CONSTRAINT IF EXISTS moviles_observacione_usuario_creacion_id_f073dbd5_fk_auth_user;
        """,
        """
        ALTER TABLE moviles_observaciones
        ADD CONSTRAINT moviles_observacione_usuario_creacion_id_f073dbd5_fk_auth_user
        FOREIGN KEY (usuario_creacion_id) REFERENCES auth_user (id) ON DELETE SET NULL;
        """,
        # moviles_fotos.usuario_captura → auth_user (SET NULL)
        """
        ALTER TABLE moviles_fotos
        DROP CONSTRAINT IF EXISTS moviles_fotos_usuario_captura_id_3b4f9dbd_fk_auth_user_id;
        """,
        """
        ALTER TABLE moviles_fotos
        ADD CONSTRAINT moviles_fotos_usuario_captura_id_3b4f9dbd_fk_auth_user_id
        FOREIGN KEY (usuario_captura_id) REFERENCES auth_user (id) ON DELETE SET NULL;
        """,
        # moviles_fotos.observacion → moviles_observaciones (SET NULL)
        """
        ALTER TABLE moviles_fotos
        DROP CONSTRAINT IF EXISTS moviles_fotos_observacion_id_90a27161_fk_moviles_o;
        """,
        """
        ALTER TABLE moviles_fotos
        ADD CONSTRAINT moviles_fotos_observacion_id_90a27161_fk_moviles_o
        FOREIGN KEY (observacion_id) REFERENCES moviles_observaciones (id) ON DELETE SET NULL;
        """,
        # moviles_notas.usuario_actualizacion → auth_user (SET NULL)
        """
        ALTER TABLE moviles_notas
        DROP CONSTRAINT IF EXISTS moviles_notas_usuario_actualizacion_id_be2a3964_fk_auth_user_id;
        """,
        """
        ALTER TABLE moviles_notas
        ADD CONSTRAINT moviles_notas_usuario_actualizacion_id_be2a3964_fk_auth_user_id
        FOREIGN KEY (usuario_actualizacion_id) REFERENCES auth_user (id) ON DELETE SET NULL;
        """,
    ]

    with schema_editor.connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)


def rebuild_indexes(apps, schema_editor):
    statements = [
        "CREATE INDEX IF NOT EXISTS moviles_sta_estado__383ade_idx ON moviles_status (estado_conexion);",
        "CREATE INDEX IF NOT EXISTS moviles_sta_fecha_gp_b0e393_idx ON moviles_status (fecha_gps);",
        "CREATE INDEX IF NOT EXISTS moviles_sta_ultima_a_6bb179_idx ON moviles_status (ultima_actualizacion);",
        "CREATE INDEX IF NOT EXISTS moviles_geo_provin_7758aa_idx ON moviles_geocode (provincia, localidad);",
        "CREATE INDEX IF NOT EXISTS moviles_geo_fecha_g_27dbab_idx ON moviles_geocode (fecha_geocodificacion);",
        "CREATE INDEX IF NOT EXISTS moviles_obs_movil_id__0b3bc6_idx ON moviles_observaciones (movil_id, fecha_creacion);",
        "CREATE INDEX IF NOT EXISTS moviles_obs_categoria_592cc7_idx ON moviles_observaciones (categoria);",
        "CREATE INDEX IF NOT EXISTS moviles_obs_estado_c746e9_idx ON moviles_observaciones (estado);",
        "CREATE INDEX IF NOT EXISTS moviles_obs_priorida_b13c51_idx ON moviles_observaciones (prioridad);",
        "CREATE INDEX IF NOT EXISTS moviles_fot_movil_id__4bdd7d_idx ON moviles_fotos (movil_id, orden);",
        "CREATE INDEX IF NOT EXISTS moviles_fot_categoria_8198f2_idx ON moviles_fotos (categoria);",
        "CREATE INDEX IF NOT EXISTS moviles_fot_es_princi_112a67_idx ON moviles_fotos (es_principal);",
        "CREATE INDEX IF NOT EXISTS moviles_fot_fecha_cap_cb72bd_idx ON moviles_fotos (fecha_captura);",
        "CREATE UNIQUE INDEX IF NOT EXISTS unique_foto_principal_por_movil ON moviles_fotos (movil_id) WHERE es_principal;",
    ]

    with schema_editor.connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)


class Migration(migrations.Migration):

    dependencies = [
        ('moviles', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(rebuild_foreign_keys, migrations.RunPython.noop),
        migrations.RunPython(rebuild_indexes, migrations.RunPython.noop),
        migrations.RunSQL(
            "ALTER TABLE moviles ALTER COLUMN activo SET DEFAULT TRUE;",
            "ALTER TABLE moviles ALTER COLUMN activo DROP DEFAULT;",
        ),
        migrations.RunSQL(
            "ALTER TABLE moviles_status ALTER COLUMN ignicion SET DEFAULT FALSE;",
            "ALTER TABLE moviles_status ALTER COLUMN ignicion DROP DEFAULT;",
        ),
        migrations.RunSQL(
            "ALTER TABLE moviles_status ALTER COLUMN estado_conexion SET DEFAULT 'desconectado';",
            "ALTER TABLE moviles_status ALTER COLUMN estado_conexion DROP DEFAULT;",
        ),
    ]

