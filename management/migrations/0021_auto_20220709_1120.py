# Generated by Django 3.2.6 on 2022-07-09 16:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('management', '0020_merge_20220703_2308'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tasklinks',
            name='added_by',
            field=models.ForeignKey(default=1, limit_choices_to=models.Q(('is_employee', True), ('is_admin', True), ('is_superuser', True), _connector='OR'), on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='tasklinks',
            name='link',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.RemoveField(
            model_name='tasklinks',
            name='task',
        ),
        migrations.AddField(
            model_name='tasklinks',
            name='task',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='task_featured', to='management.task'),
        ),
    ]
