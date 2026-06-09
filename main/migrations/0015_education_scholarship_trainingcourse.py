import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0014_crisis_safety_alert_subscription'),
    ]

    operations = [
        migrations.CreateModel(
            name='Scholarship',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_value', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('amount_currency', models.CharField(choices=[('USD', 'US Dollar ($)'), ('KES', 'Kenyan Shilling (Ksh)'), ('EUR', 'Euro (€)'), ('GBP', 'British Pound (£)')], default='USD', max_length=3)),
                ('amount_description', models.CharField(blank=True, help_text="E.g., 'Full tuition', 'Partial funding', etc.", max_length=100)),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(blank=True, unique=True)),
                ('provider', models.CharField(default='', max_length=255)),
                ('level', models.CharField(choices=[('Undergraduate', 'Undergraduate'), ('Masters', 'Masters'), ('PhD', 'PhD'), ('Vocational', 'Vocational')], default='Undergraduate', max_length=100)),
                ('field', models.CharField(choices=[('STEM', 'STEM'), ('Humanities', 'Humanities'), ('Business', 'Business'), ('Arts', 'Arts')], default='STEM', max_length=100)),
                ('location', models.CharField(choices=[('Kenya', 'Kenya'), ('Global', 'Global'), ('UK', 'UK'), ('USA', 'USA')], default='Global', max_length=200)),
                ('deadline', models.DateField(default=django.utils.timezone.now)),
                ('status', models.CharField(choices=[('Open', 'Open'), ('Closing Soon', 'Closing Soon'), ('Closed', 'Closed')], default='Open', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['deadline'],
            },
        ),
        migrations.CreateModel(
            name='TrainingCourse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(blank=True, unique=True)),
                ('course_code', models.CharField(blank=True, help_text='e.g., CS101', max_length=20)),
                ('category', models.CharField(choices=[('Tech', 'Tech'), ('Business', 'Business'), ('Art', 'Art'), ('Health', 'Health')], default='Tech', max_length=50)),
                ('description', models.TextField(blank=True, help_text='Brief course description')),
                ('duration', models.CharField(default='Self-paced', help_text="e.g., '6 weeks', '3 months', 'Self-paced'", max_length=100)),
                ('format', models.CharField(choices=[('Online', 'Online'), ('Offline', 'Offline'), ('Hybrid', 'Hybrid')], default='Online', max_length=50)),
                ('enrollment', models.CharField(choices=[('Open', 'Open'), ('Closed', 'Closed'), ('Closing Soon', 'Closing Soon')], default='Open', max_length=50)),
                ('max_students', models.PositiveIntegerField(blank=True, help_text='Maximum capacity', null=True)),
                ('enrolled_students', models.PositiveIntegerField(default=0, editable=False)),
                ('start_date', models.DateField(default=django.utils.timezone.now)),
                ('end_date', models.DateField(blank=True, help_text='Optional: Course end date', null=True)),
                ('status', models.CharField(choices=[('Upcoming', 'Upcoming'), ('Ongoing', 'Ongoing'), ('Completed', 'Completed')], default='Upcoming', editable=False, max_length=20)),
                ('instructor', models.CharField(blank=True, max_length=255)),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('certificate_offered', models.BooleanField(default=False)),
                ('syllabus', models.TextField(blank=True, help_text='Course outline/syllabus')),
                ('prerequisites', models.TextField(blank=True, help_text='Required knowledge or courses')),
                ('image', models.ImageField(blank=True, null=True, upload_to='courses/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Training Course',
                'verbose_name_plural': 'Training Courses',
                'ordering': ['start_date'],
                'indexes': [
                    models.Index(fields=['status'], name='main_trainin_status_idx'),
                    models.Index(fields=['category'], name='main_trainin_categor_idx'),
                    models.Index(fields=['start_date'], name='main_trainin_start_d_idx'),
                ],
            },
        ),
    ]
