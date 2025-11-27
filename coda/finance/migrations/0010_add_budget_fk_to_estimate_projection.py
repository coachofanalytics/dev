# Generated manually - Add missing budget ForeignKey to BudgetEstimateProjection
# The model has the field but the migration that created the model didn't include it

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0008_auto_20251118_2147'),  # Changed from 0009 to 0008 as 0009 doesn't exist in PROD
    ]

    operations = [
        migrations.AddField(
            model_name='budgetestimateprojection',
            name='budget',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='projections',
                to='finance.budget',
                null=True,  # Temporarily allow null for existing records
                blank=True
            ),
        ),
        # Note: After applying this migration, you may want to:
        # 1. Assign budgets to existing BudgetEstimateProjection records
        # 2. Create a data migration to make the field non-nullable
        # For now, we allow null to prevent breaking existing data
    ]

