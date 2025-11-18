import logging
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime
from finance.models import (
    Transaction,
    Budget,
    BudgetCategory,
    BudgetSubCategory,
    LoanApplication,
    Payment_Information,
)
from main.models import Company
from accounts.models import Department
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
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
            category=category
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


def _safe_int(value) -> int:
    """Convert Decimal/float to int safely."""
    try:
        return int(Decimal(str(value)))
    except Exception:
        return 0


@receiver(post_save, sender=LoanApplication)
def sync_payment_info_on_loan_approval(sender, instance, created, **kwargs):
    """
    Ensure approved loans automatically create Payment_Information entries
    so the unified payment system has context for repayments.
    """
    if instance.status != 'approved':
        return

    try:
        payment_ref = f"loan-{instance.id}"
        total_payable = instance.total_payable or instance.amount_requested or Decimal('0')
        monthly_payment = instance.monthly_payment or Decimal('0')
        plan_months = instance.duration or (instance.loan_product.term_months if instance.loan_product else 0)
        borrower = instance.borrower
        borrower_signature = borrower.username or borrower.get_full_name() or borrower.email or "client"
        approver_signature = (
            instance.approved_by.get_full_name()
            if instance.approved_by and instance.approved_by.get_full_name()
            else (instance.approved_by.username if instance.approved_by else "LoanSystem")
        )
        currency = (getattr(instance, "user_currency", None) or "USD")[:3].upper()
        now = timezone.now()

        defaults = {
            'customer': borrower,
            'payment_fees': _safe_int(total_payable),
            'down_payment': _safe_int(monthly_payment),
            'student_bonus': 0,
            'plan': plan_months or 0,
            'subplan': instance.loan_plan_id,
            'pricing_plan': instance.loan_product.id if instance.loan_product else None,
            'client_signature': borrower_signature,
            'company_rep': approver_signature,
            'client_date': now.strftime("%Y-%m-%d"),
            'rep_date': now.strftime("%Y-%m-%d"),
            'amount': total_payable,
            'currency': currency,
            'payment_method': 'loan',
            'status': 'pending',
            'payment_date': now,
            'notes': f"Loan {instance.application_number} approved on {now.strftime('%Y-%m-%d')}",
            'transaction_id': payment_ref,
        }

        payment_info, created_info = Payment_Information.objects.get_or_create(
            transaction_id=payment_ref,
            defaults=defaults,
        )

        if not created_info:
            payment_info.payment_fees = defaults['payment_fees']
            payment_info.down_payment = defaults['down_payment']
            payment_info.plan = defaults['plan']
            payment_info.subplan = defaults['subplan']
            payment_info.pricing_plan = defaults['pricing_plan']
            payment_info.amount = defaults['amount']
            payment_info.currency = defaults['currency']
            payment_info.payment_method = 'loan'
            payment_info.status = 'pending'
            payment_info.payment_date = now
            payment_info.notes = defaults['notes']
            payment_info.client_signature = payment_info.client_signature or borrower_signature
            payment_info.company_rep = defaults['company_rep']
            payment_info.client_date = defaults['client_date']
            payment_info.rep_date = defaults['rep_date']
            payment_info.save()

        logger.info(
            "Synced Payment_Information for approved loan %s (payment record %s)",
            instance.id,
            payment_info.id,
        )
    except Exception as exc:
        logger.error(
            "Failed to sync Payment_Information for loan %s: %s",
            instance.id,
            exc,
            exc_info=True,
        )

