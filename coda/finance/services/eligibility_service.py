from decimal import Decimal
from django.utils import timezone
from core.services.base import ModelService
import logging

logger = logging.getLogger(__name__)

class EligibilityService(ModelService):
    """Unified eligibility checking service for all user types"""
    
    def __init__(self, user):
        super(EligibilityService, self).__init__()
        self.user = user
        self.user_type = self._determine_user_type()
    
    def _determine_user_type(self):
        """Determine user type based on category and profile"""
        try:
            # PRIORITY 1: Staff users are always staff, never KCC
            if self.user.category == 2:
                return 'staff'
            # PRIORITY 2: Only check KCC if not staff
            elif self._check_kcc_membership():
                return 'kcc_member'
            else:
                return 'external'
        except Exception as e:
            self.logger.error("Error determining user type for {}: {}".format(self.user.username, e))
            return 'external'
    
    def _check_kcc_membership(self):
        """Check if user is a Karen Country Club member (non-staff only)"""
        try:
            # CRITICAL: Staff users are NEVER KCC members
            if self.user.category == 2:
                return False
                
            if hasattr(self.user, 'profile') and self.user.profile:
                profile = self.user.profile
                if profile.is_karen_country_club_member:
                    if profile.kcc_membership_expiry:
                        if profile.kcc_membership_expiry >= timezone.now().date():
                            return True
                        else:
                            self.logger.warning("KCC membership expired for user {}".format(self.user.username))
                            return False
                    else:
                        # No expiry date, assume valid
                        return True
            return False
        except Exception as e:
            self.logger.error("Error checking KCC membership for user {}: {}".format(self.user.username, e))
            return False
    
    def check_loan_eligibility(self):
        """Unified eligibility check for all user types"""
        try:
            if self.user_type == 'staff':
                return self._check_staff_eligibility()
            elif self.user_type == 'kcc_member':
                return self._check_kcc_eligibility()
            else:
                return self._check_external_eligibility()
        except Exception as e:
            return self.handle_error(e, "Checking loan eligibility for user {}".format(self.user.username))
    
    def _check_staff_eligibility(self):
        """Staff-specific eligibility logic"""
        try:
            return {
                'eligible': True,
                'reason': 'eligible',
                'message': 'You are eligible for a staff loan.',
                'loan_limits': {
                    'min_amount': Decimal('100.00'),
                    'max_amount': Decimal('5000.00'),
                    'user_type': 'staff'
                },
                'unpaid_loans': [],
                'total_outstanding': Decimal('0.00'),
                'user_type': 'staff'
            }
        except Exception as e:
            return self.handle_error(e, "Checking staff eligibility for user {}".format(self.user.username))
    
    def _check_kcc_eligibility(self):
        """KCC-specific eligibility logic"""
        try:
            return {
                'eligible': True,
                'reason': 'eligible',
                'message': 'You are eligible for a KCC premium loan.',
                'loan_limits': {
                    'min_amount': Decimal('500.00'),
                    'max_amount': Decimal('10000.00'),
                    'user_type': 'kcc_member'
                },
                'unpaid_loans': [],
                'total_outstanding': Decimal('0.00'),
                'user_type': 'kcc_member'
            }
        except Exception as e:
            return self.handle_error(e, "Checking KCC eligibility for user {}".format(self.user.username))
    
    def _check_external_eligibility(self):
        """External user eligibility logic"""
        try:
            return {
                'eligible': True,
                'reason': 'eligible',
                'message': 'You are eligible for a loan.',
                'loan_limits': {
                    'min_amount': Decimal('200.00'),
                    'max_amount': Decimal('2000.00'),
                    'user_type': 'external'
                },
                'unpaid_loans': [],
                'total_outstanding': Decimal('0.00'),
                'user_type': 'external'
            }
        except Exception as e:
            return self.handle_error(e, "Checking external eligibility for user {}".format(self.user.username))