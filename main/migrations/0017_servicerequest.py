from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0016_community_support'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service_type', models.CharField(choices=[('consular', 'Consular Assistance'), ('healthcare', 'Healthcare'), ('finance', 'Finance'), ('crisis', 'Crisis Support'), ('education', 'Education'), ('community', 'Community'), ('news', 'News')], default='consular', max_length=30)),
                ('full_name', models.CharField(max_length=200)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(blank=True, default='', max_length=30)),
                ('consultation_type', models.CharField(choices=[('Legal & Immigration', 'Legal & Immigration'), ('Documentation', 'Documentation'), ('Property & Estate', 'Property & Estate'), ('Other', 'Other')], max_length=50)),
                ('preferred_language', models.CharField(default='English', max_length=50)),
                ('location', models.CharField(blank=True, default='', max_length=200)),
                ('question', models.TextField(help_text="User's main consultation description")),
                ('urgency', models.CharField(choices=[('Not Urgent', 'Not Urgent'), ('Moderately Urgent', 'Moderately Urgent'), ('Very Urgent', 'Very Urgent'), ('Emergency', 'Emergency')], default='Not Urgent', max_length=30)),
                ('additional_notes', models.TextField(blank=True, default='')),
                ('status', models.CharField(choices=[('new', 'New'), ('in_review', 'In Review'), ('responded', 'Responded'), ('closed', 'Closed')], default='new', max_length=20)),
                ('admin_notes', models.TextField(blank=True, default='', help_text='Internal notes (timestamped)')),
                ('reply_message', models.TextField(blank=True, default='', help_text='Reply sent back to the user')),
                ('replied_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_to', models.ForeignKey(blank=True, help_text='Staff member assigned to handle this request', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_service_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Service Request',
                'verbose_name_plural': 'Service Requests',
                'ordering': ['-created_at'],
            },
        ),
    ]
