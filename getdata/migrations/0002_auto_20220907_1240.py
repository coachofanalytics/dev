# Generated by Django 3.2.6 on 2022-09-07 12:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('getdata', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cashappmail',
            name='from_mail',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='cashappmail',
            name='to_mail',
            field=models.CharField(max_length=100),
        ),
    ]
