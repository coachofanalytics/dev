from django.db import migrations, models
from datetime import timedelta


def set_auto_approve_dates(apps, schema_editor):
    PositionBatch = apps.get_model('investing', 'PositionBatch')
    for batch in PositionBatch.objects.all():
        if batch.auto_approve_at is None and batch.created_date:
            batch.auto_approve_at = batch.created_date + timedelta(hours=3)
            batch.save(update_fields=['auto_approve_at'])


class Migration(migrations.Migration):

    dependencies = [
        ('investing', '0018_add_api_response_data_to_options_position'),
    ]

    operations = [
        migrations.AddField(
            model_name='positionbatch',
            name='auto_approve_at',
            field=models.DateTimeField(blank=True, null=True, help_text='If the client does not respond by this time (~3 hours), the batch is auto-approved and awaits trader execution'),
        ),
        migrations.AddField(
            model_name='positionbatch',
            name='auto_approved_at',
            field=models.DateTimeField(blank=True, null=True, help_text='Timestamp when the system auto-approved this batch after client timeout'),
        ),
        migrations.AddField(
            model_name='optionsposition',
            name='auto_approved',
            field=models.BooleanField(default=False, help_text='Set when the client approval window expired and the system auto-approved the trade. Trader must still enter execution details.'),
        ),
        migrations.AddField(
            model_name='optionsposition',
            name='auto_approved_at',
            field=models.DateTimeField(blank=True, null=True, help_text='When the system auto-approved this position after client timeout.'),
        ),
        migrations.AddField(
            model_name='brokerconnection',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Disable to prevent sync jobs from using this broker connection.'),
        ),
        migrations.AddField(
            model_name='brokerconnection',
            name='is_featured',
            field=models.BooleanField(default=False, help_text='Flag for highlighting primary broker integrations in the UI.'),
        ),
        migrations.RunPython(set_auto_approve_dates, migrations.RunPython.noop),
    ]

