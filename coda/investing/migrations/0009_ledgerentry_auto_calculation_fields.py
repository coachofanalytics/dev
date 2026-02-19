# Generated migration for Phase 3 - Auto-calculation tracking fields

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('investing', '0008_member_add_profile_photo'),
    ]

    operations = [
        migrations.AddField(
            model_name='ledgerentry',
            name='is_auto_calculated',
            field=models.BooleanField(default=False, help_text='Whether this value was automatically calculated from DealConfig rates'),
        ),
        migrations.AddField(
            model_name='ledgerentry',
            name='override_reason',
            field=models.TextField(blank=True, help_text='Reason for manual override of calculated value (admin only)', null=True),
        ),
        migrations.AddField(
            model_name='ledgerentry',
            name='override_by',
            field=models.ForeignKey(blank=True, help_text='User who manually overrode the calculated value', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ledger_value_overrides', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='ledgerentry',
            name='override_at',
            field=models.DateTimeField(blank=True, help_text='When the value was manually overridden', null=True),
        ),
        migrations.AlterField(
            model_name='ledgerentry',
            name='tier_metadata',
            field=models.JSONField(blank=True, default=dict, help_text='Tier-specific structured data. IN_KIND: {valuation_method}. TIME: {role_multiplier}. WORK: {deliverable_title, impact_tier}. Auto-calculation: {is_auto_calculated, calculated_value, applied_rate}.', null=True),
        ),
    ]
