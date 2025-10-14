"""
Budget estimation service for AI-powered budget predictions and analysis.
"""

import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
from django.db.models import Q, Sum, Avg, Count
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from ..core.base import BaseFinanceService, BudgetServiceMixin
from ...models import Budget, BudgetCategory, BudgetSubCategory, Transaction, BudgetEstimateProjection

logger = logging.getLogger(__name__)


class BudgetEstimationService(BaseFinanceService, BudgetServiceMixin):
    """
    Service for budget estimation and AI-powered predictions.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_estimation_options(self, company) -> Dict[str, Any]:
        """Get available estimation options for a company."""
        try:
            # Get historical data availability
            historical_data = self._analyze_historical_data(company)
            
            # Get estimation methods
            estimation_methods = self._get_available_methods(historical_data)
            
            # Get confidence levels
            confidence_levels = self._calculate_confidence_levels(company)
            
            return {
                'historical_data': historical_data,
                'estimation_methods': estimation_methods,
                'confidence_levels': confidence_levels,
                'recommended_method': self._get_recommended_method(historical_data),
            }
        
        except Exception as e:
            self.log_error("Error getting estimation options", e)
            return {'error': str(e)}
    
    def estimate_budget(self, company, estimation_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate budget estimates based on parameters."""
        try:
            method = estimation_params.get('method', 'historical_average')
            categories = estimation_params.get('categories', [])
            timeframe = estimation_params.get('timeframe', 'monthly')
            
            # Validate parameters
            self.validate_required_fields(estimation_params, ['method', 'timeframe'])
            
            # Generate estimates based on method
            if method == 'historical_average':
                estimates = self._estimate_historical_average(company, categories, timeframe)
            elif method == 'trend_analysis':
                estimates = self._estimate_trend_analysis(company, categories, timeframe)
            elif method == 'ai_prediction':
                estimates = self._estimate_ai_prediction(company, categories, timeframe)
            else:
                raise ValueError(f"Unknown estimation method: {method}")
            
            # Calculate confidence
            confidence = self._calculate_estimation_confidence(company, estimates)
            
            # Create projection record
            projection = self._create_projection(company, estimation_params, estimates, confidence)
            
            return {
                'success': True,
                'projection_id': projection.id,
                'estimates': estimates,
                'confidence': confidence,
                'method': method,
                'timeframe': timeframe,
            }
        
        except Exception as e:
            self.log_error("Error estimating budget", e)
            return {'error': str(e)}
    
    def _analyze_historical_data(self, company) -> Dict[str, Any]:
        """Analyze historical data availability for estimation."""
        try:
            # Get date ranges
            now = timezone.now()
            one_year_ago = now - timedelta(days=365)
            six_months_ago = now - timedelta(days=180)
            three_months_ago = now - timedelta(days=90)
            
            # Analyze transaction data
            transactions_1y = Transaction.objects.filter(
                company=company,
                transaction_date__gte=one_year_ago
            ).count()
            
            transactions_6m = Transaction.objects.filter(
                company=company,
                transaction_date__gte=six_months_ago
            ).count()
            
            transactions_3m = Transaction.objects.filter(
                company=company,
                transaction_date__gte=three_months_ago
            ).count()
            
            # Analyze budget data
            budgets_total = Budget.objects.filter(company=company).count()
            budgets_1y = Budget.objects.filter(
                company=company,
                created_at__gte=one_year_ago
            ).count()
            
            # Calculate data quality score
            data_quality = self._calculate_data_quality_score(
                transactions_1y, transactions_6m, transactions_3m, budgets_total
            )
            
            return {
                'transactions_1y': transactions_1y,
                'transactions_6m': transactions_6m,
                'transactions_3m': transactions_3m,
                'budgets_total': budgets_total,
                'budgets_1y': budgets_1y,
                'data_quality_score': data_quality,
                'has_sufficient_data': data_quality >= 0.6,
            }
        
        except Exception as e:
            self.log_error("Error analyzing historical data", e)
            return {'error': str(e)}
    
    def _get_available_methods(self, historical_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get available estimation methods based on historical data."""
        methods = []
        
        # Historical average method
        methods.append({
            'id': 'historical_average',
            'name': 'Historical Average',
            'description': 'Use average of historical transactions',
            'available': historical_data.get('has_sufficient_data', False),
            'confidence': 'Medium',
        })
        
        # Trend analysis method
        if historical_data.get('transactions_6m', 0) >= 50:
            methods.append({
                'id': 'trend_analysis',
                'name': 'Trend Analysis',
                'description': 'Analyze trends in historical data',
                'available': True,
                'confidence': 'High',
            })
        
        # AI prediction method
        if historical_data.get('data_quality_score', 0) >= 0.8:
            methods.append({
                'id': 'ai_prediction',
                'name': 'AI Prediction',
                'description': 'Advanced AI-powered prediction',
                'available': True,
                'confidence': 'Very High',
            })
        
        return methods
    
    def _calculate_confidence_levels(self, company) -> Dict[str, float]:
        """Calculate confidence levels for different estimation methods."""
        try:
            # Analyze data quality
            historical_data = self._analyze_historical_data(company)
            data_quality = historical_data.get('data_quality_score', 0)
            
            # Base confidence on data quality
            base_confidence = data_quality * 100
            
            return {
                'historical_average': min(base_confidence, 85),
                'trend_analysis': min(base_confidence + 10, 90),
                'ai_prediction': min(base_confidence + 15, 95),
            }
        
        except Exception as e:
            self.log_error("Error calculating confidence levels", e)
            return {'historical_average': 50, 'trend_analysis': 60, 'ai_prediction': 70}
    
    def _get_recommended_method(self, historical_data: Dict[str, Any]) -> str:
        """Get recommended estimation method based on data quality."""
        data_quality = historical_data.get('data_quality_score', 0)
        
        if data_quality >= 0.8:
            return 'ai_prediction'
        elif data_quality >= 0.6:
            return 'trend_analysis'
        else:
            return 'historical_average'
    
    def _estimate_historical_average(self, company, categories: List[int], timeframe: str) -> List[Dict[str, Any]]:
        """Estimate budget using historical average method."""
        try:
            estimates = []
            
            # Get date range for historical data
            end_date = timezone.now()
            if timeframe == 'monthly':
                start_date = end_date - relativedelta(months=12)
            elif timeframe == 'quarterly':
                start_date = end_date - relativedelta(months=24)
            else:  # yearly
                start_date = end_date - relativedelta(years=3)
            
            # Get categories to estimate
            if categories:
                category_objects = BudgetCategory.objects.filter(id__in=categories)
            else:
                category_objects = BudgetCategory.objects.all()
            
            for category in category_objects:
                # Get historical transactions for this category
                transactions = Transaction.objects.filter(
                    company=company,
                    budget_category=category,
                    transaction_date__gte=start_date,
                    transaction_date__lte=end_date
                )
                
                if transactions.exists():
                    # Calculate average amount
                    avg_amount = transactions.aggregate(avg=Avg('amount'))['avg'] or Decimal('0')
                    transaction_count = transactions.count()
                    
                    # Calculate frequency
                    if timeframe == 'monthly':
                        frequency = transaction_count / 12
                    elif timeframe == 'quarterly':
                        frequency = transaction_count / 8
                    else:  # yearly
                        frequency = transaction_count / 3
                    
                    # Estimate total
                    estimated_total = avg_amount * frequency
                    
                    estimates.append({
                        'category_id': category.id,
                        'category_name': category.name,
                        'estimated_amount': float(estimated_total),
                        'avg_transaction_amount': float(avg_amount),
                        'transaction_count': transaction_count,
                        'frequency': frequency,
                        'method': 'historical_average',
                    })
            
            return estimates
        
        except Exception as e:
            self.log_error("Error in historical average estimation", e)
            return []
    
    def _estimate_trend_analysis(self, company, categories: List[int], timeframe: str) -> List[Dict[str, Any]]:
        """Estimate budget using trend analysis method."""
        try:
            estimates = []
            
            # Get categories to estimate
            if categories:
                category_objects = BudgetCategory.objects.filter(id__in=categories)
            else:
                category_objects = BudgetCategory.objects.all()
            
            for category in category_objects:
                # Get monthly transaction data for trend analysis
                monthly_data = self._get_monthly_transaction_data(company, category)
                
                if len(monthly_data) >= 3:  # Need at least 3 months of data
                    # Calculate trend
                    trend = self._calculate_trend(monthly_data)
                    
                    # Predict next period
                    last_amount = monthly_data[-1]['amount']
                    predicted_amount = last_amount * (1 + trend)
                    
                    estimates.append({
                        'category_id': category.id,
                        'category_name': category.name,
                        'estimated_amount': float(predicted_amount),
                        'trend': trend,
                        'last_amount': float(last_amount),
                        'method': 'trend_analysis',
                    })
            
            return estimates
        
        except Exception as e:
            self.log_error("Error in trend analysis estimation", e)
            return []
    
    def _estimate_ai_prediction(self, company, categories: List[int], timeframe: str) -> List[Dict[str, Any]]:
        """Estimate budget using AI prediction method."""
        try:
            # This is a placeholder for AI prediction
            # In a real implementation, this would use machine learning models
            
            estimates = []
            
            # Get categories to estimate
            if categories:
                category_objects = BudgetCategory.objects.filter(id__in=categories)
            else:
                category_objects = BudgetCategory.objects.all()
            
            for category in category_objects:
                # Get comprehensive data for AI analysis
                ai_data = self._get_ai_analysis_data(company, category)
                
                # Simple AI prediction (placeholder)
                predicted_amount = self._simple_ai_prediction(ai_data)
                
                estimates.append({
                    'category_id': category.id,
                    'category_name': category.name,
                    'estimated_amount': float(predicted_amount),
                    'ai_confidence': 0.85,
                    'method': 'ai_prediction',
                })
            
            return estimates
        
        except Exception as e:
            self.log_error("Error in AI prediction estimation", e)
            return []
    
    def _calculate_data_quality_score(self, transactions_1y: int, transactions_6m: int, 
                                    transactions_3m: int, budgets_total: int) -> float:
        """Calculate data quality score (0-1)."""
        try:
            # Weight different time periods
            score = 0
            
            # Recent data is more important
            if transactions_3m >= 20:
                score += 0.4
            elif transactions_3m >= 10:
                score += 0.2
            
            if transactions_6m >= 50:
                score += 0.3
            elif transactions_6m >= 25:
                score += 0.15
            
            if transactions_1y >= 100:
                score += 0.2
            elif transactions_1y >= 50:
                score += 0.1
            
            # Budget data availability
            if budgets_total >= 10:
                score += 0.1
            
            return min(score, 1.0)
        
        except Exception as e:
            self.log_error("Error calculating data quality score", e)
            return 0.5
    
    def _get_monthly_transaction_data(self, company, category) -> List[Dict[str, Any]]:
        """Get monthly transaction data for trend analysis."""
        try:
            # Get last 12 months of data
            end_date = timezone.now()
            start_date = end_date - relativedelta(months=12)
            
            monthly_data = []
            current_date = start_date
            
            while current_date <= end_date:
                month_start = current_date.replace(day=1)
                month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)
                
                transactions = Transaction.objects.filter(
                    company=company,
                    budget_category=category,
                    transaction_date__gte=month_start,
                    transaction_date__lte=month_end
                )
                
                total_amount = transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0')
                
                monthly_data.append({
                    'month': month_start.strftime('%Y-%m'),
                    'amount': total_amount,
                })
                
                current_date = month_start + relativedelta(months=1)
            
            return monthly_data
        
        except Exception as e:
            self.log_error("Error getting monthly transaction data", e)
            return []
    
    def _calculate_trend(self, monthly_data: List[Dict[str, Any]]) -> float:
        """Calculate trend from monthly data."""
        try:
            if len(monthly_data) < 2:
                return 0.0
            
            # Simple linear trend calculation
            amounts = [float(item['amount']) for item in monthly_data]
            
            # Calculate average change
            changes = []
            for i in range(1, len(amounts)):
                if amounts[i-1] > 0:
                    change = (amounts[i] - amounts[i-1]) / amounts[i-1]
                    changes.append(change)
            
            if changes:
                return sum(changes) / len(changes)
            else:
                return 0.0
        
        except Exception as e:
            self.log_error("Error calculating trend", e)
            return 0.0
    
    def _get_ai_analysis_data(self, company, category) -> Dict[str, Any]:
        """Get comprehensive data for AI analysis."""
        try:
            # Get transaction data
            transactions = Transaction.objects.filter(
                company=company,
                budget_category=category
            ).order_by('-transaction_date')[:100]
            
            # Get budget data
            budgets = Budget.objects.filter(
                company=company,
                category=category
            )
            
            # Calculate various metrics
            total_transactions = transactions.count()
            avg_amount = transactions.aggregate(avg=Avg('amount'))['avg'] or Decimal('0')
            
            return {
                'total_transactions': total_transactions,
                'avg_amount': avg_amount,
                'budget_count': budgets.count(),
                'recent_transactions': list(transactions.values('amount', 'transaction_date')[:10]),
            }
        
        except Exception as e:
            self.log_error("Error getting AI analysis data", e)
            return {}
    
    def _simple_ai_prediction(self, ai_data: Dict[str, Any]) -> Decimal:
        """Simple AI prediction (placeholder for real ML model)."""
        try:
            avg_amount = ai_data.get('avg_amount', Decimal('0'))
            total_transactions = ai_data.get('total_transactions', 0)
            
            # Simple prediction based on average and transaction frequency
            if total_transactions > 0:
                # Predict monthly amount
                monthly_prediction = avg_amount * (total_transactions / 12)
                return monthly_prediction
            else:
                return Decimal('0')
        
        except Exception as e:
            self.log_error("Error in simple AI prediction", e)
            return Decimal('0')
    
    def _calculate_estimation_confidence(self, company, estimates: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence for the estimation."""
        try:
            if not estimates:
                return 0.0
            
            # Base confidence on data quality
            historical_data = self._analyze_historical_data(company)
            base_confidence = historical_data.get('data_quality_score', 0.5)
            
            # Adjust based on number of estimates
            estimate_count = len(estimates)
            if estimate_count >= 10:
                confidence_boost = 0.1
            elif estimate_count >= 5:
                confidence_boost = 0.05
            else:
                confidence_boost = 0.0
            
            return min(base_confidence + confidence_boost, 1.0)
        
        except Exception as e:
            self.log_error("Error calculating estimation confidence", e)
            return 0.5
    
    def _create_projection(self, company, estimation_params: Dict[str, Any], 
                          estimates: List[Dict[str, Any]], confidence: float) -> BudgetEstimateProjection:
        """Create a budget estimate projection record."""
        try:
            projection = BudgetEstimateProjection.objects.create(
                company=company,
                projection_name=f"Budget Estimation - {timezone.now().strftime('%Y-%m-%d %H:%M')}",
                description=f"Budget estimation using {estimation_params.get('method', 'unknown')} method",
                estimation_method=estimation_params.get('method', 'unknown'),
                estimation_source='AI Service',
                estimation_confidence=confidence * 100,
                total_estimated_amount=sum(estimate.get('estimated_amount', 0) for estimate in estimates),
                projection_data={
                    'estimation_params': estimation_params,
                    'estimates': estimates,
                    'confidence': confidence,
                }
            )
            
            return projection
        
        except Exception as e:
            self.log_error("Error creating projection", e)
            raise
