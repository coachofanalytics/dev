# Generated by Django 3.0.7 on 2020-10-27 19:22

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Rating',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('topic', models.CharField(default=None, max_length=100)),
                ('rating_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('punctuality', models.IntegerField(choices=[(1, 'Low'), (2, 'Medium'), (3, 'High'), (4, 'Highest'), (5, 'Excellent')])),
                ('communication', models.IntegerField(choices=[(1, 'Low'), (2, 'Medium'), (3, 'High'), (4, 'Highest'), (5, 'Excellent')])),
                ('understanding', models.IntegerField(choices=[(1, 'Low'), (2, 'Medium'), (3, 'High'), (4, 'Highest'), (5, 'Excellent')])),
            ],
        ),
        migrations.AddField(
            model_name='application',
            name='application_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.CreateModel(
            name='InteviewUpload',
            fields=[
                ('Id', models.AutoField(primary_key=True, serialize=False)),
                ('Interviewid', models.PositiveIntegerField(null=True)),
                ('interviewppt', models.FileField(upload_to='interviewppt/ppt/')),
                ('interviewtab', models.FileField(default=None, upload_to='interviewtab/tab/')),
                ('interviewalteryx', models.FileField(upload_to='interviewalteryx/alteryx/')),
                ('interviewdb', models.FileField(default=None, upload_to='interviewdb/dba/')),
                ('interviewother', models.FileField(default=None, upload_to='interviewother/general/')),
                ('Applicant', models.ManyToManyField(to='application.Application')),
            ],
        ),
    ]
