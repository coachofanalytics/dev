from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime
from .models import Transaction, CodaBudget, Department, BudgetCategory, BudgetSubCategory, Company

@receiver(post_save, sender=Transaction)
def sync_transaction_to_codabudget(sender, instance, created, **kwargs):
    """
    Auto-sync Transaction records to CodaBudget whenever a new transaction is added or updated.
    """
    print("This is my data ")
    
    # Ensure transaction has a department
    if not hasattr(instance, 'department') or instance.department is None:
        return

    # Find or create the related Department
    department, _ = Department.objects.get_or_create(name=instance.department.name)

    # Find or create corresponding BudgetCategory
    category_name = 'Other'  # Default category name
    category, _ = BudgetCategory.objects.get_or_create(
        name=category_name,
        defaults={'description': 'Default description'}
    )

    # Find or create corresponding BudgetSubCategory
    subcategory, _ = BudgetSubCategory.objects.get_or_create(name="Other", category=category)

    # Find or create the default Company
    company, _ = Company.objects.get_or_create(name='Default Company')

    # Get the budget lead
    budget_lead = instance.sender if instance.sender else None  # Use sender or None

    # Truncate fields to prevent exceeding max length
    truncated_description = (instance.description or 'No description provided')[:1000]
    truncated_item = instance.type[:100]
    truncated_receipt_link = instance.receipt_link[:255] if instance.receipt_link else None

    # **Check if the transaction already exists in CodaBudget**
    try:
        coda_budget, created = CodaBudget.objects.update_or_create(
            budget_lead=budget_lead,
            company=company,
            department=department,
            category=category,
            subcategory=subcategory,
            item=truncated_item,
            defaults={  # Fields to update if it already exists
                "cases": 1,
                "qty": instance.qty,
                "unit_price": instance.amount,
                "created_at": instance.transaction_date,
                "description": truncated_description,
                "receipt_link": truncated_receipt_link
            }
        )

        if created:
            print(f"✅ New CodaBudget entry created for Transaction {instance.id}")
        else:
            print(f"🔄 CodaBudget entry updated for Transaction {instance.id}")
    
    except CodaBudget.MultipleObjectsReturned:
        # If duplicates exist, just create a new entry
        print(f"⚠️  Multiple CodaBudgets found for Transaction {instance.id}, creating new entry")
        CodaBudget.objects.create(
            budget_lead=budget_lead,
            company=company,
            department=department,
            category=category,
            subcategory=subcategory,
            item=truncated_item,
            cases=1,
            qty=instance.qty,
            unit_price=instance.amount,
            created_at=instance.transaction_date,
            description=truncated_description,
            receipt_link=truncated_receipt_link
        )

