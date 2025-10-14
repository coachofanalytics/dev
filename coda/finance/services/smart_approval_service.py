"""
Smart Approval Service for Budget Requests
Automatically determines approval requirements based on category and amount
"""

from decimal import Decimal

class SmartApprovalService:
    """Smart approval service that determines auto-approval based on category and amount"""
    
    def __init__(self):
        # Define known categories that should auto-approve
        self.auto_approve_categories = {
            'utilities': {
                'categories': ['Utilities'],
                'subcategories': ['Electricity', 'Internet and phone services'],
                'max_amount': Decimal('50000')  # Up to 50k for utilities
            },
            'it_services': {
                'categories': ['IT and Software'],
                'subcategories': ['Communication Tools', 'Communication Services'],
                'max_amount': Decimal('15000')  # Up to 15k for IT services
            },
            'salaries': {
                'categories': ['Salaries and Wages', 'Human Resources'],
                'subcategories': ['Regular employee salaries', 'Payroll services'],
                'max_amount': Decimal('15000')  # Up to 15k for salaries
            }
        }
    
    def should_auto_approve(self, budget_request):
        """
        Determine if a budget request should be auto-approved
        Returns: (should_auto_approve: bool, reason: str)
        """
        amount = budget_request.amount
        category = budget_request.budget_category
        subcategory = None  # BudgetRequest doesn't have budget_subcategory field
        
        # Check each auto-approve category
        for category_type, rules in self.auto_approve_categories.items():
            # Check if amount is within limits
            if amount > rules['max_amount']:
                continue
            
            # Check category match
            if category and category.name in rules['categories']:
                return True, f"Auto-approved: {category.name} under {rules['max_amount']} KES"
        
        # Check for specific known items
        if self._is_known_utility(amount, category, subcategory):
            return True, f"Auto-approved: Known utility bill under {amount} KES"
        
        if self._is_safaricom_internet(amount, category, subcategory):
            return True, f"Auto-approved: Internet/Safaricom bill under {amount} KES"
        
        if self._is_salary_payment(amount, category, subcategory):
            return True, f"Auto-approved: Salary payment under {amount} KES"
        
        # Default: require manual approval
        return False, "Requires manual approval: Variable expense"
    
    def _is_known_utility(self, amount, category, subcategory):
        """Check if this is a known utility bill"""
        if not category:
            return False
        
        utility_keywords = ['electricity', 'utility', 'kplc', 'power']
        category_name = category.name.lower()
        
        if any(keyword in category_name for keyword in utility_keywords):
            return amount <= Decimal('50000')
        
        return False
    
    def _is_safaricom_internet(self, amount, category, subcategory):
        """Check if this is a Safaricom/Internet bill"""
        if not category:
            return False
        
        internet_keywords = ['internet', 'phone', 'communication', 'safaricom', 'data']
        category_name = category.name.lower()
        
        if any(keyword in category_name for keyword in internet_keywords):
            return amount <= Decimal('15000')
        
        return False
    
    def _is_salary_payment(self, amount, category, subcategory):
        """Check if this is a salary payment from management tasks"""
        if not category:
            return False
        
        salary_keywords = ['salary', 'wage', 'payroll', 'human resources', 'employee']
        category_name = category.name.lower()
        
        if any(keyword in category_name for keyword in salary_keywords):
            return amount <= Decimal('15000')
        
        return False
    
    def process_budget_request(self, budget_request):
        """Process a budget request and set appropriate status"""
        should_auto_approve, reason = self.should_auto_approve(budget_request)
        
        if should_auto_approve:
            budget_request.status = 'approved'
            budget_request.approved_by = budget_request.created_by  # Self-approved
            budget_request.save()
            print(f"✅ AUTO-APPROVED: {reason}")
            return True
        else:
            budget_request.status = 'submitted'
            budget_request.save()
            print(f"📋 MANUAL APPROVAL REQUIRED: {reason}")
            return False
