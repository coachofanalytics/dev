"""
Data Quality Service

Improves budget estimates by analyzing historical data quality,
detecting outliers, and providing data-driven recommendations.
"""

import statistics
from decimal import Decimal
from typing import Dict, List, Any, Tuple
from django.db.models import Q, Avg, StdDev, Count
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from ..models import Transaction, BudgetCategory
from .budget_estimation_service import BudgetEstimationService

logger = logging.getLogger(__name__)


class DataQualityService:
    """
    Service for improving data quality and budget estimates
    """
    
    def __init__(self):
        self.estimation_service = BudgetEstimationService()
    
    def analyze_data_quality(self, company, department=None, months=12) -> Dict[str, Any]:
        """
        Analyze data quality for budget estimation
        
        Args:
            company: Company object
            department: Department object (optional)
            months: Number of months to analyze
            
        Returns:
            Dictionary with data quality analysis
        """
        try:
            # Get transactions
            end_date = timezone.now()
            start_date = end_date - timedelta(days=months * 30)
            
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
            
            analysis = {
                'total_transactions': transactions.count(),
                'date_range': {
                    'start': start_date,
                    'end': end_date,
                    'months': months
                },
                'quality_issues': [],
                'recommendations': [],
                'category_analysis': {},
                'outlier_analysis': {},
                'trend_analysis': {},
                'completeness_score': 0.0,
                'accuracy_score': 0.0,
                'overall_score': 0.0
            }
            
            if not transactions.exists():
                analysis['quality_issues'].append("No transactions found in the specified period")
                return analysis
            
            # Analyze by category
            categories = transactions.values_list('category__name', flat=True).distinct()
            
            for category_name in categories:
                if not category_name:
                    continue
                    
                cat_transactions = transactions.filter(category__name=category_name)
                cat_analysis = self._analyze_category_quality(cat_transactions, category_name)
                analysis['category_analysis'][category_name] = cat_analysis
            
            # Overall quality assessment
            analysis['completeness_score'] = self._calculate_completeness_score(transactions)
            analysis['accuracy_score'] = self._calculate_accuracy_score(transactions)
            analysis['overall_score'] = (analysis['completeness_score'] + analysis['accuracy_score']) / 2
            
            # Generate recommendations
            analysis['recommendations'] = self._generate_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing data quality: {e}")
            return {'error': str(e)}
    
    def _analyze_category_quality(self, transactions, category_name: str) -> Dict[str, Any]:
        """Analyze quality for a specific category"""
        amounts = []
        for txn in transactions:
            if hasattr(txn, 'amount_usd') and txn.amount_usd:
                amount = float(txn.amount_usd * txn.qty) if txn.qty else float(txn.amount_usd)
            else:
                amount = float(txn.amount * txn.qty) if txn.qty else float(txn.amount)
            amounts.append(amount)
        
        if not amounts:
            return {'error': 'No valid amounts found'}
        
        # Statistical analysis
        if len(amounts) == 0:
            return {'error': 'No valid amounts found'}
        
        mean_amount = statistics.mean(amounts)
        median_amount = statistics.median(amounts)
        std_dev = statistics.stdev(amounts) if len(amounts) > 1 else 0
        
        # Outlier detection (using IQR method)
        if len(amounts) >= 4:
            quantiles = statistics.quantiles(amounts, n=4)
            q1 = quantiles[0]
            q3 = quantiles[2]
            iqr = q3 - q1
        else:
            # Not enough data for IQR, use simple outlier detection
            q1 = min(amounts)
            q3 = max(amounts)
            iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = [amount for amount in amounts if amount < lower_bound or amount > upper_bound]
        
        # Data quality issues
        issues = []
        if len(outliers) > len(amounts) * 0.2:  # More than 20% outliers
            issues.append(f"High number of outliers ({len(outliers)}/{len(amounts)})")
        
        if std_dev > mean_amount:  # High variance
            issues.append("High variance in transaction amounts")
        
        if len(amounts) < 5:  # Low sample size
            issues.append("Low sample size for reliable estimation")
        
        return {
            'transaction_count': len(amounts),
            'mean_amount': mean_amount,
            'median_amount': median_amount,
            'std_deviation': std_dev,
            'coefficient_of_variation': std_dev / mean_amount if mean_amount > 0 else 0,
            'outliers': {
                'count': len(outliers),
                'percentage': len(outliers) / len(amounts) * 100,
                'amounts': outliers
            },
            'issues': issues,
            'quality_score': self._calculate_category_quality_score(len(amounts), len(outliers), std_dev, mean_amount)
        }
    
    def _calculate_completeness_score(self, transactions) -> float:
        """Calculate data completeness score (0-1)"""
        total_fields = 0
        filled_fields = 0
        
        for txn in transactions:
            # Check required fields
            fields_to_check = ['amount', 'category', 'transaction_date', 'description']
            for field in fields_to_check:
                total_fields += 1
                if getattr(txn, field, None) is not None:
                    filled_fields += 1
        
        return filled_fields / total_fields if total_fields > 0 else 0.0
    
    def _calculate_accuracy_score(self, transactions) -> float:
        """Calculate data accuracy score (0-1)"""
        # Check for common accuracy issues
        issues = 0
        total_checks = 0
        
        for txn in transactions:
            total_checks += 1
            
            # Check for negative amounts (might be refunds, but flag for review)
            if txn.amount and txn.amount < 0:
                issues += 0.5  # Half penalty for negative amounts
            
            # Check for extremely large amounts (potential data entry errors)
            if txn.amount and txn.amount > 1000000:  # > $1M
                issues += 0.3
            
            # Check for missing descriptions
            if not txn.description or txn.description.strip() == '':
                issues += 0.2
        
        return max(0.0, 1.0 - (issues / total_checks)) if total_checks > 0 else 0.0
    
    def _calculate_category_quality_score(self, count: int, outliers: int, std_dev: float, mean: float) -> float:
        """Calculate quality score for a category (0-1)"""
        score = 1.0
        
        # Penalize low sample size
        if count < 5:
            score -= 0.3
        elif count < 10:
            score -= 0.1
        
        # Penalize high outlier percentage
        outlier_percentage = outliers / count if count > 0 else 1.0
        if outlier_percentage > 0.2:
            score -= 0.3
        elif outlier_percentage > 0.1:
            score -= 0.1
        
        # Penalize high variance
        if mean > 0:
            cv = std_dev / mean
            if cv > 2.0:
                score -= 0.3
            elif cv > 1.0:
                score -= 0.1
        
        return max(0.0, score)
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate data quality recommendations"""
        recommendations = []
        
        # Overall score recommendations
        if analysis['overall_score'] < 0.5:
            recommendations.append("Data quality is poor. Consider data cleanup before making budget estimates.")
        elif analysis['overall_score'] < 0.7:
            recommendations.append("Data quality is moderate. Review and clean data for better estimates.")
        
        # Completeness recommendations
        if analysis['completeness_score'] < 0.8:
            recommendations.append("Improve data completeness by ensuring all required fields are filled.")
        
        # Accuracy recommendations
        if analysis['accuracy_score'] < 0.8:
            recommendations.append("Review transaction data for accuracy and consistency.")
        
        # Category-specific recommendations
        for category, cat_analysis in analysis['category_analysis'].items():
            if cat_analysis.get('quality_score', 1.0) < 0.6:
                recommendations.append(f"Review {category} transactions for data quality issues.")
            
            if cat_analysis.get('transaction_count', 0) < 5:
                recommendations.append(f"Insufficient data for {category}. Consider collecting more historical data.")
        
        return recommendations
    
    def improve_estimates_with_quality_analysis(self, company, department=None, horizon='monthly') -> Dict[str, Any]:
        """
        Generate improved estimates using data quality analysis
        
        Args:
            company: Company object
            department: Department object (optional)
            horizon: Estimation horizon
            
        Returns:
            Dictionary with improved estimates and quality insights
        """
        try:
            # Get base estimates
            if horizon == 'monthly':
                base_estimates = self.estimation_service.estimate_next_month_budget(
                    company, department, method='average'
                )
            else:
                annual_estimates = self.estimation_service.estimate_annual_budget(
                    company, department, method='ytd_average'
                )
                factor = 2 if horizon == 'two_year' else 5
                base_estimates = {
                    'estimates': annual_estimates.get('estimates', {}),
                    'total_estimate': (annual_estimates.get('total_estimate') or 0) * factor,
                    'method': f"ytd_average_x{factor}",
                }
            
            # Get data quality analysis
            quality_analysis = self.analyze_data_quality(company, department)
            
            # Apply quality adjustments
            improved_estimates = self._apply_quality_adjustments(base_estimates, quality_analysis)
            
            return {
                'estimates': improved_estimates,
                'quality_analysis': quality_analysis,
                'improvements_applied': self._get_improvements_applied(quality_analysis),
                'confidence_level': self._calculate_confidence_level(quality_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error improving estimates: {e}")
            return {'error': str(e)}
    
    def _apply_quality_adjustments(self, estimates: Dict[str, Any], quality_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Apply quality-based adjustments to estimates"""
        adjusted_estimates = estimates.copy()
        
        # Adjust estimates based on data quality
        for category, amount in estimates.get('estimates', {}).items():
            if category in quality_analysis['category_analysis']:
                cat_analysis = quality_analysis['category_analysis'][category]
                quality_score = cat_analysis.get('quality_score', 1.0)
                
                # Apply confidence factor based on quality
                if quality_score < 0.5:
                    # Low quality - reduce confidence
                    adjusted_amount = amount * 0.8
                elif quality_score < 0.7:
                    # Medium quality - slight reduction
                    adjusted_amount = amount * 0.9
                else:
                    # High quality - keep original
                    adjusted_amount = amount
                
                adjusted_estimates['estimates'][category] = adjusted_amount
        
        # Recalculate total
        adjusted_estimates['total_estimate'] = sum(adjusted_estimates['estimates'].values())
        
        return adjusted_estimates
    
    def _get_improvements_applied(self, quality_analysis: Dict[str, Any]) -> List[str]:
        """Get list of improvements applied based on quality analysis"""
        improvements = []
        
        if quality_analysis['overall_score'] < 0.7:
            improvements.append("Applied conservative adjustments due to data quality concerns")
        
        for category, cat_analysis in quality_analysis['category_analysis'].items():
            if cat_analysis.get('quality_score', 1.0) < 0.6:
                improvements.append(f"Reduced confidence for {category} due to data quality issues")
        
        return improvements
    
    def _calculate_confidence_level(self, quality_analysis: Dict[str, Any]) -> str:
        """Calculate confidence level for estimates"""
        overall_score = quality_analysis.get('overall_score', 0.0)
        
        if overall_score >= 0.8:
            return "High"
        elif overall_score >= 0.6:
            return "Medium"
        else:
            return "Low"
