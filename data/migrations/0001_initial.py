# Generated by Django 3.2.6 on 2022-09-16 11:36

import data.models
import datetime
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
            name='FeaturedCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(choices=[('Course Overview', 'Course Overview'), ('Initiation & Planning', 'Initiation & Planning'), ('Development', 'Development'), ('Testing', 'Testing'), ('Deployment', 'Deployment'), ('Other', 'Other')], default='Other', max_length=25, unique=True)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(default=datetime.datetime.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.IntegerField(default=1)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='UserLevel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(choices=[('Level A', 'Level A'), ('Level B', 'Level B'), ('Level C', 'Level C'), ('Level D', 'Level D'), ('Level E', 'Level E'), ('Other', 'Other')], default='Level A', max_length=25, unique=True)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.IntegerField(default=1)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'levels',
            },
        ),
        migrations.CreateModel(
            name='JobRole',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('upload_date', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ('category', models.CharField(choices=[('Project Management', 'Project Management'), ('Business Analyst', 'Business Analysis'), ('Quality Assurance', 'Quality Assurance'), ('User Interface', 'User Experience'), ('Reporting', 'Reporting'), ('ETL', 'ETL'), ('Database', 'Database'), ('Python', 'Python'), ('Other', 'Other')], default='Other', max_length=25)),
                ('question_type', models.CharField(choices=[('introduction', 'introduction'), ('Project Story', 'project story'), ('performance', 'performance'), ('methodology', 'methodology'), ('sdlc', 'sdlc'), ('testing', 'testing'), ('environment', 'environment'), ('resume', 'resume'), ('Other', 'Other')], default='Other', max_length=25)),
                ('doc', models.FileField(default='None', upload_to='Uploads/doc/')),
                ('videolink', models.CharField(blank=True, max_length=255, null=True)),
                ('doclink', models.CharField(blank=True, max_length=255, null=True)),
                ('desc1', models.TextField(blank=True, max_length=1000, null=True)),
                ('desc2', models.TextField(blank=True, max_length=1000, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(blank=True, limit_choices_to={'is_active': True, 'is_client': True}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='Client_Name', to=settings.AUTH_USER_MODEL, verbose_name='Client')),
            ],
            options={
                'verbose_name_plural': 'Roles',
            },
        ),
        migrations.CreateModel(
            name='Job_Tracker',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.CharField(blank=True, max_length=100, null=True)),
                ('recruiter', models.CharField(blank=True, max_length=100, null=True)),
                ('vendor_phone', models.CharField(blank=True, max_length=100, null=True)),
                ('primary_tool', models.CharField(blank=True, max_length=100, null=True)),
                ('secondary_tool', models.CharField(blank=True, max_length=100, null=True)),
                ('job_location', models.CharField(blank=True, max_length=100, null=True)),
                ('offer', models.DecimalField(decimal_places=2, error_messages={'name': {' max_length': 'The earning must be between 0 and 4999.99'}}, max_digits=10)),
                ('status', models.CharField(choices=[('screening call', 'screening call'), ('1st interview', '1st interview'), ('2nd interview', '2nd interview'), ('3rd interview', '3rd interview'), ('Other', 'Other')], default='other', max_length=25)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('updated_resume', models.FileField(default='None', upload_to='training/docs/')),
                ('is_active', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'jobs',
            },
        ),
        migrations.CreateModel(
            name='Interviews',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('upload_date', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ('category', models.CharField(choices=[('Project Management', 'Project Management'), ('Business Analyst', 'Business Analysis'), ('Quality Assurance', 'Quality Assurance'), ('User Interface', 'User Experience'), ('Reporting', 'Reporting'), ('ETL', 'ETL'), ('Database', 'Database'), ('Python', 'Python'), ('Other', 'Other')], default='Other', max_length=25)),
                ('question_type', models.CharField(choices=[('introduction', 'introduction'), ('Project Story', 'project story'), ('performance', 'performance'), ('methodology', 'methodology'), ('sdlc', 'sdlc'), ('testing', 'testing'), ('environment', 'environment'), ('resume', 'resume'), ('Other', 'Other')], default='Other', max_length=25)),
                ('doc', models.FileField(default='None', upload_to='Uploads/doc/')),
                ('link', models.CharField(blank=True, max_length=255, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('client', models.ForeignKey(default=1, on_delete=django.db.models.deletion.RESTRICT, related_name='client_assiged', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'InterviewUploaded',
            },
        ),
        migrations.CreateModel(
            name='FeaturedSubCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(default='General')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('title', models.CharField(max_length=255)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.IntegerField(default=1)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('featuredcategory', models.ForeignKey(default=data.models.FeaturedCategory.get_default_pk, on_delete=django.db.models.deletion.CASCADE, to='data.featuredcategory')),
            ],
            options={
                'verbose_name_plural': 'Subcategories',
            },
        ),
        migrations.CreateModel(
            name='FeaturedActivity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity_name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.IntegerField(default=1)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('featuredsubcategory', models.ManyToManyField(blank=True, related_name='subcategories_fetured', to='data.FeaturedSubCategory')),
            ],
            options={
                'verbose_name_plural': 'activities',
            },
        ),
        migrations.CreateModel(
            name='DSU',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('Interview', 'Interview'), ('BI Training', 'BI Training'), ('Job Support', 'Job Support'), ('Other', 'Other')], default='Other', max_length=25)),
                ('type', models.CharField(choices=[('client', 'client'), ('Staff', 'Staff'), ('Other', 'Other')], default='Other', max_length=25)),
                ('client_name', models.CharField(default='admin', max_length=255)),
                ('task', models.TextField()),
                ('plan', models.TextField()),
                ('challenge', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('uploaded', models.BooleanField(default=False)),
                ('cohort', models.PositiveIntegerField(default=1)),
                ('trained_by', models.ForeignKey(limit_choices_to=models.Q(('is_employee', True), ('is_client', True), ('is_admin', True), ('is_superuser', True), _connector='OR'), on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'DSU',
            },
        ),
        migrations.CreateModel(
            name='ActivityLinks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('link_name', models.CharField(default='General', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('doc', models.FileField(default='None', upload_to='training/docs/')),
                ('link', models.CharField(blank=True, max_length=100, null=True)),
                ('is_active', models.IntegerField(default=1)),
                ('Activity', models.ManyToManyField(blank=True, related_name='activity_featured', to='data.FeaturedActivity')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'links',
            },
        ),
    ]
