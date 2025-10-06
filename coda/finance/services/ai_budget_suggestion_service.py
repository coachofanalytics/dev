"""
AI-Powered Budget Suggestion Service

Builds upon existing AI infrastructure to provide intelligent budget suggestions
based on historical data analysis, pattern recognition, and learning systems.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from django.db.models import Q, Sum, Avg, Count, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta
import statistics
import json

from ..models import Transaction, BudgetCategory, BudgetEstimateProjection
from .budget.estimation import BudgetEstimationService
from .data_quality_service import DataQualityService
from ai_services.ai_integration_service import RealAIService
from ai_services.models import DiasporaAnalysisData, AIModelTypes

logger = logging.getLogger(__name__)


class AIBudgetSuggestionService:
    """
    AI-powered budget suggestion service that learns from historical data
    and provides intelligent recommendations for budget planning.
    """
    
    def __init__(self):
        self.budget_service = BudgetEstimationService()
        self.data_quality_service = DataQualityService()
        self.ai_service = RealAIService()
        self.learning_cache = {}
    
    def get_intelligent_suggestions(self, company, department=None, horizon='monthly') -> Dict[str, Any]:
        """
        Get AI-powered intelligent budget suggestions
        
        Args:
            company: Company object
            department: Department object (optional)
            horizon: Budget horizon (monthly, quarterly, yearly, etc.)
            
        Returns:
            Dictionary with intelligent suggestions and recommendations
        """
        try:
            # Get historical data analysis
            historical_analysis = self._analyze_historical_patterns(company, department)
            
            # Get data quality insights
            quality_analysis = self.data_quality_service.analyze_data_quality(company, department)
            
            # Get AI-powered predictions
            ai_predictions = self._get_ai_predictions(company, department, horizon, historical_analysis)
            
            # Generate smart suggestions
            suggestions = self._generate_smart_suggestions(
                historical_analysis, quality_analysis, ai_predictions, horizon
            )
            
            # Learn from patterns and save for future use
            self._learn_from_patterns(company, department, suggestions)
            
            return {
                'suggestions': suggestions,
                'historical_analysis': historical_analysis,
                'quality_analysis': quality_analysis,
                'ai_predictions': ai_predictions,
                'confidence_score': self._calculate_overall_confidence(quality_analysis, ai_predictions),
                'learning_insights': self._get_learning_insights(company, department)
            }
            
        except Exception as e:
            logger.error(f"Error generating AI suggestions: {e}")
            return {'error': str(e)}
    
    def _analyze_historical_patterns(self, company, department=None) -> Dict[str, Any]:
        """Analyze historical spending patterns for intelligent suggestions"""
        try:
            # Get transactions from last 12 months
            end_date = timezone.now()
            start_date = end_date - timedelta(days=365)
            
            if department:
                transactions = Transaction.objects.filter(
                    department=department,
                    transaction_date__gte=start_date,
                    transaction_date__lte=end_date
                )
            else:
                transactions = Transaction.objects.filter(
                    transaction_date__gte=start_date,
                    transaction_date__lte=end_date
                )
            
            # Analyze spending patterns by category
            category_patterns = {}
            seasonal_patterns = {}
            trend_analysis = {}
            
            for category in BudgetCategory.objects.all():
                cat_transactions = transactions.filter(category=category)
                
                if cat_transactions.exists():
                    # Monthly spending patterns
                    monthly_spending = {}
                    for i in range(12):
                        month_start = start_date + timedelta(days=i * 30)
                        month_end = month_start + timedelta(days=30)
                        month_txns = cat_transactions.filter(
                            transaction_date__gte=month_start,
                            transaction_date__lte=month_end
                        )
                        
                        total = sum(
                            (txn.amount_usd or txn.amount) * (txn.qty or 1) 
                            for txn in month_txns
                        )
                        monthly_spending[month_start.strftime('%Y-%m')] = float(total)
                    
                    # Calculate patterns
                    amounts = list(monthly_spending.values())
                    if amounts:
                        category_patterns[category.name] = {
                            'average_monthly': statistics.mean(amounts),
                            'median_monthly': statistics.median(amounts),
                            'std_deviation': statistics.stdev(amounts) if len(amounts) > 1 else 0,
                            'trend': self._calculate_trend(amounts),
                            'seasonality': self._detect_seasonality(amounts),
                            'volatility': statistics.stdev(amounts) / statistics.mean(amounts) if statistics.mean(amounts) > 0 else 0
                        }
            
            return {
                'category_patterns': category_patterns,
                'total_transactions': transactions.count(),
                'analysis_period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'data_quality_score': self._calculate_data_quality_score(transactions)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing historical patterns: {e}")
            return {}
    
    def _get_ai_predictions(self, company, department, horizon, historical_analysis) -> Dict[str, Any]:
        """Get AI-powered predictions using existing AI infrastructure"""
        try:
            # Prepare input data for AI
            input_data = {
                'company_name': company.name,
                'department': department.name if department else 'All',
                'horizon': horizon,
                'historical_patterns': historical_analysis.get('category_patterns', {}),
                'data_quality_score': historical_analysis.get('data_quality_score', 0),
                'total_transactions': historical_analysis.get('total_transactions', 0)
            }
            
            # Use existing AI service
            ai_response = self.ai_service.get_prediction(
                analysis_type='budget_prediction',
                input_data=input_data,
                session_id=f"budget_{company.id}_{department.id if department else 'all'}"
            )
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error getting AI predictions: {e}")
            return {'error': str(e)}
    
    def _generate_smart_suggestions(self, historical_analysis, quality_analysis, ai_predictions, horizon) -> Dict[str, Any]:
        """Generate smart suggestions based on analysis"""
        suggestions = {
            'budget_recommendations': {},
            'data_improvements': [],
            'risk_alerts': [],
            'optimization_tips': [],
            'category_suggestions': {}
        }
        
        # Generate category-specific suggestions
        category_patterns = historical_analysis.get('category_patterns', {})
        
        for category, patterns in category_patterns.items():
            avg_monthly = patterns.get('average_monthly', 0)
            volatility = patterns.get('volatility', 0)
            trend = patterns.get('trend', 0)
            
            # Smart budget recommendations
            if volatility > 0.5:  # High volatility
                suggested_amount = avg_monthly * 1.2  # 20% buffer
                suggestions['budget_recommendations'][category] = {
                    'suggested_amount': suggested_amount,
                    'reason': 'High volatility detected - recommend 20% buffer',
                    'confidence': 0.8
                }
            elif trend > 0.1:  # Increasing trend
                suggested_amount = avg_monthly * 1.1  # 10% increase
                suggestions['budget_recommendations'][category] = {
                    'suggested_amount': suggested_amount,
                    'reason': 'Increasing trend detected - recommend 10% increase',
                    'confidence': 0.9
                }
            elif trend < -0.1:  # Decreasing trend
                suggested_amount = avg_monthly * 0.9  # 10% decrease
                suggestions['budget_recommendations'][category] = {
                    'suggested_amount': suggested_amount,
                    'reason': 'Decreasing trend detected - recommend 10% decrease',
                    'confidence': 0.9
                }
            else:  # Stable
                suggested_amount = avg_monthly
                suggestions['budget_recommendations'][category] = {
                    'suggested_amount': suggested_amount,
                    'reason': 'Stable spending pattern - use historical average',
                    'confidence': 0.95
                }
            
            # Category-specific optimization tips
            if volatility > 0.3:
                suggestions['optimization_tips'].append(
                    f"Consider setting up alerts for {category} spending to better control volatility"
                )
            
            if patterns.get('seasonality', 0) > 0.2:
                suggestions['optimization_tips'].append(
                    f"{category} shows seasonal patterns - plan accordingly for peak months"
                )
        
        # Data quality improvements
        if quality_analysis.get('overall_score', 0) < 0.7:
            suggestions['data_improvements'].extend(quality_analysis.get('recommendations', []))
        
        # Risk alerts
        high_volatility_categories = [
            cat for cat, patterns in category_patterns.items()
            if patterns.get('volatility', 0) > 0.5
        ]
        
        if high_volatility_categories:
            suggestions['risk_alerts'].append(
                f"High spending volatility detected in: {', '.join(high_volatility_categories)}"
            )
        
        return suggestions
    
    def _learn_from_patterns(self, company, department, suggestions) -> None:
        """Learn from patterns and save for future predictions"""
        try:
            # Save learning data
            learning_data = {
                'company_id': company.id,
                'department_id': department.id if department else None,
                'timestamp': timezone.now().isoformat(),
                'suggestions': suggestions,
                'learning_type': 'budget_pattern_analysis'
            }
            
            # Store in AI analysis data
            DiasporaAnalysisData.objects.create(
                session_id=f"budget_learning_{company.id}_{department.id if department else 'all'}",
                analysis_type='budget_pattern_learning',
                user_input=learning_data,
                ai_prediction=suggestions,
                model_used=AIModelTypes.LOCAL_OFFLINE,
                confidence_score=0.85,
                processing_time=0.1,
                fallback_used=False,
                is_real_ai=False
            )
            
            # Cache for quick access
            cache_key = f"budget_learning_{company.id}_{department.id if department else 'all'}"
            self.learning_cache[cache_key] = learning_data
            
        except Exception as e:
            logger.error(f"Error learning from patterns: {e}")
    
    def _get_learning_insights(self, company, department) -> Dict[str, Any]:
        """Get insights from previous learning data"""
        try:
            # Get recent learning data
            recent_learning = DiasporaAnalysisData.objects.filter(
                analysis_type='budget_pattern_learning',
                session_id__startswith=f"budget_learning_{company.id}_{department.id if department else 'all'}"
            ).order_by('-created_at')[:5]
            
            insights = {
                'total_learning_sessions': recent_learning.count(),
                'recent_patterns': [],
                'improvement_trends': []
            }
            
            for learning in recent_learning:
                if learning.ai_prediction:
                    insights['recent_patterns'].append({
                        'timestamp': learning.created_at.isoformat(),
                        'confidence': learning.confidence_score,
                        'key_insights': learning.ai_prediction.get('budget_recommendations', {})
                    })
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting learning insights: {e}")
            return {}
    
    def _calculate_trend(self, amounts: List[float]) -> float:
        """Calculate trend direction (-1 to 1)"""
        if len(amounts) < 2:
            return 0.0
        
        # Simple linear trend calculation
        n = len(amounts)
        x = list(range(n))
        y = amounts
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        return max(-1, min(1, slope / y_mean))  # Normalize to -1 to 1
    
    def _detect_seasonality(self, amounts: List[float]) -> float:
        """Detect seasonality in spending patterns (0 to 1)"""
        if len(amounts) < 6:  # Need at least 6 months
            return 0.0
        
        # Calculate coefficient of variation for seasonality
        mean_amount = statistics.mean(amounts)
        if mean_amount == 0:
            return 0.0
        
        std_dev = statistics.stdev(amounts) if len(amounts) > 1 else 0
        return min(1.0, std_dev / mean_amount)
    
    def _calculate_data_quality_score(self, transactions) -> float:
        """Calculate data quality score for transactions"""
        if not transactions.exists():
            return 0.0
        
        total_fields = 0
        filled_fields = 0
        
        for txn in transactions:
            fields_to_check = ['amount', 'category', 'description', 'transaction_date']
            for field in fields_to_check:
                total_fields += 1
                if getattr(txn, field, None) is not None:
                    filled_fields += 1
        
        return filled_fields / total_fields if total_fields > 0 else 0.0
    
    def _calculate_overall_confidence(self, quality_analysis, ai_predictions) -> float:
        """Calculate overall confidence score"""
        quality_score = quality_analysis.get('overall_score', 0.5)
        ai_confidence = ai_predictions.get('confidence_score', 0.5)
        
        return (quality_score + ai_confidence) / 2
