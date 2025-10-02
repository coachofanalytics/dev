"""
Analyze Budget Templates

Phase 4: Identify which templates to keep, deprecate, or remove
"""

from django.core.management.base import BaseCommand
import os
from pathlib import Path


class Command(BaseCommand):
    help = "Analyze budget templates for Phase 4 consolidation"
    
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('PHASE 4: BUDGET TEMPLATE ANALYSIS'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        # Template base directory
        template_dir = Path('coda/finance/templates/finance/budgets')
        
        # Categorize templates
        keep_templates = {
            'unified_dashboard.html': 'Phase 3 - Unified dashboard with 5 tabs',
            'unified_planning.html': 'Phase 3 - Unified planning with timeframe parameter',
            'tabs/overview_tab.html': 'Phase 3 - Overview tab content',
            'tabs/estimation_tab.html': 'Phase 3 - Estimation tab content',
            'tabs/planning_tab.html': 'Phase 3 - Planning tab content',
            'tabs/approvals_tab.html': 'Phase 3 - Approvals tab content',
            'tabs/analytics_tab.html': 'Phase 3 - Analytics tab content',
            'budget.html': 'General budget view (still in use)',
            'newbudget.html': 'Budget creation form (still in use)',
            'coda_budget.html': 'Website cost estimation tool (special purpose)',
            'coda_development_estimation.html': 'CODA development cost calculator (special purpose)',
        }
        
        deprecate_templates = {
            'automated_estimation.html': 'Replaced by unified_dashboard.html?tab=estimation',
            'enhanced_budget_dashboard.html': 'Replaced by unified_dashboard.html?tab=planning',
            'consolidation_dashboard.html': 'Replaced by unified_dashboard.html?tab=overview',
            'budget_projection.html': 'Replaced by unified_dashboard.html?tab=analytics',
            'weekly_planning.html': 'Replaced by unified_planning.html?timeframe=weekly',
            'monthly_planning.html': 'Replaced by unified_planning.html?timeframe=monthly',
            'yearly_planning.html': 'Replaced by unified_planning.html?timeframe=yearly',
            'multi_year_planning.html': 'Replaced by unified_planning.html?timeframe=multi_year',
        }
        
        review_templates = {
            'base_planning.html': 'Base template - check if still used',
            'consolidation_report.html': 'Consolidation report - check usage',
            'investment_planning.html': 'Investment planning - check if separate or consolidate',
        }
        
        # Print analysis
        self.stdout.write(self.style.SUCCESS('1. TEMPLATES TO KEEP'))
        self.stdout.write('-' * 80)
        for template, reason in keep_templates.items():
            status = '✅' if (template_dir / template).exists() else '❌'
            self.stdout.write(f"{status} {template:<45} {reason}")
        self.stdout.write(f"\nTotal: {len(keep_templates)} templates")
        
        self.stdout.write(self.style.WARNING('\n2. TEMPLATES TO DEPRECATE'))
        self.stdout.write('-' * 80)
        for template, reason in deprecate_templates.items():
            status = '⚠️' if (template_dir / template).exists() else '✓'
            self.stdout.write(f"{status}  {template:<45} {reason}")
        self.stdout.write(f"\nTotal: {len(deprecate_templates)} templates")
        
        self.stdout.write(self.style.WARNING('\n3. TEMPLATES TO REVIEW'))
        self.stdout.write('-' * 80)
        for template, reason in review_templates.items():
            status = '📋' if (template_dir / template).exists() else '✓'
            self.stdout.write(f"{status} {template:<45} {reason}")
        self.stdout.write(f"\nTotal: {len(review_templates)} templates")
        
        # Count actual files
        if template_dir.exists():
            actual_files = list(template_dir.glob('*.html'))
            self.stdout.write(self.style.SUCCESS('\n4. ACTUAL FILES IN DIRECTORY'))
            self.stdout.write('-' * 80)
            self.stdout.write(f"Total .html files: {len(actual_files)}")
            self.stdout.write(f"Subdirectories: {len(list(template_dir.glob('*/')))} (tabs/)")
        
        # Calculate consolidation impact
        self.stdout.write(self.style.SUCCESS('\n5. CONSOLIDATION IMPACT'))
        self.stdout.write('-' * 80)
        total_before = len(keep_templates) + len(deprecate_templates) + len(review_templates)
        total_after = len(keep_templates)
        reduction = ((len(deprecate_templates) / total_before) * 100)
        
        self.stdout.write(f"Before consolidation: {total_before} templates")
        self.stdout.write(f"After consolidation:  {total_after} core templates")
        self.stdout.write(f"Templates to deprecate: {len(deprecate_templates)}")
        self.stdout.write(f"Reduction: {reduction:.1f}%")
        
        # Recommendations
        self.stdout.write(self.style.SUCCESS('\n6. RECOMMENDATIONS'))
        self.stdout.write('-' * 80)
        self.stdout.write("Phase 4 Actions:")
        self.stdout.write("  1. Add deprecation notices to old templates")
        self.stdout.write("  2. Extract common CSS to budget-common.css")
        self.stdout.write("  3. Extract common JS to budget-common.js")
        self.stdout.write("  4. Test all views with new structure")
        self.stdout.write("  5. Delete deprecated templates in Phase 5")
        
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('ANALYSIS COMPLETE'))
        self.stdout.write('='*80 + '\n')




