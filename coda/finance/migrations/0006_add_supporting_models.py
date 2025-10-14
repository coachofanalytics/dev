# Generated manually to add supporting models

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0005_auto_20250926_1601'),
        ('main', '0001_initial'),
        ('accounts', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BudgetEstimationTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(max_length=1000)),
                ('budget_type', models.CharField(choices=[('general', 'General Budget'), ('website_development', 'Website Development'), ('operations', 'Operations'), ('marketing', 'Marketing'), ('infrastructure', 'Infrastructure'), ('investment', 'Investment')], max_length=30)),
                ('estimation_config', models.JSONField(help_text='JSON configuration for estimation parameters')),
                ('development_tasks', models.JSONField(default=dict, help_text='Development task configuration (createview, updateview, etc.)')),
                ('hourly_rate', models.DecimalField(decimal_places=2, default=30.0, help_text='Default hourly rate for development tasks', max_digits=10)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Budget Estimation Template',
                'verbose_name_plural': 'Budget Estimation Templates',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='MultiYearBudgetPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(max_length=2000)),
                ('start_year', models.PositiveIntegerField()),
                ('end_year', models.PositiveIntegerField()),
                ('plan_type', models.CharField(choices=[('1_year', '1 Year Plan'), ('2_year', '2 Year Plan'), ('5_year', '5 Year Plan'), ('custom', 'Custom Duration')], max_length=20)),
                ('total_investment_required', models.DecimalField(decimal_places=2, default=0, help_text='Total investment required for the plan', max_digits=15)),
                ('funding_sources', models.JSONField(default=list, help_text='List of funding sources and amounts')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('in_review', 'In Review'), ('approved', 'Approved'), ('active', 'Active'), ('completed', 'Completed')], default='draft', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='multi_year_plans', to='main.company')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_plans', to=settings.AUTH_USER_MODEL)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='multi_year_plans', to='accounts.department')),
            ],
            options={
                'verbose_name': 'Multi-Year Budget Plan',
                'verbose_name_plural': 'Multi-Year Budget Plans',
                'ordering': ['-created_at'],
            },
        ),
    ]
