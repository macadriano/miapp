# Generated manually to fix gps_id null constraint

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gps', '0002_alter_movil_alias_alter_movil_gps_id_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            # Permitir NULL en gps_id
            sql='ALTER TABLE moviles ALTER COLUMN gps_id DROP NOT NULL;',
            reverse_sql='ALTER TABLE moviles ALTER COLUMN gps_id SET NOT NULL;',
        ),
    ]

