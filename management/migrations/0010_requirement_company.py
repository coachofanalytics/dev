# Generated by Django 3.2.6 on 2022-06-10 14:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0009_alter_requirement_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='requirement',
            name='company',
            field=models.CharField(default='CODA', max_length=255),
        ),
    ]