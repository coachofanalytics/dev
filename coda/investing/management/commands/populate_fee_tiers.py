"""
Management command to populate initial fee tier configurations
Run: python manage.py populate_fee_tiers
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from investing.models import FeeTierConfiguration


class Command(BaseCommand):
    help = 'Populate initial fee tier configurations (admin-editable)'

    def handle(self, *args, **options):
        self.stdout.write("🔧 Populating fee tier configurations...")
        
        tiers_data = [
            {
                'tier_code': 'balanced',
                'tier_name': 'Balanced Automation - $900 Monthly Goal',
                'minimum_capital': Decimal('25000.00'),
                'monthly_fee': Decimal('249.00'),
                'per_session_fee': Decimal('0.00'),
                'profit_share_percentage': Decimal('12.00'),
                'max_sessions_per_month': 0,
                'short_description': 'Primary automation tier using OptionPlay + Unusual Whales cadence.',
                'features': [
                    'Auto-approval of top-ranked positions (Core + Momentum sleeves)',
                    'Twice-daily OptionPlay ingestion with Playwright fallback',
                    'Weekly Unusual Whales Pro passes during rebalance windows',
                    'SMS & WhatsApp trader alerts included',
                    'Monthly sleeve performance recap for upgrade storytelling'
                ],
                'compatible_risk_levels': ['moderate', 'aggressive'],
                'display_order': 1,
                'is_active': True,
            },
            {
                'tier_code': 'consultative',
                'tier_name': 'Consultative Coaching (Legacy $420 Plan)',
                'minimum_capital': Decimal('25000.00'),
                'monthly_fee': Decimal('420.00'),
                'per_session_fee': Decimal('250.00'),
                'profit_share_percentage': Decimal('10.00'),
                'max_sessions_per_month': 4,
                'short_description': 'Grandfathered sleeve with 1-on-1 mentorship and manual trade entry.',
                'features': [
                    'Locked pricing for existing managed client ($420/mo + sessions)',
                    'Trader confirms execution before dashboard flips to active',
                    'Optional Unusual Whales weekly pass during rebalance weeks',
                    'Keeps coaching cadence intact while automation matures'
                ],
                'compatible_risk_levels': ['moderate'],
                'display_order': 2,
                'is_active': True,
            },
            {
                'tier_code': 'elite',
                'tier_name': 'Elite Desk (Coming Soon)',
                'minimum_capital': Decimal('50000.00'),
                'monthly_fee': Decimal('399.00'),
                'per_session_fee': Decimal('0.00'),
                'profit_share_percentage': Decimal('18.00'),
                'max_sessions_per_month': 0,
                'short_description': 'Preview tier for continuous UW Pro access once broker auto-entry is live.',
                'features': [
                    'Continuous Unusual Whales Pro data + premium alert channel',
                    'Portfolio auto-entry once Schwab execution service is activated',
                    'Weekly desk performance review & scenario explorer upgrades',
                    'Reserved for clients migrating from Balanced once automation proves win-rate'
                ],
                'compatible_risk_levels': ['aggressive'],
                'display_order': 3,
                'is_active': True,
            },
            {
                'tier_code': 'starter',
                'tier_name': 'Starter (Legacy)',
                'minimum_capital': Decimal('5000.00'),
                'monthly_fee': Decimal('0.00'),
                'per_session_fee': Decimal('0.00'),
                'profit_share_percentage': Decimal('10.00'),
                'max_sessions_per_month': 0,
                'short_description': 'Legacy automation tier (kept for historical records).',
                'features': [
                    'Deprecated pricing - migrate clients to Balanced Automation',
                ],
                'compatible_risk_levels': ['low', 'medium'],
                'display_order': 10,
                'is_active': False,
            },
            {
                'tier_code': 'professional',
                'tier_name': 'Professional (Legacy)',
                'minimum_capital': Decimal('15000.00'),
                'monthly_fee': Decimal('0.00'),
                'per_session_fee': Decimal('0.00'),
                'profit_share_percentage': Decimal('15.00'),
                'max_sessions_per_month': 0,
                'short_description': 'Legacy tier retained for audit trail.',
                'features': [
                    'Deprecated pricing - migrate clients to Balanced Automation',
                ],
                'compatible_risk_levels': ['low', 'medium', 'high'],
                'display_order': 11,
                'is_active': False,
            },
            {
                'tier_code': 'premium',
                'tier_name': 'Premium (Legacy)',
                'minimum_capital': Decimal('25000.00'),
                'monthly_fee': Decimal('0.00'),
                'per_session_fee': Decimal('0.00'),
                'profit_share_percentage': Decimal('20.00'),
                'max_sessions_per_month': 0,
                'short_description': 'Legacy tier retained for audit trail.',
                'features': [
                    'Deprecated pricing - migrate clients to Balanced Automation',
                ],
                'compatible_risk_levels': ['medium', 'high'],
                'display_order': 12,
                'is_active': False,
            },
            {
                'tier_code': 'co_invest',
                'tier_name': 'Co-Investment Partnership (Legacy)',
                'minimum_capital': Decimal('100000.00'),
                'monthly_fee': Decimal('0.00'),
                'per_session_fee': Decimal('0.00'),
                'profit_share_percentage': Decimal('30.00'),
                'max_sessions_per_month': 0,
                'short_description': 'Legacy co-investment structure (paused while automation scales).',
                'features': [
                    'Deprecated pricing - contact leadership before reactivating',
                ],
                'compatible_risk_levels': ['high', 'very_high'],
                'display_order': 13,
                'is_active': False,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for tier_data in tiers_data:
            tier, created = FeeTierConfiguration.objects.update_or_create(
                tier_code=tier_data['tier_code'],
                defaults=tier_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Created: {tier.tier_name} (${tier.minimum_capital:,.0f}+)")
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f"♻️  Updated: {tier.tier_name} (${tier.minimum_capital:,.0f}+)")
                )
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"✅ Summary: {created_count} created, {updated_count} updated"))
        self.stdout.write("="*60)
        self.stdout.write("\n📝 Next steps:")
        self.stdout.write("   1. Go to Django Admin → Fee Tier Configurations")
        self.stdout.write("   2. Edit tiers to update minimums, fees, or descriptions")
        self.stdout.write("   3. Changes take effect immediately (no code deploy needed!)")
        self.stdout.write("\n")

