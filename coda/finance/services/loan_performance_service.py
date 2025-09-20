"""
Loan Performance Service
Handles all business logic for loan performance tracking and KCC scaling
"""

from decimal import Decimal
from django.utils import timezone
from django.db.models import Q, Count, Avg
from core.services.base import ModelService
import logging

logger = logging.getLogger(__name__)

class LoanPerformanceService(ModelService):
    """Service for loan performance business logic - FOLLOWING OUR ARCHITECTURE"""
    
    def __init__(self):
        super().__init__()
    
    def calculate_next_loan_amount(self, performance_record):
        """Calculate next loan amount based on performance and tier scaling (KCC only)"""
        if not performance_record.is_kcc_member:
            return None
        
        try:
            # Get user's current tier configuration
            profile = performance_record.user.profile
            if not profile:
                return None
            
            current_tier = getattr(profile, 'performance_tier', 'new')
            
            # Get tier configuration from LoanConfiguration
            try:
                from finance.models import LoanConfiguration
                tier_config = LoanConfiguration.objects.filter(
                    tier_modifiers__has_key=current_tier,
                    is_active=True
                ).first()
                
                if not tier_config:
                    return None
                
                # Calculate based on payment timing
                scaling_multiplier = self._get_scaling_multiplier(performance_record.payment_timing)
                
                # Apply scaling to current loan amount
                current_amount = performance_record.loan_application.amount_requested
                next_amount = current_amount * scaling_multiplier
                
                # Get tier limits from configuration
                tier_modifiers = tier_config.tier_modifiers
                tier_multiplier = Decimal(str(tier_modifiers.get(current_tier, 1.0)))
                
                # Apply tier multiplier
                next_amount = next_amount * tier_multiplier
                
                # Enforce reasonable limits
                next_amount = self._enforce_loan_limits(next_amount)
                
                # Update the model
                performance_record.scaling_factor_applied = scaling_multiplier
                performance_record.next_loan_amount = next_amount.quantize(Decimal('0.01'))
                performance_record.save()
                
                return performance_record.next_loan_amount
                
            except Exception as e:
                self.logger.error(f"Error getting tier configuration: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error calculating next loan amount: {e}")
            return None
    
    def update_performance_score(self, performance_record):
        """Update performance score based on payment timing"""
        try:
            score_change = self._get_score_change(performance_record.payment_timing)
            
            new_score = performance_record.performance_score + score_change
            performance_record.performance_score = max(0, min(100, new_score))
            
            # Update consecutive counters
            self._update_consecutive_counters(performance_record)
            
            performance_record.save()
            return performance_record.performance_score
            
        except Exception as e:
            self.logger.error(f"Error updating performance score: {e}")
            return None
    
    def get_performance_summary(self, performance_record):
        """Get comprehensive performance summary"""
        try:
            return {
                'user_type': performance_record.user_type,
                'is_kcc_member': performance_record.is_kcc_member,
                'performance_score': performance_record.performance_score,
                'payment_timing': performance_record.payment_timing,
                'consecutive_successful': performance_record.consecutive_successful_loans,
                'consecutive_late': performance_record.consecutive_late_payments,
                'scaling_factor': performance_record.scaling_factor_applied,
                'next_loan_amount': performance_record.next_loan_amount,
                'tier_progression': performance_record.tier_progression,
                'performance_category': performance_record.performance_category,
                'has_kcc_benefits': performance_record.has_kcc_benefits,
            }
        except Exception as e:
            self.logger.error(f"Error getting performance summary: {e}")
            return {}
    
    def get_user_performance_history(self, user):
        """Get comprehensive performance history for a user"""
        try:
            from finance.models import LoanPerformance
            
            performances = LoanPerformance.objects.filter(user=user).order_by('-created_at')
            
            if not performances.exists():
                return {
                    'total_records': 0,
                    'average_score': 0,
                    'best_performance': None,
                    'worst_performance': None,
                    'kcc_benefits_earned': 0,
                    'recommendations': []
                }
            
            # Calculate statistics
            total_records = performances.count()
            average_score = performances.aggregate(avg=Avg('performance_score'))['avg'] or 0
            best_performance = performances.order_by('performance_score').first()
            worst_performance = performances.order_by('-performance_score').first()
            kcc_benefits_earned = performances.filter(
                Q(scaling_factor_applied__isnull=False) | 
                Q(next_loan_amount__isnull=False)
            ).count()
            
            # Generate recommendations
            recommendations = self._generate_performance_recommendations(performances)
            
            return {
                'total_records': total_records,
                'average_score': round(average_score, 2),
                'best_performance': best_performance.payment_timing if best_performance else None,
                'worst_performance': worst_performance.payment_timing if worst_performance else None,
                'kcc_benefits_earned': kcc_benefits_earned,
                'recommendations': recommendations,
                'recent_performances': list(performances[:5].values(
                    'payment_timing', 'performance_score', 'created_at'
                ))
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user performance history: {e}")
            return {}
    
    def get_system_performance_analytics(self):
        """Get system-wide performance analytics"""
        try:
            from finance.models import LoanPerformance
            
            total_performances = LoanPerformance.objects.count()
            
            if total_performances == 0:
                return {'status': 'no_data'}
            
            # Performance distribution
            performance_distribution = {
                'excellent': LoanPerformance.objects.filter(performance_score__gte=80).count(),
                'good': LoanPerformance.objects.filter(performance_score__gte=60, performance_score__lt=80).count(),
                'fair': LoanPerformance.objects.filter(performance_score__gte=40, performance_score__lt=60).count(),
                'poor': LoanPerformance.objects.filter(performance_score__lt=40).count(),
            }
            
            # Payment timing distribution
            timing_distribution = {}
            for choice in LoanPerformance.PAYMENT_TIMING_CHOICES:
                timing_distribution[choice[0]] = LoanPerformance.objects.filter(
                    payment_timing=choice[0]
                ).count()
            
            # KCC benefits usage
            kcc_benefits_used = LoanPerformance.objects.filter(
                Q(scaling_factor_applied__isnull=False) | 
                Q(next_loan_amount__isnull=False)
            ).count()
            
            return {
                'total_performances': total_performances,
                'performance_distribution': performance_distribution,
                'timing_distribution': timing_distribution,
                'kcc_benefits_used': kcc_benefits_used,
                'average_score': LoanPerformance.objects.aggregate(
                    avg=Avg('performance_score')
                )['avg'] or 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system performance analytics: {e}")
            return {'status': 'error', 'message': str(e)}
    
    # PRIVATE HELPER METHODS
    
    def _get_scaling_multiplier(self, payment_timing):
        """Get scaling multiplier based on payment timing"""
        scaling_rules = {
            'early': Decimal('1.20'),    # +20%
            'on_time': Decimal('1.20'),  # +20%
            'late': Decimal('0.80'),     # -20%
            'defaulted': Decimal('1.00') # No change
        }
        return scaling_rules.get(payment_timing, Decimal('1.00'))
    
    def _get_score_change(self, payment_timing):
        """Get score change based on payment timing"""
        score_rules = {
            'early': 20,
            'on_time': 10,
            'late': -15,
            'defaulted': -50
        }
        return score_rules.get(payment_timing, 0)
    
    def _enforce_loan_limits(self, amount):
        """Enforce reasonable loan amount limits"""
        min_amount = Decimal('100.00')
        max_amount = Decimal('10000.00')  # Can be configured
        return max(min_amount, min(amount, max_amount))
    
    def _update_consecutive_counters(self, performance_record):
        """Update consecutive success/failure counters"""
        if performance_record.payment_timing in ['early', 'on_time']:
            performance_record.consecutive_successful_loans += 1
            performance_record.consecutive_late_payments = 0
        else:
            performance_record.consecutive_late_payments += 1
            performance_record.consecutive_successful_loans = 0
    
    def _generate_performance_recommendations(self, performances):
        """Generate performance improvement recommendations"""
        recommendations = []
        
        # Check for late payments
        late_payments = performances.filter(payment_timing='late').count()
        if late_payments > 0:
            recommendations.append(f"Consider setting up automatic payments to avoid {late_payments} late payment(s)")
        
        # Check for consecutive failures
        recent_performances = performances[:5]
        consecutive_late = 0
        for perf in recent_performances:
            if perf.payment_timing in ['late', 'defaulted']:
                consecutive_late += 1
            else:
                consecutive_late = 0
        
        if consecutive_late >= 3:
            recommendations.append("Multiple consecutive late payments detected. Consider restructuring loan terms.")
        
        # Check for KCC eligibility
        kcc_performances = performances.filter(
            Q(scaling_factor_applied__isnull=False) | 
            Q(next_loan_amount__isnull=False)
        )
        if kcc_performances.exists():
            recommendations.append("You're earning KCC benefits! Maintain good payment history to increase benefits.")
        
        return recommendations 