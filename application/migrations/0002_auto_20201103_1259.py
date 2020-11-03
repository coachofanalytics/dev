# Generated by Django 3.0.7 on 2020-11-03 18:59

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Rated',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('topic', models.CharField(default=None, max_length=100)),
                ('rating_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('punctuality', models.IntegerField(choices=[(1, 'Very Poor'), (2, 'Poor'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')])),
                ('communication', models.IntegerField(choices=[(1, 'Very Poor'), (2, 'Poor'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')])),
                ('understanding', models.IntegerField(choices=[(1, 'Very Poor'), (2, 'Poor'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')])),
            ],
        ),
        migrations.DeleteModel(
            name='Ratings',
        ),
    ]
