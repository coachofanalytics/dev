"""
Budget Consolidation Service for CODA Finance System

Service for consolidating Budget and CodaBudget models including:
- Data migration between models
- Unified reporting
- Model consolidation strategies
- Legacy support
"""

from decimal import Decimal
from typing import Dict, List, Any, Optional
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime
import logging

from ..models import Budget, CodaBudget, Transaction, Inflow, BudgetCategory, Company, Department
from ..utils.calculation_utils import CalculationUtils
from ..utils.filter_utils import FilterUtils
from .base_service import BaseFinanceService

logger = logging.getLogger(__name__)


class BudgetConsolidationService(BaseFinanceService):
    """Service for consolidating budget models"""
    
    def __init__(self):
        super().__init__()
        self.calculation_utils = CalculationUtils()
        self.filter_utils = FilterUtils()
    
    def get_unified_budget_report(self, company, department=None) -> Dict[str, Any]:
        """
        Get unified budget report across all models
        
        Args:
            company: Company object
            department: Department object (optional)
            
        Returns:
            Dictionary with unified budget report
        """
        try:
            # Get filter for company and department
            budget_filter = self.filter_utils.get_combined_filter(
                company=company, department=department
            )
            
            # Get data from Budget model (includes migrated CodaBudget data)
            budgets = Budget.objects.filter(budget_filter)
            
            # Note: CodaBudget data has been migrated to Budget model
            # No need to query CodaBudget separately
            
            # Calculate totals
            budget_total = sum(
                budget.unit_price * budget.quantity 
                for budget in budgets 
                if budget.unit_price and budget.quantity
            )
            
            combined_total = budget_total
            
            # Category breakdown
            category_breakdown = {}
            
            # Process Budget model (includes migrated CodaBudget data)
            for budget in budgets:
                if budget.category:
                    cat_name = budget.category.name
                    if cat_name not in category_breakdown:
                        category_breakdown[cat_name] = {
                            'total_amount': Decimal('0.00'),
                            'budget_count': 0
                        }
                    
                    amount = budget.unit_price * budget.quantity if budget.unit_price and budget.quantity else Decimal('0.00')
                    category_breakdown[cat_name]['total_amount'] += amount
                    category_breakdown[cat_name]['budget_count'] += 1
            
            # Department breakdown
            department_breakdown = {}
            
            for budget in budgets:
                if budget.department:
                    dept_name = budget.department.name
                    if dept_name not in department_breakdown:
                        department_breakdown[dept_name] = {
                            'total_amount': Decimal('0.00'),
                            'budget_count': 0
                        }
                    
                    amount = budget.unit_price * budget.quantity if budget.unit_price and budget.quantity else Decimal('0.00')
                    department_breakdown[dept_name]['total_amount'] += amount
                    department_breakdown[dept_name]['budget_count'] += 1
            
            return {
                'summary': {
                    'legacy_budget_total': budget_total,
                    'legacy_coda_budget_total': coda_budget_total,
                    'combined_total': combined_total,
                    'total_categories': len(category_breakdown),
                    'total_departments': len(department_breakdown)
                },
                'category_breakdown': category_breakdown,
                'department_breakdown': department_breakdown,
                'recommendations': self._generate_consolidation_recommendations(
                    budget_total, coda_budget_total, category_breakdown
                )
            }
            
        except Exception as e:
            logger.error(f"Error generating unified budget report: {str(e)}")
            return {'error': str(e)}
    
    def _generate_consolidation_recommendations(self, budget_total: Decimal, 
                                              coda_budget_total: Decimal, 
                                              category_breakdown: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations for budget consolidation
        
        Args:
            budget_total: Total from Budget model
            coda_budget_total: Total from CodaBudget model
            category_breakdown: Category breakdown data
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Model usage recommendations
        if budget_total > 0 and coda_budget_total > 0:
            recommendations.append("Both Budget and CodaBudget models are in use - consider consolidation")
        
        if budget_total > coda_budget_total * 2:
            recommendations.append("Budget model usage significantly higher than CodaBudget - consider migrating CodaBudget data")
        elif coda_budget_total > budget_total * 2:
            recommendations.append("CodaBudget model usage significantly higher than Budget - consider migrating Budget data")
        
        # Category recommendations
        for cat_name, data in category_breakdown.items():
            if data['budget_count'] > 0 and data['coda_budget_count'] > 0:
                recommendations.append(f"Category '{cat_name}' has entries in both models - consider consolidation")
        
        # General recommendations
        if budget_total > 0 or coda_budget_total > 0:
            recommendations.append("Consider creating a unified ConsolidatedBudget model")
            recommendations.append("Implement automated budget estimation based on historical spending")
            recommendations.append("Create unified API endpoints for budget operations")
        
        return recommendations
    
    def migrate_budget_data(self, company, target_model='consolidated') -> Dict[str, Any]:
        """
        Migrate budget data between models
        
        Args:
            company: Company object
            target_model: Target model ('consolidated', 'budget', 'coda_budget')
            
        Returns:
            Dictionary with migration results
        """
        try:
            migration_results = {
                'budget_migrations': 0,
                'coda_budget_migrations': 0,
                'errors': [],
                'success': True
            }
            
            if target_model == 'consolidated':
                # This would migrate to a ConsolidatedBudget model when created
                migration_results['message'] = "ConsolidatedBudget model not yet implemented"
                migration_results['success'] = False
                return migration_results
            
            elif target_model == 'coda_budget':
                # Migrate Budget to CodaBudget
                budgets = Budget.objects.filter(company=company)
                
                for budget in budgets:
                    try:
                        CodaBudget.objects.create(
                            budget_lead=budget.budget_lead,
                            company=budget.company,
                            department=budget.department,
                            category=budget.category,
                            subcategory=budget.subcategory,
                            item=budget.item_name,
                            cases=1,  # Default value
                            quantity=budget.quantity,
                            unit_price=budget.unit_price,
                            description=budget.description or "",
                            receipt_link=budget.receipt_link or ""
                        )
                        migration_results['budget_migrations'] += 1
                    except Exception as e:
                        migration_results['errors'].append(f"Error migrating budget {budget.id}: {str(e)}")
            
            elif target_model == 'budget':
                # Migrate CodaBudget to Budget
                coda_budgets = CodaBudget.objects.filter(company=company)
                
                for coda_budget in coda_budgets:
                    try:
                        Budget.objects.create(
                            budget_lead=coda_budget.budget_lead,
                            company=coda_budget.company,
                            department=coda_budget.department,
                            category=coda_budget.category,
                            subcategory=coda_budget.subcategory,
                            item=coda_budget.item_name,
                            qty=coda_budget.quantity,
                            unit_price=coda_budget.unit_price,
                            description=coda_budget.description or "",
                            receipt_link=coda_budget.receipt_link or ""
                        )
                        migration_results['coda_budget_migrations'] += 1
                    except Exception as e:
                        migration_results['errors'].append(f"Error migrating coda_budget {coda_budget.id}: {str(e)}")
            
            return migration_results
            
        except Exception as e:
            logger.error(f"Error in budget data migration: {str(e)}")
            return {'error': str(e), 'success': False}
    
    def get_model_usage_statistics(self, company) -> Dict[str, Any]:
        """
        Get usage statistics for budget models
        
        Args:
            company: Company object
            
        Returns:
            Dictionary with usage statistics
        """
        try:
            budget_filter = self.filter_utils.get_company_filter(company)
            
            # Budget model statistics
            budget_stats = Budget.objects.filter(budget_filter).aggregate(
                total_count=Count('id'),
                total_amount=Sum('unit_price') * Sum('qty'),
                avg_amount=Sum('unit_price') * Sum('qty') / Count('id')
            )
            
            # CodaBudget model statistics
            coda_budget_stats = CodaBudget.objects.filter(budget_filter).aggregate(
                total_count=Count('id'),
                total_amount=Sum('amount'),
                avg_amount=Sum('amount') / Count('id')
            )
            
            # Category usage
            budget_categories = Budget.objects.filter(budget_filter).values_list(
                'category__name', flat=True
            ).distinct()
            
            coda_budget_categories = CodaBudget.objects.filter(budget_filter).values_list(
                'category__name', flat=True
            ).distinct()
            
            # Department usage
            budget_departments = Budget.objects.filter(budget_filter).values_list(
                'department__name', flat=True
            ).distinct()
            
            coda_budget_departments = CodaBudget.objects.filter(budget_filter).values_list(
                'department__name', flat=True
            ).distinct()
            
            return {
                'budget_model': {
                    'total_entries': budget_stats['total_count'] or 0,
                    'total_amount': budget_stats['total_amount'] or Decimal('0.00'),
                    'average_amount': budget_stats['avg_amount'] or Decimal('0.00'),
                    'categories_used': len(budget_categories),
                    'departments_used': len(budget_departments)
                },
                'coda_budget_model': {
                    'total_entries': coda_budget_stats['total_count'] or 0,
                    'total_amount': coda_budget_stats['total_amount'] or Decimal('0.00'),
                    'average_amount': coda_budget_stats['avg_amount'] or Decimal('0.00'),
                    'categories_used': len(coda_budget_categories),
                    'departments_used': len(coda_budget_departments)
                },
                'consolidation_analysis': {
                    'shared_categories': len(set(budget_categories) & set(coda_budget_categories)),
                    'shared_departments': len(set(budget_departments) & set(coda_budget_departments)),
                    'total_unique_categories': len(set(budget_categories) | set(coda_budget_categories)),
                    'total_unique_departments': len(set(budget_departments) | set(coda_budget_departments))
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting model usage statistics: {str(e)}")
            return {'error': str(e)}
    
    def create_consolidated_view(self, company, department=None) -> Dict[str, Any]:
        """
        Create a consolidated view of budget data
        
        Args:
            company: Company object
            department: Department object (optional)
            
        Returns:
            Dictionary with consolidated view data
        """
        try:
            budget_filter = self.filter_utils.get_combined_filter(
                company=company, department=department
            )
            
            # Get all budget data
            budgets = Budget.objects.filter(budget_filter).select_related(
                'category', 'subcategory', 'department', 'budget_lead'
            )
            coda_budgets = CodaBudget.objects.filter(budget_filter).select_related(
                'category', 'subcategory', 'department', 'budget_lead'
            )
            
            # Create unified data structure
            consolidated_data = []
            
            # Process Budget entries
            for budget in budgets:
                consolidated_data.append({
                    'id': budget.id,
                    'model_type': 'Budget',
                    'budget_lead': budget.budget_lead.get_full_name() if budget.budget_lead else 'Unknown',
                    'department': budget.department.name if budget.department else 'Unknown',
                    'category': budget.category.name if budget.category else 'Unknown',
                    'subcategory': budget.subcategory.name if budget.subcategory else 'N/A',
                    'item': budget.item_name,
                    'quantity': budget.quantity,
                    'unit_price': budget.unit_price,
                    'amount': budget.unit_price * budget.quantity if budget.unit_price and budget.quantity else Decimal('0.00'),
                    'description': budget.description,
                    'created_at': budget.created_at,
                    'updated_at': budget.updated_at
                })
            
            # Process CodaBudget entries
            for coda_budget in coda_budgets:
                consolidated_data.append({
                    'id': coda_budget.id,
                    'model_type': 'CodaBudget',
                    'budget_lead': coda_budget.budget_lead.get_full_name() if coda_budget.budget_lead else 'Unknown',
                    'department': coda_budget.department.name if coda_budget.department else 'Unknown',
                    'category': coda_budget.category.name if coda_budget.category else 'Unknown',
                    'subcategory': coda_budget.subcategory.name if coda_budget.subcategory else 'N/A',
                    'item': coda_budget.item_name,
                    'qty': coda_budget.quantity,
                    'unit_price': coda_budget.unit_price,
                    'amount': coda_budget.amount,
                    'description': coda_budget.description,
                    'created_at': coda_budget.created_at,
                    'updated_at': coda_budget.updated_at
                })
            
            # Sort by created_at
            consolidated_data.sort(key=lambda x: x['created_at'], reverse=True)
            
            return {
                'data': consolidated_data,
                'total_entries': len(consolidated_data),
                'budget_entries': len([d for d in consolidated_data if d['model_type'] == 'Budget']),
                'coda_budget_entries': len([d for d in consolidated_data if d['model_type'] == 'CodaBudget']),
                'total_amount': sum(d['amount'] for d in consolidated_data)
            }
            
        except Exception as e:
            logger.error(f"Error creating consolidated view: {str(e)}")
            return {'error': str(e)}

