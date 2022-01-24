# Generated by Django 3.2.6 on 2022-01-24 07:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='gender',
            field=models.IntegerField(choices=[(1, 'Male'), (2, 'Female')], default=9999),
        ),
        migrations.AddField(
            model_name='application',
            name='type',
            field=models.CharField(choices=[('Applicant', 'Applicant'), ('Other', 'Other')], default='Other', max_length=25),
        ),
    ]