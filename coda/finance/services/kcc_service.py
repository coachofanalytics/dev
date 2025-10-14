from decimal import Decimal
from django.utils import timezone
from core.services.base import ModelService
import logging

logger = logging.getLogger(__name__)

class KCCOptimizationService(ModelService):
    """Service for KCC loan optimization - FOLLOWING OUR ARCHITECTURE"""
    
    def __init__(self):
        super().__init__()
    
    def get_kcc_eligibility(self, user):
        """Get comprehensive KCC eligibility information"""
        try:
            # CRITICAL: Staff users are NEVER KCC members
            if user.category == 2:
                return {
                    'status': 'success',
                    'is_kcc_member': False,
                    'message': 'Staff users are not eligible for KCC membership'
                }
            
            profile = getattr(user, 'profile', None)
            if not profile or not profile.is_karen_country_club_member:
                return {
                    'status': 'success',
                    'is_kcc_member': False,
                    'message': 'User is not a KCC member'
                }
            
            # Check membership expiry
            is_expired = False
            if profile.kcc_membership_expiry:
                is_expired = profile.kcc_membership_expiry < timezone.now().date()
            
            # Get performance tier from UserProfileService
            from accounts.services.user_service import UserProfileService
            user_profile_service = UserProfileService()
            performance_tier = user_profile_service.calculate_performance_tier(profile)
            
            return {
                'status': 'success',
                'is_kcc_member': True,
                'is_expired': is_expired,
                'membership_number': profile.kcc_membership_number,
                'membership_date': profile.kcc_membership_date,
                'membership_expiry': profile.kcc_membership_expiry,
                'performance_tier': performance_tier,
                'message': f'KCC {performance_tier} member with full benefits'
            }
            
        except Exception as e:
            return self.handle_error(e, f"Getting KCC eligibility for user {user.username}")
    
    def get_kcc_loan_limits(self, user):
        """Get KCC-specific loan limits based on performance tier"""
        try:
            eligibility = self.get_kcc_eligibility(user)
            
            # Check if eligibility check failed
            if eligibility.get('status') == 'error':
                return eligibility
            
            if not eligibility.get('is_kcc_member', False):
                return {
                    'status': 'error',
                    'message': 'User is not a KCC member'
                }
            
            profile = user.profile
            performance_tier = profile.performance_tier
            
            # Get tier-specific limits from configuration
            from finance.models import LoanConfiguration
            try:
                kcc_config = LoanConfiguration.objects.filter(
                    name__icontains='kcc',
                    is_active=True
                ).first()
                
                limits = kcc_config.get_limits_for_user(user, profile)
                
                return {
                    'status': 'success',
                    'limits': limits,
                    'performance_tier': performance_tier,
                    'kcc_benefits': True
                }
                
            except LoanConfiguration.DoesNotExist:
                # Fallback to default KCC limits
                return self._get_default_kcc_limits(performance_tier)
                
        except Exception as e:
            return self.handle_error(e, f"Getting KCC loan limits for user {user.username}")
    
    def _get_default_kcc_limits(self, performance_tier):
        """Get default KCC limits when configuration is not available"""
        default_limits = {
            'new': {
                'min_amount': Decimal('200.00'),
                'max_amount': Decimal('500.00'),
                'interest_rate': Decimal('12.00'),
                'term_weeks': 8
            },
            'bronze': {
                'min_amount': Decimal('500.00'),
                'max_amount': Decimal('750.00'),
                'interest_rate': Decimal('10.00'),
                'term_weeks': 12
            },
            'silver': {
                'min_amount': Decimal('750.00'),
                'max_amount': Decimal('1000.00'),
                'interest_rate': Decimal('9.00'),
                'term_weeks': 16
            },
            'gold': {
                'min_amount': Decimal('1000.00'),
                'max_amount': Decimal('1500.00'),
                'interest_rate': Decimal('8.00'),
                'term_weeks': 24
            },
            'platinum': {
                'min_amount': Decimal('1500.00'),
                'max_amount': Decimal('3000.00'),
                'interest_rate': Decimal('7.00'),
                'term_weeks': 52
            }
        }
        
        limits = default_limits.get(performance_tier, default_limits['new'])
        
        return {
            'status': 'success',
            'limits': limits,
            'performance_tier': performance_tier,
            'kcc_benefits': True,
            'note': 'Using default KCC limits (configuration not found)'
        }
    
    def calculate_kcc_benefits(self, user, loan_amount, term_weeks):
        """Calculate KCC-specific benefits for a loan"""
        try:
            eligibility = self.get_kcc_eligibility(user)
            if not eligibility['is_kcc_member']:
                return {
                    'status': 'error',
                    'message': 'User is not eligible for KCC benefits'
                }
            
            profile = user.profile
            performance_tier = profile.performance_tier
            
            # Calculate benefits based on tier
            benefits = self._calculate_tier_benefits(performance_tier, loan_amount, term_weeks)
            
            return {
                'status': 'success',
                'benefits': benefits,
                'performance_tier': performance_tier
            }
            
        except Exception as e:
            return self.handle_error(e, f"Calculating KCC benefits for user {user.username}")
    
    def _calculate_tier_benefits(self, performance_tier, loan_amount, term_weeks):
        """Calculate benefits based on performance tier"""
        tier_multipliers = {
            'new': {'amount_multiplier': 1.0, 'interest_discount': 0.0, 'term_extension': 0},
            'bronze': {'amount_multiplier': 1.1, 'interest_discount': 1.0, 'term_extension': 1},
            'silver': {'amount_multiplier': 1.2, 'interest_discount': 2.0, 'term_extension': 2},
            'gold': {'amount_multiplier': 1.3, 'interest_discount': 3.0, 'term_extension': 3},
            'platinum': {'amount_multiplier': 1.5, 'interest_discount': 5.0, 'term_extension': 4}
        }
        
        multipliers = tier_multipliers.get(performance_tier, tier_multipliers['new'])
        
        return {
            'amount_multiplier': multipliers['amount_multiplier'],
            'interest_discount': multipliers['interest_discount'],
            'term_extension': multipliers['term_extension'],
            'enhanced_amount': loan_amount * multipliers['amount_multiplier'],
            'enhanced_term': term_weeks + multipliers['term_extension']
        } 