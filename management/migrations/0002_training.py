# Generated by Django 3.2.6 on 2022-11-29 16:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('data', '__first__'),
        ('management', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Training',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.IntegerField(choices=[(1, 'Level 1'), (2, 'Level 2'), (3, 'Level 3'), (4, 'Level 4'), (5, 'Level 5')])),
                ('session', models.PositiveIntegerField()),
                ('session_link', models.CharField(blank=True, max_length=500, null=True)),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('expiration_date', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('featured', models.BooleanField(default=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='department_name', to='data.featuredcategory', verbose_name='departments')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='department_name', to='accounts.department', verbose_name='departments')),
                ('presenter', models.ForeignKey(limit_choices_to=models.Q(('is_active', True)), on_delete=django.db.models.deletion.CASCADE, related_name='employee_name', to=settings.AUTH_USER_MODEL, verbose_name='presenter name')),
                ('subcategory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='department_name', to='data.featuredsubcategory', verbose_name='Subcategory')),
                ('topic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='department_name', to='data.featuredactivity', verbose_name='departments')),
            ],
        ),
    ]
