# Generated manually for professional_services app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.contrib.auth import get_user_model
from shared_core.users import CustomerUser

User = get_user_model()

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
                ('title', models.CharField(max_length=25, unique=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, null=True)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.IntegerField(default=1)),
            ],
            options={
                'db_table': 'data_featuredcategory',
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='FeaturedSubCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('featuredcategory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='professional_services.featuredcategory')),
                ('order', models.IntegerField(blank=True, null=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('description', models.TextField(default='General')),
                ('title', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_featured', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'data_featuredsubcategory',
            },
        ),
        migrations.CreateModel(
            name='FeaturedActivity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('activity_name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('guiding_question', models.TextField(blank=True, null=True)),
                ('interview_question', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.IntegerField(default=1)),
            ],
            options={
                'db_table': 'data_featuredactivity',
            },
        ),
        migrations.CreateModel(
            name='ActivityLinks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('link_name', models.CharField(max_length=255, default='General')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('doc', models.FileField(default='None', upload_to='training/docs/')),
                ('link', models.CharField(max_length=1000, blank=True, null=True)),
                ('is_active', models.IntegerField(default=1)),
                ('Featuredsubcategory', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subcategorie_fetured', to='professional_services.featuredsubcategory')),
            ],
            options={
                'db_table': 'data_activitylinks',
                'verbose_name_plural': 'links',
            },
        ),
        migrations.AddField(
            model_name='featuredactivity',
            name='featuredsubcategory',
            field=models.ManyToManyField(blank=True, related_name='subcategories_fetured', to='professional_services.featuredsubcategory'),
        ),
        migrations.AddField(
            model_name='activitylinks',
            name='Activity',
            field=models.ManyToManyField(blank=True, related_name='activity_featured', to='professional_services.featuredactivity'),
        ),
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