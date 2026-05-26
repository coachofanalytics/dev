import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Opportunity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('contact', models.CharField(blank=True, max_length=255, null=True)),
                ('rejection_reason', models.TextField(blank=True, null=True)),
                ('last_notified_at', models.DateTimeField(blank=True, null=True)),
                ('is_suspicious', models.BooleanField(default=False)),
                ('type', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='NewsLetterSubscriber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('subscribed_at', models.DateTimeField(auto_now_add=True)),
                ('verification_token', models.UUIDField(default=uuid.uuid4, editable=False)),
            ],
        ),
    ]
