from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('main', '0001_squashed_0008_merge_20260218_1759'),
    ]

    operations = [
        # Remove the problematic models from Django's state
        migrations.RunSQL(
            sql="SELECT 1;",  # No-op SQL
            reverse_sql=migrations.RunSQL.noop,
            state_operations=[
                migrations.DeleteModel(
                    name='EmergencyHelpActivation',
                ),
                migrations.DeleteModel(
                    name='EmergencyHelpActivations',
                ),
                migrations.DeleteModel(
                    name='EmergencyHot',
                ),
            ]
        ),
    ]