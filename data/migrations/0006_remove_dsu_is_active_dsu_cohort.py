# Generated by Django 4.0.3 on 2022-04-07 18:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0005_dsu_type_alter_dsu_category'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dsu',
            name='is_active',
        ),
        migrations.AddField(
            model_name='dsu',
            name='cohort',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
