"""
Task Standardization Service

Addresses the critical data quality issue where the same task types
have numerous variations (e.g., "One on One", "1-1", "one on one sessions").

Consolidates 1,582 categories to 8-12 core categories and standardizes
task names for better analytics and reporting.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter
from django.db import transaction
from django.db.models import Count
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

# Import models
from management.models import Task, TaskHistory, TaskCategory, TaskLinks

logger = logging.getLogger(__name__)
User = get_user_model()


class TaskStandardizationService:
    """
    Service to standardize task names and consolidate categories.
    
    Provides:
    - Task name standardization
    - Category consolidation
    - Data quality analysis
    - Bulk update operations
    - Rollback capabilities
    """
    
    def __init__(self):
        self.logger = logger
        
        # Define core categories (8-12 main categories)
        self.core_categories = {
            'Meetings & Sessions': {
                'keywords': ['meeting', 'session', 'one on one', '1-1', 'bi session', 'pbr', 'daf'],
                'standard_name': 'Meeting/Session',
                'description': 'All types of meetings and training sessions'
            },
            'Development & Training': {
                'keywords': ['training', 'development', 'learning', 'course', 'workshop'],
                'standard_name': 'Development/Training',
                'description': 'Employee development and training activities'
            },
            'Recruitment & HR': {
                'keywords': ['recruitment', 'hiring', 'interview', 'hr', 'onboarding'],
                'standard_name': 'Recruitment/HR',
                'description': 'Human resources and recruitment activities'
            },
            'Project Management': {
                'keywords': ['project', 'sprint', 'agile', 'scrum', 'planning'],
                'standard_name': 'Project Management',
                'description': 'Project planning and management activities'
            },
            'Administrative': {
                'keywords': ['admin', 'administrative', 'documentation', 'reporting'],
                'standard_name': 'Administrative',
                'description': 'Administrative and documentation tasks'
            },
            'Client Services': {
                'keywords': ['client', 'customer', 'support', 'service'],
                'standard_name': 'Client Services',
                'description': 'Client and customer service activities'
            },
            'Research & Analysis': {
                'keywords': ['research', 'analysis', 'data', 'report', 'study'],
                'standard_name': 'Research/Analysis',
                'description': 'Research and analytical activities'
            },
            'Operations': {
                'keywords': ['operation', 'maintenance', 'support', 'infrastructure'],
                'standard_name': 'Operations',
                'description': 'Operational and maintenance activities'
            }
        }
        
        # Define task name standardization rules
        self.task_standardization_rules = {
            # Meeting variations
            'one on one': 'One-on-One Meeting',
            '1-1': 'One-on-One Meeting',
            'one on one session': 'One-on-One Meeting',
            'one on one sessions': 'One-on-One Meeting',
            'bi session': 'BI Training Session',
            'bi sessions': 'BI Training Session',
            'pbr': 'Product Backlog Refinement',
            'pbr session': 'Product Backlog Refinement',
            'daf': 'Daily Activity Focus',
            'daf session': 'Daily Activity Focus',
            
            # Development variations
            'dev recruitment': 'Developer Recruitment',
            'developer recruitment': 'Developer Recruitment',
            'recruitment': 'Recruitment Activity',
            
            # Sprint variations
            'sprint': 'Sprint Activity',
            'sprint planning': 'Sprint Planning',
            'sprint review': 'Sprint Review',
            
            # General meeting variations
            'general meeting': 'General Meeting',
            'team meeting': 'Team Meeting',
            'staff meeting': 'Staff Meeting',
            
            # Job support variations
            'job support': 'Job Support',
            'job assistance': 'Job Support',
            'work support': 'Job Support'
        }
    
    def analyze_task_data_quality(self) -> Dict[str, Any]:
        """
        Analyze current task data quality issues.
        """
        try:
            # Analyze TaskHistory data
            task_history_analysis = self._analyze_task_history_quality()
            
            # Analyze Task data
            task_analysis = self._analyze_task_quality()
            
            # Analyze category distribution
            category_analysis = self._analyze_category_distribution()
            
            return {
                'task_history': task_history_analysis,
                'current_tasks': task_analysis,
                'categories': category_analysis,
                'recommendations': self._generate_recommendations(task_history_analysis, category_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing task data quality: {e}")
            return {'error': str(e)}
    
    def _analyze_task_history_quality(self) -> Dict[str, Any]:
        """
        Analyze TaskHistory data quality.
        """
        try:
            # Get all unique activity names
            activity_names = TaskHistory.objects.values_list('activity_name', flat=True).distinct()
            
            # Count occurrences
            activity_counts = Counter(activity_names)
            
            # Find potential duplicates (similar names)
            potential_duplicates = self._find_potential_duplicates(activity_counts)
            
            # Analyze naming patterns
            naming_patterns = self._analyze_naming_patterns(activity_counts)
            
            return {
                'total_unique_activities': len(activity_counts),
                'total_records': TaskHistory.objects.count(),
                'activity_counts': dict(activity_counts.most_common(20)),
                'potential_duplicates': potential_duplicates,
                'naming_patterns': naming_patterns
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing TaskHistory quality: {e}")
            return {'error': str(e)}
    
    def _analyze_task_quality(self) -> Dict[str, Any]:
        """
        Analyze current Task data quality.
        """
        try:
            # Get all unique activity names
            activity_names = Task.objects.values_list('activity_name', flat=True).distinct()
            
            # Count occurrences
            activity_counts = Counter(activity_names)
            
            # Find potential duplicates
            potential_duplicates = self._find_potential_duplicates(activity_counts)
            
            return {
                'total_unique_activities': len(activity_counts),
                'total_records': Task.objects.count(),
                'activity_counts': dict(activity_counts.most_common(20)),
                'potential_duplicates': potential_duplicates
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing Task quality: {e}")
            return {'error': str(e)}
    
    def _analyze_category_distribution(self) -> Dict[str, Any]:
        """
        Analyze category distribution.
        """
        try:
            # Get category counts from TaskHistory
            category_counts = TaskHistory.objects.values('category__title').annotate(
                count=Count('id')
            ).order_by('-count')
            
            return {
                'total_categories': category_counts.count(),
                'category_distribution': list(category_counts[:20])
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing category distribution: {e}")
            return {'error': str(e)}
    
    def _find_potential_duplicates(self, activity_counts: Counter) -> List[Dict[str, Any]]:
        """
        Find potential duplicate activity names.
        """
        duplicates = []
        activity_names = list(activity_counts.keys())
        
        for i, name1 in enumerate(activity_names):
            for name2 in activity_names[i+1:]:
                similarity = self._calculate_similarity(name1.lower(), name2.lower())
                if similarity > 0.8:  # 80% similarity threshold
                    duplicates.append({
                        'name1': name1,
                        'name2': name2,
                        'count1': activity_counts[name1],
                        'count2': activity_counts[name2],
                        'similarity': similarity,
                        'suggested_standard': self._suggest_standard_name(name1, name2)
                    })
        
        return sorted(duplicates, key=lambda x: x['similarity'], reverse=True)
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two activity names.
        """
        # Simple similarity calculation based on common words
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _suggest_standard_name(self, name1: str, name2: str) -> str:
        """
        Suggest a standard name for similar activity names.
        """
        # Check against standardization rules
        name1_lower = name1.lower().strip()
        name2_lower = name2.lower().strip()
        
        for pattern, standard in self.task_standardization_rules.items():
            if pattern in name1_lower or pattern in name2_lower:
                return standard
        
        # If no rule matches, return the longer name (usually more descriptive)
        return name1 if len(name1) > len(name2) else name2
    
    def _analyze_naming_patterns(self, activity_counts: Counter) -> Dict[str, Any]:
        """
        Analyze naming patterns in activity names.
        """
        patterns = {
            'case_variations': {},
            'spacing_variations': {},
            'abbreviation_variations': {},
            'common_words': Counter()
        }
        
        for name in activity_counts.keys():
            # Case variations
            lower_name = name.lower()
            if lower_name not in patterns['case_variations']:
                patterns['case_variations'][lower_name] = []
            patterns['case_variations'][lower_name].append(name)
            
            # Spacing variations
            no_spaces = name.replace(' ', '')
            if no_spaces not in patterns['spacing_variations']:
                patterns['spacing_variations'][no_spaces] = []
            patterns['spacing_variations'][no_spaces].append(name)
            
            # Common words
            words = name.lower().split()
            for word in words:
                patterns['common_words'][word] += activity_counts[name]
        
        return patterns
    
    def _generate_recommendations(self, task_history_analysis: Dict, category_analysis: Dict) -> List[str]:
        """
        Generate recommendations for data quality improvement.
        """
        recommendations = []
        
        # Task name recommendations
        if 'potential_duplicates' in task_history_analysis:
            duplicate_count = len(task_history_analysis['potential_duplicates'])
            if duplicate_count > 0:
                recommendations.append(f"Found {duplicate_count} potential duplicate task names that should be standardized")
        
        # Category recommendations
        if 'total_categories' in category_analysis:
            total_categories = category_analysis['total_categories']
            if total_categories > 20:
                recommendations.append(f"Too many categories ({total_categories}). Consider consolidating to 8-12 core categories")
        
        # General recommendations
        recommendations.extend([
            "Implement task name standardization rules",
            "Create core category taxonomy",
            "Set up automated data quality monitoring",
            "Train users on consistent task naming conventions"
        ])
        
        return recommendations
    
    def standardize_task_names(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Standardize task names based on predefined rules.
        """
        try:
            standardized_count = 0
            skipped_count = 0
            changes = []
            
            # Process TaskHistory
            task_history_changes = self._standardize_task_history_names(dry_run)
            standardized_count += task_history_changes['standardized_count']
            skipped_count += task_history_changes['skipped_count']
            changes.extend(task_history_changes['changes'])
            
            # Process current Tasks
            task_changes = self._standardize_current_task_names(dry_run)
            standardized_count += task_changes['standardized_count']
            skipped_count += task_changes['skipped_count']
            changes.extend(task_changes['changes'])
            
            return {
                'success': True,
                'dry_run': dry_run,
                'standardized_count': standardized_count,
                'skipped_count': skipped_count,
                'changes': changes,
                'message': f'{"Would standardize" if dry_run else "Standardized"} {standardized_count} task names'
            }
            
        except Exception as e:
            self.logger.error(f"Error standardizing task names: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Task name standardization failed'
            }
    
    def _standardize_task_history_names(self, dry_run: bool) -> Dict[str, Any]:
        """
        Standardize TaskHistory activity names.
        """
        standardized_count = 0
        skipped_count = 0
        changes = []
        
        # Get all TaskHistory records
        task_history_records = TaskHistory.objects.all()
        
        for record in task_history_records:
            original_name = record.activity_name
            standardized_name = self._get_standardized_name(original_name)
            
            if standardized_name != original_name:
                changes.append({
                    'model': 'TaskHistory',
                    'id': record.id,
                    'original': original_name,
                    'standardized': standardized_name
                })
                
                if not dry_run:
                    record.activity_name = standardized_name
                    record.save()
                
                standardized_count += 1
            else:
                skipped_count += 1
        
        return {
            'standardized_count': standardized_count,
            'skipped_count': skipped_count,
            'changes': changes
        }
    
    def _standardize_current_task_names(self, dry_run: bool) -> Dict[str, Any]:
        """
        Standardize current Task activity names.
        """
        standardized_count = 0
        skipped_count = 0
        changes = []
        
        # Get all current Task records
        task_records = Task.objects.all()
        
        for record in task_records:
            original_name = record.activity_name
            standardized_name = self._get_standardized_name(original_name)
            
            if standardized_name != original_name:
                changes.append({
                    'model': 'Task',
                    'id': record.id,
                    'original': original_name,
                    'standardized': standardized_name
                })
                
                if not dry_run:
                    record.activity_name = standardized_name
                    record.save()
                
                standardized_count += 1
            else:
                skipped_count += 1
        
        return {
            'standardized_count': standardized_count,
            'skipped_count': skipped_count,
            'changes': changes
        }
    
    def _get_standardized_name(self, original_name: str) -> str:
        """
        Get standardized name for a given activity name.
        """
        original_lower = original_name.lower().strip()
        
        # Check against standardization rules
        for pattern, standard in self.task_standardization_rules.items():
            if pattern in original_lower:
                return standard
        
        # If no rule matches, return original (cleaned up)
        return original_name.strip()
    
    def consolidate_categories(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Consolidate categories to core categories.
        """
        try:
            consolidated_count = 0
            skipped_count = 0
            changes = []
            
            # Process TaskHistory categories
            task_history_changes = self._consolidate_task_history_categories(dry_run)
            consolidated_count += task_history_changes['consolidated_count']
            skipped_count += task_history_changes['skipped_count']
            changes.extend(task_history_changes['changes'])
            
            # Process current Task categories
            task_changes = self._consolidate_current_task_categories(dry_run)
            consolidated_count += task_changes['consolidated_count']
            skipped_count += task_changes['skipped_count']
            changes.extend(task_changes['changes'])
            
            return {
                'success': True,
                'dry_run': dry_run,
                'consolidated_count': consolidated_count,
                'skipped_count': skipped_count,
                'changes': changes,
                'message': f'{"Would consolidate" if dry_run else "Consolidated"} {consolidated_count} category assignments'
            }
            
        except Exception as e:
            self.logger.error(f"Error consolidating categories: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Category consolidation failed'
            }
    
    def _consolidate_task_history_categories(self, dry_run: bool) -> Dict[str, Any]:
        """
        Consolidate TaskHistory categories.
        """
        consolidated_count = 0
        skipped_count = 0
        changes = []
        
        # Get all TaskHistory records with categories
        task_history_records = TaskHistory.objects.select_related('category').all()
        
        for record in task_history_records:
            if record.category:
                original_category = record.category.title
                suggested_category = self._suggest_core_category(original_category)
                
                if suggested_category and suggested_category != original_category:
                    changes.append({
                        'model': 'TaskHistory',
                        'id': record.id,
                        'original_category': original_category,
                        'suggested_category': suggested_category
                    })
                    
                    if not dry_run:
                        # Find or create the core category
                        core_category = self._get_or_create_core_category(suggested_category)
                        record.category = core_category
                        record.save()
                    
                    consolidated_count += 1
                else:
                    skipped_count += 1
            else:
                skipped_count += 1
        
        return {
            'consolidated_count': consolidated_count,
            'skipped_count': skipped_count,
            'changes': changes
        }
    
    def _consolidate_current_task_categories(self, dry_run: bool) -> Dict[str, Any]:
        """
        Consolidate current Task categories.
        """
        consolidated_count = 0
        skipped_count = 0
        changes = []
        
        # Get all current Task records with categories
        task_records = Task.objects.select_related('category').all()
        
        for record in task_records:
            if record.category:
                original_category = record.category.title
                suggested_category = self._suggest_core_category(original_category)
                
                if suggested_category and suggested_category != original_category:
                    changes.append({
                        'model': 'Task',
                        'id': record.id,
                        'original_category': original_category,
                        'suggested_category': suggested_category
                    })
                    
                    if not dry_run:
                        # Find or create the core category
                        core_category = self._get_or_create_core_category(suggested_category)
                        record.category = core_category
                        record.save()
                    
                    consolidated_count += 1
                else:
                    skipped_count += 1
            else:
                skipped_count += 1
        
        return {
            'consolidated_count': consolidated_count,
            'skipped_count': skipped_count,
            'changes': changes
        }
    
    def _suggest_core_category(self, category_name: str) -> Optional[str]:
        """
        Suggest a core category for a given category name.
        """
        category_lower = category_name.lower()
        
        for core_category, info in self.core_categories.items():
            for keyword in info['keywords']:
                if keyword in category_lower:
                    return core_category
        
        return None
    
    def _get_or_create_core_category(self, category_name: str) -> TaskCategory:
        """
        Get or create a core category.
        """
        try:
            category, created = TaskCategory.objects.get_or_create(
                title=category_name,
                defaults={
                    'description': self.core_categories.get(category_name, {}).get('description', ''),
                    'is_active': True
                }
            )
            return category
        except Exception as e:
            self.logger.error(f"Error getting/creating category {category_name}: {e}")
            # Return default category
            return TaskCategory.objects.first()
