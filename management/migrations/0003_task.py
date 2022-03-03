# Generated by Django 3.2.6 on 2022-03-02 00:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('management', '0002_tag'),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group', models.CharField(default='Group A', help_text='Required', max_length=255, verbose_name='group')),
                ('activity_name', models.CharField(help_text='Required', max_length=255, verbose_name='Activity Name')),
                ('description', models.TextField(default='Add description on this activity', help_text='Not Required', verbose_name='description')),
                ('slug', models.SlugField(max_length=255)),
                ('point', models.PositiveIntegerField(error_messages={'name': {' max_length': 'Points must be less than Maximum Points'}}, help_text='Should be less than Maximum Points assigned')),
                ('mxpoint', models.PositiveIntegerField(error_messages={'name': {' max_length': 'The maximum points must be between 0 and 199'}}, help_text='Maximum 200')),
                ('mxearning', models.DecimalField(decimal_places=2, error_messages={'name': {' max_length': 'The earning must be between 0 and 4999.99'}}, help_text='Maximum 4999.99', max_digits=10)),
                ('submission', models.DateTimeField(auto_now=True, help_text='Date formart :mm/dd/yyyy', null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('featured', models.BooleanField(default=True)),
                ('category', models.ManyToManyField(blank=True, to='management.Tag')),
                ('user', models.ForeignKey(default=999, on_delete=django.db.models.deletion.RESTRICT, related_name='employee_assiged', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Activities',
                'ordering': ('-submission',),
            },
        ),
    ]
