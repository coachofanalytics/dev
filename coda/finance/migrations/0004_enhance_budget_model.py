"""
Migration to enhance existing Budget model with all new fields

This migration adds all the enhanced budget functionality to the existing Budget model:
- Budget type and timeframe fields
- Project information fields
- Estimation fields
- Status and approval fields
- Investment planning fields
- Tracking and control fields
- Timestamps and additional information
"""

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0003_add_missing_fields'),
        ('main', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add budget type and timeframe fields
        migrations.AddField(
            model_name='budget',
            name='budget_type',
            field=models.CharField(
                choices=[
                    ('general', 'General Budget'),
                    ('website_development', 'Website Development'),
                    ('operations', 'Operations'),
                    ('marketing', 'Marketing'),
                    ('infrastructure', 'Infrastructure'),
                    ('investment', 'Investment'),
                ],
                default='general',
                help_text='Type of budget (general, website development, etc.)',
                max_length=30
            ),
        ),
        migrations.AddField(
            model_name='budget',
            name='timeframe',
            field=models.CharField(
                choices=[
                    ('weekly', 'Weekly'),
                    ('monthly', 'Monthly'),
                    ('quarterly', 'Quarterly'),
                    ('yearly', 'Yearly'),
                    ('multi_year', 'Multi-Year (2-5 years)'),
                ],
                default='monthly',
                help_text='Budget timeframe',
                max_length=20
            ),
        ),
        
        # Add project information fields
        migrations.AddField(
            model_name='budget',
            name='project_name',
            field=models.CharField(
                blank=True,
                help_text='Project name (for website development budgets)',
                max_length=200,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='budget',
            name='project_description',
            field=models.TextField(
                blank=True,
                help_text='Detailed project description',
                max_length=2000,
                null=True
            ),
        ),
        
        # Rename item to item_name for consistency
        migrations.RenameField(
            model_name='budget',
            old_name='item',
            new_name='item_name',
        ),
        
        # Rename qty to quantity for consistency
        migrations.RenameField(
            model_name='budget',
            old_name='qty',
            new_name='quantity',
        ),
        
        # Add estimation fields
        migrations.AddField(
            model_name='budget',
            name='estimation_method',
            field=models.CharField(
                choices=[
                    ('manual', 'Manual Entry'),
                    ('transaction_based', 'Transaction History'),
                    ('coda_estimation', 'CODA Development Estimation'),
                    ('trend_analysis', 'Trend Analysis'),
                    ('ai_prediction', 'AI Prediction'),
                ],
                default='manual',
                help_text='Method used for budget estimation',
                max_length=30
            ),
        ),
        migrations.AddField(
            model_name='budget',
            name='estimated_amount',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Estimated total amount',
                max_digits=12,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='budget',
            name='estimation_confidence',
            field=models.DecimalField(
                decimal_places=2,
                default=0.0,
                help_text='Confidence level of estimation (0-100%)',
                max_digits=5,
                validators=[MinValueValidator(0), MaxValueValidator(100)]
            ),
        ),
        migrations.AddField(
            model_name='budget',
            name='estimation_source',
            field=models.CharField(
                blank=True,
                help_text='Source of estimation data',
                max_length=200,
                null=True
            ),
        ),
        
        # Add status and approval fields
        migrations.AddField(
            model_name='budget',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', 'Draft'),
                    ('submitted', 'Submitted'),
                    ('under_review', 'Under Review'),
                    ('approved', 'Approved'),
                    ('active', 'Active'),
                    ('completed', 'Completed'),
                    ('cancelled', 'Cancelled'),
                ],
                default='draft',
                help_text='Current budget status',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='budget',
            name='requires_approval',
            field=models.BooleanField(
                default=True,
                help_text='Whether this budget requires approval'
            ),
        ),
        migrations.AddField(
            model_name='budget',
            name='approval_policy',
            field=models.ForeignKey(
                blank=True,
                help_text='Approval policy for this budget',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='finance.approvalpolicy'
            ),
        ),
        migrations.AddField(
            model_name='budget',
            name='approved_by',
            field=models.ForeignKey(
                blank=True,
                help_text='User who approved this budget',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='approved_budgets',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='budget',
            name='approved_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Date when budget was approved',
                null=True
            ),
        ),
        
        # Add investment planning fields
        migrations.AddField(
            model_name='budget',
            name='is_investment',
            field=models.BooleanField(
                default=False,
                help_text='Whether this is an investment budget'
            ),
        ),
        migrations.AddField(
            model_name='budget',
            name='investment_type',
            field=models.CharField(
                blank=True,
                help_text='Type of investment (equipment, software, etc.)',
                max_length=50,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='budget',
            name='expected_roi',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Expected return on investment (%)',
                max_digits=5,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='budget',
            name='payback_period',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Expected payback period in months',
                null=True
            ),
        ),
        
        # Add tracking and control fields
        migrations.AddField(
            model_name='budget',
            name='actual_spent',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Actual amount spent',
                max_digits=12
            ),
        ),
        migrations.AddField(
            model_name='budget',
            name='variance',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Variance from budget (positive = over budget)',
                max_digits=12
            ),
        ),
        migrations.AddField(
            model_name='budget',
            name='variance_percentage',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Variance percentage',
                max_digits=5
            ),
        ),
        
        # Add additional information fields
        migrations.AddField(
            model_name='budget',
            name='notes',
            field=models.TextField(
                blank=True,
                help_text='Additional notes',
                max_length=2000,
                null=True
            ),
        ),
        
        # Add timestamps
        migrations.AddField(
            model_name='budget',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='budget',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        
        # Update receipt_link to URLField
        migrations.AlterField(
            model_name='budget',
            name='receipt_link',
            field=models.URLField(
                blank=True,
                help_text='Link to receipt or documentation',
                max_length=500,
                null=True
            ),
        ),
        
        # Add indexes for performance
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_budget_company_dept ON finance_budget (company_id, department_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_budget_company_dept;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_budget_type_timeframe ON finance_budget (budget_type, timeframe);",
            reverse_sql="DROP INDEX IF EXISTS idx_budget_type_timeframe;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_budget_status_created ON finance_budget (status, created_at);",
            reverse_sql="DROP INDEX IF EXISTS idx_budget_status_created;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_budget_dates ON finance_budget (start_date, end_date);",
            reverse_sql="DROP INDEX IF EXISTS idx_budget_dates;"
        ),
    ]
