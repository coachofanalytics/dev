# Generated by Django 3.2.6 on 2022-09-19 21:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='featuredactivity',
            old_name='name',
            new_name='activity_name',
        ),
    ]
