# Generated manually on 2025-10-13 04:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('finance', '0012_merge_20251004_0055'),  # Latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='budgetrequest',
            name='approved_by',
            field=models.ForeignKey(
                blank=True,
                help_text='User who approved the request',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='approved_budget_requests',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='budgetrequest',
            name='approved_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Timestamp of approval',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='budgetrequest',
            name='rejected_by',
            field=models.ForeignKey(
                blank=True,
                help_text='User who rejected the request',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='rejected_budget_requests',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='budgetrequest',
            name='rejected_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Timestamp of rejection',
                null=True
            ),
        ),
    ]

