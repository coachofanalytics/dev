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
                'tier_name': 'Starter - Automated Trading',
                'minimum_capital': Decimal('5000.00'),
                'monthly_fee': Decimal('0.00'),
                'per_session_fee': Decimal('0.00'),
                'profit_share_percentage': Decimal('10.00'),
                'max_sessions_per_month': 0,
                'short_description': 'Perfect for beginners. Our AI trades for you automatically with no monthly fees.',
                'features': [
                    'No monthly fees - you only pay when you make money (10% of profits)',
                    'AI chooses trades for you - no guesswork or stress',
                    'Trades happen automatically while you focus on life',
                    'Email support whenever you have questions',
                    'Weekly position batches - trades reviewed before execution'
                ],
                'compatible_risk_levels': ['low', 'medium'],
                'display_order': 1,
                'is_active': True,
            },
            {
                'tier_code': 'professional',
                'tier_name': 'Professional - Priority Service',
                'minimum_capital': Decimal('15000.00'),
                'monthly_fee': Decimal('0.00'),
                'per_session_fee': Decimal('0.00'),
                'profit_share_percentage': Decimal('15.00'),
                'max_sessions_per_month': 0,
                'short_description': 'Better strategies and faster execution for growing investors.',
                'features': [
                    'Still no monthly fees - only 15% when you profit',
                    'Smarter AI strategies - higher profit potential',
                    'Your trades get priority - faster execution means better prices',
                    'Priority email & phone support - faster responses',
                    'Weekly position batches with detailed explanations'
                ],
                'compatible_risk_levels': ['low', 'medium', 'high'],
                'display_order': 2,
                'is_active': True,
            },
            {
                'tier_code': 'premium',
                'tier_name': 'Premium - Advanced Strategies',
                'minimum_capital': Decimal('25000.00'),
                'monthly_fee': Decimal('0.00'),
                'per_session_fee': Decimal('0.00'),
                'profit_share_percentage': Decimal('20.00'),
                'max_sessions_per_month': 0,
                'short_description': 'Sophisticated strategies for serious investors seeking higher returns.',
                'features': [
                    'No monthly fees - 20% profit share (you keep 80% of all gains)',
                    'Advanced strategies - spreads, iron condors, covered calls',
                    'Real-time monitoring - we watch your account 24/7',
                    'Premium support - dedicated account manager',
                    'Priority execution - your trades go first'
                ],
                'compatible_risk_levels': ['medium', 'high'],
                'display_order': 3,
                'is_active': True,
            },
            {
                'tier_code': 'consultative',
                'tier_name': 'Consultative - Personal Coaching',
                'minimum_capital': Decimal('25000.00'),
                'monthly_fee': Decimal('420.00'),
                'per_session_fee': Decimal('250.00'),
                'profit_share_percentage': Decimal('20.00'),
                'max_sessions_per_month': 4,
                'short_description': 'Learn to trade yourself with 1-on-1 mentorship from expert traders.',
                'features': [
                    '$420/month base + $250 per session (up to 4 sessions monthly)',
                    '20% profit share - same as Premium, plus you learn the skills',
                    '1-on-1 video calls with your personal trading coach',
                    'Custom strategy built for YOUR goals and risk tolerance',
                    'Learn the "why" behind each trade - become independent',
                    'Direct access to your account manager via phone/text'
                ],
                'compatible_risk_levels': ['medium', 'high'],
                'display_order': 4,
                'is_active': True,
            },
            {
                'tier_code': 'co_invest',
                'tier_name': 'Co-Investment Partnership',
                'minimum_capital': Decimal('100000.00'),
                'monthly_fee': Decimal('0.00'),
                'per_session_fee': Decimal('0.00'),
                'profit_share_percentage': Decimal('30.00'),
                'max_sessions_per_month': 0,
                'short_description': 'CODA invests our own money alongside yours - true partnership.',
                'features': [
                    'No monthly fees - 30% profit share (you keep 70%)',
                    'CODA puts our own capital in the same trades - we win when you win',
                    'Skin in the game - we take the same risks you do',
                    'Elite strategies - our best techniques reserved for partners',
                    'VIP support - direct line to senior traders',
                    'Quarterly strategy reviews and performance reports'
                ],
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

