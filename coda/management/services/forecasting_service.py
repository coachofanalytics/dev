"""
Forecasting Service for Management App

Phase 3: Advanced Analytics
Service for forecasting activity trends, budget needs, and performance predictions.

Provides:
- Activity trend forecasting (3+ months)
- Budget prediction based on historical patterns
- Task completion rate forecasting
- Department capacity forecasting
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Q, Sum, Avg, Count, Max, Min, F
from django.utils import timezone
from django.contrib.auth import get_user_model

from management.models import TaskHistory, Task, TaskCategory
from management.services.taskhistory_analyzer import TaskHistoryAnalyzer
from shared_core.users import CustomerUser, Department

logger = logging.getLogger(__name__)
User = get_user_model()


class ForecastingService:
    """
    Service for forecasting activity trends and budget needs.
    
    Phase 3: Advanced Analytics
    Provides forecasting capabilities for:
    - Activity trends (3+ months ahead)
    - Budget predictions
    - Task completion rates
    - Department capacity
    """
    
    def __init__(self):
        self.logger = logger
        self.analyzer = TaskHistoryAnalyzer()
    
    def forecast_activity_trends(
        self,
        months_ahead: int = 3,
        department_id: Optional[int] = None,
        category_id: Optional[int] = None,
        historical_months: int = 12
    ) -> Dict[str, Any]:
        """
        Forecast activity trends for the next N months.
        
        Args:
            months_ahead: Number of months to forecast (default: 3)
            department_id: Optional department filter
            category_id: Optional category filter
            historical_months: Number of historical months to analyze (default: 12)
        
        Returns:
            Dict with forecast data:
            {
                'success': bool,
                'forecast_period': 'YYYY-MM to YYYY-MM',
                'historical_data': [...],
                'forecasted_data': [...],
                'trends': {...},
                'confidence': float (0-1),
                'insights': [...]
            }
        """
        try:
            self.logger.info(
                f"Forecasting activity trends for {months_ahead} months ahead "
                f"(department={department_id}, category={category_id})"
            )
            
            # Get historical data
            end_date = timezone.now().date()
            start_date = end_date - relativedelta(months=historical_months)
            
            # Build query
            query = Q(
                daf_date__gte=start_date,
                daf_date__lte=end_date,
                employee__is_active=True,
                employee__is_staff=True
            )
            
            if department_id:
                query &= Q(employee__department_id=department_id)
            if category_id:
                query &= Q(category_id=category_id)
            
            # Get historical monthly data
            historical_data = self._get_monthly_activity_data(query, start_date, end_date)
            
            if not historical_data:
                return {
                    'success': False,
                    'message': 'Insufficient historical data for forecasting',
                    'forecast_period': None,
                    'historical_data': [],
                    'forecasted_data': [],
                    'trends': {},
                    'confidence': 0.0,
                    'insights': ['Insufficient data for reliable forecasting']
                }
            
            # Calculate trends
            trends = self._calculate_trends(historical_data)
            
            # Generate forecast
            forecasted_data = self._generate_forecast(
                historical_data,
                trends,
                months_ahead
            )
            
            # Calculate confidence
            confidence = self._calculate_forecast_confidence(historical_data, trends)
            
            # Generate insights
            insights = self._generate_forecast_insights(trends, forecasted_data, confidence)
            
            # Calculate forecast period
            forecast_start = end_date + relativedelta(months=1)
            forecast_end = forecast_start + relativedelta(months=months_ahead - 1)
            
            return {
                'success': True,
                'forecast_period': f"{forecast_start.strftime('%Y-%m')} to {forecast_end.strftime('%Y-%m')}",
                'historical_data': historical_data,
                'forecasted_data': forecasted_data,
                'trends': trends,
                'confidence': round(confidence, 2),
                'insights': insights,
                'metadata': {
                    'months_ahead': months_ahead,
                    'historical_months': historical_months,
                    'department_id': department_id,
                    'category_id': category_id
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error forecasting activity trends: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Forecasting error: {str(e)}',
                'forecast_period': None,
                'historical_data': [],
                'forecasted_data': [],
                'trends': {},
                'confidence': 0.0,
                'insights': []
            }
    
    def _get_monthly_activity_data(
        self,
        query: Q,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get monthly aggregated activity data."""
        monthly_data = []
        current_date = start_date.replace(day=1)  # Start of first month
        
        while current_date <= end_date:
            month_end = (current_date + relativedelta(months=1) - timedelta(days=1))
            if month_end > end_date:
                month_end = end_date
            
            month_query = query & Q(
                daf_date__gte=current_date,
                daf_date__lte=month_end
            )
            
            tasks = TaskHistory.objects.filter(month_query)
            
            totals = tasks.aggregate(
                total_minutes=Sum('duration'),
                total_points=Sum('point'),
                total_max_points=Sum('mxpoint'),
                total_earnings=Sum(F('point') / F('mxpoint') * F('mxearning'), output_field=Decimal),
                task_count=Count('id'),
                unique_employees=Count('employee', distinct=True)
            )
            
            total_points = totals['total_points'] or 0
            total_max_points = totals['total_max_points'] or 0
            completion_rate = (total_points / total_max_points) if total_max_points > 0 else 0.0
            
            monthly_data.append({
                'month': current_date.strftime('%Y-%m'),
                'year': current_date.year,
                'month_number': current_date.month,
                'total_minutes': totals['total_minutes'] or 0,
                'total_points': float(total_points),
                'total_max_points': float(total_max_points),
                'total_earnings': float(totals['total_earnings'] or 0),
                'task_count': totals['task_count'] or 0,
                'unique_employees': totals['unique_employees'] or 0,
                'completion_rate': round(completion_rate, 2),
                'avg_points_per_employee': round(
                    (total_points / totals['unique_employees']) if totals['unique_employees'] > 0 else 0,
                    2
                )
            })
            
            current_date = current_date + relativedelta(months=1)
        
        return monthly_data
    
    def _calculate_trends(
        self,
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate trends from historical data."""
        if len(historical_data) < 2:
            return {
                'trend_direction': 'insufficient_data',
                'trend_strength': 0.0,
                'monthly_growth_rate': 0.0,
                'volatility': 0.0
            }
        
        # Calculate trend for key metrics
        metrics = ['total_points', 'total_earnings', 'task_count', 'completion_rate']
        trends = {}
        
        for metric in metrics:
            values = [d[metric] for d in historical_data if metric in d]
            if len(values) < 2:
                continue
            
            # Simple linear trend (slope)
            n = len(values)
            x_mean = (n - 1) / 2
            y_mean = sum(values) / n
            
            numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            
            if denominator > 0:
                slope = numerator / denominator
                trend_direction = 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'
                
                # Calculate volatility (coefficient of variation)
                if y_mean > 0:
                    volatility = (sum((v - y_mean) ** 2 for v in values) / n) ** 0.5 / y_mean
                else:
                    volatility = 0.0
                
                trends[metric] = {
                    'slope': slope,
                    'direction': trend_direction,
                    'volatility': round(volatility, 2),
                    'average': round(y_mean, 2)
                }
        
        # Overall trend direction
        if trends:
            avg_slope = sum(t['slope'] for t in trends.values()) / len(trends)
            if avg_slope > 0.01:
                overall_direction = 'increasing'
            elif avg_slope < -0.01:
                overall_direction = 'decreasing'
            else:
                overall_direction = 'stable'
        else:
            overall_direction = 'insufficient_data'
            avg_slope = 0.0
        
        # Calculate monthly growth rate (average)
        if len(historical_data) >= 2:
            first_value = historical_data[0].get('total_points', 0)
            last_value = historical_data[-1].get('total_points', 0)
            if first_value > 0:
                total_growth = (last_value - first_value) / first_value
                monthly_growth_rate = total_growth / len(historical_data)
            else:
                monthly_growth_rate = 0.0
        else:
            monthly_growth_rate = 0.0
        
        return {
            'trend_direction': overall_direction,
            'trend_strength': round(abs(avg_slope), 4),
            'monthly_growth_rate': round(monthly_growth_rate, 4),
            'volatility': round(sum(t.get('volatility', 0) for t in trends.values()) / len(trends) if trends else 0, 2),
            'metric_trends': trends
        }
    
    def _generate_forecast(
        self,
        historical_data: List[Dict[str, Any]],
        trends: Dict[str, Any],
        months_ahead: int
    ) -> List[Dict[str, Any]]:
        """Generate forecasted data for next N months."""
        if not historical_data:
            return []
        
        forecasted = []
        last_month = historical_data[-1]
        monthly_growth = trends.get('monthly_growth_rate', 0.0)
        
        # Start from next month
        current_date = timezone.now().date().replace(day=1) + relativedelta(months=1)
        
        for i in range(months_ahead):
            forecast_month = current_date + relativedelta(months=i)
            
            # Simple forecast: last value * (1 + growth_rate) ^ months_ahead
            growth_factor = (1 + monthly_growth) ** (i + 1)
            
            forecasted.append({
                'month': forecast_month.strftime('%Y-%m'),
                'year': forecast_month.year,
                'month_number': forecast_month.month,
                'total_points': round(last_month.get('total_points', 0) * growth_factor, 2),
                'total_earnings': round(last_month.get('total_earnings', 0) * growth_factor, 2),
                'task_count': round(last_month.get('task_count', 0) * growth_factor, 0),
                'completion_rate': last_month.get('completion_rate', 0.0),  # Keep stable
                'unique_employees': last_month.get('unique_employees', 0),  # Keep stable
                'is_forecast': True,
                'confidence': self._calculate_month_confidence(i + 1, trends)
            })
        
        return forecasted
    
    def _calculate_forecast_confidence(
        self,
        historical_data: List[Dict[str, Any]],
        trends: Dict[str, Any]
    ) -> float:
        """Calculate overall forecast confidence (0-1)."""
        if not historical_data:
            return 0.0
        
        # Base confidence on:
        # 1. Amount of historical data (more = better)
        data_points = len(historical_data)
        data_confidence = min(1.0, data_points / 12.0)  # 12 months = 100%
        
        # 2. Trend stability (less volatility = better)
        volatility = trends.get('volatility', 1.0)
        stability_confidence = max(0.0, 1.0 - volatility)
        
        # 3. Trend strength (stronger trends = more predictable)
        trend_strength = trends.get('trend_strength', 0.0)
        trend_confidence = min(1.0, trend_strength * 10)  # Normalize
        
        # Weighted average
        confidence = (
            data_confidence * 0.4 +
            stability_confidence * 0.4 +
            trend_confidence * 0.2
        )
        
        return min(1.0, max(0.0, confidence))
    
    def _calculate_month_confidence(
        self,
        months_ahead: int,
        trends: Dict[str, Any]
    ) -> float:
        """Calculate confidence for a specific forecast month."""
        base_confidence = trends.get('confidence', 0.5)
        # Confidence decreases the further ahead we forecast
        decay_factor = 1.0 / (1.0 + months_ahead * 0.1)
        return round(base_confidence * decay_factor, 2)
    
    def _generate_forecast_insights(
        self,
        trends: Dict[str, Any],
        forecasted_data: List[Dict[str, Any]],
        confidence: float
    ) -> List[str]:
        """Generate insights from forecast data."""
        insights = []
        
        trend_direction = trends.get('trend_direction', 'stable')
        monthly_growth = trends.get('monthly_growth_rate', 0.0)
        
        if trend_direction == 'increasing':
            insights.append(f"Activity is trending upward with {monthly_growth*100:.1f}% monthly growth")
        elif trend_direction == 'decreasing':
            insights.append(f"Activity is trending downward with {monthly_growth*100:.1f}% monthly decline")
        else:
            insights.append("Activity trends are relatively stable")
        
        if forecasted_data:
            first_forecast = forecasted_data[0]
            last_forecast = forecasted_data[-1]
            growth = ((last_forecast.get('total_points', 0) - first_forecast.get('total_points', 0)) 
                     / first_forecast.get('total_points', 1) * 100)
            insights.append(f"Forecasted growth over {len(forecasted_data)} months: {growth:.1f}%")
        
        if confidence >= 0.8:
            insights.append("High confidence forecast based on stable historical patterns")
        elif confidence >= 0.6:
            insights.append("Moderate confidence forecast - some uncertainty in trends")
        else:
            insights.append("Low confidence forecast - limited or volatile historical data")
        
        volatility = trends.get('volatility', 0.0)
        if volatility > 0.3:
            insights.append("High volatility detected - forecasts may be less reliable")
        
        return insights
    
    def forecast_budget_needs(
        self,
        months_ahead: int = 3,
        department_id: Optional[int] = None,
        historical_months: int = 12
    ) -> Dict[str, Any]:
        """
        Forecast budget needs based on activity patterns.
        
        Args:
            months_ahead: Number of months to forecast
            department_id: Optional department filter
            historical_months: Historical data to analyze
        
        Returns:
            Dict with budget forecast
        """
        try:
            # Get activity forecast
            activity_forecast = self.forecast_activity_trends(
                months_ahead=months_ahead,
                department_id=department_id,
                historical_months=historical_months
            )
            
            if not activity_forecast.get('success'):
                return activity_forecast
            
            # Calculate budget needs from earnings forecast
            forecasted_data = activity_forecast.get('forecasted_data', [])
            
            budget_forecast = []
            for month_data in forecasted_data:
                budget_forecast.append({
                    'month': month_data['month'],
                    'estimated_earnings': month_data.get('total_earnings', 0),
                    'estimated_points': month_data.get('total_points', 0),
                    'estimated_tasks': month_data.get('task_count', 0),
                    'confidence': month_data.get('confidence', 0.0)
                })
            
            total_forecasted_earnings = sum(m['estimated_earnings'] for m in budget_forecast)
            
            return {
                'success': True,
                'forecast_period': activity_forecast.get('forecast_period'),
                'total_forecasted_earnings': round(total_forecasted_earnings, 2),
                'monthly_forecasts': budget_forecast,
                'trends': activity_forecast.get('trends', {}),
                'confidence': activity_forecast.get('confidence', 0.0),
                'insights': activity_forecast.get('insights', [])
            }
            
        except Exception as e:
            self.logger.error(f"Error forecasting budget needs: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Budget forecasting error: {str(e)}'
            }

