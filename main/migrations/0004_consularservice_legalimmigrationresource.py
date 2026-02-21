# Generated migration for ConsularService and LegalImmigrationResource moved from communities to main

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_rename_emergencyhotline_emergencyhotlines'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConsularService',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('service_type', models.CharField(choices=[('government', 'Government Agency'), ('legal_aid', 'Legal Aid Organization'), ('nonprofit', 'Non-Profit Organization'), ('consultation', 'Consultation Service')], max_length=20)),
                ('description', models.TextField()),
                ('website', models.URLField(blank=True, null=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('address', models.TextField(blank=True, null=True)),
                ('country_coverage', models.CharField(help_text='e.g., USA, Mexico, Global', max_length=255)),
                ('services_offered', models.TextField(help_text='Comma-separated list of services')),
                ('is_featured', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Consular Services',
                'ordering': ['-is_featured', '-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='LegalImmigrationResource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('category', models.CharField(choices=[('visa', 'Visa Information'), ('green_card', 'Green Card & Permanent Residency'), ('citizenship', 'Citizenship & Naturalization'), ('employment', 'Employment Authorization'), ('asylum', 'Asylum & Refugee'), ('deportation', 'Deportation Defense'), ('family', 'Family Sponsorship'), ('rights', 'Legal Rights')], max_length=20)),
                ('content', models.TextField()),
                ('external_url', models.URLField(blank=True, null=True)),
                ('keywords', models.CharField(blank=True, help_text='Comma-separated keywords for search', max_length=255)),
                ('is_critical', models.BooleanField(default=False, help_text='Mark as critical information')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('related_service', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resources', to='main.consularservice')),
            ],
            options={
                'verbose_name_plural': 'Legal Immigration Resources',
                'ordering': ['-is_critical', '-updated_at'],
            },
        ),
    ]
