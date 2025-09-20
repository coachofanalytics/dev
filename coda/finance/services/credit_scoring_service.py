"""
Credit Scoring and Loan Progression Service

This service handles:
1. Credit scoring based on payment history
2. Loan tier progression
3. Automatic loan amount recommendations
"""
from decimal import Decimal
from django.db.models import Q, Sum, Count, Avg
from datetime import datetime, timedelta
from finance.models import LoanApplication, Payment
from accounts.models import CustomerUser


class CreditScoringService:
    """Service for calculating credit scores and determining loan progression"""
    
    def __init__(self, user):
        self.user = user
        self.score = None
        self.tier = None
        self.recommended_amount = None
        self.recommended_product = None
    
    def calculate_credit_score(self):
        """
        Calculate credit score based on:
        - Payment history (on-time payments)
        - Loan completion rate
        - Average loan amount
        - Time since last loan
        - Number of successful loans
        """
        print(f"🔍 DEBUG: Calculating credit score for {self.user.username}")
        
        # Get user's loan history
        user_loans = LoanApplication.objects.filter(borrower=self.user)
        
        if not user_loans.exists():
            # New user - start at Tier 1
            self.score = 300  # Base score for new users
            self.tier = 1
            print(f"🔍 DEBUG: New user - base score: {self.score}, tier: {self.tier}")
            return self.score
        
        # Calculate payment history score (0-400 points)
        payment_score = self._calculate_payment_history_score(user_loans)
        
        # Calculate loan completion score (0-300 points)
        completion_score = self._calculate_completion_score(user_loans)
        
        # Calculate amount progression score (0-200 points)
        amount_score = self._calculate_amount_progression_score(user_loans)
        
        # Calculate consistency score (0-100 points)
        consistency_score = self._calculate_consistency_score(user_loans)
        
        # Total score (300-1000)
        self.score = 300 + payment_score + completion_score + amount_score + consistency_score
        
        # Determine tier based on score
        self.tier = self._determine_tier(self.score)
        
        print(f"🔍 DEBUG: Credit score breakdown:")
        print(f"  Base score: 300")
        print(f"  Payment history: {payment_score}")
        print(f"  Completion rate: {completion_score}")
        print(f"  Amount progression: {amount_score}")
        print(f"  Consistency: {consistency_score}")
        print(f"  Total score: {self.score}")
        print(f"  Determined tier: {self.tier}")
        
        return self.score
    
    def _calculate_payment_history_score(self, user_loans):
        """Calculate score based on on-time payments (0-400 points)"""
        # Count loans with good payment history
        good_payment_loans = user_loans.filter(
            status__in=['repaid', 'completed'],
            # Add conditions for on-time payments when Payment model is available
        )
        
        total_loans = user_loans.count()
        if total_loans == 0:
            return 0
        
        good_payment_rate = good_payment_loans.count() / total_loans
        return int(good_payment_rate * 400)
    
    def _calculate_completion_score(self, user_loans):
        """Calculate score based on loan completion rate (0-300 points)"""
        completed_loans = user_loans.filter(status__in=['repaid', 'completed'])
        total_loans = user_loans.count()
        
        if total_loans == 0:
            return 0
        
        completion_rate = completed_loans.count() / total_loans
        return int(completion_rate * 300)
    
    def _calculate_amount_progression_score(self, user_loans):
        """Calculate score based on successful loan amount progression (0-200 points)"""
        if user_loans.count() < 2:
            return 0
        
        # Get average loan amount
        avg_amount = user_loans.aggregate(avg_amount=Avg('amount_requested'))['avg_amount'] or 0
        
        # Score based on average amount (higher amounts = higher score)
        if avg_amount >= 1000:
            return 200
        elif avg_amount >= 750:
            return 150
        elif avg_amount >= 500:
            return 100
        elif avg_amount >= 300:
            return 50
        else:
            return 0
    
    def _calculate_consistency_score(self, user_loans):
        """Calculate score based on consistent borrowing behavior (0-100 points)"""
        if user_loans.count() < 3:
            return 0
        
        # Check if user has consistent borrowing pattern
        # (e.g., regular intervals, similar amounts)
        recent_loans = user_loans.order_by('-created_at')[:3]
        
        # Simple consistency check - if all recent loans are completed
        completed_recent = 0
        for loan in recent_loans:
            if loan.status in ['repaid', 'completed']:
                completed_recent += 1
        
        consistency_rate = completed_recent / 3
        
        return int(consistency_rate * 100)
    
    def _determine_tier(self, score):
        """Determine loan tier based on credit score"""
        if score >= 900:
            return 4  # Tier 4: $500-$1000
        elif score >= 750:
            return 3  # Tier 3: $400-$750
        elif score >= 600:
            return 2  # Tier 2: $300-$500
        else:
            return 1  # Tier 1: $200-$300
    
    def get_recommended_loan_product(self):
        """Get the recommended loan product based on user's tier"""
        from finance.models import LoanProduct
        
        # Get loan products ordered by tier (min_amount)
        products = LoanProduct.objects.filter(
            is_active=True,
            product_type='kcc_member'
        ).order_by('min_amount')
        
        if not products.exists():
            return None
        
        # Get product for current tier
        tier_products = list(products)
        
        # Ensure tier doesn't exceed available products
        tier_index = min(self.tier - 1, len(tier_products) - 1)
        self.recommended_product = tier_products[tier_index]
        
        print(f"🔍 DEBUG: Recommended product for tier {self.tier}: {self.recommended_product.name}")
        return self.recommended_product
    
    def get_recommended_amount(self):
        """Get recommended loan amount based on tier and history"""
        if not self.recommended_product:
            self.get_recommended_loan_product()
        
        if not self.recommended_product:
            return Decimal('250.00')  # Default amount
        
        # Start with minimum amount for the tier
        min_amount = self.recommended_product.min_amount
        
        # If user has good history, allow higher amounts
        if self.score >= 800:
            # Excellent credit - allow maximum amount
            self.recommended_amount = self.recommended_product.max_amount
        elif self.score >= 700:
            # Good credit - allow 75% of max amount
            self.recommended_amount = min_amount + (self.recommended_product.max_amount - min_amount) * Decimal('0.75')
        elif self.score >= 600:
            # Fair credit - allow 50% of max amount
            self.recommended_amount = min_amount + (self.recommended_product.max_amount - min_amount) * Decimal('0.50')
        else:
            # Poor credit - minimum amount only
            self.recommended_amount = min_amount
        
        print(f"🔍 DEBUG: Recommended amount: ${self.recommended_amount}")
        return self.recommended_amount
    
    def get_credit_report(self):
        """Get comprehensive credit report for user"""
        self.calculate_credit_score()
        self.get_recommended_loan_product()
        self.get_recommended_amount()
        
        # Get user's loan history
        user_loans = LoanApplication.objects.filter(borrower=self.user)
        
        report = {
            'user': self.user,
            'credit_score': self.score,
            'tier': self.tier,
            'recommended_product': self.recommended_product,
            'recommended_amount': self.recommended_amount,
            'total_loans': user_loans.count(),
            'completed_loans': user_loans.filter(status__in=['repaid', 'completed']).count(),
            'pending_loans': user_loans.filter(status__in=['submitted', 'under_review', 'pending_guarantor']).count(),
            'overdue_loans': user_loans.filter(status='overdue').count(),
            'average_loan_amount': user_loans.aggregate(avg_amount=Avg('amount_requested'))['avg_amount'] or 0,
            'last_loan_date': user_loans.order_by('-created_at').first().created_at if user_loans.exists() else None,
            'tier_description': self._get_tier_description(self.tier),
            'next_tier_requirements': self._get_next_tier_requirements()
        }
        
        return report
    
    def _get_tier_description(self, tier):
        """Get human-readable tier description"""
        descriptions = {
            1: "Starter Tier - Building Credit History",
            2: "Growth Tier - Establishing Trust",
            3: "Established Tier - Proven Reliability", 
            4: "Premium Tier - Excellent Credit History"
        }
        return descriptions.get(tier, "Unknown Tier")
    
    def _get_next_tier_requirements(self):
        """Get requirements to move to next tier"""
        if self.tier >= 4:
            return "You're at the highest tier!"
        
        next_tier_score = {
            1: 600,  # Tier 1 -> Tier 2
            2: 750,  # Tier 2 -> Tier 3
            3: 900   # Tier 3 -> Tier 4
        }
        
        required_score = next_tier_score.get(self.tier, 600)
        points_needed = required_score - self.score
        
        return f"Need {points_needed} more points to reach Tier {self.tier + 1}"
