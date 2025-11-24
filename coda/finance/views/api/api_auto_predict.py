"""
Intelligent Auto-Prediction API
Predicts and auto-fills transaction fields based on historical patterns + AI

Uses 3-tier hybrid system:
- Tier 1: Historical transactions (95% coverage, FREE)
- Tier 2: AI cache (4% coverage, FREE)
- Tier 3: AI API or Dummy AI (1% coverage, ~$1/month)

When user enters receiver name (like "KPLC"), automatically suggests:
- Category (Utilities)
- Subcategory (Electricity)
- Type/Item (Electricity Bill)
- Typical amount ($1,946 average)
- Description template
- Department (if consistent)
"""
from django.http import JsonResponse
from django.db.models import Count, Avg, Q, Max
from django.views.decorators.http import require_http_methods
from collections import Counter
import logging

from finance.models import Transaction, BudgetCategory, BudgetSubCategory
from shared_core.users import Department
from finance.services.hybrid_ai_service import HybridAIPredictionService

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def api_predict_all_fields(request):
    """
    Predict ALL fields based on receiver name + optional context
    
    Usage: /api/predict-all/?receiver=KPLC&department_id=1
    
    Returns comprehensive prediction:
    {
        "receiver_info": {
            "name": "KPLC",
            "type": "company",
            "is_known": true,
            "transaction_count": 9
        },
        "predictions": {
            "category_id": 5,
            "category_name": "Utilities",
            "subcategory_id": 12,
            "subcategory_name": "Electricity",
            "type": "Electricity Bill",
            "amount": 4272.89,
            "department_id": 1,
            "department_name": "HR Department",
            "description": "Electricity bill payment to KPLC",
            "payment_method": "Mpesa"
        },
        "confidence": {
            "overall": "high",
            "category": 100,
            "subcategory": 89,
            "type": 89,
            "amount": 78
        },
        "alternatives": [...]
    }
    """
    receiver = request.GET.get('receiver', '').strip()
    department_id = request.GET.get('department_id')
    amount_str = request.GET.get('amount')
    
    if not receiver:
        return JsonResponse({'error': 'receiver parameter required'}, status=400)
    
    # Convert amount to float if provided
    amount = None
    if amount_str:
        try:
            amount = float(amount_str)
        except ValueError:
            pass
    
    # Use hybrid AI service
    service = HybridAIPredictionService()
    result = service.predict_transaction_fields(receiver, department_id, amount)
    
    # If no predictions, return appropriate message
    if not result['predictions'] or not result['predictions'].get('category_id'):
        return JsonResponse({
            'receiver_info': {
                'name': receiver,
                'type': _guess_receiver_type(receiver),
                'is_known': False,
                'transaction_count': 0
            },
            'predictions': None,
            'message': f'No data found for {receiver}. {result.get("note", "Enter manually.")}'
        })
    
    # Return successful prediction
    return JsonResponse({
        'receiver_info': {
            'name': receiver,
            'type': _guess_receiver_type(receiver),
            'is_known': True,
            'transaction_count': result.get('transaction_count', result.get('times_reused', 0)),
            'source': result['source'],
            'cost': result['cost'],
        },
        'predictions': result['predictions'],
        'confidence': result['confidence'],
        'note': result.get('note', '')
    })


def _guess_receiver_type(receiver):
    """
    Guess if receiver is a company or person based on name patterns
    """
    receiver_lower = receiver.lower()
    
    # Company indicators
    company_keywords = [
        'kplc', 'safaricom', 'ltd', 'limited', 'inc', 'corp', 
        'company', 'hardware', 'supplies', 'services'
    ]
    
    # Person indicators  
    person_keywords = [
        'idah', 'george', 'collins', 'david', 'eunice', 'philip',
        'sylvia', 'nicodemus', 'maxwel', 'edwin', 'brenda', 'luke'
    ]
    
    for keyword in company_keywords:
        if keyword in receiver_lower:
            return 'company'
    
    for keyword in person_keywords:
        if keyword in receiver_lower:
            return 'person'
    
    # Check if has multiple capital letters (company pattern)
    if sum(1 for c in receiver if c.isupper()) >= 3:
        return 'company'
    
    # Default to person if title case (First Last)
    words = receiver.split()
    if len(words) >= 2 and all(w[0].isupper() if w else False for w in words):
        return 'person'
    
    return 'unknown'


def _analyze_transaction_patterns(transactions, receiver):
    """
    Analyze historical transaction patterns for this receiver
    """
    # Most common exact receiver name (for case variations)
    receiver_names = [t.receiver for t in transactions]
    most_common_name = Counter(receiver_names).most_common(1)[0][0]
    
    # Categories
    categories = [
        (t.category_id, t.category.name if t.category else None) 
        for t in transactions if t.category
    ]
    category_counter = Counter(categories)
    most_common_category = category_counter.most_common(1)[0][0] if category_counter else (None, None)
    
    # Subcategories
    subcategories = [
        (t.subcategory_id, t.subcategory.name if t.subcategory else None)
        for t in transactions if t.subcategory
    ]
    subcategory_counter = Counter(subcategories)
    most_common_subcategory = subcategory_counter.most_common(1)[0][0] if subcategory_counter else (None, None)
    
    # Types/Items
    types = [t.type for t in transactions if t.type]
    type_counter = Counter(types)
    most_common_type = type_counter.most_common(1)[0][0] if type_counter else None
    
    # Departments
    departments = [
        (t.department_id, t.department.name if t.department else None)
        for t in transactions if hasattr(t, 'department') and t.department
    ]
    dept_counter = Counter(departments)
    most_common_dept = dept_counter.most_common(1)[0][0] if dept_counter else (None, None)
    
    # Payment methods
    payment_methods = [t.payment_method for t in transactions if t.payment_method]
    payment_counter = Counter(payment_methods)
    most_common_payment = payment_counter.most_common(1)[0][0] if payment_counter else None
    
    # Amounts
    amounts = [float(t.amount) for t in transactions if t.amount]
    avg_amount = sum(amounts) / len(amounts) if amounts else 0
    min_amount = min(amounts) if amounts else 0
    max_amount = max(amounts) if amounts else 0
    
    # Descriptions (extract common words)
    descriptions = [t.description for t in transactions if t.description]
    description_words = []
    for desc in descriptions:
        description_words.extend(desc.lower().split())
    common_words = [word for word, count in Counter(description_words).most_common(5) if len(word) > 3]
    
    # Date range
    date_range = transactions.aggregate(
        first=Max('transaction_date'),
        last=Max('transaction_date')
    )
    
    return {
        'most_common_receiver_name': most_common_name,
        'category': most_common_category,
        'subcategory': most_common_subcategory,
        'type': most_common_type,
        'department': most_common_dept,
        'payment_method': most_common_payment,
        'amount': {
            'avg': avg_amount,
            'min': min_amount,
            'max': max_amount
        },
        'description_keywords': common_words,
        'date_range': date_range,
        'category_consistency': len(category_counter) == 1,  # True if always same category
        'type_consistency': len(type_counter) == 1,
        'total_transactions': len(transactions)
    }


def _build_predictions(analysis, receiver, department_id=None, amount=None):
    """
    Build prediction object from analysis
    """
    category_id, category_name = analysis['category']
    subcategory_id, subcategory_name = analysis['subcategory']
    dept_id, dept_name = analysis['department']
    
    # Generate smart description
    description = _generate_description(
        receiver, 
        category_name, 
        analysis['type'],
        analysis['description_keywords']
    )
    
    return {
        'category_id': category_id,
        'category_name': category_name,
        'subcategory_id': subcategory_id,
        'subcategory_name': subcategory_name,
        'type': analysis['type'],
        'amount': round(analysis['amount']['avg'], 2) if not amount else float(amount),
        'amount_range': {
            'min': round(analysis['amount']['min'], 2),
            'max': round(analysis['amount']['max'], 2),
            'avg': round(analysis['amount']['avg'], 2)
        },
        'department_id': dept_id if not department_id else int(department_id),
        'department_name': dept_name,
        'description': description,
        'payment_method': analysis['payment_method']
    }


def _generate_description(receiver, category, item_type, keywords):
    """
    Generate smart description based on patterns
    """
    # Start with receiver
    desc = f"Payment to {receiver}"
    
    # Add context from category/type
    if item_type:
        desc = f"{item_type} - {desc}"
    elif category:
        desc = f"{category} - {desc}"
    
    # Add common keywords if relevant
    if keywords and len(keywords) > 0:
        # Filter out very common words
        stop_words = {'payment', 'to', 'for', 'the', 'and', 'bill', 'paid'}
        relevant_keywords = [k for k in keywords if k not in stop_words]
        if relevant_keywords:
            desc += f" ({', '.join(relevant_keywords[:2])})"
    
    return desc


def _calculate_confidence(analysis, transaction_count):
    """
    Calculate confidence scores for predictions
    """
    # Base confidence on transaction count
    base_confidence = min(transaction_count * 10, 100)  # 10 points per transaction, max 100
    
    # Adjust for consistency
    category_confidence = 100 if analysis['category_consistency'] else base_confidence * 0.8
    type_confidence = 100 if analysis['type_consistency'] else base_confidence * 0.7
    
    # Amount confidence based on variance
    amount_range = analysis['amount']['max'] - analysis['amount']['min']
    amount_avg = analysis['amount']['avg']
    amount_variance = (amount_range / amount_avg) if amount_avg > 0 else 1
    amount_confidence = max(20, 100 - (amount_variance * 50))  # Lower confidence if high variance
    
    # Overall confidence
    overall_score = (category_confidence + type_confidence + amount_confidence) / 3
    
    if overall_score >= 80:
        overall = 'high'
    elif overall_score >= 50:
        overall = 'medium'
    else:
        overall = 'low'
    
    return {
        'overall': overall,
        'category': round(category_confidence),
        'subcategory': round(category_confidence * 0.9),  # Slightly lower than category
        'type': round(type_confidence),
        'amount': round(amount_confidence),
        'department': base_confidence if analysis['department'][0] else 0
    }


def _get_alternatives(analysis):
    """
    Get alternative predictions if available
    """
    alternatives = []
    
    # Add amount range as alternative
    if analysis['amount']['min'] != analysis['amount']['max']:
        alternatives.append({
            'field': 'amount',
            'options': [
                {'value': analysis['amount']['min'], 'label': f"Minimum: ${analysis['amount']['min']:.2f}"},
                {'value': analysis['amount']['avg'], 'label': f"Average: ${analysis['amount']['avg']:.2f}"},
                {'value': analysis['amount']['max'], 'label': f"Maximum: ${analysis['amount']['max']:.2f}"}
            ]
        })
    
    return alternatives

