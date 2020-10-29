# Generated by Django 3.0.7 on 2020-10-27 19:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0002_auto_20201027_1422'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rating',
            name='communication',
            field=models.IntegerField(choices=[(1, 'Very Poor'), (2, 'Poor'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')]),
        ),
        migrations.AlterField(
            model_name='rating',
            name='punctuality',
            field=models.IntegerField(choices=[(1, 'Very Poor'), (2, 'Poor'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')]),
        ),
        migrations.AlterField(
            model_name='rating',
            name='understanding',
            field=models.IntegerField(choices=[(1, 'Very Poor'), (2, 'Poor'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')]),
        ),
    ]
