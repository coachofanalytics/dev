"""
Migration to add Vendor models and location field to Transaction

Changes:
1. Add Vendor model for standardized receiver names
2. Add VendorAlias model for name variations
3. Add VendorCategory model for category patterns
4. Add location field to Transaction model (separate office locations from receivers)
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0009_add_currency_fields'),
    ]

    operations = [
        # Create Vendor model
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Standardized vendor/receiver name', max_length=200, unique=True)),
                ('vendor_type', models.CharField(choices=[('employee', 'Employee'), ('supplier', 'Supplier/Vendor'), ('utility', 'Utility Company'), ('service_provider', 'Service Provider'), ('government', 'Government Agency'), ('contractor', 'Contractor'), ('other', 'Other')], help_text='Type of vendor', max_length=30)),
                ('phone', models.CharField(blank=True, max_length=50, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('total_transactions', models.IntegerField(default=0, help_text='Total number of transactions with this vendor')),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, help_text='Total amount transacted with this vendor', max_digits=15)),
                ('average_transaction', models.DecimalField(decimal_places=2, default=0, help_text='Average transaction amount', max_digits=15)),
                ('is_active', models.BooleanField(default=True, help_text='Is this vendor still active?')),
                ('notes', models.TextField(blank=True, help_text='Additional notes about this vendor', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('default_category', models.ForeignKey(blank=True, help_text='Suggested category for transactions with this vendor', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='default_vendors', to='finance.budgetcategory')),
            ],
            options={
                'verbose_name': 'Vendor',
                'verbose_name_plural': 'Vendors',
                'ordering': ['name'],
            },
        ),
        
        # Create VendorAlias model
        migrations.CreateModel(
            name='VendorAlias',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alias', models.CharField(help_text='Alternative spelling/name', max_length=200, unique=True)),
                ('confidence', models.CharField(choices=[('exact', 'Exact Match'), ('high', 'High Confidence'), ('medium', 'Medium Confidence'), ('low', 'Low Confidence - Review')], default='high', help_text='Confidence level for this alias match', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('vendor', models.ForeignKey(help_text='The standardized vendor this alias refers to', on_delete=django.db.models.deletion.CASCADE, related_name='aliases', to='finance.vendor')),
            ],
            options={
                'verbose_name': 'Vendor Alias',
                'verbose_name_plural': 'Vendor Aliases',
                'ordering': ['vendor', 'alias'],
            },
        ),
        
        # Create VendorCategory model
        migrations.CreateModel(
            name='VendorCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_count', models.IntegerField(default=0, help_text='Number of transactions in this category')),
                ('percentage', models.DecimalField(decimal_places=2, default=0, help_text="Percentage of vendor's transactions in this category", max_digits=5)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='finance.budgetcategory')),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='category_patterns', to='finance.vendor')),
            ],
            options={
                'verbose_name': 'Vendor Category Pattern',
                'verbose_name_plural': 'Vendor Category Patterns',
                'ordering': ['-transaction_count'],
                'unique_together': {('vendor', 'category')},
            },
        ),
        
        # Add location field to Transaction model
        migrations.AddField(
            model_name='transaction',
            name='location',
            field=models.CharField(
                blank=True,
                choices=[
                    ('matunda', 'Matunda Office'),
                    ('makutano', 'Makutano Office'),
                    ('nairobi_hq', 'Nairobi HQ'),
                    ('remote', 'Remote/External'),
                ],
                help_text='CODA office location (if applicable). Do NOT use for receiver names.',
                max_length=100,
                null=True,
                verbose_name='Office Location'
            ),
        ),
        
        # Add vendor foreign key to Transaction (optional, for future use)
        migrations.AddField(
            model_name='transaction',
            name='vendor',
            field=models.ForeignKey(
                blank=True,
                help_text='Standardized vendor (auto-populated based on receiver)',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='transactions',
                to='finance.vendor'
            ),
        ),
    ]

