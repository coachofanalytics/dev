"""
Compliance KPI Service for Management App

Phase 3: Advanced Analytics
Service for real-time compliance monitoring and KPI tracking.

Provides:
- Real-time compliance KPIs
- Historical compliance trends
- Department-level compliance metrics
- Automated compliance alerts
- Compliance dashboard data
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Q, Sum, Avg, Count, Max, Min, F
from django.utils import timezone
from django.contrib.auth import get_user_model

from management.models import TaskHistory, Task
from management.services.employee_compliance_service import EmployeeComplianceService
from shared_core.users import CustomerUser, Department

logger = logging.getLogger(__name__)
User = get_user_model()


class ComplianceKPIService:
    """
    Service for tracking compliance KPIs and real-time monitoring.
    
    Phase 3: Advanced Analytics
    Provides comprehensive compliance tracking for:
    - Real-time compliance metrics
    - Historical compliance trends
    - Department-level KPIs
    - Automated alerts
    """
    
    def __init__(self):
        self.logger = logger
        self.compliance_service = EmployeeComplianceService()
        self.compliance_threshold = 33.0
    
    def get_realtime_compliance_kpis(
        self,
        department_id: Optional[int] = None,
        target_month: Optional[int] = None,
        target_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get real-time compliance KPIs.
        
        Args:
            department_id: Optional department filter
            target_month: Target month (default: last month)
            target_year: Target year (default: current year)
        
        Returns:
            Dict with real-time compliance KPIs
        """
        try:
            # Default to last month
            if target_month is None or target_year is None:
                last_month = date.today() - relativedelta(months=1)
                target_month = target_month or last_month.month
                target_year = target_year or last_month.year
            
            self.logger.info(
                f"Getting real-time compliance KPIs for {target_month}/{target_year} "
                f"(department={department_id})"
            )
            
            # Build query
            query = Q(
                daf_date__month=target_month,
                daf_date__year=target_year,
                employee__is_active=True,
                employee__is_staff=True
            )
            
            if department_id:
                query &= Q(employee__department_id=department_id)
            
            # Exclude system users
            query &= ~Q(employee__username__in=['coda_info', 'luke', 'angel'])
            
            # Get employee-level compliance
            employees_data = TaskHistory.objects.filter(query).values('employee').annotate(
                emp_points=Sum('point'),
                emp_max_points=Sum('mxpoint'),
                task_count=Count('id')
            ).filter(emp_max_points__gt=0)
            
            total_employees = employees_data.count()
            compliant_count = 0
            non_compliant_count = 0
            at_risk_count = 0  # Between 25-33%
            
            compliance_details = []
            
            for emp_data in employees_data:
                employee_id = emp_data['employee']
                emp_points = emp_data['emp_points'] or 0
                emp_max_points = emp_data['emp_max_points'] or 0
                compliance_rate = (emp_points / emp_max_points * 100) if emp_max_points > 0 else 0.0
                
                if compliance_rate >= self.compliance_threshold:
                    compliant_count += 1
                    status = 'compliant'
                elif compliance_rate >= 25.0:
                    at_risk_count += 1
                    status = 'at_risk'
                else:
                    non_compliant_count += 1
                    status = 'non_compliant'
                
                try:
                    employee = CustomerUser.objects.get(id=employee_id)
                    compliance_details.append({
                        'employee_id': employee_id,
                        'employee_name': f"{employee.first_name} {employee.last_name}".strip() or employee.username,
                        'username': employee.username,
                        'department': employee.department.name if hasattr(employee, 'department') and employee.department else 'Unknown',
                        'compliance_rate': round(compliance_rate, 2),
                        'status': status,
                        'points': float(emp_points),
                        'max_points': float(emp_max_points),
                        'task_count': emp_data['task_count']
                    })
                except CustomerUser.DoesNotExist:
                    continue
            
            # Calculate overall metrics
            overall_compliance_rate = (compliant_count / total_employees * 100) if total_employees > 0 else 0.0
            
            # Get department-level breakdown
            department_breakdown = self._get_department_compliance(query, target_month, target_year)
            
            # Calculate trends (compare with previous month)
            previous_month = date(target_year, target_month, 1) - relativedelta(months=1)
            previous_trends = self._get_compliance_trend(
                previous_month.month,
                previous_month.year,
                department_id
            )
            
            return {
                'success': True,
                'period': {
                    'month': target_month,
                    'year': target_year,
                    'period_label': f"{target_month}/{target_year}"
                },
                'overall_metrics': {
                    'total_employees': total_employees,
                    'compliant_count': compliant_count,
                    'non_compliant_count': non_compliant_count,
                    'at_risk_count': at_risk_count,
                    'overall_compliance_rate': round(overall_compliance_rate, 2),
                    'compliance_threshold': self.compliance_threshold
                },
                'employee_details': sorted(compliance_details, key=lambda x: x['compliance_rate'], reverse=True),
                'department_breakdown': department_breakdown,
                'trends': {
                    'current_compliance_rate': round(overall_compliance_rate, 2),
                    'previous_compliance_rate': previous_trends.get('compliance_rate', 0),
                    'change': round(overall_compliance_rate - previous_trends.get('compliance_rate', 0), 2),
                    'direction': 'improving' if overall_compliance_rate > previous_trends.get('compliance_rate', 0) else 'declining' if overall_compliance_rate < previous_trends.get('compliance_rate', 0) else 'stable'
                },
                'alerts': self._generate_compliance_alerts(compliance_details, overall_compliance_rate),
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting real-time compliance KPIs: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Compliance KPI error: {str(e)}',
                'overall_metrics': {},
                'employee_details': [],
                'department_breakdown': [],
                'trends': {},
                'alerts': []
            }
    
    def _get_department_compliance(
        self,
        query: Q,
        target_month: int,
        target_year: int
    ) -> List[Dict[str, Any]]:
        """Get compliance breakdown by department."""
        departments = Department.objects.all()
        department_breakdown = []
        
        for department in departments:
            dept_query = query & Q(employee__department=department)
            employees_data = TaskHistory.objects.filter(dept_query).values('employee').annotate(
                emp_points=Sum('point'),
                emp_max_points=Sum('mxpoint')
            ).filter(emp_max_points__gt=0)
            
            if not employees_data.exists():
                continue
            
            total_employees = employees_data.count()
            compliant_count = 0
            
            for emp_data in employees_data:
                emp_points = emp_data['emp_points'] or 0
                emp_max_points = emp_data['emp_max_points'] or 0
                compliance_rate = (emp_points / emp_max_points * 100) if emp_max_points > 0 else 0.0
                if compliance_rate >= self.compliance_threshold:
                    compliant_count += 1
            
            dept_compliance_rate = (compliant_count / total_employees * 100) if total_employees > 0 else 0.0
            
            department_breakdown.append({
                'department_id': department.id,
                'department_name': department.name,
                'total_employees': total_employees,
                'compliant_count': compliant_count,
                'non_compliant_count': total_employees - compliant_count,
                'compliance_rate': round(dept_compliance_rate, 2),
                'status': 'compliant' if dept_compliance_rate >= 80 else 'at_risk' if dept_compliance_rate >= 60 else 'non_compliant'
            })
        
        return sorted(department_breakdown, key=lambda x: x['compliance_rate'], reverse=True)
    
    def _get_compliance_trend(
        self,
        target_month: int,
        target_year: int,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get compliance trend for a specific month."""
        try:
            query = Q(
                daf_date__month=target_month,
                daf_date__year=target_year,
                employee__is_active=True,
                employee__is_staff=True
            )
            
            if department_id:
                query &= Q(employee__department_id=department_id)
            
            query &= ~Q(employee__username__in=['coda_info', 'luke', 'angel'])
            
            employees_data = TaskHistory.objects.filter(query).values('employee').annotate(
                emp_points=Sum('point'),
                emp_max_points=Sum('mxpoint')
            ).filter(emp_max_points__gt=0)
            
            total_employees = employees_data.count()
            compliant_count = 0
            
            for emp_data in employees_data:
                emp_points = emp_data['emp_points'] or 0
                emp_max_points = emp_data['emp_max_points'] or 0
                compliance_rate = (emp_points / emp_max_points * 100) if emp_max_points > 0 else 0.0
                if compliance_rate >= self.compliance_threshold:
                    compliant_count += 1
            
            compliance_rate = (compliant_count / total_employees * 100) if total_employees > 0 else 0.0
            
            return {
                'compliance_rate': round(compliance_rate, 2),
                'compliant_count': compliant_count,
                'total_employees': total_employees
            }
        except Exception:
            return {
                'compliance_rate': 0,
                'compliant_count': 0,
                'total_employees': 0
            }
    
    def _generate_compliance_alerts(
        self,
        compliance_details: List[Dict[str, Any]],
        overall_compliance_rate: float
    ) -> List[Dict[str, Any]]:
        """Generate compliance alerts based on current metrics."""
        alerts = []
        
        # Overall compliance alert
        if overall_compliance_rate < 70:
            alerts.append({
                'type': 'critical',
                'severity': 'high',
                'message': f'Overall compliance rate is below 70% ({overall_compliance_rate:.1f}%)',
                'action_required': 'Review department compliance and provide support'
            })
        elif overall_compliance_rate < 80:
            alerts.append({
                'type': 'warning',
                'severity': 'medium',
                'message': f'Overall compliance rate is below 80% ({overall_compliance_rate:.1f}%)',
                'action_required': 'Monitor compliance trends'
            })
        
        # Individual employee alerts
        non_compliant = [e for e in compliance_details if e['status'] == 'non_compliant']
        if len(non_compliant) > 0:
            alerts.append({
                'type': 'employee_non_compliant',
                'severity': 'high',
                'message': f'{len(non_compliant)} employee(s) are non-compliant',
                'count': len(non_compliant),
                'action_required': 'Review individual employee compliance and provide support'
            })
        
        at_risk = [e for e in compliance_details if e['status'] == 'at_risk']
        if len(at_risk) > 0:
            alerts.append({
                'type': 'employee_at_risk',
                'severity': 'medium',
                'message': f'{len(at_risk)} employee(s) are at risk (25-33% compliance)',
                'count': len(at_risk),
                'action_required': 'Monitor at-risk employees closely'
            })
        
        return alerts
    
    def get_compliance_history(
        self,
        months_back: int = 12,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get historical compliance data for trend analysis.
        
        Args:
            months_back: Number of months to analyze
            department_id: Optional department filter
        
        Returns:
            Dict with historical compliance data
        """
        try:
            historical_data = []
            current_date = date.today()
            
            for i in range(months_back):
                target_date = current_date - relativedelta(months=i)
                trend_data = self._get_compliance_trend(
                    target_date.month,
                    target_date.year,
                    department_id
                )
                
                historical_data.append({
                    'month': target_date.strftime('%Y-%m'),
                    'year': target_date.year,
                    'month_number': target_date.month,
                    'compliance_rate': trend_data['compliance_rate'],
                    'compliant_count': trend_data['compliant_count'],
                    'total_employees': trend_data['total_employees']
                })
            
            # Calculate trend
            if len(historical_data) >= 2:
                first_rate = historical_data[-1]['compliance_rate']
                last_rate = historical_data[0]['compliance_rate']
                trend_direction = 'improving' if last_rate > first_rate else 'declining' if last_rate < first_rate else 'stable'
                trend_change = last_rate - first_rate
            else:
                trend_direction = 'insufficient_data'
                trend_change = 0.0
            
            return {
                'success': True,
                'historical_data': list(reversed(historical_data)),  # Oldest first
                'trend': {
                    'direction': trend_direction,
                    'change': round(trend_change, 2),
                    'current_rate': historical_data[0]['compliance_rate'] if historical_data else 0,
                    'average_rate': round(sum(d['compliance_rate'] for d in historical_data) / len(historical_data), 2) if historical_data else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting compliance history: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Compliance history error: {str(e)}',
                'historical_data': [],
                'trend': {}
            }

