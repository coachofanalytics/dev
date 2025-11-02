"""
Management Command: Apply Position Sizing Rules to Existing Accounts

Adds industry-standard position sizing rules (2% max per position, 15% max total exposure)
to all existing managed trading accounts that don't have these rules yet.

Usage:
    python manage.py apply_position_sizing_rules
    python manage.py apply_position_sizing_rules --dry-run  # Preview changes
"""

from django.core.management.base import BaseCommand
from decimal import Decimal
from investing.models import ManagedTradingAccount, TradingRule


class Command(BaseCommand):
    help = 'Add position sizing rules to existing managed trading accounts'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made\n'))
        
        # Get all active accounts
        accounts = ManagedTradingAccount.objects.filter(status='active')
        self.stdout.write(f"📊 Found {accounts.count()} active managed trading accounts\n")
        
        # New rules to add
        new_rule_types = ['position_size_percentage', 'exposure_limit']
        
        accounts_updated = 0
        rules_added = 0
        
        for account in accounts:
            self.stdout.write(f"\n🔍 Checking {account.account_number} ({account.client.get_full_name()})...")
            
            # Check existing rules
            existing_rule_types = account.trading_rules.values_list('rule_type', flat=True)
            
            rules_to_add = []
            
            # Position Size % Rule
            if 'position_size_percentage' not in existing_rule_types:
                rules_to_add.append({
                    'rule_name': 'Position Sizing - % of Capital',
                    'rule_type': 'position_size_percentage',
                    'rule_config': {
                        'max_percentage_per_position': 2.0,  # Industry standard: 2-5%
                        'description': 'No single position can use more than 2% of total capital'
                    },
                    'priority': 1,
                    'is_active': True
                })
                self.stdout.write(self.style.SUCCESS(
                    f"  ✅ Will add: Position Sizing Rule (2% max per position)"
                ))
            
            # Total Exposure Limit Rule
            if 'exposure_limit' not in existing_rule_types:
                rules_to_add.append({
                    'rule_name': 'Total Portfolio Exposure',
                    'rule_type': 'exposure_limit',
                    'rule_config': {
                        'max_total_exposure_percentage': 15.0,  # 15% of total capital
                        'description': 'Total capital deployed cannot exceed 15% of account value'
                    },
                    'priority': 1,
                    'is_active': True
                })
                self.stdout.write(self.style.SUCCESS(
                    f"  ✅ Will add: Total Exposure Rule (15% max deployed)"
                ))
            
            # Apply rules
            if rules_to_add:
                if not dry_run:
                    for rule_data in rules_to_add:
                        TradingRule.objects.create(
                            managed_account=account,
                            **rule_data
                        )
                        rules_added += 1
                else:
                    rules_added += len(rules_to_add)
                
                accounts_updated += 1
            else:
                self.stdout.write(self.style.WARNING(
                    f"  ⏭️  Skipped: Already has position sizing rules"
                ))
        
        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"\n✅ SUMMARY:"))
        self.stdout.write(f"   Accounts checked: {accounts.count()}")
        self.stdout.write(f"   Accounts updated: {accounts_updated}")
        self.stdout.write(f"   Rules added: {rules_added}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"\n⚠️  DRY RUN - No changes were made. Run without --dry-run to apply."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\n🎉 Position sizing rules applied successfully!"
            ))
        
        self.stdout.write("\n" + "=" * 60 + "\n")
        
        # Industry standards info
        self.stdout.write(self.style.SUCCESS("\n📚 Industry Standards Applied:"))
        self.stdout.write("   • Single Position Risk: 2% of total capital")
        self.stdout.write("   • Total Portfolio Exposure: 15% of capital")
        self.stdout.write("   • These rules prevent over-concentration and excessive risk")
        self.stdout.write("\n")

