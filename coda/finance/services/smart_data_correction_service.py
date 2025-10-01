"""
Smart Data Correction Service

Uses AI and pattern recognition to intelligently correct and suggest
improvements for budget data, categories, and department assignments.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import difflib
import re

from ..models import Transaction, BudgetCategory, Company, Department
from ai_services.ai_integration_service import RealAIService
from ai_services.models import DiasporaAnalysisData, AIModelTypes

logger = logging.getLogger(__name__)


class SmartDataCorrectionService:
    """
    Service for intelligent data correction and suggestions
    """
    
    def __init__(self):
        self.ai_service = RealAIService()
        self.correction_cache = {}
    
    def analyze_and_correct_data(self, company, department=None) -> Dict[str, Any]:
        """
        Analyze data for potential corrections and improvements
        
        Args:
            company: Company object
            department: Department object (optional)
            
        Returns:
            Dictionary with correction suggestions and analysis
        """
        try:
            # Get recent transactions for analysis
            end_date = timezone.now()
            start_date = end_date - timedelta(days=90)  # Last 3 months
            
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
            
            # Analyze different aspects
            category_corrections = self._analyze_category_corrections(transactions)
            department_corrections = self._analyze_department_corrections(transactions)
            description_improvements = self._analyze_description_improvements(transactions)
            amount_outliers = self._detect_amount_outliers(transactions)
            duplicate_detection = self._detect_potential_duplicates(transactions)
            
            # Get AI-powered suggestions
            ai_suggestions = self._get_ai_correction_suggestions(
                company, department, {
                    'category_corrections': category_corrections,
                    'department_corrections': department_corrections,
                    'description_improvements': description_improvements,
                    'amount_outliers': amount_outliers,
                    'duplicate_detection': duplicate_detection
                }
            )
            
            return {
                'category_corrections': category_corrections,
                'department_corrections': department_corrections,
                'description_improvements': description_improvements,
                'amount_outliers': amount_outliers,
                'duplicate_detection': duplicate_detection,
                'ai_suggestions': ai_suggestions,
                'total_issues_found': len(category_corrections) + len(department_corrections) + 
                                    len(description_improvements) + len(amount_outliers) + len(duplicate_detection),
                'analysis_period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing data corrections: {e}")
            return {'error': str(e)}
    
    def _analyze_category_corrections(self, transactions) -> List[Dict[str, Any]]:
        """Analyze and suggest category corrections"""
        corrections = []
        
        # Get all categories for matching
        all_categories = list(BudgetCategory.objects.values_list('name', flat=True))
        
        for txn in transactions:
            if not txn.category:
                # Find best matching category based on description
                best_match = self._find_best_category_match(txn.description, all_categories)
                if best_match:
                    corrections.append({
                        'transaction_id': txn.id,
                        'current_category': None,
                        'suggested_category': best_match,
                        'confidence': 0.8,
                        'reason': 'Missing category - suggested based on description analysis',
                        'description': txn.description
                    })
            else:
                # Check if category seems incorrect based on description
                category_match_score = self._calculate_category_match_score(
                    txn.description, txn.category.name
                )
                
                if category_match_score < 0.3:  # Low match score
                    best_match = self._find_best_category_match(txn.description, all_categories)
                    if best_match and best_match != txn.category.name:
                        corrections.append({
                            'transaction_id': txn.id,
                            'current_category': txn.category.name,
                            'suggested_category': best_match,
                            'confidence': 0.9,
                            'reason': f'Category mismatch - description suggests "{best_match}"',
                            'description': txn.description
                        })
        
        return corrections
    
    def _analyze_department_corrections(self, transactions) -> List[Dict[str, Any]]:
        """Analyze and suggest department corrections"""
        corrections = []
        
        # Get all departments for matching
        all_departments = list(Department.objects.values_list('name', flat=True))
        
        for txn in transactions:
            if not txn.department:
                # Find best matching department based on description and category
                best_match = self._find_best_department_match(
                    txn.description, txn.category.name if txn.category else None, all_departments
                )
                if best_match:
                    corrections.append({
                        'transaction_id': txn.id,
                        'current_department': None,
                        'suggested_department': best_match,
                        'confidence': 0.7,
                        'reason': 'Missing department - suggested based on description and category',
                        'description': txn.description
                    })
            else:
                # Check if department seems incorrect
                department_match_score = self._calculate_department_match_score(
                    txn.description, txn.department.name, txn.category.name if txn.category else None
                )
                
                if department_match_score < 0.4:  # Low match score
                    best_match = self._find_best_department_match(
                        txn.description, txn.category.name if txn.category else None, all_departments
                    )
                    if best_match and best_match != txn.department.name:
                        corrections.append({
                            'transaction_id': txn.id,
                            'current_department': txn.department.name,
                            'suggested_department': best_match,
                            'confidence': 0.8,
                            'reason': f'Department mismatch - context suggests "{best_match}"',
                            'description': txn.description
                        })
        
        return corrections
    
    def _analyze_description_improvements(self, transactions) -> List[Dict[str, Any]]:
        """Analyze and suggest description improvements"""
        improvements = []
        
        for txn in transactions:
            if not txn.description or len(txn.description.strip()) < 5:
                improvements.append({
                    'transaction_id': txn.id,
                    'current_description': txn.description or '',
                    'suggested_description': self._generate_description_suggestion(txn),
                    'confidence': 0.6,
                    'reason': 'Description too short or missing - generated based on context',
                    'amount': float(txn.amount or 0),
                    'category': txn.category.name if txn.category else 'Unknown'
                })
            elif self._is_description_poor_quality(txn.description):
                improvements.append({
                    'transaction_id': txn.id,
                    'current_description': txn.description,
                    'suggested_description': self._improve_description(txn.description, txn),
                    'confidence': 0.7,
                    'reason': 'Description quality could be improved',
                    'amount': float(txn.amount or 0),
                    'category': txn.category.name if txn.category else 'Unknown'
                })
        
        return improvements
    
    def _detect_amount_outliers(self, transactions) -> List[Dict[str, Any]]:
        """Detect amount outliers that might be data entry errors"""
        outliers = []
        
        # Group by category for outlier detection
        category_amounts = {}
        for txn in transactions:
            if txn.category and txn.amount:
                cat_name = txn.category.name
                if cat_name not in category_amounts:
                    category_amounts[cat_name] = []
                category_amounts[cat_name].append(float(txn.amount))
        
        for cat_name, amounts in category_amounts.items():
            if len(amounts) < 3:  # Need at least 3 transactions for outlier detection
                continue
            
            # Calculate outlier thresholds using IQR method
            amounts.sort()
            q1 = amounts[len(amounts) // 4]
            q3 = amounts[3 * len(amounts) // 4]
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            # Find outliers
            for txn in transactions:
                if (txn.category and txn.category.name == cat_name and 
                    txn.amount and (txn.amount < lower_bound or txn.amount > upper_bound)):
                    
                    outliers.append({
                        'transaction_id': txn.id,
                        'amount': float(txn.amount),
                        'category': cat_name,
                        'description': txn.description,
                        'confidence': 0.8,
                        'reason': f'Amount is an outlier for {cat_name} category',
                        'suggested_action': 'Review amount for potential data entry error',
                        'normal_range': f'${lower_bound:.2f} - ${upper_bound:.2f}'
                    })
        
        return outliers
    
    def _detect_potential_duplicates(self, transactions) -> List[Dict[str, Any]]:
        """Detect potential duplicate transactions"""
        duplicates = []
        
        # Group transactions by amount and date
        amount_groups = {}
        for txn in transactions:
            if txn.amount:
                key = f"{txn.amount}_{txn.transaction_date.date()}"
                if key not in amount_groups:
                    amount_groups[key] = []
                amount_groups[key].append(txn)
        
        # Find groups with multiple transactions
        for key, group in amount_groups.items():
            if len(group) > 1:
                # Check if descriptions are similar
                for i, txn1 in enumerate(group):
                    for txn2 in group[i+1:]:
                        similarity = self._calculate_description_similarity(
                            txn1.description or '', txn2.description or ''
                        )
                        
                        if similarity > 0.7:  # High similarity
                            duplicates.append({
                                'transaction_ids': [txn1.id, txn2.id],
                                'amount': float(txn1.amount),
                                'date': txn1.transaction_date.date(),
                                'similarity_score': similarity,
                                'confidence': 0.9,
                                'reason': 'Potential duplicate transactions detected',
                                'descriptions': [txn1.description, txn2.description]
                            })
        
        return duplicates
    
    def _find_best_category_match(self, description: str, categories: List[str]) -> Optional[str]:
        """Find best matching category based on description"""
        if not description:
            return None
        
        # Use fuzzy matching
        matches = difflib.get_close_matches(
            description.lower(), 
            [cat.lower() for cat in categories], 
            n=1, 
            cutoff=0.6
        )
        
        if matches:
            return matches[0].title()
        
        # Use keyword matching
        description_lower = description.lower()
        for category in categories:
            category_lower = category.lower()
            if any(word in description_lower for word in category_lower.split()):
                return category
        
        return None
    
    def _find_best_department_match(self, description: str, category: str, departments: List[str]) -> Optional[str]:
        """Find best matching department based on description and category"""
        if not description:
            return None
        
        # Department mapping based on category
        category_department_map = {
            'salaries and wages': 'HR Department',
            'human resources': 'HR Department',
            'utilities': 'Finance Department',
            'office supplies': 'Finance Department',
            'it and software': 'IT Department',
            'marketing': 'Marketing Department',
            'facilities and equipment': 'Management Department',
            'travel and entertainment': 'Management Department'
        }
        
        # Check category-based mapping first
        if category:
            category_lower = category.lower()
            for cat_key, dept in category_department_map.items():
                if cat_key in category_lower and dept in departments:
                    return dept
        
        # Use fuzzy matching on description
        matches = difflib.get_close_matches(
            description.lower(),
            [dept.lower() for dept in departments],
            n=1,
            cutoff=0.5
        )
        
        if matches:
            return matches[0]
        
        return None
    
    def _calculate_category_match_score(self, description: str, category: str) -> float:
        """Calculate how well description matches category"""
        if not description or not category:
            return 0.0
        
        # Simple keyword matching
        description_lower = description.lower()
        category_lower = category.lower()
        
        # Check for exact word matches
        category_words = category_lower.split()
        matches = sum(1 for word in category_words if word in description_lower)
        
        return matches / len(category_words) if category_words else 0.0
    
    def _calculate_department_match_score(self, description: str, department: str, category: str) -> float:
        """Calculate how well description matches department"""
        if not description or not department:
            return 0.0
        
        # Use category-department mapping
        category_department_map = {
            'salaries and wages': 'HR Department',
            'human resources': 'HR Department',
            'utilities': 'Finance Department',
            'office supplies': 'Finance Department',
            'it and software': 'IT Department',
            'marketing': 'Marketing Department',
            'facilities and equipment': 'Management Department',
            'travel and entertainment': 'Management Department'
        }
        
        if category:
            category_lower = category.lower()
            for cat_key, expected_dept in category_department_map.items():
                if cat_key in category_lower and expected_dept == department:
                    return 1.0
        
        # Use fuzzy matching
        return difflib.SequenceMatcher(None, description.lower(), department.lower()).ratio()
    
    def _generate_description_suggestion(self, transaction) -> str:
        """Generate a better description for a transaction"""
        parts = []
        
        if transaction.category:
            parts.append(transaction.category.name)
        
        if transaction.amount:
            parts.append(f"${transaction.amount}")
        
        if transaction.transaction_date:
            parts.append(transaction.transaction_date.strftime("%Y-%m"))
        
        return " - ".join(parts) if parts else "Transaction"
    
    def _is_description_poor_quality(self, description: str) -> bool:
        """Check if description is of poor quality"""
        if not description:
            return True
        
        # Check for common poor quality indicators
        poor_indicators = [
            len(description.strip()) < 10,
            description.lower() in ['transaction', 'payment', 'expense', 'cost'],
            re.match(r'^\d+$', description.strip()),  # Only numbers
            description.count(' ') < 2  # Too few words
        ]
        
        return any(poor_indicators)
    
    def _improve_description(self, current_description: str, transaction) -> str:
        """Improve an existing description"""
        if not current_description:
            return self._generate_description_suggestion(transaction)
        
        # Add context if missing
        parts = [current_description]
        
        if transaction.category and transaction.category.name.lower() not in current_description.lower():
            parts.append(f"({transaction.category.name})")
        
        return " ".join(parts)
    
    def _calculate_description_similarity(self, desc1: str, desc2: str) -> float:
        """Calculate similarity between two descriptions"""
        if not desc1 or not desc2:
            return 0.0
        
        return difflib.SequenceMatcher(None, desc1.lower(), desc2.lower()).ratio()
    
    def _get_ai_correction_suggestions(self, company, department, analysis_data) -> Dict[str, Any]:
        """Get AI-powered correction suggestions"""
        try:
            input_data = {
                'company_name': company.name,
                'department': department.name if department else 'All',
                'analysis_data': analysis_data,
                'correction_types': list(analysis_data.keys())
            }
            
            ai_response = self.ai_service.get_prediction(
                analysis_type='data_correction',
                input_data=input_data,
                session_id=f"correction_{company.id}_{department.id if department else 'all'}"
            )
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error getting AI correction suggestions: {e}")
            return {'error': str(e)}
    
    def apply_corrections(self, corrections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply suggested corrections to transactions"""
        results = {
            'applied': 0,
            'failed': 0,
            'errors': []
        }
        
        for correction in corrections:
            try:
                transaction_id = correction.get('transaction_id')
                if not transaction_id:
                    continue
                
                txn = Transaction.objects.get(id=transaction_id)
                
                # Apply category correction
                if 'suggested_category' in correction:
                    category = BudgetCategory.objects.filter(
                        name=correction['suggested_category']
                    ).first()
                    if category:
                        txn.category = category
                
                # Apply department correction
                if 'suggested_department' in correction:
                    department = Department.objects.filter(
                        name=correction['suggested_department']
                    ).first()
                    if department:
                        txn.department = department
                
                # Apply description improvement
                if 'suggested_description' in correction:
                    txn.description = correction['suggested_description']
                
                txn.save()
                results['applied'] += 1
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Transaction {transaction_id}: {str(e)}")
        
        return results
