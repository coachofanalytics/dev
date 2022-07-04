# Generated by Django 3.2.6 on 2022-07-03 18:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('data', '0008_job_tracker'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dsu',
            name='trained_by',
            field=models.ForeignKey(limit_choices_to=models.Q(('is_employee', True), ('is_client', True), ('is_admin', True), ('is_superuser', True), _connector='OR'), on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
