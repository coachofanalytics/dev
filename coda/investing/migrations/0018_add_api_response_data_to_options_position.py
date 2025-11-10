from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('investing', '0017_add_broker_connection'),
    ]

    operations = [
        migrations.AddField(
            model_name='optionsposition',
            name='api_response_data',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Raw broker or analytics API payloads associated with this position',
            ),
        ),
    ]


