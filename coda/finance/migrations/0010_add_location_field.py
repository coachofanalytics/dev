# Generated migration to add location field to Transaction
# Simplified to avoid dependency issues on Heroku

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0009_add_currency_fields'),
    ]

    operations = [
        # Add location field to Transaction model
        migrations.AddField(
            model_name='transaction',
            name='location',
            field=models.CharField(
                blank=True,
                choices=[
                    ('matunda', 'Matunda Office'),
                    ('makutano', 'Makutano Office'),
                    ('nairobi_hq', 'Nairobi HQ'),
                    ('remote', 'Remote/External'),
                ],
                help_text='CODA office location (if applicable). Do NOT use for receiver names.',
                max_length=100,
                null=True,
                verbose_name='Office Location'
            ),
        ),
    ]


