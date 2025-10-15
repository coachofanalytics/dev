# Finance utilities package

def update_link(service_array, user_payment_history, service_categories):
    """Update service links based on user payment history"""
    updated_automation = []
    for automation_service in service_array:
        # Simple implementation - just return the service as-is
        # In a real implementation, this would check payment history
        # and update service availability/links accordingly
        updated_automation.append(automation_service)
    return updated_automation

def validate_amount(amount):
    """Validate payment amount"""
    try:
        amount = float(amount)
        if amount <= 0:
            return False, "Amount must be greater than zero"
        if amount > 1000000:  # 1 million limit
            return False, "Amount exceeds maximum limit"
        return True, "Valid amount"
    except (ValueError, TypeError):
        return False, "Invalid amount format"

def save_payment_history(user, payment_info, method, reference, amount, status="completed"):
    """Save payment history record - matches payment processing expectations"""
    try:
        from finance.models import Payment_History
        
        payment_history = Payment_History.objects.create(
            customer=user,
            payment_fees=amount,
            payment_method=method,
            plan=payment_info.plan,
            subplan=payment_info.subplan,
            pricing_plan=payment_info.pricing_plan,
            down_payment=payment_info.down_payment,
            student_bonus=payment_info.student_bonus,
            description=f"Payment via {method} - Ref: {reference}",
            contract_submitted_date=payment_info.contract_submitted_date,
            client_signature=payment_info.client_signature,
            company_rep=payment_info.company_rep,
            client_date=payment_info.client_date,
            rep_date=payment_info.rep_date,
        )
        return True
    except Exception as e:
        print(f"Error saving payment history: {str(e)}")
        return False

def validate_user_payment_eligibility(user, amount, payment_method="general"):
    """Validate if user is eligible for payments with amount and method"""
    try:
        from finance.models import Payment_Information
        
        # Basic user validation
        if not user.is_active:
            return False, "User account is not active", None
        
        # Validate amount
        amount_valid, amount_message = validate_amount(amount)
        if not amount_valid:
            return False, amount_message, None
        
        amount_float = float(amount)
        
        # Check user payment information
        payment_info = Payment_Information.objects.filter(customer_id=user.id).first()
        if not payment_info:
            return False, "No payment information found", None
        
        # Check if user has negative balance (owes money)
        if payment_info.payment_fees < 0:
            return (
                False,
                f"Account has negative balance of ${abs(payment_info.payment_fees)}. Please resolve outstanding balance first.",
                None
            )
        
        # Check if user has $0 balance and trying to make payment
        if payment_info.payment_fees == 0:
            return False, "Account has $0 balance. Please add funds or contact support.", None
        
        # Check if payment amount exceeds available balance
        if amount_float > payment_info.payment_fees:
            return (
                False,
                f"Payment amount ${amount_float} exceeds available balance of ${payment_info.payment_fees}",
                None
            )
        
        return True, "Payment eligible", amount_float
        
    except Exception as e:
        return False, f"Error checking payment eligibility: {str(e)}", None

def get_user_currency(user):
    """Get user's preferred currency based on their country"""
    try:
        if hasattr(user, "profile") and user.profile and user.profile.country:
            return user.profile.country.code
        return "USD"  # Default to USD
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting user currency for {user.username}: {e}")
        return "USD"

def check_user_loan_eligibility(user):
    """Check if a user is eligible for a new loan"""
    try:
        from decimal import Decimal
        
        # Basic eligibility check - simplified version
        if not user.is_active:
            return {
                "eligible": False,
                "reason": "inactive_account",
                "message": "Your account is not active. Please contact support.",
                "unpaid_loans": [],
                "total_outstanding": Decimal("0.00"),
            }
        
        # For now, return basic eligibility
        return {
            "eligible": True,
            "reason": "eligible",
            "message": "You are eligible for a loan.",
            "unpaid_loans": [],
            "total_outstanding": Decimal("0.00"),
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error checking loan eligibility: {e}")
        return {
            "eligible": False,
            "reason": "error",
            "message": "Unable to determine eligibility. Please contact support.",
            "unpaid_loans": [],
            "total_outstanding": Decimal("0.00"),
        }

def get_eligible_staff_guarantors(limit=5):
    """Get eligible staff members who can act as guarantors"""
    try:
        from accounts.models import CustomerUser
        from datetime import timedelta
        from django.utils import timezone
        
        # Calculate 3 months ago date
        three_months_ago = timezone.now().date() - timedelta(days=90)
        
        # Get active staff members who have been employed for more than 3 months
        eligible_guarantors = CustomerUser.objects.filter(
            category=2,           # Staff members only
            is_active=True,       # Must be active
            is_staff=True,        # Must be current staff
            date_joined__lte=three_months_ago  # Must have been employed for 3+ months
        ).exclude(
            is_superuser=True  # Exclude superusers
        ).order_by("first_name", "last_name")[:limit]
        
        return [
            {
                "id": guarantor.id,
                "name": f"{guarantor.first_name} {guarantor.last_name}",
                "email": guarantor.email,
                "score": 100,  # Default score for staff
                "employment_months": (timezone.now().date() - guarantor.date_joined.date()).days // 30,
            }
            for guarantor in eligible_guarantors
        ]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting eligible staff guarantors: {e}")
        return []


def get_eligible_kcc_guarantors(limit=5):
    """Get eligible KCC members who can act as guarantors"""
    try:
        from accounts.models import CustomerUser
        from django.utils import timezone
        
        # Get active KCC members who are not staff
        eligible_guarantors = CustomerUser.objects.filter(
            is_active=True,
            profile__is_karen_country_club_member=True,
            category__in=[1, 3, 4, 5]  # Non-staff categories only
        ).exclude(
            category=2  # Exclude staff members
        ).filter(
            # Check if KCC membership is not expired
            Q(profile__kcc_membership_expiry__isnull=True) |
            Q(profile__kcc_membership_expiry__gte=timezone.now().date())
        ).order_by("first_name", "last_name")[:limit]
        
        return [
            {
                "id": guarantor.id,
                "name": f"{guarantor.first_name} {guarantor.last_name}",
                "email": guarantor.email,
                "score": 100,  # Default score for KCC members
                "kcc_tier": 1,  # Default tier
            }
            for guarantor in eligible_guarantors
        ]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting eligible KCC guarantors: {e}")
        return []

def get_existing_guarantor_info(user):
    """Get existing guarantor information for a user"""
    try:
        # This would typically query a guarantor model
        # For now, return empty dict to prevent errors
        return {}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting guarantor info: {e}")
        return {}

def get_standard_rejection_reasons():
    """Get standard rejection reasons for loan applications"""
    return [
        {"code": "insufficient_income", "message": "Insufficient income to support loan repayment"},
        {"code": "poor_credit_history", "message": "Poor credit history or payment record"},
        {"code": "incomplete_documents", "message": "Incomplete or missing required documents"},
        {"code": "existing_loans", "message": "Existing outstanding loans"},
        {"code": "inactive_account", "message": "Account is inactive or suspended"},
    ]

def notify_user_of_guarantor_availability(user, guarantor_info):
    """Notify user when a guarantor becomes available"""
    try:
        # Placeholder for notification logic
        # In a real implementation, this would send email/SMS notifications
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Guarantor available notification for user {user.username}: {guarantor_info}")
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending guarantor notification: {e}")
        return False

def calculate_paypal_charges(amount):
    """
    Calculate PayPal transaction fees using tiered pricing structure.
    Lower fees for higher transaction amounts (volume discount).

    Args:
        amount (Decimal): The payment amount

    Returns:
        Decimal: The PayPal fees based on tiered pricing
    """
    try:
        from decimal import Decimal
        import logging
        logger = logging.getLogger(__name__)
        
        if not amount or amount <= 0:
            return Decimal("0.00")

        # Define the PayPal charge brackets and corresponding fees
        # Format: (start_amount, end_amount, fee_percentage, fee_fixed)
        charge_brackets = [
            (0, 500.00, 0.029, 0.30),  # 2.9% + $0.30 for $0 - $500
            (500.01, 1000.00, 0.027, 0.30),  # 2.7% + $0.30 for $500.01 - $1,000
            (1000.01, 5000.00, 0.025, 0.30),  # 2.5% + $0.30 for $1,000.01 - $5,000
            (5000.01, 10000.00, 0.023, 0.30),  # 2.3% + $0.30 for $5,000.01 - $10,000
            (10000.01, 15000.00, 0.021, 0.30),  # 2.1% + $0.30 for $10,000.01 - $15,000
            (15000.01, float("inf"), 0.019, 0.30),  # 1.9% + $0.30 for $15,000.01+
        ]

        # Cast the amount to float for comparison
        amount_float = float(amount)

        # Iterate over the charge brackets to find the applicable fee
        for bracket in charge_brackets:
            start_amount, end_amount, fee_percentage, fee_fixed = bracket
            if start_amount <= amount_float <= end_amount:
                # Calculate the PayPal charge
                charge = amount_float * fee_percentage + fee_fixed
                return Decimal(str(round(charge, 2)))

        # If the amount is not within any of the charge brackets, return 0
        logger.warning(f"Amount {amount} does not fit within PayPal charge brackets")
        return Decimal("0.00")

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error calculating PayPal charges for amount {amount}: {e}")
        return Decimal("0.00")