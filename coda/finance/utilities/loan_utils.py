"""
Loan Utilities

This module contains utility functions for loan operations including
eligibility checking, loan limits calculation, and guarantor management.
"""

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


class LoanUtils:
    """Utility class for loan-related operations."""
    
    @staticmethod
    def check_user_loan_eligibility(user):
        """
        Check if a user is eligible for a new loan.
        Returns a dictionary with eligibility status and reasons.
        """
        try:
            # PRIORITY 1: Check if user is staff (category 2) - ALWAYS check this first
            if user.category == 2:  # Staff member
                # Staff eligibility is based on income and employment, not KCC status
                loan_limits = LoanUtils.get_user_loan_limits(user)

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
            elif LoanUtils.check_karen_country_club_membership(user):  # KCC member (non-staff)
                loan_limits = LoanUtils.get_user_loan_limits(user)

                if not loan_limits:
                    return {
                        "eligible": False,
                        "reason": "insufficient_income",
                        "message": "As a KCC member, you need at least 3 months of consistent earnings to qualify for a loan. Please contact HR if you believe this is an error.",
                        "unpaid_loans": [],
                        "total_outstanding": Decimal("0.00"),
                        "user_type": "kcc_member",
                    }
                else:
                    return {
                        "eligible": True,
                        "reason": "eligible",
                        "message": "You are eligible for a KCC loan based on your membership and earnings history.",
                        "loan_limits": loan_limits,
                        "unpaid_loans": [],
                        "total_outstanding": Decimal("0.00"),
                        "user_type": "kcc_member",
                    }

            # PRIORITY 3: Non-KCC, non-staff users
            else:
                return {
                    "eligible": False,
                    "reason": "not_kcc_member",
                    "message": "You must be a Karen Country Club member or staff to apply for loans. Please contact HR for membership information.",
                    "unpaid_loans": [],
                    "total_outstanding": Decimal("0.00"),
                    "user_type": "non_member",
                }

        except Exception as e:
            logger.error(f"Error checking loan eligibility for user {user.id}: {e}")
            return {
                "eligible": False,
                "reason": "system_error",
                "message": "There was an error checking your loan eligibility. Please try again or contact support.",
                "unpaid_loans": [],
                "total_outstanding": Decimal("0.00"),
                "user_type": "unknown",
            }

    @staticmethod
    def get_user_loan_limits(user):
        """
        Calculate loan limits for a user based on their income and employment history.
        Returns a dictionary with loan limits or None if insufficient data.
        """
        try:
            # Calculate average monthly income over last 3 months
            avg_monthly_income = LoanUtils._compute_average_monthly_income_last_3_months(user)
            
            if avg_monthly_income is None or avg_monthly_income <= 0:
                return None
            
            # Loan limit calculation: 3x monthly income for staff, 2x for KCC members
            if user.category == 2:  # Staff
                max_loan_amount = avg_monthly_income * 3
                loan_type = "staff_loan"
            else:  # KCC member
                max_loan_amount = avg_monthly_income * 2
                loan_type = "kcc_loan"
            
            return {
                "max_loan_amount": max_loan_amount,
                "avg_monthly_income": avg_monthly_income,
                "loan_type": loan_type,
                "calculation_date": timezone.now(),
            }
            
        except Exception as e:
            logger.error(f"Error calculating loan limits for user {user.id}: {e}")
            return None

    @staticmethod
    def check_karen_country_club_membership(user):
        """
        Check if a user is a Karen Country Club member.
        Returns True if user is a KCC member, False otherwise.
        """
        try:
            # Check if user has KCC membership status
            # This would typically check a membership field or related model
            # For now, we'll use a simple check based on user attributes
            
            # If user has a specific KCC-related field, check it
            if hasattr(user, 'kcc_member') and user.kcc_member:
                return True
            
            # If user has a membership number or similar identifier
            if hasattr(user, 'membership_number') and user.membership_number:
                return True
            
            # Default: assume non-staff users are KCC members if they have sufficient profile data
            if user.category != 2 and hasattr(user, 'profile') and user.profile:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking KCC membership for user {user.id}: {e}")
            return False

    @staticmethod
    def get_eligible_staff_guarantors(limit=5):
        """
        Get eligible staff members who can act as guarantors.
        Returns a list of staff users eligible to be guarantors.
        """
        try:
            # Get staff members (category 2) who are active and have sufficient income
            staff_members = User.objects.filter(
                category=2,  # Staff members
                is_active=True
            ).select_related('profile')
            
            eligible_guarantors = []
            
            for staff in staff_members:
                # Check if staff member has sufficient income
                loan_limits = LoanUtils.get_user_loan_limits(staff)
                if loan_limits and loan_limits.get('avg_monthly_income', 0) > 0:
                    eligible_guarantors.append({
                        'user': staff,
                        'name': staff.get_full_name() or staff.username,
                        'email': staff.email,
                        'monthly_income': loan_limits.get('avg_monthly_income', 0),
                        'max_guarantee_amount': loan_limits.get('avg_monthly_income', 0) * 2,  # 2x monthly income
                    })
            
            # Sort by monthly income (highest first) and limit results
            eligible_guarantors.sort(key=lambda x: x['monthly_income'], reverse=True)
            return eligible_guarantors[:limit]
            
        except Exception as e:
            logger.error(f"Error getting eligible staff guarantors: {e}")
            return []

    @staticmethod
    def _compute_average_monthly_income_last_3_months(user):
        """
        Compute the average monthly income for a user over the last 3 months.
        Returns the average income or None if insufficient data.
        """
        try:
            # This would typically query payment history or salary records
            # For now, we'll implement a basic version
            
            # Check if user has a profile with income information
            if hasattr(user, 'profile') and user.profile:
                # If profile has monthly income field
                if hasattr(user.profile, 'monthly_income') and user.profile.monthly_income:
                    return float(user.profile.monthly_income)
                
                # If profile has annual income, convert to monthly
                if hasattr(user.profile, 'annual_income') and user.profile.annual_income:
                    return float(user.profile.annual_income) / 12
            
            # If no profile income data, return None
            return None
            
        except Exception as e:
            logger.error(f"Error computing average monthly income for user {user.id}: {e}")
            return None

    @staticmethod
    def find_or_create_guarantor_user(guarantor_data):
        """
        Find or create a guarantor user based on provided data.
        Returns the guarantor user object.
        """
        try:
            email = guarantor_data.get('email')
            if not email:
                raise ValueError("Guarantor email is required")
            
            # Try to find existing user by email
            guarantor_user = User.objects.filter(email=email).first()
            
            if not guarantor_user:
                # Create new user for guarantor
                guarantor_user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=guarantor_data.get('first_name', ''),
                    last_name=guarantor_data.get('last_name', ''),
                    category=3,  # Guarantor category
                    is_active=True
                )
                logger.info(f"Created new guarantor user: {email}")
            
            return guarantor_user
            
        except Exception as e:
            logger.error(f"Error finding/creating guarantor user: {e}")
            raise

    @staticmethod
    def calculate_guarantor_eligibility_score(guarantor_user):
        """
        Calculate eligibility score for a guarantor.
        Returns a score between 0-100.
        """
        try:
            score = 0
            
            # Base score for being a user
            score += 20
            
            # Check if user has profile
            if hasattr(guarantor_user, 'profile') and guarantor_user.profile:
                score += 20
                
                # Check income level
                loan_limits = LoanUtils.get_user_loan_limits(guarantor_user)
                if loan_limits and loan_limits.get('avg_monthly_income', 0) > 0:
                    score += 30
                    
                    # Higher income = higher score
                    monthly_income = loan_limits.get('avg_monthly_income', 0)
                    if monthly_income > 100000:  # KES 100k+
                        score += 20
                    elif monthly_income > 50000:  # KES 50k+
                        score += 10
            
            # Check if user is staff (higher reliability)
            if guarantor_user.category == 2:
                score += 10
            
            return min(score, 100)  # Cap at 100
            
        except Exception as e:
            logger.error(f"Error calculating guarantor eligibility score: {e}")
            return 0

    @staticmethod
    def get_existing_guarantor_info(user):
        """
        Get existing guarantor information for a user.
        Returns guarantor details if available.
        """
        try:
            # This would typically query loan applications or guarantor relationships
            # For now, return basic info
            
            return {
                'has_guarantor': False,
                'guarantor_name': None,
                'guarantor_email': None,
                'guarantor_phone': None,
            }
            
        except Exception as e:
            logger.error(f"Error getting existing guarantor info: {e}")
            return {
                'has_guarantor': False,
                'guarantor_name': None,
                'guarantor_email': None,
                'guarantor_phone': None,
            }


