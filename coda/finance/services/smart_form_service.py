"""
Smart Form Service for Auto-Populating Budget Request Fields
Uses previous data and industry standards to simplify form filling
"""

from decimal import Decimal
from collections import defaultdict, Counter
from django.db.models import Count, Avg, Max

class SmartFormService:
    """Service to auto-populate form fields based on historical data and patterns"""
    
    def __init__(self):
        self.department_patterns = {
            'IT Department': {
                'common_categories': ['IT and Software', 'Utilities'],
                'common_subcategories': ['Internet and phone services', 'Communication Tools'],
                'typical_amounts': {'Internet and phone services': 15000, 'Communication Tools': 8000}
            },
            'HR Department': {
                'common_categories': ['Human Resources', 'Salaries and Wages'],
                'common_subcategories': ['Regular employee salaries', 'Payroll services'],
                'typical_amounts': {'Regular employee salaries': 15000, 'Payroll services': 5000}
            },
            'Finance Department': {
                'common_categories': ['Operational Expenses', 'IT and Software'],
                'common_subcategories': ['Financial software', 'Accounting services'],
                'typical_amounts': {'Financial software': 25000, 'Accounting services': 15000}
            },
            'Marketing Department': {
                'common_categories': ['Marketing and Advertising', 'Operational Expenses'],
                'common_subcategories': ['Digital marketing', 'Event management'],
                'typical_amounts': {'Digital marketing': 30000, 'Event management': 50000}
            }
        }
        
        self.purpose_keywords = {
            'electricity': {'category': 'Utilities', 'subcategory': 'Electricity', 'amount_range': (5000, 50000)},
            'internet': {'category': 'IT and Software', 'subcategory': 'Internet and phone services', 'amount_range': (5000, 15000)},
            'salary': {'category': 'Salaries and Wages', 'subcategory': 'Regular employee salaries', 'amount_range': (10000, 15000)},
            'marketing': {'category': 'Marketing and Advertising', 'subcategory': 'Digital marketing', 'amount_range': (15000, 50000)},
            'travel': {'category': 'Operational Expenses', 'subcategory': 'Business travel expenses', 'amount_range': (10000, 30000)},
            'office': {'category': 'Operational Expenses', 'subcategory': 'Office supplies', 'amount_range': (5000, 15000)},
            'training': {'category': 'Human Resources', 'subcategory': 'Training and development', 'amount_range': (10000, 25000)},
            'software': {'category': 'IT and Software', 'subcategory': 'Software licenses', 'amount_range': (15000, 40000)},
            'equipment': {'category': 'Facilities and Equipment', 'subcategory': 'Office equipment', 'amount_range': (20000, 100000)},
            'cleaning': {'category': 'Operational Expenses', 'subcategory': 'Cleaning services', 'amount_range': (5000, 15000)},
        }
    
    def analyze_purpose(self, purpose_text):
        """
        Analyze purpose text and suggest category, subcategory, and amount
        Returns: (category, subcategory, suggested_amount, confidence)
        """
        purpose_lower = purpose_text.lower()
        confidence = 0
        best_match = None
        
        # Check for keyword matches
        for keyword, data in self.purpose_keywords.items():
            if keyword in purpose_lower:
                confidence = 0.9  # High confidence for direct keyword match
                best_match = data
                break
        
        # If no direct match, try partial matches
        if not best_match:
            for keyword, data in self.purpose_keywords.items():
                if any(word in purpose_lower for word in keyword.split()):
                    confidence = 0.7  # Medium confidence for partial match
                    best_match = data
                    break
        
        if best_match:
            suggested_amount = (best_match['amount_range'][0] + best_match['amount_range'][1]) / 2
            return (
                best_match['category'],
                best_match['subcategory'], 
                Decimal(str(suggested_amount)),
                confidence
            )
        
        return None, None, None, 0
    
    def get_department_suggestions(self, department_name):
        """
        Get common categories and amounts for a department
        Returns: (common_categories, typical_amounts)
        """
        if department_name in self.department_patterns:
            dept_data = self.department_patterns[department_name]
            return dept_data['common_categories'], dept_data['typical_amounts']
        
        return [], {}
    
    def suggest_fields(self, purpose, department_name=None, amount=None):
        """
        Main method to suggest form fields based on input
        Returns: dict with suggested values
        """
        suggestions = {
            'category': None,
            'subcategory': None,
            'suggested_amount': None,
            'confidence': 0,
            'reasoning': []
        }
        
        # Analyze purpose for category/subcategory/amount
        if purpose:
            category, subcategory, suggested_amount, confidence = self.analyze_purpose(purpose)
            if category:
                suggestions['category'] = category
                suggestions['subcategory'] = subcategory
                suggestions['suggested_amount'] = suggested_amount
                suggestions['confidence'] = confidence
                suggestions['reasoning'].append(f"Based on purpose: '{purpose}'")
        
        # If department is provided, get department-specific suggestions
        if department_name:
            common_categories, typical_amounts = self.get_department_suggestions(department_name)
            if common_categories and not suggestions['category']:
                suggestions['category'] = common_categories[0]  # Most common
                suggestions['confidence'] = 0.6
                suggestions['reasoning'].append(f"Common for {department_name}")
        
        # If amount is provided, validate against typical ranges
        if amount and suggestions['suggested_amount']:
            amount_decimal = Decimal(str(amount))
            if abs(amount_decimal - suggestions['suggested_amount']) > suggestions['suggested_amount'] * 0.5:
                suggestions['reasoning'].append("Amount seems unusual for this category")
        
        return suggestions
    
    def get_smart_defaults(self, user_department=None):
        """
        Get smart defaults for a user based on their department
        Returns: dict with default values
        """
        defaults = {
            'currency': 'KES',
            'priority': 'medium',
            'cost_center': f'DEPT-{user_department.replace(" ", "-").upper()}' if user_department else 'DEPT-GENERAL'
        }
        
        if user_department:
            common_categories, typical_amounts = self.get_department_suggestions(user_department)
            if common_categories:
                defaults['suggested_category'] = common_categories[0]
                defaults['suggested_amount'] = list(typical_amounts.values())[0] if typical_amounts else 15000
        
        return defaults

def test_smart_form_service():
    """Test the smart form service"""
    service = SmartFormService()
    
    test_cases = [
        {
            'purpose': 'Electricity bill for office',
            'department': 'IT Department',
            'expected_category': 'Utilities'
        },
        {
            'purpose': 'Internet and phone services',
            'department': 'IT Department', 
            'expected_category': 'IT and Software'
        },
        {
            'purpose': 'Employee salary payment',
            'department': 'HR Department',
            'expected_category': 'Salaries and Wages'
        },
        {
            'purpose': 'Marketing campaign expenses',
            'department': 'Marketing Department',
            'expected_category': 'Marketing and Advertising'
        }
    ]
    
    print("🧪 Testing Smart Form Service:")
    for i, test in enumerate(test_cases, 1):
        suggestions = service.suggest_fields(
            test['purpose'], 
            test['department']
        )
        
        status = "✅ PASS" if suggestions['category'] == test['expected_category'] else "❌ FAIL"
        print(f"  {i}. {status} - '{test['purpose']}' → {suggestions['category']} (Confidence: {suggestions['confidence']:.1f})")
        print(f"      Suggested Amount: {suggestions['suggested_amount']} KES")
        print(f"      Reasoning: {', '.join(suggestions['reasoning'])}")

if __name__ == "__main__":
    test_smart_form_service()
