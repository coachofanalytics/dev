"""Generated migration to add IdempotencyKey model.

This migration is added manually to ensure tests that rely on DB-backed idempotency can run.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_subscriptionplan_billing_period_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='IdempotencyKey',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(db_index=True, max_length=255, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('used', 'Used'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('response', models.JSONField(blank=True, help_text='Stored gateway response for idempotent replay', null=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
            ],
            options={
                'verbose_name': 'Idempotency Key',
                'verbose_name_plural': 'Idempotency Keys',
                'ordering': ['-created_at'],
            },
        ),
    ]
