from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Assets',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('category', models.CharField(blank=True, default='background', max_length=200, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('image_url', models.CharField(blank=True, max_length=1000, null=True)),
            ],
            options={
                'verbose_name_plural': 'Assets',
            },
        ),
        migrations.CreateModel(
            name='ContactMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('message', models.TextField()),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ContactUs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('phone_number', models.CharField(blank=True, max_length=15, null=True)),
                ('message', models.TextField()),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('is_resolved', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Content',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section', models.CharField(choices=[('Our Story', 'Our Story'), ('Newsletter', 'Newsletter'), ('Blog', 'Blog')], max_length=50)),
                ('title', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField()),
                ('link', models.URLField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Donation_organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('donor_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('message', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(

            name='EmergencyHelpActivation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('call_link_clicked', 'Call Link Clicked'), ('callback_requested', 'Callback Requested')], max_length=32)),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('phone', models.CharField(blank=True, max_length=32, null=True)),
                ('location', models.CharField(blank=True, max_length=255, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(

            name='EmergencyHotline',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Display label, e.g., Global Hotline', max_length=100)),
                ('number', models.CharField(help_text='E.164 like +15551234567 or local format', max_length=32)),
                ('is_active', models.BooleanField(default=True)),
                ('sort_order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Gallery_image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('image', models.ImageField(upload_to='gallery/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('event_date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='MedicalResourceInquiry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('content', models.TextField()),
                ('link', models.URLField(blank=True, null=True)),
                ('published_date', models.DateField()),
                ('is_event', models.BooleanField(default=False)),
                ('image', models.ImageField(blank=True, null=True, upload_to='news_images/')),
            ],
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('page_name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Scholarship',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('provider', models.CharField(blank=True, max_length=255, null=True)),
                ('level', models.CharField(blank=True, choices=[('Undergraduate', 'Undergraduate'), ('Masters', 'Masters'), ('PhD', 'PhD'), ('Vocational', 'Vocational')], max_length=100, null=True)),
                ('field', models.CharField(blank=True, choices=[('STEM', 'STEM'), ('Humanities', 'Humanities'), ('Business', 'Business'), ('Arts', 'Arts')], max_length=100, null=True)),
                ('location', models.CharField(blank=True, choices=[('Kenya', 'Kenya'), ('Global', 'Global'), ('UK', 'UK'), ('USA', 'USA')], max_length=200, null=True)),
                ('deadline', models.DateField(blank=True, null=True)),
                ('amount', models.CharField(blank=True, max_length=100, null=True)),
                ('status', models.CharField(blank=True, choices=[('Open', 'Open'), ('Closing Soon', 'Closing Soon'), ('Closed', 'Closed')], max_length=50, null=True)),
            ],
            options={
                'verbose_name': 'Scholarship',
                'verbose_name_plural': 'Scholarships',
                'ordering': ['deadline'],
            },
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='StaffContact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('phone', models.CharField(blank=True, max_length=32, null=True)),
                ('notify_via_email', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('leadership', models.CharField(choices=[('Local', 'Local'), ('Global', 'Global')], default='Local', max_length=50)),
                ('facebook_link', models.URLField(blank=True, null=True)),
                ('role', models.CharField(choices=[('Governor', 'Governor'), ('Deputy Governor', 'Deputy Governor'), ('Regional Coordinator', 'Regional Coordinator'), ('Team Member', 'Team Member')], max_length=50)),
                ('region', models.CharField(blank=True, max_length=255, null=True)),
                ('image', models.ImageField(upload_to='people/')),
                ('bio', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Testimonial',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('position', models.CharField(blank=True, max_length=100)),
                ('organization', models.CharField(blank=True, max_length=100)),
                ('testimonial', models.TextField()),
                ('image', models.ImageField(blank=True, upload_to='Testimonial/')),
                ('date', models.DateField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='TrainingCourse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('category', models.CharField(blank=True, max_length=150, null=True)),
                ('duration', models.CharField(blank=True, max_length=100, null=True)),
                ('format', models.CharField(blank=True, max_length=100, null=True)),
                ('enrollment', models.CharField(blank=True, max_length=100, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Training Course',
                'verbose_name_plural': 'Training Courses',
            },
        ),
        migrations.CreateModel(
            name='SubService',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subservices', to='main.service')),
            ],
        ),
        migrations.CreateModel(
            name='SafetyAlertSubscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topic', models.CharField(max_length=254)),
                ('description', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Donation_organisation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('donor_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('message', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Description',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('content', models.TextField()),
                ('page', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='descriptions', to='main.page')),
            ],
        ),
    ]
