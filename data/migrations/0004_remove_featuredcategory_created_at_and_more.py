# Generated by Django 4.0.3 on 2022-03-27 23:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0003_remove_featuredcategory_is_active'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='featuredcategory',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='featuredcategory',
            name='updated_at',
        ),
    ]
