# Generated manually for budget item library
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0007_add_vendor_and_location'),
    ]

    operations = [
        migrations.CreateModel(
            name='BudgetItemLibrary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_name', models.CharField(help_text="Name of the budget item (e.g., 'Safaricom internet subscription')", max_length=200)),
                ('description', models.TextField(blank=True, help_text='Detailed description of the item')),
                ('typical_amount', models.DecimalField(blank=True, decimal_places=2, help_text='Typical/average amount based on historical data', max_digits=12, null=True)),
                ('unit_type', models.CharField(blank=True, default='each', help_text='Unit of measurement (each, month, year, etc.)', max_length=50)),
                ('usage_count', models.IntegerField(default=0, help_text='Number of times this item has been used (for sorting)')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this item is active and available for selection')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(help_text='Budget category this item belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='items', to='finance.budgetcategory')),
                ('subcategory', models.ForeignKey(help_text='Budget subcategory this item belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='items', to='finance.budgetsubcategory')),
            ],
            options={
                'verbose_name': 'Budget Item',
                'verbose_name_plural': 'Budget Item Library',
                'ordering': ['-usage_count', 'item_name'],
                'unique_together': {('category', 'subcategory', 'item_name')},
            },
        ),
    ]

