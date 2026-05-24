import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_communitymember_communitypost_eventcalendar_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Doctor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('title', models.CharField(max_length=200)),
                ('specialty', models.CharField(max_length=200)),
                ('categories', models.JSONField(default=list)),
                ('location_city', models.CharField(max_length=200)),
                ('location_country', models.CharField(max_length=200)),
                ('clinic_name', models.CharField(blank=True, max_length=200)),
                ('languages', models.JSONField(default=list)),
                ('telehealth', models.BooleanField(default=False)),
                ('available', models.BooleanField(default=True)),
                ('rating', models.DecimalField(decimal_places=1, default=4.5, max_digits=3)),
                ('review_count', models.PositiveIntegerField(default=0)),
                ('bio', models.TextField()),
                ('education', models.JSONField(default=list)),
                ('avatar_color', models.CharField(default='#4A90D9', max_length=7)),
                ('avatar_initials', models.CharField(blank=True, max_length=3)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-rating', '-review_count'],
            },
        ),
        migrations.CreateModel(
            name='AppointmentRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=200)),
                ('email', models.EmailField(max_length=254)),
                ('preferred_date', models.DateField()),
                ('preferred_time', models.CharField(choices=[('morning', 'Morning (8am-12pm)'), ('afternoon', 'Afternoon (12pm-5pm)'), ('evening', 'Evening (5pm-8pm)')], max_length=20)),
                ('reason', models.TextField()),
                ('status', models.CharField(choices=[('new', 'New'), ('contacted', 'Contacted'), ('confirmed', 'Confirmed'), ('declined', 'Declined')], default='new', max_length=20)),
                ('honeypot', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appointment_requests', to='main.doctor')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MedicalResourceInquiry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='InsurancePlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider_name', models.CharField(max_length=100)),
                ('plan_name', models.CharField(max_length=100)),
                ('network', models.CharField(max_length=100)),
                ('max_benefit', models.CharField(max_length=50)),
                ('evacuation', models.CharField(max_length=50)),
                ('score', models.DecimalField(decimal_places=1, max_digits=3)),
                ('is_active', models.BooleanField(default=True)),
                ('display_order', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Insurance Plan',
                'verbose_name_plural': 'Insurance Plans',
                'ordering': ['display_order', '-score'],
            },
        ),
        migrations.CreateModel(
            name='AIRecommendationRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('age_bracket', models.CharField(choices=[('young', '18 - 30 Years'), ('mid', '31 - 55 Years'), ('senior', '56+ Years')], max_length=20)),
                ('residence', models.CharField(choices=[('usa', 'USA / Canada'), ('europe', 'Europe / UK'), ('other', 'Rest of World')], max_length=20)),
                ('priority', models.CharField(choices=[('budget', 'Cost Savings'), ('comprehensive', 'Full Coverage'), ('emergency', 'Emergency Only')], max_length=20)),
                ('recommendation_text', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recommended_plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.insuranceplan')),
            ],
            options={
                'verbose_name': 'AI Recommendation Rule',
                'verbose_name_plural': 'AI Recommendation Rules',
                'unique_together': {('age_bracket', 'residence', 'priority')},
            },
        ),
        migrations.CreateModel(
            name='ExpertInquiry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=200)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('question', models.TextField()),
                ('is_contacted', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('first_response_time', models.DateTimeField(blank=True, help_text='When this inquiry was first responded to', null=True)),
                ('resolution_time', models.DateTimeField(blank=True, help_text='When this inquiry was resolved', null=True)),
                ('sla_deadline', models.DateTimeField(blank=True, help_text='SLA deadline based on priority', null=True)),
                ('escalated', models.BooleanField(default=False, help_text='Whether this inquiry has been escalated')),
                ('escalated_at', models.DateTimeField(blank=True, null=True)),
                ('interested_plan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.insuranceplan')),
                ('assigned_to', models.ForeignKey(blank=True, help_text='Agent assigned to this inquiry', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_inquiries', to=settings.AUTH_USER_MODEL)),
                ('escalated_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='escalated_inquiries', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Expert Inquiry',
                'verbose_name_plural': 'Expert Inquiries',
                'ordering': ['-created_at'],
            },
        ),
    ]
