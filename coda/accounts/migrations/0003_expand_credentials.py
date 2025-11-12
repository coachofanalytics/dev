from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='credential',
            name='credential_type',
            field=models.CharField(choices=[('api', 'API keys / secrets'), ('oauth', 'OAuth tokens'), ('login', 'Username / password'), ('webhook', 'Webhook / endpoints'), ('other', 'Other')], default='api', max_length=32),
        ),
        migrations.AddField(
            model_name='credential',
            name='environment',
            field=models.CharField(default='prod', help_text='Environment this credential applies to (e.g. local, staging, uat, prod).', max_length=20),
        ),
        migrations.AddField(
            model_name='credential',
            name='integration_key',
            field=models.CharField(blank=True, help_text="System identifier (e.g. 'twilio', 'optionplay', 'unusual_whales').", max_length=64),
        ),
        migrations.AddField(
            model_name='credential',
            name='last_rotated_at',
            field=models.DateTimeField(blank=True, help_text='Last time secrets were rotated.', null=True),
        ),
        migrations.AddField(
            model_name='credential',
            name='metadata',
            field=models.JSONField(blank=True, default=dict, help_text='Non-sensitive metadata (account IDs, contact info, etc.).'),
        ),
        migrations.AddField(
            model_name='credential',
            name='notes',
            field=models.TextField(blank=True, help_text='Operational notes, onboarding steps, or escalation details.'),
        ),
        migrations.AddField(
            model_name='credential',
            name='payload_encrypted',
            field=models.TextField(blank=True, help_text='Encrypted JSON payload containing key/value pairs for this integration.'),
        ),
        migrations.AddField(
            model_name='credential',
            name='payload_last_updated',
            field=models.DateTimeField(blank=True, help_text='Timestamp when the payload was last rotated or updated.', null=True),
        ),
        migrations.AddField(
            model_name='credential',
            name='rotation_frequency_days',
            field=models.PositiveIntegerField(default=0, help_text='Optional reminder cadence for credential rotation. Zero disables reminders.'),
        ),
        migrations.AddConstraint(
            model_name='credential',
            constraint=models.UniqueConstraint(
                condition=~models.Q(integration_key=''),
                fields=('integration_key', 'environment'),
                name='unique_integration_environment',
            ),
        ),
        migrations.AddIndex(
            model_name='credential',
            index=models.Index(fields=['integration_key', 'environment'], name='accounts_cr_integr_3dd65a_idx'),
        ),
    ]

