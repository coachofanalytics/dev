from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_countries.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerUser',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('email', models.CharField(max_length=100)),
                ('gender', models.IntegerField(blank=True, choices=[(1, 'Male'), (2, 'Female')], null=True)),
                ('phone', models.CharField(default='90001', max_length=100)),
                ('address', models.CharField(blank=True, max_length=100, null=True)),
                ('city', models.CharField(blank=True, max_length=100, null=True)),
                ('state', models.CharField(blank=True, max_length=100, null=True)),
                ('country', django_countries.fields.CountryField(blank=True, max_length=2, null=True)),
                ('category', models.IntegerField(choices=[(1, 'Applicant Or Job Applicant'), (2, 'Coda Staff Member'), (3, 'Client Or Customer Or Student')], default=999)),
                ('sub_category', models.IntegerField(blank=True, choices=[(0, 'No Selection'), (1, 'Job Support'), (2, 'Student'), (3, 'Full Time'), (4, 'Contractual'), (5, 'Part Time')], null=True)),
                ('is_admin', models.BooleanField(default=False, verbose_name='Is admin')),
                ('is_employee', models.BooleanField(default=False, verbose_name='Is employee')),
                ('is_client', models.BooleanField(default=False, verbose_name='Is Client')),
                ('is_applicant', models.BooleanField(default=False, verbose_name='Is applicant')),
                ('resume_file', models.FileField(blank=True, null=True, upload_to='resumes/doc/')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'ordering': ['date_joined'],
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Tracker',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('Job_Support', 'Job_Support'), ('Interview', 'Interview'), ('Training', 'Training'), ('Mentorship', 'Mentorship'), ('Any Other', 'Other')], max_length=25)),
                ('task', models.CharField(choices=[('reporting', 'reporting'), ('database', 'database'), ('Business Analysis', 'Business Analysis'), ('Data Cleaning', 'Data Cleaning'), ('Any Other', 'Other')], max_length=25)),
                ('plan', models.CharField(default='B', help_text='Required', max_length=255, verbose_name='group')),
                ('employee', models.CharField(default='CODA', help_text='Required', max_length=255, verbose_name='Employee Name')),
                ('login_date', models.DateTimeField(auto_now_add=True)),
                ('start_time', models.TimeField(auto_now_add=True)),
                ('duration', models.IntegerField(choices=[(1, 'One Hour'), (2, 'Two Hours'), (3, 'Three Hours'), (4, 'Four Hours'), (5, 'Five Hours'), (8, 'Eight Hours'), (10, 'Ten Hours')], default=2)),
                ('time', models.PositiveIntegerField(default=120, error_messages={'name': {' max_length': 'The maximum hours must be between 0 and 199'}}, help_text='Maximum 200')),
                ('author', models.ForeignKey(limit_choices_to={'is_client': True}, on_delete=django.db.models.deletion.CASCADE, related_name='author', to=settings.AUTH_USER_MODEL, verbose_name='Client Name')),
            ],
            options={
                'ordering': ['login_date'],
            },
        ),
    ]
