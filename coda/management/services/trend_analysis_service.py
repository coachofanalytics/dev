"""
Trend Analysis Service for Management App

Phase 3: Advanced Analytics
Service for analyzing historical trends and patterns in activity data.

Provides:
- Historical trend analysis
- Department/category performance trends
- Employee performance trends
- Seasonal pattern detection
- Anomaly detection
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
from accounts.models import CustomerUser, Department

logger = logging.getLogger(__name__)
User = get_user_model()


class TrendAnalysisService:
    """
    Service for analyzing trends in activity data.
    
    Phase 3: Advanced Analytics
    Provides comprehensive trend analysis for:
    - Historical performance trends
    - Department/category trends
    - Employee performance trends
    - Seasonal patterns
    - Anomaly detection
    """
    
    def __init__(self):
        self.logger = logger
    
    def analyze_historical_trends(
        self,
        months_back: int = 12,
        department_id: Optional[int] = None,
        category_id: Optional[int] = None,
        employee_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze historical trends for the specified period.
        
        Args:
            months_back: Number of months to analyze (default: 12)
            department_id: Optional department filter
            category_id: Optional category filter
            employee_id: Optional employee filter
        
        Returns:
            Dict with trend analysis data
        """
        try:
            self.logger.info(
                f"Analyzing historical trends for {months_back} months "
                f"(department={department_id}, category={category_id}, employee={employee_id})"
            )
            
            # Calculate date range
            end_date = timezone.now().date()
            start_date = end_date - relativedelta(months=months_back)
            
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
            if employee_id:
                query &= Q(employee_id=employee_id)
            
            # Get monthly trends
            monthly_trends = self._get_monthly_trends(query, start_date, end_date)
            
            # Get category trends
            category_trends = self._get_category_trends(query, start_date, end_date)
            
            # Get department trends
            department_trends = self._get_department_trends(query, start_date, end_date)
            
            # Detect seasonal patterns
            seasonal_patterns = self._detect_seasonal_patterns(monthly_trends)
            
            # Detect anomalies
            anomalies = self._detect_anomalies(monthly_trends)
            
            # Calculate overall trends
            overall_trends = self._calculate_overall_trends(monthly_trends)
            
            return {
                'success': True,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'months_analyzed': months_back
                },
                'monthly_trends': monthly_trends,
                'category_trends': category_trends,
                'department_trends': department_trends,
                'seasonal_patterns': seasonal_patterns,
                'anomalies': anomalies,
                'overall_trends': overall_trends,
                'metadata': {
                    'department_id': department_id,
                    'category_id': category_id,
                    'employee_id': employee_id
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing historical trends: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Trend analysis error: {str(e)}',
                'period': None,
                'monthly_trends': [],
                'category_trends': [],
                'department_trends': [],
                'seasonal_patterns': {},
                'anomalies': [],
                'overall_trends': {}
            }
    
    def _get_monthly_trends(
        self,
        query: Q,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get monthly aggregated trends."""
        monthly_data = []
        current_date = start_date.replace(day=1)
        
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
                unique_employees=Count('employee', distinct=True),
                avg_completion_rate=Avg(F('point') / F('mxpoint'))
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
                'avg_completion_rate': float(totals['avg_completion_rate'] or 0)
            })
            
            current_date = current_date + relativedelta(months=1)
        
        return monthly_data
    
    def _get_category_trends(
        self,
        query: Q,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get trends by category."""
        categories = TaskCategory.objects.all()
        category_trends = []
        
        for category in categories:
            category_query = query & Q(category=category)
            tasks = TaskHistory.objects.filter(category_query)
            
            if not tasks.exists():
                continue
            
            totals = tasks.aggregate(
                total_points=Sum('point'),
                total_max_points=Sum('mxpoint'),
                total_earnings=Sum(F('point') / F('mxpoint') * F('mxearning'), output_field=Decimal),
                task_count=Count('id')
            )
            
            total_points = totals['total_points'] or 0
            total_max_points = totals['total_max_points'] or 0
            completion_rate = (total_points / total_max_points) if total_max_points > 0 else 0.0
            
            category_trends.append({
                'category_id': category.id,
                'category_name': category.name,
                'total_points': float(total_points),
                'total_max_points': float(total_max_points),
                'total_earnings': float(totals['total_earnings'] or 0),
                'task_count': totals['task_count'] or 0,
                'completion_rate': round(completion_rate, 2)
            })
        
        return sorted(category_trends, key=lambda x: x['total_points'], reverse=True)
    
    def _get_department_trends(
        self,
        query: Q,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get trends by department."""
        departments = Department.objects.all()
        department_trends = []
        
        for department in departments:
            dept_query = query & Q(employee__department=department)
            tasks = TaskHistory.objects.filter(dept_query)
            
            if not tasks.exists():
                continue
            
            totals = tasks.aggregate(
                total_points=Sum('point'),
                total_max_points=Sum('mxpoint'),
                total_earnings=Sum(F('point') / F('mxpoint') * F('mxearning'), output_field=Decimal),
                task_count=Count('id'),
                unique_employees=Count('employee', distinct=True)
            )
            
            total_points = totals['total_points'] or 0
            total_max_points = totals['total_max_points'] or 0
            completion_rate = (total_points / total_max_points) if total_max_points > 0 else 0.0
            
            department_trends.append({
                'department_id': department.id,
                'department_name': department.name,
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
        
        return sorted(department_trends, key=lambda x: x['total_points'], reverse=True)
    
    def _detect_seasonal_patterns(
        self,
        monthly_trends: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Detect seasonal patterns in monthly data."""
        if len(monthly_trends) < 12:
            return {
                'has_seasonal_pattern': False,
                'message': 'Insufficient data for seasonal pattern detection (need 12+ months)'
            }
        
        # Group by month number (1-12)
        by_month = {}
        for data in monthly_trends:
            month_num = data['month_number']
            if month_num not in by_month:
                by_month[month_num] = []
            by_month[month_num].append(data)
        
        # Calculate average for each month
        monthly_averages = {}
        for month_num in range(1, 13):
            if month_num in by_month:
                month_data = by_month[month_num]
                monthly_averages[month_num] = {
                    'avg_points': sum(d['total_points'] for d in month_data) / len(month_data),
                    'avg_earnings': sum(d['total_earnings'] for d in month_data) / len(month_data),
                    'avg_completion_rate': sum(d['completion_rate'] for d in month_data) / len(month_data),
                    'count': len(month_data)
                }
        
        # Detect patterns (e.g., higher in certain months)
        if len(monthly_averages) >= 6:
            avg_points = sum(m['avg_points'] for m in monthly_averages.values()) / len(monthly_averages)
            
            peak_months = [
                month_num for month_num, data in monthly_averages.items()
                if data['avg_points'] > avg_points * 1.1
            ]
            low_months = [
                month_num for month_num, data in monthly_averages.items()
                if data['avg_points'] < avg_points * 0.9
            ]
            
            return {
                'has_seasonal_pattern': len(peak_months) > 0 or len(low_months) > 0,
                'monthly_averages': monthly_averages,
                'peak_months': peak_months,
                'low_months': low_months,
                'overall_average': round(avg_points, 2)
            }
        
        return {
            'has_seasonal_pattern': False,
            'message': 'Insufficient data for seasonal analysis'
        }
    
    def _detect_anomalies(
        self,
        monthly_trends: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in monthly trends."""
        if len(monthly_trends) < 3:
            return []
        
        anomalies = []
        
        # Calculate statistics
        points_values = [d['total_points'] for d in monthly_trends]
        earnings_values = [d['total_earnings'] for d in monthly_trends]
        
        if not points_values:
            return []
        
        # Calculate mean and standard deviation
        mean_points = sum(points_values) / len(points_values)
        variance_points = sum((x - mean_points) ** 2 for x in points_values) / len(points_values)
        std_dev_points = variance_points ** 0.5
        
        mean_earnings = sum(earnings_values) / len(earnings_values) if earnings_values else 0
        variance_earnings = sum((x - mean_earnings) ** 2 for x in earnings_values) / len(earnings_values) if earnings_values else 0
        std_dev_earnings = variance_earnings ** 0.5 if variance_earnings > 0 else 0
        
        # Detect outliers (beyond 2 standard deviations)
        threshold = 2.0
        
        for data in monthly_trends:
            points_z_score = abs((data['total_points'] - mean_points) / std_dev_points) if std_dev_points > 0 else 0
            earnings_z_score = abs((data['total_earnings'] - mean_earnings) / std_dev_earnings) if std_dev_earnings > 0 else 0
            
            if points_z_score > threshold or earnings_z_score > threshold:
                anomalies.append({
                    'month': data['month'],
                    'type': 'outlier',
                    'severity': 'high' if max(points_z_score, earnings_z_score) > 3 else 'medium',
                    'points_z_score': round(points_z_score, 2),
                    'earnings_z_score': round(earnings_z_score, 2),
                    'total_points': data['total_points'],
                    'total_earnings': data['total_earnings'],
                    'description': f"Unusual activity in {data['month']}"
                })
        
        return anomalies
    
    def _calculate_overall_trends(
        self,
        monthly_trends: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate overall trend direction and strength."""
        if len(monthly_trends) < 2:
            return {
                'direction': 'insufficient_data',
                'strength': 0.0,
                'growth_rate': 0.0
            }
        
        # Calculate trend for total_points
        points_values = [d['total_points'] for d in monthly_trends]
        n = len(points_values)
        x_mean = (n - 1) / 2
        y_mean = sum(points_values) / n
        
        numerator = sum((i - x_mean) * (points_values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator > 0:
            slope = numerator / denominator
        else:
            slope = 0.0
        
        # Determine direction
        if slope > 0.01:
            direction = 'increasing'
        elif slope < -0.01:
            direction = 'decreasing'
        else:
            direction = 'stable'
        
        # Calculate growth rate
        if points_values[0] > 0:
            total_growth = (points_values[-1] - points_values[0]) / points_values[0]
            monthly_growth_rate = total_growth / n
        else:
            monthly_growth_rate = 0.0
        
        return {
            'direction': direction,
            'strength': round(abs(slope), 4),
            'monthly_growth_rate': round(monthly_growth_rate, 4),
            'first_month_points': points_values[0],
            'last_month_points': points_values[-1],
            'total_change': round(points_values[-1] - points_values[0], 2),
            'percent_change': round((points_values[-1] - points_values[0]) / points_values[0] * 100, 2) if points_values[0] > 0 else 0.0
        }
    
    def analyze_employee_trends(
        self,
        employee_id: int,
        months_back: int = 12
    ) -> Dict[str, Any]:
        """
        Analyze trends for a specific employee.
        
        Args:
            employee_id: Employee ID
            months_back: Number of months to analyze
        
        Returns:
            Dict with employee trend analysis
        """
        try:
            return self.analyze_historical_trends(
                months_back=months_back,
                employee_id=employee_id
            )
        except Exception as e:
            self.logger.error(f"Error analyzing employee trends: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Employee trend analysis error: {str(e)}'
            }

