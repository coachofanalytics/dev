import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(blank=True, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='NewsArticle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(blank=True, max_length=255, unique=True)),
                ('author', models.CharField(max_length=100)),
                ('featured_image', models.ImageField(upload_to='news_images/')),
                ('content', models.TextField()),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('PUBLISHED', 'Published')], default='DRAFT', max_length=10)),
                ('ai_summary', models.TextField(blank=True, help_text='AI_generated summary for index page')),
                ('is_breaking', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('views', models.PositiveBigIntegerField(default=0)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='articles', to='main.category')),
            ],
        ),
        migrations.CreateModel(
            name='Subscriber',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('conf_token', models.CharField(default=uuid.uuid4, editable=False, max_length=100)),
                ('confirmed', models.BooleanField(default=False)),
                ('subscribed_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Subscribers',
                'ordering': ['-subscribed_at'],
            },
        ),
    ]
