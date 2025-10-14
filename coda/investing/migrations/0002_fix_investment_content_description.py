# Generated manually to fix InvestmentContent description field

from django.db import migrations

def fix_investment_content_descriptions(apps, schema_editor):
    """Fix any InvestmentContent records with NULL descriptions"""
    InvestmentContent = apps.get_model('investing', 'InvestmentContent')
    
    # Update any records with NULL or empty descriptions
    InvestmentContent.objects.filter(
        description__isnull=True
    ).update(description="Welcome to our investment platform. We provide comprehensive investment solutions for all types of investors.")
    
    InvestmentContent.objects.filter(
        description=""
    ).update(description="Welcome to our investment platform. We provide comprehensive investment solutions for all types of investors.")

def reverse_fix_investment_content_descriptions(apps, schema_editor):
    """Reverse migration - no action needed"""
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('investing', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            fix_investment_content_descriptions,
            reverse_fix_investment_content_descriptions,
        ),
    ]

