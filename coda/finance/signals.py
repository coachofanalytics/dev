from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime
from finance.models import Transaction, Budget, BudgetCategory, BudgetSubCategory
from main.models import Company
from accounts.models import Department
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=Transaction)
def sync_transaction_to_budget(sender, instance, created, **kwargs):
    """
    Auto-sync Transaction records to Budget whenever a new transaction is added or updated.
    """
    print("This is my data ")
    
    # Skip sync during bulk operations or if no category assigned yet
    # The signal will run again after categorization when category is set
    if not hasattr(instance, 'category') or instance.category is None:
        return
    
    # Ensure transaction has a department
    if not hasattr(instance, 'department') or instance.department is None:
        return
    
    # Ensure transaction has a sender (required for budget_lead)
    if not hasattr(instance, 'sender') or instance.sender is None:
        # Skip transactions without a sender - cannot create budget without budget_lead
        return

    # Find or create the related Department
    department, _ = Department.objects.get_or_create(name=instance.department.name)

    # Use the transaction's actual category and subcategory
    category = instance.category
    subcategory = instance.subcategory if hasattr(instance, 'subcategory') and instance.subcategory else None
    
    # If no subcategory, try to get or create a default one
    if subcategory is None:
        subcategory, _ = BudgetSubCategory.objects.get_or_create(
            name="Other", 
            category=category,
            defaults={'description': 'Default subcategory'}
        )

    # Find or create the default Company
    company, _ = Company.objects.get_or_create(name='Default Company')

    # Get the budget lead - use sender or default "coda_info" user
    if instance.sender:
        budget_lead = instance.sender
    else:
        # Get or create default system user for transactions without sender
        budget_lead, _ = User.objects.get_or_create(
            username='coda_info',
            defaults={
                'email': 'system@coda.co.ke',
                'first_name': 'CODA',
                'last_name': 'System',
                'is_active': True,
                'is_staff': False,
            }
        )

    # Truncate fields to prevent exceeding max length
    truncated_description = (instance.description or 'No description provided')[:1000]
    truncated_item = instance.type[:100]
    truncated_receipt_link = instance.receipt_link[:255] if instance.receipt_link else None

    # **Check if the transaction already exists in Budget**
    try:
        coda_budget, created = Budget.objects.update_or_create(
            budget_lead=budget_lead,
            company=company,
            department=department,
            category=category,
            subcategory=subcategory,
            item_name=truncated_item,
            defaults={  # Fields to update if it already exists
                "cases": 1,
                "quantity": instance.qty,
                "unit_price": instance.amount,
                "start_date": instance.transaction_date.date() if hasattr(instance.transaction_date, 'date') else instance.transaction_date,
                "end_date": instance.transaction_date.date() if hasattr(instance.transaction_date, 'date') else instance.transaction_date,
                "description": truncated_description,
                "receipt_link": truncated_receipt_link
            }
        )

        if created:
            print(f"✅ New Budget entry created for Transaction {instance.id}")
        else:
            print(f"🔄 Budget entry updated for Transaction {instance.id}")
    
    except Budget.MultipleObjectsReturned:
        # If duplicates exist, just create a new entry
        print(f"⚠️  Multiple Budgets found for Transaction {instance.id}, creating new entry")
        Budget.objects.create(
            budget_lead=budget_lead,
            company=company,
            department=department,
            category=category,
            subcategory=subcategory,
            item_name=truncated_item,
            cases=1,
            quantity=instance.qty,
            unit_price=instance.amount,
            start_date=instance.transaction_date.date() if hasattr(instance.transaction_date, 'date') else instance.transaction_date,
            end_date=instance.transaction_date.date() if hasattr(instance.transaction_date, 'date') else instance.transaction_date,
            description=truncated_description,
            receipt_link=truncated_receipt_link
        )

