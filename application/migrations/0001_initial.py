# Generated by Django 3.2.6 on 2021-10-04 18:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=100)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('application_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('phone', models.CharField(blank=True, max_length=100, null=True)),
                ('country', models.CharField(blank=True, max_length=100, null=True)),
                ('resume', models.FileField(upload_to='resumes/doc/')),
            ],
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('topic', models.CharField(default=None, max_length=100)),
                ('employee_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('punctuality', models.IntegerField(choices=[(1, 'Very Poor'), (2, 'Poor'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')])),
                ('communication', models.IntegerField(choices=[(1, 'Very Poor'), (2, 'Poor'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')])),
                ('understanding', models.IntegerField(choices=[(1, 'Very Poor'), (2, 'Poor'), (3, 'Good'), (4, 'Very Good'), (5, 'Excellent')])),
                ('rated_by', models.CharField(default='CEO', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Policy',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('first_name', models.CharField(blank=True, max_length=100, null=True)),
                ('last_name', models.CharField(blank=True, max_length=100, null=True)),
                ('upload_date', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ('policy_type', models.CharField(choices=[('Leave', 'Leave'), ('Working Hours', 'Working Hours'), ('Working Days', 'Working Days'), ('Unpaid Training', 'Unpaid_Training'), ('Location', 'Location'), ('Other', 'Other')], default='Other', max_length=25)),
                ('description', models.TextField()),
                ('policy_doc', models.FileField(blank=True, default=None, null=True, upload_to='policy/doc/')),
            ],
        ),
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
        migrations.CreateModel(
            name='Reporting',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('first_name', models.CharField(blank=True, max_length=100, null=True)),
                ('last_name', models.CharField(blank=True, max_length=100, null=True)),
                ('interview_type', models.CharField(choices=[('Internal Interview', 'Internal Interview'), ('First Interview', 'First Interview'), ('Second Interview', 'Second Interview'), ('Third Interview', 'Third Interview')], max_length=25)),
                ('gender', models.CharField(blank=True, choices=[('Male', 'Male'), ('Female', 'Female')], max_length=25, null=True)),
                ('method', models.CharField(blank=True, choices=[('Direct', 'Direct'), ('Indirect', 'Indirect')], max_length=25, null=True)),
                ('reporting_date', models.DateTimeField(blank=True, null=True, verbose_name='Reporting Date(mm/dd/yyyy)')),
                ('update_date', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ('comment', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='InteviewUploads',
            fields=[
                ('Id', models.AutoField(primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=30, null=True)),
                ('upload_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('ppt', models.FileField(default=None, upload_to='Powerpoints/doc/')),
                ('report', models.FileField(default=None, upload_to='Reports/doc/')),
                ('workflow', models.FileField(default=None, upload_to='Workflows/doc/')),
                ('proc', models.FileField(default=None, upload_to='Procedures/doc/')),
                ('other', models.FileField(default=None, upload_to='Others/doc/')),
                ('Applicant', models.ManyToManyField(to='application.Application')),
            ],
        ),
        migrations.CreateModel(
            name='FirstUpload',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=100)),
                ('first_name', models.CharField(blank=True, max_length=100, null=True)),
                ('last_name', models.CharField(blank=True, max_length=100, null=True)),
                ('upload_date', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ('ppt', models.FileField(upload_to='Powerpoints/doc/')),
                ('report', models.FileField(blank=True, null=True, upload_to='Reports/doc/')),
                ('workflow', models.FileField(blank=True, null=True, upload_to='Workflows/doc/')),
                ('proc', models.FileField(blank=True, null=True, upload_to='Procedures/doc/')),
                ('other', models.FileField(default='None', upload_to='Others/doc/')),
                ('Applicant', models.ManyToManyField(to='application.Application')),
            ],
        ),
        migrations.CreateModel(
            name='Applicant_Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(default='default.jpg', upload_to='applicant_profile_pics')),
                ('applicant', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
