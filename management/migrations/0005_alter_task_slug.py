# Generated by Django 3.2.6 on 2022-03-03 01:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0004_auto_20220302_0018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='slug',
            field=models.SlugField(blank=True, max_length=255, unique=True),
        ),
    ]