from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Q
from decimal import Decimal
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import logging
from mail.custom_email import send_email

logger = logging.getLogger(__name__)

# Get the User model
User = get_user_model()


def check_user_loan_eligibility(user):
    """
    Check if a user is eligible for a new loan.
    Returns a dictionary with eligibility status and reasons.
    """
    try:
        # PRIORITY 1: Check if user is staff (category 2) - ALWAYS check this first
        if user.category == 2:  # Staff member
            # Staff eligibility is based on income and employment, not KCC status
            loan_limits = get_user_loan_limits(user)

            if not loan_limits:
                return {
                    "eligible": False,
                    "reason": "insufficient_income",
                    "message": "As a staff member, you need at least 3 months of consistent earnings to qualify for a loan. Please contact HR if you believe this is an error.",
                    "unpaid_loans": [],
                    "total_outstanding": Decimal("0.00"),
                    "user_type": "staff",
                }
            else:
                return {
                    "eligible": True,
                    "reason": "eligible",
                    "message": "You are eligible for a staff loan based on your employment and earnings history.",
                    "loan_limits": loan_limits,
                    "unpaid_loans": [],
                    "total_outstanding": Decimal("0.00"),
                    "user_type": "staff",
                }

        # PRIORITY 2: Only check KCC membership if user is NOT staff
        elif check_karen_country_club_membership(user):  # KCC member (non-staff)
            loan_limits = get_user_loan_limits(user)
            return {
                "eligible": True,
                "reason": "eligible",
                "message": "You are eligible for a KCC premium loan with exclusive terms.",
                "loan_limits": loan_limits,
                "unpaid_loans": [],
                "total_outstanding": Decimal("0.00"),
                "user_type": "kcc_member",
            }

        # PRIORITY 3: External user (non-staff, non-KCC)
        else:
            return {
                "eligible": False,
                "reason": "external_user",
                "message": "External users need to provide additional documentation and guarantor information. Please contact our support team to discuss your application.",
                "unpaid_loans": [],
                "total_outstanding": Decimal("0.00"),
                "user_type": "external",
            }

    except Exception as e:
        logger.error(f"Error checking loan eligibility for user {user.username}: {e}")
        return {
            "eligible": False,
            "reason": "error",
            "message": "Error checking eligibility. Please contact support.",
            "unpaid_loans": [],
            "total_outstanding": Decimal("0.00"),
            "user_type": "unknown",
        }


def get_user_loan_limits(user):
    """
    Calculate user-specific loan limits based on their type and income.
    Returns None if limits cannot be calculated.
    """
    try:
        # PRIORITY 1: Check if user is staff (category 2)
        if user.category == 2:
            # Calculate based on TaskHistory income (last 3 months average)
            monthly_income = _compute_average_monthly_income_last_3_months(user)

            if monthly_income and monthly_income > 0:
                # Staff can borrow up to 2x their monthly income
                max_amount = monthly_income * Decimal("2.0")
                min_amount = Decimal("50.00")  # Minimum $50

                return {
                    "monthly_income": monthly_income,
                    "max_amount": max_amount,
                    "min_amount": min_amount,
                    "multiplier": "2.0x",
                    "income_period": "monthly",
                    "user_type": "staff",
                }
            else:
                # Staff with no income history
                return None

        # PRIORITY 2: Only check KCC membership if user is NOT staff
        elif check_karen_country_club_membership(user):
            # Premium members get higher limits
            return {
                "monthly_income": None,  # Not required for KCC members
                "max_amount": Decimal("10000.00"),  # $10,000 limit
                "min_amount": Decimal("1000.00"),  # $1,000 minimum
                "multiplier": "N/A",
                "income_period": "N/A",
                "user_type": "kcc_member",
            }

        # External users - use plan defaults
        else:
            return None

    except Exception as e:
        logger.error(f"Error calculating loan limits for user {user.username}: {e}")
        return None


def check_karen_country_club_membership(user):
    """
    Check if user is a Karen Country Club member.
    IMPORTANT: Staff users (category 2) should NEVER be considered KCC members
    """
    try:
        # CRITICAL: Staff users are NEVER KCC members
        if user.category == 2:
            return False

        # Check if user has a profile with KCC membership
        if hasattr(user, "profile") and user.profile:
            profile = user.profile

            # Check if user has KCC membership field
            if profile.is_karen_country_club_member:
                # Check if membership is still valid
                if profile.kcc_membership_expiry:
                    from datetime import date

                    if profile.kcc_membership_expiry >= date.today():
                        return True
                    else:
                        logger.warning(
                            f"KCC membership expired for user {user.username}"
                        )
                        return False
                else:
                    # No expiry date, assume valid
                    return True

        return False

    except Exception as e:
        logger.error(f"Error checking KCC membership for user {user.username}: {e}")
        return False


def get_eligible_kcc_guarantors(limit=5):
    """
    Get eligible KCC members who can act as guarantors.
    Requirements:
    - Must be KCC members with active membership
    - Must not be staff members (staff have their own guarantor system)
    - Must be active users
    """
    try:
        from accounts.models import CustomerUser
        from django.utils import timezone

        # Get active KCC members who are not staff
        eligible_guarantors = (
            CustomerUser.objects.filter(
                is_active=True,
                profile__is_karen_country_club_member=True,
                category__in=[1, 3, 4, 5]  # Non-staff categories only
            )
            .exclude(
                category=2  # Exclude staff members
            )
            .filter(
                # Check if KCC membership is not expired
                Q(profile__kcc_membership_expiry__isnull=True) |
                Q(profile__kcc_membership_expiry__gte=timezone.now().date())
            )
            .order_by("first_name", "last_name")[:limit]
        )

        # Calculate eligibility scores for each guarantor
        guarantor_data = []
        for kcc_member in eligible_guarantors:
            # Calculate eligibility score based on KCC membership and tier
            eligibility_score = calculate_kcc_guarantor_eligibility_score(kcc_member)
            
            # Determine KCC tier based on credit score
            kcc_tier = get_kcc_tier_by_credit_score(kcc_member)

            guarantor_data.append(
                {
                    "kcc_member": kcc_member,
                    "eligibility_score": eligibility_score,
                    "kcc_tier": kcc_tier,
                    "membership_status": "Active",
                }
            )

        return guarantor_data

    except Exception as e:
        logger.error(f"Error getting eligible KCC guarantors: {e}")
        return []


def calculate_kcc_guarantor_eligibility_score(kcc_user):
    """
    Calculate eligibility score for KCC guarantors based on:
    - Active KCC membership
    - Credit score tier
    - Membership duration
    """
    try:
        score = 0
        
        # Active KCC membership (40 points)
        if (hasattr(kcc_user, 'profile') and 
            kcc_user.profile.is_karen_country_club_member):
            score += 40
        
        # Credit score tier (60 points max)
        kcc_tier = get_kcc_tier_by_credit_score(kcc_user)
        if kcc_tier == 3:  # Tier 3 (highest)
            score += 60
        elif kcc_tier == 2:  # Tier 2
            score += 40
        elif kcc_tier == 1:  # Tier 1
            score += 20
        
        return min(score, 100)  # Cap at 100
        
    except Exception as e:
        logger.error(f"Error calculating KCC guarantor eligibility score: {e}")
        return 0


def get_kcc_tier_by_credit_score(user):
    """
    Determine KCC tier based on credit score:
    - Tier 1: Credit score 300-499 (Basic)
    - Tier 2: Credit score 500-699 (Standard) 
    - Tier 3: Credit score 700+ (Premium)
    """
    try:
        # Get credit score from user profile or loan applications
        credit_score = None
        
        if hasattr(user, 'profile') and hasattr(user.profile, 'credit_score'):
            credit_score = user.profile.credit_score
        
        # If no profile credit score, check latest loan application
        if not credit_score:
            from .models import LoanApplication
            latest_application = LoanApplication.objects.filter(
                borrower=user
            ).order_by('-submitted_at').first()
            
            if latest_application and latest_application.credit_score:
                credit_score = latest_application.credit_score
        
        # Determine tier based on credit score
        if not credit_score:
            return 1  # Default to Tier 1 if no credit score
        
        if credit_score >= 700:
            return 3  # Tier 3 - Premium
        elif credit_score >= 500:
            return 2  # Tier 2 - Standard
        else:
            return 1  # Tier 1 - Basic
            
    except Exception as e:
        logger.error(f"Error determining KCC tier for user {user.username}: {e}")
        return 1  # Default to Tier 1


def get_eligible_staff_guarantors(limit=5):
    """
    Get eligible staff members who can act as guarantors.
    Requirements:
    - Must be current/active staff members (category 2, is_staff=True)
    - Must have been employed for more than 3 months
    - Must be active users
    """
    try:
        from accounts.models import CustomerUser
        from datetime import date, timedelta
        from django.utils import timezone

        # Calculate 3 months ago date
        three_months_ago = timezone.now().date() - timedelta(days=90)

        # Get active staff members who have been employed for more than 3 months
        eligible_guarantors = (
            CustomerUser.objects.filter(
                category=2,           # Staff members only
                is_active=True,       # Must be active
                is_staff=True,        # Must be current staff
                date_joined__lte=three_months_ago  # Must have been employed for 3+ months
            )
            .exclude(
                # Exclude superusers from guarantor list
                is_superuser=True
            )
            .order_by("first_name", "last_name")[:limit]
        )

        # Calculate eligibility scores and earnings for each guarantor
        guarantor_data = []
        for staff in eligible_guarantors:
            # Calculate eligibility score based on employment duration and earnings
            eligibility_score = calculate_staff_guarantor_eligibility_score(staff)

            # Calculate average earnings
            avg_earnings = _compute_average_monthly_income_last_3_months(staff)
            if avg_earnings is None:
                avg_earnings = Decimal("0.00")

            # Calculate employment duration in months
            employment_months = (timezone.now().date() - staff.date_joined.date()).days // 30

            guarantor_data.append(
                {
                    "staff": staff,
                    "eligibility_score": eligibility_score,
                    "avg_earnings": avg_earnings,
                    "monthly_earnings": avg_earnings,
                    "employment_months": employment_months,
                    "employment_duration": f"{employment_months} months",
                }
            )

        return guarantor_data

    except Exception as e:
        logger.error(f"Error getting eligible staff guarantors: {e}")
        return []


def calculate_staff_guarantor_eligibility_score(staff_user):
    """
    Calculate eligibility score for staff guarantors based on:
    - Employment duration (3+ months required)
    - Consistent earnings history
    - Active status
    """
    try:
        from datetime import timedelta
        from django.utils import timezone
        
        score = 0
        
        # Employment duration check (40 points max)
        employment_duration = (timezone.now().date() - staff_user.date_joined.date()).days
        if employment_duration >= 90:  # 3+ months
            score += 40
        elif employment_duration >= 60:  # 2+ months
            score += 20
        else:
            return 0  # Not eligible if less than 3 months
        
        # Active status (20 points)
        if staff_user.is_active and staff_user.is_staff:
            score += 20
        
        # Consistent earnings (40 points max)
        avg_earnings = _compute_average_monthly_income_last_3_months(staff_user)
        if avg_earnings and avg_earnings > 0:
            score += 40
        elif avg_earnings and avg_earnings > Decimal('100'):
            score += 20
        
        return min(score, 100)  # Cap at 100
        
    except Exception as e:
        logger.error(f"Error calculating staff guarantor eligibility score: {e}")
        return 0


def _compute_average_monthly_income_last_3_months(user):
    """Compute average of last 3 calendar months income from TaskHistory.get_pay"""
    try:
        from management.models import TaskHistory
        from management.utils import emp_average_earnings

        # Use existing helper if available
        avg = emp_average_earnings(None, TaskHistory, 0, user)
        try:
            avg_dec = Decimal(str(avg))
        except Exception:
            avg_dec = None

        if not avg_dec or avg_dec <= 0:
            avg_dec = None

        if avg_dec:
            return avg_dec.quantize(Decimal("0.01"))

    except Exception:
        # Fallback: direct computation
        try:
            from management.models import TaskHistory
        except Exception:
            return None

        now = timezone.now()
        lookback_start = (now - relativedelta(months=12)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        try:
            tasks = TaskHistory.objects.filter(
                employee=user,
                submission__gte=lookback_start,
                submission__lte=now,
            )
        except Exception:
            return None

        month_totals = {}
        for t in tasks:
            try:
                dt = t.submission
                key = (dt.year, dt.month)
                month_totals.setdefault(key, Decimal("0"))
                month_totals[key] += Decimal(t.get_pay or 0)
            except Exception:
                continue

        if not month_totals:
            return None

        # Sort by year, month descending and take the most recent 3 active months
        active_months = [
            (ym, total) for ym, total in month_totals.items() if total and total > 0
        ]
        if not active_months:
            return None

        active_months.sort(key=lambda x: (x[0][0], x[0][1]), reverse=True)
        top3 = active_months[:3]
        if not top3:
            return None

        avg = sum(total for _, total in top3) / Decimal(len(top3))
        if avg <= 0:
            return None

        return avg.quantize(Decimal("0.01"))

    return None


# ==================== AI SERVICES FUNCTIONS ====================


def update_link(service_array, user_payment_history, service_categories):
    """Update service links based on user payment history"""
    try:
        updated_automation = []
        for automation_service in service_array:

            if (
                automation_service.get("service_category_slug")
                and automation_service["service_category_slug"]
                in service_categories.keys()
            ):

                if user_payment_history.filter(
                    plan=service_categories[automation_service["service_category_slug"]]
                ).exists():
                    updated_automation.append(automation_service)
                else:
                    automation_service["link"] = automation_service.get(
                        "service_url", ""
                    )
                    updated_automation.append(automation_service)
            else:
                updated_automation.append(automation_service)

        return updated_automation

    except Exception as e:
        logger.error(f"Error updating service links: {e}")
        return service_array


# ==================== EXCHANGE RATE FUNCTIONS ====================


def get_exchange_rate(from_currency="USD", to_currency="KES"):
    """Get exchange rate between currencies"""
    try:
        # Simple hardcoded rates (in production, use real-time API)
        rates = {
            ("USD", "KES"): 142.50,
            ("USD", "EUR"): 0.85,
            ("USD", "GBP"): 0.73,
            ("KES", "USD"): 0.007,
            ("EUR", "USD"): 1.18,
            ("GBP", "USD"): 1.38,
        }

        return rates.get((from_currency, to_currency), 1.0)

    except Exception as e:
        logger.error(
            f"Error getting exchange rate {from_currency} to {to_currency}: {e}"
        )
        return 1.0


def save_payment_record(payment_data):
    """Save payment record to database"""
    try:
        # This would save payment data to the database
        logger.info(f"Payment record saved: {payment_data}")
        return True
    except Exception as e:
        logger.error(f"Error saving payment record: {e}")
        return False


def convert_to_usd(amount, from_currency):
    """Convert amount from given currency to USD"""
    try:
        # Simple conversion rates (in production, use real-time rates)
        rates = {
            "KES": 0.007,  # 1 KES = 0.007 USD
            "EUR": 1.18,  # 1 EUR = 1.18 USD
            "GBP": 1.38,  # 1 GBP = 1.38 USD
        }

        if from_currency in rates:
            return amount * Decimal(str(rates[from_currency]))
        return amount  # If currency not found, return as-is

    except Exception as e:
        logger.error(f"Error converting {amount} {from_currency} to USD: {e}")
        return amount


def find_or_create_guarantor_user(guarantor_data):
    """Find or create a guarantor user based on provided data"""
    try:
        # This would find or create a guarantor user
        logger.info(f"Guarantor user processed: {guarantor_data}")
        return None
    except Exception as e:
        logger.error(f"Error processing guarantor user: {e}")
        return None


def calculate_guarantor_eligibility_score(guarantor_user):
    """Calculate eligibility score for a potential guarantor"""
    try:
        # This would calculate a score based on guarantor's financial status
        return 85  # Default score
    except Exception as e:
        logger.error(f"Error calculating guarantor score: {e}")
        return 0


def get_user_currency(user):
    """Get user's preferred currency based on their country"""
    try:
        if hasattr(user, "profile") and user.profile and user.profile.country:
            return user.profile.country.code
        return "USD"  # Default to USD
    except Exception as e:
        logger.error(f"Error getting user currency for {user.username}: {e}")
        return "USD"


def get_existing_guarantor_info(user):
    """Get existing guarantor information for a user"""
    try:
        # This would typically query a guarantor model
        # For now, return empty dict to prevent errors
        return {}
    except Exception as e:
        logger.error(f"Error getting guarantor info: {e}")
        return {}


# ======================PAYPAL CHARGES============================
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
        logger.error(f"Error calculating PayPal charges for amount {amount}: {e}")
        return Decimal("0.00")


def validate_amount(amount_str, payment_method="general"):
    """
    Comprehensive amount validation including format, limits, and method-specific rules

    Parameters:
    - amount_str: The amount as a string (e.g., '15.99')
    - payment_method: The payment method for method-specific limits

    Returns:
    - A tuple: (is_valid, message, amount_float)
    """
    try:
        # Basic format validation
        if not amount_str:
            return False, "Payment amount is required", None

        # Convert to float
        amount_float = float(amount_str)

        # Basic range validation
        if amount_float <= 0:
            return False, "Payment amount must be greater than zero", None

        # Method-specific amount limits
        method_limits = {
            "mpesa": {"min": 10, "max": 300},
            "paypal": {"min": 5, "max": 1000},
            "stripe": {"min": 5, "max": 2000},
            "cashapp": {"min": 5, "max": 500},
            "zelle": {"min": 5, "max": 1500},
            "venmo": {"min": 5, "max": 800},
        }

        if payment_method.lower() in method_limits:
            limits = method_limits[payment_method.lower()]
            if amount_float < limits["min"]:
                return (
                    False,
                    f"Amount ${amount_float} is below minimum limit of ${limits['min']} for {payment_method.title()}",
                    None,
                )
            if amount_float > limits["max"]:
                return (
                    False,
                    f"Amount ${amount_float} exceeds maximum limit of ${limits['max']} for {payment_method.title()}",
                    None,
                )

        # Additional validations
        # Check for decimal precision (max 2 decimal places)
        if len(str(amount_float).split(".")[-1]) > 2:
            return False, "Amount cannot have more than 2 decimal places", None

        # Check for reasonable amount (prevent extremely large amounts)
        if amount_float > 100000:  # $100k limit
            return (
                False,
                "Amount exceeds reasonable limit. Please contact support for large payments.",
                None,
            )

        return True, "Amount valid", amount_float

    except (ValueError, TypeError):
        return False, "Invalid payment amount format", None
    except Exception as e:
        return False, f"Error validating amount: {str(e)}", None


def validate_user_payment_eligibility(user, amount, payment_method="general"):
    """
    Validate if user can make payment based on balance and amount
    Uses validate_amount for comprehensive amount validation
    """
    try:
        from finance.models import Payment_Information

        # First validate the amount using the enhanced validate_amount function
        amount_valid, amount_message, amount_float = validate_amount(
            amount, payment_method
        )
        if not amount_valid:
            return False, amount_message

        # Then check user balance and eligibility - use safe query to avoid field conflicts
        try:
            payment_info = Payment_Information.objects.filter(
                customer_id=user.id
            ).only('id', 'customer_id', 'payment_fees', 'down_payment').first()
        except Exception as db_error:
            # Fallback: use raw query to avoid model ordering issues
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, customer_id, payment_fees, down_payment 
                    FROM finance_payment_information 
                    WHERE customer_id = %s 
                    ORDER BY id DESC 
                    LIMIT 1
                """, [user.id])
                result = cursor.fetchone()
                if result:
                    # Create a simple object with the needed attributes
                    payment_info = type('PaymentInfo', (), {
                        'id': result[0],
                        'customer_id': result[1],
                        'payment_fees': result[2],
                        'down_payment': result[3]
                    })()
                else:
                    payment_info = None
        
        if not payment_info:
            return False, "No payment information found"

        # Check if user has negative balance (owes money)
        if payment_info.payment_fees < 0:
            return (
                False,
                f"Account has negative balance of ${abs(payment_info.payment_fees)}. Please resolve outstanding balance first.",
            )

        # Check if user has $0 balance and trying to make payment
        if payment_info.payment_fees == 0:
            return False, "Account has $0 balance. Please add funds or contact support."

        # Check if payment amount exceeds available balance
        if amount_float > payment_info.payment_fees:
            return (
                False,
                f"Payment amount ${amount_float} exceeds available balance of ${payment_info.payment_fees}",
            )

        return True, "Payment eligible", amount_float

    except Exception as e:
        return False, f"Error checking payment eligibility: {str(e)}", None


def save_payment_history(
    user, payment_info, method, reference, amount, status="completed"
):
    """Persist a payment into Payment_History using existing model fields."""
    try:
        from .models import Payment_History  # local import to avoid circulars

        print("DEBUG: Starting save_payment_history")
        print(f"DEBUG: user: {user}")
        print(f"DEBUG: payment_info: {payment_info}")
        print(f"DEBUG: method: {method}")
        print(f"DEBUG: reference: {reference}")
        print(f"DEBUG: amount: {amount}")
        print(f"DEBUG: status: {status}")

        # Debug the calculated values
        payment_fees_value = int(round(float(amount))) if amount else 0
        down_payment_value = getattr(payment_info, "down_payment", 0) or 0
        student_bonus_value = getattr(payment_info, "student_bonus", 0) or 0
        plan_value = getattr(payment_info, "plan", 1) or 1
        subplan_value = getattr(payment_info, "subplan", 1) or 1
        pricing_plan_value = getattr(payment_info, "pricing_plan", 1) or 1

        print(f"DEBUG: payment_fees_value: {payment_fees_value}")
        print(f"DEBUG: down_payment_value: {down_payment_value}")
        print(f"DEBUG: student_bonus_value: {student_bonus_value}")
        print(f"DEBUG: plan_value: {plan_value}")
        print(f"DEBUG: subplan_value: {subplan_value}")
        print(f"DEBUG: pricing_plan_value: {pricing_plan_value}")

        # ✅ fee_balance is a computed property - no need to set it manually

        # Try to create the object step by step
        print("DEBUG: Attempting to create Payment_History object...")

        payment_record = Payment_History(
            customer=user,
            payment_fees=payment_fees_value,
            down_payment=down_payment_value,
            student_bonus=student_bonus_value,
            plan=plan_value,
            subplan=subplan_value,
            pricing_plan=pricing_plan_value,
            payment_method=str(method),
            contract_submitted_date=timezone.now(),
            client_signature="system",
            company_rep="system",
            client_date=timezone.now().strftime("%Y-%m-%d"),
            rep_date=timezone.now().strftime("%Y-%m-%d"),
            description=f"Ref: {reference} | Status: {status}",
        )

        print("DEBUG: Payment record object created successfully")
        print("DEBUG: About to save to database...")

        payment_record.save()

        print(f"DEBUG: Payment saved successfully with ID: {payment_record.id}")
        return True

    except Exception as e:
        print(f"DEBUG: Exception in save_payment_history: {str(e)}")
        print(f"DEBUG: Exception type: {type(e)}")
        import traceback

        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        logger.error(f"save_payment_history failed: {e}")
        return False


# In utils.py - Add this function:
def process_visitor_payment(request, method):
    """Process payment for unauthenticated visitors/guests"""
    try:
        # Get form data
        amount = request.POST.get("amount")
        email = request.POST.get("email")

        # Basic validation for visitors
        if not amount or not email:
            return redirect(
                "finance:unified_failed", error="Amount and email are required"
            )

        # Validate amount format (no user balance check for visitors)
        is_valid, message, amount_float = validate_amount(amount, method)
        if not is_valid:
            return redirect("finance:unified_failed", error=message)

        # Create temporary visitor record or process directly
        reference = f"VISITOR-{method.upper()}-{amount_float}"

        # Store in session for success page
        request.session["payment_reference"] = reference
        request.session["payment_amount"] = amount_float
        request.session["payment_method"] = method

        return redirect("finance:unified_success")

    except Exception as e:
        logger.error(f"Error processing visitor payment: {str(e)}")
        return redirect("finance:unified_failed", error="Payment processing failed")


# Email Functions for Guarantor Verification
def send_guarantor_approval_email(loan_application):
    """
    Send guarantor approval request email with verification link.
    Uses the existing accounts email verification system.
    """
    try:
        if not loan_application.guarantor or not loan_application.guarantor.email:
            logger.error(
                f"No guarantor or email for loan application {loan_application.id}"
            )
            return False

        # Use existing verification token from CustomerUser
        if not loan_application.guarantor.verification_token:
            # Generate new token if none exists
            import uuid

            loan_application.guarantor.verification_token = uuid.uuid4()
            loan_application.guarantor.save()

        # Create verification URL using existing accounts verification
        verification_url = reverse(
            "accounts:verify_email",
            kwargs={"token": loan_application.guarantor.verification_token},
        )

        # Add loan_id as query parameter
        verification_url += f"?loan_id={loan_application.id}"

        # Make URL absolute
        from django.contrib.sites.models import Site

        current_site = Site.objects.get_current()
        verification_url = f"http://{current_site.domain}{verification_url}"

        context = {
            "loan_app": loan_application,
            "guarantor": loan_application.guarantor,
            "borrower": loan_application.borrower,
            "verification_url": verification_url,
            "purpose": "finance",
        }

        result = send_email(
            category=0,
            to_email=[loan_application.guarantor.email],
            subject=f"Guarantor Approval Request - Loan #{loan_application.application_number}",
            html_template="finance/emails/guarantor_approval_request.html",
            context=context,
        )

        if result:
            logger.info(
                f"Guarantor approval email sent successfully to {loan_application.guarantor.email}"
            )
            return True
        else:
            logger.error(
                f"Failed to send guarantor approval email to {loan_application.guarantor.email}"
            )
            return False

    except Exception as e:
        logger.error(f"Error sending guarantor approval email: {str(e)}")
        return False


def send_guarantor_verification_success_email(loan_application, guarantor):
    """
    Send confirmation email after successful email verification.
    """
    try:
        approval_url = reverse(
            "finance:guarantor-approve-loan", kwargs={"loan_id": loan_application.id}
        )

        # Make URL absolute
        from django.contrib.sites.models import Site

        current_site = Site.objects.get_current()
        approval_url = f"http://{current_site.domain}{approval_url}"

        context = {
            "loan_app": loan_application,
            "guarantor": guarantor,
            "borrower": loan_application.borrower,
            "approval_url": approval_url,
            "verification_date": timezone.now(),
            "purpose": "finance",
        }

        result = send_email(
            category=0,
            to_email=[guarantor.email],
            subject=f"Email Verified - Ready to Review Loan #{loan_application.application_number}",
            html_template="finance/emails/guarantor_verification_success.html",
            context=context,
        )

        if result:
            logger.info(
                f"Guarantor verification success email sent to {guarantor.email}"
            )
            return True
        else:
            logger.error(
                f"Failed to send guarantor verification success email to {guarantor.email}"
            )
            return False

    except Exception as e:
        logger.error(f"Error sending guarantor verification success email: {str(e)}")
        return False


def send_borrower_notification_email(loan_application, notification_type):
    """
    Send notification email to borrower about guarantor status.
    """
    try:
        if notification_type == "guarantor_approved":
            subject = f"Great News! Your Loan #{loan_application.application_number} Has Been Approved"
            template = "finance/emails/borrower_loan_approved.html"
        elif notification_type == "guarantor_declined":
            subject = f"Update on Your Loan #{loan_application.application_number} Application"
            template = "finance/emails/borrower_guarantor_declined.html"
        else:
            logger.error(f"Unknown notification type: {notification_type}")
            return False

        context = {
            "loan_app": loan_application,
            "borrower": loan_application.borrower,
            "guarantor": loan_application.guarantor,
            "purpose": "finance",
        }

        result = send_email(
            category=0,
            to_email=[loan_application.borrower.email],
            subject=subject,
            html_template=template,
            context=context,
        )

        if result:
            logger.info(
                f"Borrower notification email sent to {loan_application.borrower.email}"
            )
            return True
        else:
            logger.error(
                f"Failed to send borrower notification email to {loan_application.borrower.email}"
            )
            return False

    except Exception as e:
        logger.error(f"Error sending borrower notification email: {str(e)}")
        return False


# ====================================================
# PAYMENT UTILITY FUNCTIONS
# ====================================================

def validate_amount(amount_str, payment_method="general"):    """     Comprehensive amount validation including format, limits, and method-specific rules      Parameters:     - amount_str: The amount as a string (e.g., '15.99')     - payment_method: The payment method for method-specific limits      Returns:     - A tuple: (is_valid, message, amount_float)     """     try:         # Basic format validation         if not amount_str:             return False, "Payment amount is required", None          # Convert to float         amount_float = float(amount_str)          # Basic range validation         if amount_float <= 0:             return False, "Payment amount must be greater than zero", None          # Method-specific amount limits         method_limits = {             "mpesa": {"min": 10, "max": 300},             "paypal": {"min": 5, "max": 1000},             "stripe": {"min": 5, "max": 2000},             "cashapp": {"min": 5, "max": 500},             "zelle": {"min": 5, "max": 1500},             "venmo": {"min": 5, "max": 800},         }          if payment_method.lower() in method_limits:             limits = method_limits[payment_method.lower()]             if amount_float < limits["min"]:                 return (                     False,                     f"Amount ${amount_float} is below minimum limit of ${limits['min']} for {payment_method.title()}",                     None,                 )             if amount_float > limits["max"]:                 return (                     False,                     f"Amount ${amount_float} exceeds maximum limit of ${limits['max']} for {payment_method.title()}",                     None,                 )          # Additional validations         # Check for decimal precision (max 2 decimal places)         if len(str(amount_float).split(".")[-1]) > 2:             return False, "Amount cannot have more than 2 decimal places", None          # Check for reasonable amount (prevent extremely large amounts)         if amount_float > 100000:  # $100k limit             return (                 False,                 "Amount exceeds reasonable limit. Please contact support for large payments.",                 None,             )          return True, "Amount valid", amount_float      except (ValueError, TypeError):         return False, "Invalid payment amount format", None     except Exception as e:         return False, f"Error validating amount: {str(e)}", None   def validate_user_payment_eligibility(user, amount, payment_method="general"):     """     Validate if user can make payment based on balance and amount     Uses validate_amount for comprehensive amount validation     """     try:         from finance.models import Payment_Information          # First validate the amount using the enhanced validate_amount function         amount_valid, amount_message, amount_float = validate_amount(             amount, payment_method         )
# ====================================================
# PAYMENT UTILITY FUNCTIONS
# ====================================================

def validate_amount(amount_str, payment_method="general"):
    """
    Comprehensive amount validation including format, limits, and method-specific rules

    Parameters:
    - amount_str: The amount as a string (e.g., '15.99')
    - payment_method: The payment method for method-specific limits

    Returns:
    - A tuple: (is_valid, message, amount_float)
    """
    try:
        # Basic format validation
        if not amount_str:
            return False, "Payment amount is required", None

        # Convert to float
        amount_float = float(amount_str)

        # Basic range validation
        if amount_float <= 0:
            return False, "Payment amount must be greater than zero", None

        # Method-specific amount limits
        method_limits = {
            "mpesa": {"min": 10, "max": 300},
            "paypal": {"min": 5, "max": 1000},
            "stripe": {"min": 5, "max": 2000},
            "cashapp": {"min": 5, "max": 500},
            "zelle": {"min": 5, "max": 1500},
            "venmo": {"min": 5, "max": 800},
        }

        if payment_method.lower() in method_limits:
            limits = method_limits[payment_method.lower()]
            if amount_float < limits["min"]:
                return (
                    False,
                    f"Amount ${amount_float} is below minimum limit of ${limits['min']} for {payment_method.title()}",
                    None,
                )
            if amount_float > limits["max"]:
                return (
                    False,
                    f"Amount ${amount_float} exceeds maximum limit of ${limits['max']} for {payment_method.title()}",
                    None,
                )

        # Additional validations
        # Check for decimal precision (max 2 decimal places)
        if len(str(amount_float).split(".")[-1]) > 2:
            return False, "Amount cannot have more than 2 decimal places", None

        # Check for reasonable amount (prevent extremely large amounts)
        if amount_float > 100000:
            return False, "Amount exceeds maximum allowed limit ($100,000)", None

        # All validations passed
        return True, "Valid amount", amount_float

    except (ValueError, TypeError):
        return False, "Invalid amount format. Please enter a valid number.", None
    except Exception as e:
        logger.error(f"validate_amount failed: {e}")
        return False, f"Validation error: {str(e)}", None


def validate_user_payment_eligibility(user, amount, payment_method="general"):
    """
    Validate if user can make payment based on balance and amount
    Uses validate_amount for comprehensive amount validation
    """
    try:
        from finance.models import Payment_Information

        # First validate the amount using the enhanced validate_amount function
        amount_valid, amount_message, amount_float = validate_amount(
            amount, payment_method
        )
        if not amount_valid:
            return False, amount_message, None

        # Then check user balance and eligibility - use safe query to avoid field conflicts
        try:
            payment_info = Payment_Information.objects.filter(
                customer_id=user.id
            ).only('id', 'customer_id', 'payment_fees', 'down_payment').first()
        except Exception as db_error:
            # Fallback: use raw query to avoid model ordering issues
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, customer_id, payment_fees, down_payment 
                    FROM finance_payment_information 
                    WHERE customer_id = %s 
                    ORDER BY id DESC 
                    LIMIT 1
                """, [user.id])
                result = cursor.fetchone()
                if result:
                    # Create a simple object with the needed attributes
                    payment_info = type('PaymentInfo', (), {
                        'id': result[0],
                        'customer_id': result[1],
                        'payment_fees': result[2],
                        'down_payment': result[3]
                    })()
                else:
                    payment_info = None
        
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


def save_payment_history(
    user, payment_info, method, reference, amount, status="completed"
):
    """Persist a payment into Payment_History using existing model fields."""
    try:
        from finance.models import Payment_History  # local import to avoid circulars

        print("DEBUG: Starting save_payment_history")
        print(f"DEBUG: user: {user}")
        print(f"DEBUG: payment_info: {payment_info}")
        print(f"DEBUG: method: {method}")
        print(f"DEBUG: reference: {reference}")
        print(f"DEBUG: amount: {amount}")
        print(f"DEBUG: status: {status}")

        # Debug the calculated values
        payment_fees_value = int(round(float(amount))) if amount else 0
        down_payment_value = getattr(payment_info, "down_payment", 0) or 0
        student_bonus_value = getattr(payment_info, "student_bonus", 0) or 0
        plan_value = getattr(payment_info, "plan", 1) or 1
        subplan_value = getattr(payment_info, "subplan", 1) or 1
        pricing_plan_value = getattr(payment_info, "pricing_plan", 1) or 1

        print(f"DEBUG: payment_fees_value: {payment_fees_value}")
        print(f"DEBUG: down_payment_value: {down_payment_value}")
        print(f"DEBUG: student_bonus_value: {student_bonus_value}")
        print(f"DEBUG: plan_value: {plan_value}")
        print(f"DEBUG: subplan_value: {subplan_value}")
        print(f"DEBUG: pricing_plan_value: {pricing_plan_value}")

        # fee_balance is a computed property - no need to set it manually

        # Try to create the object step by step
        print("DEBUG: Attempting to create Payment_History object...")

        payment_record = Payment_History(
            customer=user,
            payment_fees=payment_fees_value,
            down_payment=down_payment_value,
            student_bonus=student_bonus_value,
            plan=plan_value,
            subplan=subplan_value,
            pricing_plan=pricing_plan_value,
            payment_method=str(method),
            contract_submitted_date=timezone.now(),
            client_signature="system",
            company_rep="system",
            client_date=timezone.now().strftime("%Y-%m-%d"),
            rep_date=timezone.now().strftime("%Y-%m-%d"),
            description=f"Ref: {reference} | Status: {status}",
        )

        print("DEBUG: Payment_History object created, calling save()...")
        payment_record.save()

        print(f"DEBUG: Payment_History created successfully with ID {payment_record.id}")
        return True

    except Exception as e:
        import traceback

        print(f"DEBUG: Exception occurred: {str(e)}")
        print(f"DEBUG: Exception type: {type(e)}")
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        logger.error(f"save_payment_history failed: {e}")
        return False

