# Generated by Django 3.2.6 on 2022-06-30 23:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('management', '0012_alter_requirement_assigned_to'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='employee',
            field=models.ForeignKey(default=999, limit_choices_to=models.Q(('is_employee', True), ('is_admin', True), ('is_superuser', True), _connector='OR'), on_delete=django.db.models.deletion.RESTRICT, related_name='user_assiged', to=settings.AUTH_USER_MODEL),
        ),
    ]
