"""
Sync Budgets from Transactions

Automatically create and update budgets based on transaction patterns.
This command analyzes recent transactions and ensures budgets exist for
all active spending categories.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from decimal import Decimal

from finance.models import Budget, BudgetCategory, Transaction
from finance.services.budget_service import BudgetService
from shared_core.models import Company
from shared_core.users import Department


User = get_user_model()


class Command(BaseCommand):
    help = 'Auto-sync budgets based on transaction patterns'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            default='coda',
            help='Company slug (default: coda)'
        )
        parser.add_argument(
            '--analysis-months',
            type=int,
            default=6,
            help='Months of transaction history to analyze (default: 6)'
        )
        parser.add_argument(
            '--projection-months',
            type=int,
            default=12,
            help='Months to project forward (default: 12)'
        )
        parser.add_argument(
            '--min-transactions',
            type=int,
            default=5,
            help='Minimum transactions required to create budget (default: 5)'
        )
        parser.add_argument(
            '--variance-threshold',
            type=float,
            default=20.0,
            help='Variance threshold % for updating budgets (default: 20)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving'
        )
    
    def handle(self, *args, **options):
        company_slug = options['company']
        analysis_months = options['analysis_months']
        projection_months = options['projection_months']
        min_transactions = options['min_transactions']
        variance_threshold = Decimal(str(options['variance_threshold']))
        dry_run = options['dry_run']
        
        self.stdout.write("="*80)
        self.stdout.write("AUTO-SYNC BUDGETS FROM TRANSACTIONS")
        self.stdout.write("="*80)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n⚠️  DRY RUN MODE - No changes will be saved\n"))
        
        # Get company
        try:
            company = Company.objects.get(slug=company_slug)
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Company '{company_slug}' not found"))
            return
        
        # Get default department and user
        default_dept = Department.objects.first()
        default_user = User.objects.filter(username='coda_info').first()
        if not default_user:
            default_user = User.objects.filter(is_staff=True).first()
        
        if not default_user or not default_dept:
            self.stdout.write(self.style.ERROR("❌ Default user or department not found"))
            return
        
        self.stdout.write(f"Company: {company.name}")
        self.stdout.write(f"Analysis period: Last {analysis_months} months")
        self.stdout.write(f"Projection period: Next {projection_months} months")
        self.stdout.write(f"Minimum transactions: {min_transactions}")
        self.stdout.write(f"Variance threshold: {variance_threshold}%")
        
        # Analyze transactions
        self.stdout.write("\n" + "="*80)
        self.stdout.write("ANALYZING TRANSACTIONS")
        self.stdout.write("="*80 + "\n")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=analysis_months*30)
        
        spending_by_category = BudgetService.get_spending_by_category(
            company=company,
            start_date=start_date,
            end_date=end_date
        )
        
        self.stdout.write(f"Found {len(spending_by_category)} active spending categories\n")
        
        # Sync budgets
        self.stdout.write("="*80)
        self.stdout.write("SYNCING BUDGETS")
        self.stdout.write("="*80 + "\n")
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for cat_id, spending_data in spending_by_category.items():
            try:
                category = BudgetCategory.objects.get(id=cat_id)
                
                # Skip if not enough transactions
                if spending_data['count'] < min_transactions:
                    self.stdout.write(
                        f"⏭️  Skip {category.name}: Only {spending_data['count']} transactions "
                        f"(min: {min_transactions})"
                    )
                    skipped_count += 1
                    continue
                
                # Generate projection
                projection = BudgetService.generate_budget_projection(
                    company=company,
                    category=category,
                    months_ahead=projection_months,
                    growth_factor=1.10
                )
                
                # Check if budget exists
                existing_budget = Budget.objects.filter(
                    company=company,
                    category=category,
                    estimation_method='trend_analysis',
                    is_active=True
                ).first()
                
                if existing_budget:
                    # Calculate variance from current budget
                    current_monthly = existing_budget.unit_price
                    new_monthly = projection['projected_monthly']
                    
                    if current_monthly > 0:
                        variance_pct = abs((new_monthly - current_monthly) / current_monthly * 100)
                    else:
                        variance_pct = 100
                    
                    # Update if variance exceeds threshold
                    if variance_pct > variance_threshold:
                        if not dry_run:
                            existing_budget.unit_price = new_monthly
                            existing_budget.cases = projection_months
                            existing_budget.estimated_amount = projection['total_annual']
                            existing_budget.estimation_confidence = projection['confidence']
                            existing_budget.description = (
                                f"Auto-synced from {spending_data['count']} transactions. "
                                f"Monthly avg: ${projection['historical_monthly']:,.2f}. "
                                f"Updated: {timezone.now().date()}"
                            )
                            existing_budget.save()
                        
                        self.stdout.write(
                            f"📝 Updated {category.name}: "
                            f"${current_monthly:,.2f} → ${new_monthly:,.2f}/month "
                            f"({variance_pct:.1f}% variance)"
                        )
                        updated_count += 1
                    else:
                        self.stdout.write(
                            f"✓ {category.name}: Within threshold "
                            f"({variance_pct:.1f}% variance)"
                        )
                        skipped_count += 1
                
                else:
                    # Create new budget
                    if not dry_run:
                        Budget.objects.create(
                            company=company,
                            department=default_dept,
                            budget_lead=default_user,
                            category=category,
                            item_name=f"{category.name} - Auto-Generated Budget",
                            description=(
                                f"Auto-created from {spending_data['count']} transactions. "
                                f"Monthly avg: ${projection['historical_monthly']:,.2f}. "
                                f"Confidence: {projection['confidence']}%"
                            ),
                            quantity=1,
                            unit_price=projection['projected_monthly'],
                            cases=projection_months,
                            is_active=True,
                            status='active',
                            estimation_method='trend_analysis',
                            estimated_amount=projection['total_annual'],
                            estimation_confidence=projection['confidence'],
                            estimation_source='Auto-sync from transaction patterns',
                            start_date=timezone.now(),
                            end_date=timezone.now() + timedelta(days=projection_months*30),
                            budget_type='general',
                            timeframe='yearly'
                        )
                    
                    self.stdout.write(
                        f"✨ Created {category.name}: ${projection['projected_monthly']:,.2f}/month "
                        f"({spending_data['count']} txns, {projection['confidence']:.0f}% confidence)"
                    )
                    created_count += 1
                
            except BudgetCategory.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Category ID {cat_id} not found")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error processing {spending_data.get('name', 'Unknown')}: {e}")
                )
        
        # Summary
        self.stdout.write("\n" + "="*80)
        self.stdout.write("SYNC SUMMARY")
        self.stdout.write("="*80 + "\n")
        
        self.stdout.write(f"Categories analyzed: {len(spending_by_category)}")
        self.stdout.write(f"✨ Budgets created: {created_count}")
        self.stdout.write(f"📝 Budgets updated: {updated_count}")
        self.stdout.write(f"⏭️  Skipped: {skipped_count}")
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING("\n⚠️  DRY RUN - Run without --dry-run to apply changes")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\n✅ Sync complete! {created_count + updated_count} budgets processed")
            )
            
            # Show next steps
            self.stdout.write("\n" + "="*80)
            self.stdout.write("NEXT STEPS")
            self.stdout.write("="*80 + "\n")
            self.stdout.write("1. Review created/updated budgets:")
            self.stdout.write("   Budget.objects.filter(estimation_method='trend_analysis')")
            self.stdout.write("\n2. View in dashboard:")
            self.stdout.write(f"   https://your-domain.com/finance/budget-dashboard/{company_slug}/")
            self.stdout.write("\n3. Set up cron job for automatic sync:")
            self.stdout.write("   0 0 * * 0 python manage.py sync_budgets  # Weekly on Sunday")


