"""
Budget System Usage Audit Script

Phase 0 Task 0.2: Document current usage of Budget, CodaBudget, and EnhancedBudget models
"""

from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Q
from django.utils import timezone
from finance.models import Budget, CodaBudget, BudgetCategory
from datetime import datetime
import json

# Optional imports - handle gracefully if models don't exist
try:
    from finance.models import BudgetEstimateProjection
except ImportError:
    BudgetEstimateProjection = None

try:
    from finance.models_detailed_budget import BudgetItemDetail, BudgetEstimateItem
except ImportError:
    BudgetItemDetail = None
    BudgetEstimateItem = None

# Note: EnhancedBudget import commented out due to model conflicts
# Will check for existence via model registry instead


class Command(BaseCommand):
    help = "Audit budget system usage - Phase 0 of consolidation plan"
    
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('BUDGET SYSTEM USAGE AUDIT REPORT'))
        self.stdout.write(self.style.SUCCESS(f'Generated: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        # 1. Model Record Counts
        self._audit_record_counts()
        
        # 2. Data Quality Analysis
        self._audit_data_quality()
        
        # 3. Field Usage Analysis
        self._audit_field_usage()
        
        # 4. Relationship Analysis
        self._audit_relationships()
        
        # 5. Timeframe Analysis
        self._audit_timeframes()
        
        # 6. Summary and Recommendations
        self._generate_summary()
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('AUDIT COMPLETE'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
    
    def _audit_record_counts(self):
        """Count records in each budget model"""
        self.stdout.write(self.style.WARNING('\n1. MODEL RECORD COUNTS'))
        self.stdout.write('-' * 80)
        
        budget_count = Budget.objects.count()
        coda_budget_count = CodaBudget.objects.count()
        
        # Check for EnhancedBudget safely
        try:
            from django.apps import apps
            EnhancedBudget = apps.get_model('finance', 'EnhancedBudget')
            enhanced_budget_count = EnhancedBudget.objects.count()
        except LookupError:
            enhanced_budget_count = 0
            self.stdout.write(self.style.WARNING("  ⚠️  EnhancedBudget model not found in app registry"))
        
        projection_count = BudgetEstimateProjection.objects.count()
        item_detail_count = BudgetItemDetail.objects.count()
        estimate_item_count = BudgetEstimateItem.objects.count()
        
        self.stdout.write(f"Budget records:                    {budget_count:>8}")
        self.stdout.write(f"CodaBudget records:                {coda_budget_count:>8}")
        self.stdout.write(f"EnhancedBudget records:            {enhanced_budget_count:>8}")
        self.stdout.write(f"BudgetEstimateProjection records:  {projection_count:>8}")
        self.stdout.write(f"BudgetItemDetail records:          {item_detail_count:>8}")
        self.stdout.write(f"BudgetEstimateItem records:        {estimate_item_count:>8}")
        self.stdout.write(f"\nTotal budget records:              {budget_count + coda_budget_count + enhanced_budget_count:>8}")
        
        # Store for summary
        self.budget_count = budget_count
        self.coda_budget_count = coda_budget_count
        self.enhanced_budget_count = enhanced_budget_count
    
    def _audit_data_quality(self):
        """Analyze data quality in each model"""
        self.stdout.write(self.style.WARNING('\n2. DATA QUALITY ANALYSIS'))
        self.stdout.write('-' * 80)
        
        # Budget model quality
        self.stdout.write("\nBudget Model:")
        budget_with_category = Budget.objects.filter(category__isnull=False).count()
        budget_with_lead = Budget.objects.filter(budget_lead__isnull=False).count()
        budget_active = Budget.objects.filter(is_active=True).count()
        budget_with_dates = Budget.objects.filter(
            start_date__isnull=False, 
            end_date__isnull=False
        ).count()
        
        self.stdout.write(f"  - With category assigned:        {budget_with_category:>8} / {self.budget_count}")
        self.stdout.write(f"  - With budget lead assigned:     {budget_with_lead:>8} / {self.budget_count}")
        self.stdout.write(f"  - Active budgets:                {budget_active:>8} / {self.budget_count}")
        self.stdout.write(f"  - With start/end dates:          {budget_with_dates:>8} / {self.budget_count}")
        
        # CodaBudget model quality
        self.stdout.write("\nCodaBudget Model:")
        coda_with_category = CodaBudget.objects.filter(category__isnull=False).count()
        coda_with_lead = CodaBudget.objects.filter(budget_lead__isnull=False).count()
        
        self.stdout.write(f"  - With category assigned:        {coda_with_category:>8} / {self.coda_budget_count}")
        self.stdout.write(f"  - With budget lead assigned:     {coda_with_lead:>8} / {self.coda_budget_count}")
    
    def _audit_field_usage(self):
        """Analyze which fields are actually being used"""
        self.stdout.write(self.style.WARNING('\n3. FIELD USAGE ANALYSIS'))
        self.stdout.write('-' * 80)
        
        # Budget enhanced fields usage
        self.stdout.write("\nBudget Model Enhanced Fields Usage:")
        budget_with_type = Budget.objects.filter(budget_type__isnull=False).exclude(budget_type='').count()
        budget_with_timeframe = Budget.objects.filter(timeframe__isnull=False).exclude(timeframe='').count()
        budget_with_estimation = Budget.objects.filter(estimation_method__isnull=False).exclude(estimation_method='').count()
        
        self.stdout.write(f"  - budget_type field used:        {budget_with_type:>8} / {self.budget_count}")
        self.stdout.write(f"  - timeframe field used:          {budget_with_timeframe:>8} / {self.budget_count}")
        self.stdout.write(f"  - estimation_method field used:  {budget_with_estimation:>8} / {self.budget_count}")
        
        # Check if enhanced fields are populated
        if budget_with_type == 0 and budget_with_timeframe == 0 and budget_with_estimation == 0:
            self.stdout.write(self.style.WARNING("\n  ⚠️  Enhanced fields in Budget model are NOT being used!"))
        else:
            self.stdout.write(self.style.SUCCESS("\n  ✓ Enhanced fields in Budget model ARE being used"))
    
    def _audit_relationships(self):
        """Analyze relationships between models"""
        self.stdout.write(self.style.WARNING('\n4. RELATIONSHIP ANALYSIS'))
        self.stdout.write('-' * 80)
        
        # Department distribution
        self.stdout.write("\nBudget records by department:")
        budget_by_dept = Budget.objects.values('department__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for dept in budget_by_dept[:10]:  # Top 10 departments
            dept_name = dept['department__name'] or 'Unassigned'
            self.stdout.write(f"  - {dept_name:<30} {dept['count']:>8}")
        
        # Category distribution
        self.stdout.write("\nBudget records by category:")
        budget_by_cat = Budget.objects.filter(category__isnull=False).values(
            'category__name'
        ).annotate(count=Count('id')).order_by('-count')
        
        for cat in budget_by_cat[:10]:  # Top 10 categories
            self.stdout.write(f"  - {cat['category__name']:<30} {cat['count']:>8}")
    
    def _audit_timeframes(self):
        """Analyze budget timeframes"""
        self.stdout.write(self.style.WARNING('\n5. TIMEFRAME ANALYSIS'))
        self.stdout.write('-' * 80)
        
        # Date range analysis for Budget
        self.stdout.write("\nBudget date ranges:")
        budget_with_dates = Budget.objects.filter(
            start_date__isnull=False,
            end_date__isnull=False
        )
        
        if budget_with_dates.exists():
            earliest = budget_with_dates.order_by('start_date').first()
            latest = budget_with_dates.order_by('-end_date').first()
            
            self.stdout.write(f"  - Earliest start date: {earliest.start_date.date()}")
            self.stdout.write(f"  - Latest end date:     {latest.end_date.date()}")
            
            # Calculate average duration
            from django.db.models import F, ExpressionWrapper, DurationField
            from datetime import timedelta
            
            avg_duration = budget_with_dates.annotate(
                duration=ExpressionWrapper(
                    F('end_date') - F('start_date'),
                    output_field=DurationField()
                )
            ).aggregate(
                avg=Sum('duration')
            )['avg']
            
            if avg_duration:
                avg_days = avg_duration.total_seconds() / 86400 / budget_with_dates.count()
                self.stdout.write(f"  - Average duration:    {avg_days:.1f} days")
        else:
            self.stdout.write("  - No budgets with date ranges found")
        
        # BudgetEstimateProjection horizons
        self.stdout.write("\nBudget estimate projection horizons:")
        projection_by_horizon = BudgetEstimateProjection.objects.values(
            'horizon'
        ).annotate(count=Count('id')).order_by('-count')
        
        for horizon in projection_by_horizon:
            self.stdout.write(f"  - {horizon['horizon']:<15} {horizon['count']:>8}")
    
    def _generate_summary(self):
        """Generate summary and recommendations"""
        self.stdout.write(self.style.WARNING('\n6. SUMMARY & RECOMMENDATIONS'))
        self.stdout.write('-' * 80)
        
        self.stdout.write("\nKey Findings:")
        
        # Check for duplication
        if self.budget_count > 0 and self.coda_budget_count > 0:
            self.stdout.write(self.style.WARNING(
                f"  ⚠️  DUPLICATION DETECTED: {self.budget_count} Budget + {self.coda_budget_count} CodaBudget records"
            ))
            self.stdout.write("     → Recommendation: Consolidate CodaBudget into Budget model")
        
        # Check EnhancedBudget usage
        if self.enhanced_budget_count == 0:
            self.stdout.write(self.style.WARNING(
                "  ⚠️  EnhancedBudget model has ZERO records"
            ))
            self.stdout.write("     → Recommendation: Deprecate or remove EnhancedBudget model")
        else:
            self.stdout.write(self.style.SUCCESS(
                f"  ✓ EnhancedBudget model has {self.enhanced_budget_count} records"
            ))
        
        # Check data quality
        budget_with_category = Budget.objects.filter(category__isnull=False).count()
        if budget_with_category < self.budget_count * 0.8:  # Less than 80% have category
            self.stdout.write(self.style.WARNING(
                f"  ⚠️  Only {budget_with_category}/{self.budget_count} ({budget_with_category/self.budget_count*100:.1f}%) Budget records have category assigned"
            ))
            self.stdout.write("     → Recommendation: Improve data quality before consolidation")
        
        # Calculate potential consolidation impact
        total_current = self.budget_count + self.coda_budget_count + self.enhanced_budget_count
        total_after = max(self.budget_count, self.coda_budget_count) + self.enhanced_budget_count
        
        self.stdout.write(f"\nConsolidation Impact:")
        self.stdout.write(f"  - Current total records:    {total_current}")
        self.stdout.write(f"  - After consolidation:      {total_after}")
        self.stdout.write(f"  - Records to migrate:       {min(self.budget_count, self.coda_budget_count)}")
        
        # Next steps
        self.stdout.write("\nNext Steps for Phase 1:")
        self.stdout.write("  1. Create backup of all budget data")
        self.stdout.write("  2. Create migration script for CodaBudget → Budget")
        self.stdout.write("  3. Test migration on staging")
        self.stdout.write("  4. Deprecate EnhancedBudget (if unused)")
        self.stdout.write("  5. Update all code references")

