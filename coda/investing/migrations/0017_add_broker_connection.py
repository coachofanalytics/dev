from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('investing', '0016_add_phase1_indexes'),
    ]

    operations = [
        migrations.CreateModel(
            name='BrokerConnection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('broker', models.CharField(choices=[('td', 'TD Ameritrade'), ('ibkr', 'Interactive Brokers'), ('tasty', 'Tastytrade'), ('schwab', 'Schwab')], max_length=20)),
                ('api_key_encrypted', models.TextField(blank=True, help_text='Encrypted API key. Set using set_api_key() helper.', null=True)),
                ('api_key_last4', models.CharField(blank=True, help_text='Last 4 characters of the API key for display.', max_length=4)),
                ('api_secret_encrypted', models.TextField(blank=True, help_text='Encrypted API secret. Set using set_api_secret() helper.', null=True)),
                ('api_secret_last4', models.CharField(blank=True, help_text='Last 4 characters of the API secret for display.', max_length=4)),
                ('last_sync', models.DateTimeField(blank=True, help_text='Timestamp of the most recent successful broker sync.', null=True)),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Optional metadata returned by the broker API (account numbers, permissions, etc).')),
                ('managed_account', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='broker_connection', to='investing.managedtradingaccount')),
            ],
            options={
                'verbose_name': 'Broker Connection',
                'verbose_name_plural': 'Broker Connections',
                'ordering': ['-updated_at'],
            },
        ),
    ]

