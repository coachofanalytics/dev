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
                'tier_code': 'starter',
                'tier_name': 'Starter - AI Powered',
                'minimum_capital': Decimal('5000.00'),
                'monthly_fee': Decimal('0.00'),
                'per_session_fee': Decimal('0.00'),
                'profit_share_percentage': Decimal('10.00'),
                'max_sessions_per_month': 0,
                'short_description': 'AI-powered automated options trading',
                'features': ['AI-powered analysis', 'Automated execution', 'Standard support', 'Weekly position batches'],
                'compatible_risk_levels': ['low', 'medium'],
                'display_order': 1,
                'is_active': True,
            },
            {
                'tier_code': 'professional',
                'tier_name': 'Professional',
                'minimum_capital': Decimal('15000.00'),
                'monthly_fee': Decimal('0.00'),
                'per_session_fee': Decimal('0.00'),
                'profit_share_percentage': Decimal('15.00'),
                'max_sessions_per_month': 0,
                'short_description': 'Enhanced strategies with priority support',
                'features': ['Enhanced AI analysis', 'Priority execution', 'Priority support', 'Weekly batches'],
                'compatible_risk_levels': ['low', 'medium', 'high'],
                'display_order': 2,
                'is_active': True,
            },
            {
                'tier_code': 'premium',
                'tier_name': 'Premium',
                'minimum_capital': Decimal('25000.00'),
                'monthly_fee': Decimal('0.00'),
                'per_session_fee': Decimal('0.00'),
                'profit_share_percentage': Decimal('20.00'),
                'max_sessions_per_month': 0,
                'short_description': 'Advanced strategies and premium service',
                'features': ['Advanced strategies', 'Premium support', 'Priority execution', 'Real-time monitoring'],
                'compatible_risk_levels': ['medium', 'high'],
                'display_order': 3,
                'is_active': True,
            },
            {
                'tier_code': 'consultative',
                'tier_name': 'Consultative Coaching',
                'minimum_capital': Decimal('25000.00'),  # Changed from 50K to 25K
                'monthly_fee': Decimal('420.00'),
                'per_session_fee': Decimal('250.00'),
                'profit_share_percentage': Decimal('20.00'),
                'max_sessions_per_month': 4,
                'short_description': '1-on-1 consultations with expert traders',
                'features': ['1-on-1 consultations', 'Custom strategies', 'White-glove service', 'Direct manager access'],
                'compatible_risk_levels': ['medium', 'high'],
                'display_order': 4,
                'is_active': True,
            },
            {
                'tier_code': 'co_invest',
                'tier_name': 'Co-Investment',
                'minimum_capital': Decimal('100000.00'),
                'monthly_fee': Decimal('0.00'),
                'per_session_fee': Decimal('0.00'),
                'profit_share_percentage': Decimal('30.00'),
                'max_sessions_per_month': 0,
                'short_description': 'CODA co-invests alongside you',
                'features': ['CODA co-invests with you', 'Shared risk/reward', 'Elite strategies', 'VIP support'],
                'compatible_risk_levels': ['high', 'very_high'],
                'display_order': 5,
                'is_active': True,
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

