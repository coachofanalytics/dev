# Generated by Django 3.2.6 on 2022-07-31 02:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_alter_tracker_employee'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tracker',
            name='employee',
            field=models.ForeignKey(default=1, limit_choices_to=models.Q(('is_active', True)), on_delete=django.db.models.deletion.RESTRICT, related_name='employee', to=settings.AUTH_USER_MODEL),
        ),
    ]
