# Generated by Django 3.2.6 on 2022-07-01 04:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicant_profile',
            name='section',
            field=models.CharField(default='A', max_length=2),
        ),
    ]