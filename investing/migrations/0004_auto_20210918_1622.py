# Generated by Django 3.2.6 on 2021-09-18 21:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('investing', '0003_auto_20210226_2335'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='document',
            options={'verbose_name_plural': 'Documents'},
        ),
        migrations.AlterModelOptions(
            name='uploads',
            options={'verbose_name_plural': 'Uploads'},
        ),
    ]
