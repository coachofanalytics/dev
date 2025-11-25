"""
Hybrid AI Prediction Service with 3-Tier Caching

Tier 1: Historical Data (FREE, 95% coverage)
Tier 2: AI Cache (FREE, 4% coverage)
Tier 3: AI API / Dummy AI (PAID, 1% coverage)

System learns over time and becomes self-reliant.
"""
import hashlib
import json
import logging
from decimal import Decimal
from datetime import timedelta
from collections import Counter

from django.utils import timezone
from django.conf import settings
from django.db.models import Avg, Count

from finance.models import Transaction, BudgetCategory, BudgetSubCategory
from shared_core.users import Department

logger = logging.getLogger(__name__)

# Try to import AI cache model
try:
    from finance.models_ai_cache import AIPredictionCache
except ImportError:
    AIPredictionCache = None
    logger.warning("AIPredictionCache model not available yet")


class HybridAIPredictionService:
    """
    Intelligent prediction service that minimizes AI API costs
    
    Usage:
        service = HybridAIPredictionService()
        result = service.predict_transaction_fields(
            receiver="KPLC",
            department_id=1,
            amount=5000
        )
        
        # Result includes:
        # - source: 'historical', 'ai_cache', or 'ai_api'
        # - predictions: {category_id, subcategory_id, type, amount, description...}
        # - confidence: {overall, category, amount...}
        # - cost: 0 for cache, >0 for AI API
    """
    
    def __init__(self):
        self.use_cache = True
        self.cache_expiry_days = 90
        self.use_dummy_ai = not self._has_real_api_key()
        
        if self.use_dummy_ai:
            logger.info("Using DUMMY AI - no API key configured")
        else:
            logger.info("Using REAL AI - API key configured")
    
    def _has_real_api_key(self):
        """Check if real API key is configured"""
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        return api_key and api_key != 'dummy-key-for-testing' and not api_key.startswith('sk-dummy')
    
    def predict_transaction_fields(self, receiver, department_id=None, amount=None):
        """
        Main prediction method with 3-tier fallback
        
        Returns:
            dict with 'source', 'predictions', 'confidence', 'cost'
        """
        logger.info(f"Predicting for receiver: {receiver}")
        
        # Get department object if ID provided
        department = None
        if department_id:
            try:
                department = Department.objects.get(id=department_id)
            except Department.DoesNotExist:
                pass
        
        # TIER 1: Check historical transactions (FREE, 95% coverage)
        historical = self._check_historical_data(receiver, department, amount)
        if historical and historical.get('confidence', {}).get('overall') == 'high':
            logger.info(f"✓ TIER 1: Historical data hit for {receiver}")
            return {
                'source': 'historical_data',
                'predictions': historical['predictions'],
                'confidence': historical['confidence'],
                'cost': 0,
                'tokens': 0,
                'note': f"Based on {historical['transaction_count']} actual transactions"
            }
        
        # TIER 2: Check AI cache (FREE if cached)
        if self.use_cache and AIPredictionCache:
            cached = self._check_cache(receiver, department, amount)
            if cached:
                logger.info(f"✓ TIER 2: Cache hit for {receiver} (saved ${cached.api_cost:.4f})")
                cached.mark_as_used()
                
                return {
                    'source': 'ai_cache',
                    'predictions': self._format_cached_prediction(cached),
                    'confidence': {'overall': 'high', 'category': cached.confidence_score},
                    'cost': 0,
                    'tokens': 0,
                    'cache_age_days': cached.cache_age_days,
                    'times_reused': cached.times_used,
                    'note': f'Cached AI prediction (reused {cached.times_used}x, saved ${cached.money_saved:.2f})'
                }
        
        # TIER 3: Call AI API or Dummy AI
        if self.use_dummy_ai:
            logger.info(f"✓ TIER 3: Using DUMMY AI for {receiver}")
            ai_prediction = self._call_dummy_ai(receiver, department, amount, historical)
        else:
            logger.info(f"✓ TIER 3: Calling REAL AI API for {receiver}")
            ai_prediction = self._call_real_ai_api(receiver, department, amount, historical)
        
        # Save to cache for future use
        if ai_prediction and AIPredictionCache:
            self._save_to_cache(receiver, department, amount, ai_prediction)
        
        return {
            'source': 'ai_api' if not self.use_dummy_ai else 'dummy_ai',
            'predictions': ai_prediction.get('predictions', {}),
            'confidence': ai_prediction.get('confidence', {}),
            'cost': ai_prediction.get('cost', 0),
            'tokens': ai_prediction.get('tokens_used', 0),
            'note': ai_prediction.get('note', 'AI prediction (cached for future use)')
        }
    
    def _check_historical_data(self, receiver, department, amount):
        """Tier 1: Use our 350 clean transactions (FREE!)"""
        similar = Transaction.objects.filter(
            receiver__icontains=receiver,
            category__isnull=False
        ).select_related('category', 'subcategory', 'department')
        
        if not similar.exists():
            return None
        
        transaction_count = similar.count()
        
        # Analyze patterns
        categories = [(t.category_id, t.category.name) for t in similar if t.category]
        category_counter = Counter(categories)
        most_common_category = category_counter.most_common(1)[0][0] if category_counter else (None, None)
        
        subcategories = [(t.subcategory_id, t.subcategory.name) for t in similar if t.subcategory]
        subcategory_counter = Counter(subcategories)
        most_common_subcategory = subcategory_counter.most_common(1)[0][0] if subcategory_counter else (None, None)
        
        types = [t.type for t in similar if t.type]
        type_counter = Counter(types)
        most_common_type = type_counter.most_common(1)[0][0] if type_counter else None
        
        amounts = [float(t.amount) for t in similar if t.amount]
        avg_amount = sum(amounts) / len(amounts) if amounts else 0
        
        # Calculate confidence
        category_consistency = len(category_counter) == 1
        confidence_level = 'high' if (transaction_count >= 5 and category_consistency) else 'medium' if transaction_count >= 2 else 'low'
        
        return {
            'predictions': {
                'category_id': most_common_category[0],
                'category_name': most_common_category[1],
                'subcategory_id': most_common_subcategory[0],
                'subcategory_name': most_common_subcategory[1],
                'type': most_common_type,
                'amount': round(avg_amount, 2),
                'description': f"Payment to {receiver}",
            },
            'confidence': {
                'overall': confidence_level,
                'category': 100 if category_consistency else 70,
            },
            'transaction_count': transaction_count
        }
    
    def _check_cache(self, receiver, department, amount):
        """Tier 2: Check if AI already predicted this before"""
        if not AIPredictionCache:
            return None
        
        context_hash = self._generate_cache_key(receiver, department, amount)
        
        # Look for unexpired cache entry
        cached = AIPredictionCache.objects.filter(
            context_hash=context_hash,
            expires_at__gte=timezone.now()
        ).first()
        
        return cached
    
    def _call_dummy_ai(self, receiver, department, amount, historical_context):
        """Dummy AI for testing (no API cost)"""
        # Use historical data or make educated guess
        if historical_context:
            pred = historical_context['predictions']
            return {
                'predictions': pred,
                'confidence': {'overall': 'medium', 'category': 75},
                'cost': 0,
                'tokens_used': 250,  # Simulated
                'note': 'Dummy AI (testing mode)',
                'ai_provider': 'dummy'
            }
        
        # Default fallback
        return {
            'predictions': {
                'category_id': None,
                'category_name': 'Operational Expenses',
                'subcategory_id': None,
                'type': 'General expense',
                'amount': float(amount) if amount else 1000,
                'description': f"Payment to {receiver}",
            },
            'confidence': {'overall': 'low', 'category': 30},
            'cost': 0,
            'tokens_used': 200,
            'note': 'Dummy AI fallback',
            'ai_provider': 'dummy'
        }
    
    def _call_real_ai_api(self, receiver, department, amount, historical_context):
        """Tier 3: Call OpenAI API (REAL, costs money)"""
        try:
            import openai
            openai.api_key = settings.OPENAI_API_KEY
            
            prompt = self._build_ai_prompt(receiver, department, amount, historical_context)
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{
                    "role": "system",
                    "content": "You are a financial analyst helping categorize transactions."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.3,
                max_tokens=300
            )
            
            ai_response = json.loads(response.choices[0].message.content)
            tokens_used = response.usage.total_tokens
            cost = tokens_used * 0.00003  # Approx cost
            
            return {
                'predictions': ai_response,
                'confidence': {'overall': 'high', 'category': ai_response.get('confidence', 80)},
                'cost': cost,
                'tokens_used': tokens_used,
                'note': 'OpenAI GPT-4 prediction',
                'ai_provider': 'openai'
            }
            
        except Exception as e:
            logger.error(f"Real AI API call failed: {str(e)}")
            # Fallback to dummy
            return self._call_dummy_ai(receiver, department, amount, historical_context)
    
    def _build_ai_prompt(self, receiver, department, amount, historical_context):
        """Build prompt for AI"""
        prompt = f"""Analyze this transaction and predict missing fields:

Receiver: {receiver}
Department: {department.name if department else 'Unknown'}
Amount: ${amount:.2f if amount else 'Unknown'}

"""
        if historical_context:
            prompt += f"Historical Context: {json.dumps(historical_context, indent=2)}\n\n"
        
        prompt += """Predict:
1. Budget Category
2. Subcategory
3. Item/Type
4. Expected amount
5. Description

Respond in JSON:
{
    "category": "Utilities",
    "subcategory": "Electricity",
    "type": "Electricity Bill",
    "amount": 4272.89,
    "description": "Monthly electricity payment",
    "confidence": 95
}"""
        return prompt
    
    def _save_to_cache(self, receiver, department, amount, ai_prediction):
        """Save AI response to cache"""
        if not AIPredictionCache:
            return
        
        context_hash = self._generate_cache_key(receiver, department, amount)
        pred = ai_prediction['predictions']
        
        # Get or create category
        try:
            category = BudgetCategory.objects.get(name=pred.get('category_name', pred.get('category')))
        except BudgetCategory.DoesNotExist:
            logger.warning(f"Category not found: {pred.get('category')}")
            return
        
        # Save cache entry
        try:
            AIPredictionCache.objects.update_or_create(
                context_hash=context_hash,
                defaults={
                    'receiver_name': receiver,
                    'department': department,
                    'amount_range_min': Decimal(str(amount * 0.8)) if amount else None,
                    'amount_range_max': Decimal(str(amount * 1.2)) if amount else None,
                    'predicted_category': category,
                    'predicted_item': pred.get('type', 'Unknown'),
                    'predicted_amount': Decimal(str(pred.get('amount', 0))),
                    'predicted_description': pred.get('description', ''),
                    'ai_provider': ai_prediction.get('ai_provider', 'dummy'),
                    'confidence_score': ai_prediction.get('confidence', {}).get('category', 70),
                    'ai_reasoning': ai_prediction.get('note', ''),
                    'tokens_used': ai_prediction.get('tokens_used', 0),
                    'api_cost': Decimal(str(ai_prediction.get('cost', 0))),
                    'expires_at': timezone.now() + timedelta(days=self.cache_expiry_days),
                    'times_used': 0
                }
            )
            logger.info(f"✓ Saved prediction to cache: {receiver} → {category.name}")
        except Exception as e:
            logger.error(f"Failed to save cache: {str(e)}")
    
    def _format_cached_prediction(self, cached):
        """Format cached prediction for API response"""
        return {
            'category_id': cached.predicted_category.id,
            'category_name': cached.predicted_category.name,
            'subcategory_id': cached.predicted_subcategory.id if cached.predicted_subcategory else None,
            'subcategory_name': cached.predicted_subcategory.name if cached.predicted_subcategory else None,
            'type': cached.predicted_item,
            'amount': float(cached.predicted_amount),
            'description': cached.predicted_description,
        }
    
    def _generate_cache_key(self, receiver, department, amount):
        """Generate hash for cache lookup"""
        key_parts = [
            receiver.lower().strip(),
            str(department.id) if department else 'none',
            f"{int(amount/100)*100}" if amount else 'none'  # Round to nearest $100
        ]
        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_cache_stats(self):
        """Get cache performance statistics"""
        if not AIPredictionCache:
            return None
        
        from django.db.models import Sum, Avg, Count, F
        
        stats = AIPredictionCache.objects.aggregate(
            total_predictions=Count('id'),
            total_uses=Sum('times_used'),
            total_tokens_saved=Sum(F('tokens_used') * F('times_used')),
            avg_confidence=Avg('confidence_score'),
            avg_accuracy=Avg('accuracy_score')
        )
        
        money_saved = float(stats['total_tokens_saved'] or 0) * 0.00003
        
        return {
            'total_cached': stats['total_predictions'],
            'total_reuses': stats['total_uses'],
            'money_saved': f"${money_saved:.2f}",
            'avg_confidence': round(stats['avg_confidence'] or 0, 1),
            'avg_accuracy': round(stats['avg_accuracy'] or 0, 1) if stats['avg_accuracy'] else 'N/A',
        }


