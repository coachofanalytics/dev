# Generated manually for Training_Responses model

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('professional_services', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Training_Responses',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=1000, null=True)),
                ('response', models.CharField(blank=True, max_length=1000, null=True)),
                ('question', models.CharField(blank=True, max_length=1055, null=True)),
                ('question1', models.TextField(default='Write Your Reponse')),
                ('is_active', models.BooleanField(default=True)),
                ('review', models.TextField(blank=True, null=True)),
                ('link', models.CharField(blank=True, max_length=500, null=True)),
                ('comment', models.TextField()),
                ('score', models.PositiveIntegerField(blank=True, null=True)),
                ('upload_date', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ('first_displayed_at', models.DateTimeField(blank=True, null=True)),
                ('seen_notifications', models.BooleanField(default=False)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_assigned', to='accounts.customeruser')),
            ],
            options={
                'db_table': 'data_training_responses',
                'verbose_name_plural': 'Training Responses',
            },
        ),
    ]