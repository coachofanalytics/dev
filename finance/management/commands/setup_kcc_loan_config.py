#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enhanced management command to set up KCC loan configurations with hybrid system.
Combines tier-based limits with performance-based scaling.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

class Command(BaseCommand):
    help = 'Set up enhanced KCC loan configurations with hybrid scaling system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of existing configurations',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up Enhanced KCC Loan Configurations...')
        )
        
        try:
            with transaction.atomic():
                # Import here to avoid circular imports
                from finance.models import KCCLoanConfiguration
                
                # UPDATED: Configurations with reduced amounts to match KCC service
                default_configs = [
                    {
                        'performance_tier': 'new',
                        'loan_type': 'payday_short_term',
                        'min_amount': Decimal('200.00'),
                        'max_amount': Decimal('500.00'),
                        'starting_amount': Decimal('200.00'),
                        'scaling_factor': Decimal('1.20'),
                        'interest_rate_2weeks': Decimal('12.00'),
                        'interest_rate_1month': Decimal('12.00'),
                        'interest_rate_2months': Decimal('12.00'),
                        'rollover_interest_rate': Decimal('15.00'),
                        'min_term_weeks': 2,
                        'max_term_weeks': 8,
                        'description': 'New KCC members: Start at $200, scale by 20% within $200-$500 range'
                    },
                    {
                        'performance_tier': 'bronze',
                        'loan_type': 'medium_term',
                        'min_amount': Decimal('500.00'),
                        'max_amount': Decimal('750.00'),
                        'starting_amount': Decimal('500.00'),
                        'scaling_factor': Decimal('1.20'),
                        'interest_rate_2weeks': Decimal('10.00'),
                        'interest_rate_1month': Decimal('10.00'),
                        'interest_rate_2months': Decimal('10.00'),
                        'rollover_interest_rate': Decimal('13.00'),
                        'min_term_weeks': 4,
                        'max_term_weeks': 12,
                        'description': 'Bronze members: Start at $500, scale by 20% within $500-$750 range'
                    },
                    {
                        'performance_tier': 'silver',
                        'loan_type': 'medium_term',
                        'min_amount': Decimal('750.00'),
                        'max_amount': Decimal('1000.00'),
                        'starting_amount': Decimal('750.00'),
                        'scaling_factor': Decimal('1.20'),
                        'interest_rate_2weeks': Decimal('9.00'),
                        'interest_rate_1month': Decimal('9.00'),
                        'interest_rate_2months': Decimal('9.00'),
                        'rollover_interest_rate': Decimal('12.00'),
                        'min_term_weeks': 6,
                        'max_term_weeks': 16,
                        'description': 'Silver members: Start at $750, scale by 20% within $750-$1000 range'
                    },
                    {
                        'performance_tier': 'gold',
                        'loan_type': 'long_term_premium',
                        'min_amount': Decimal('1000.00'),
                        'max_amount': Decimal('1500.00'),
                        'starting_amount': Decimal('1000.00'),
                        'scaling_factor': Decimal('1.20'),
                        'interest_rate_2weeks': Decimal('8.00'),
                        'interest_rate_1month': Decimal('8.00'),
                        'interest_rate_2months': Decimal('8.00'),
                        'rollover_interest_rate': Decimal('11.00'),
                        'min_term_weeks': 8,
                        'max_term_weeks': 24,
                        'description': 'Gold members: Start at $1000, scale by 20% within $1000-$1500 range'
                    },
                    {
                        'performance_tier': 'platinum',
                        'loan_type': 'long_term_premium',
                        'min_amount': Decimal('1500.00'),
                        'max_amount': Decimal('3000.00'),
                        'starting_amount': Decimal('1500.00'),
                        'scaling_factor': Decimal('1.20'),
                        'interest_rate_2weeks': Decimal('7.00'),
                        'interest_rate_1month': Decimal('7.00'),
                        'interest_rate_2months': Decimal('7.00'),
                        'rollover_interest_rate': Decimal('10.00'),
                        'min_term_weeks': 12,
                        'max_term_weeks': 52,
                        'description': 'Platinum members: Start at $1500, scale by 20% within $1500-$3000 range'
                    }
                ]
                
                created_count = 0
                updated_count = 0
                
                for config_data in default_configs:
                    # Remove description as it's not a model field
                    description = config_data.pop('description', '')
                    
                    config, created = KCCLoanConfiguration.objects.update_or_create(
                        performance_tier=config_data['performance_tier'],
                        defaults=config_data
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ Created {config.performance_tier} configuration'
                            )
                        )
                    else:
                        if options['force']:
                            # Update existing configuration
                            for key, value in config_data.items():
                                setattr(config, key, value)
                            config.save()
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f'↻ Updated {config.performance_tier} configuration'
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'⚠ Skipped {config.performance_tier} configuration (already exists)'
                                )
                            )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n🎉 Enhanced KCC loan configurations setup completed!'
                    )
                )
                self.stdout.write(
                    f'   Created: {created_count}'
                )
                self.stdout.write(
                    f'   Updated: {updated_count}'
                )
                self.stdout.write(
                    f'   Total: {created_count + updated_count}'
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n�� HYBRID SYSTEM FEATURES:'
                    )
                )
                self.stdout.write(
                    f'   ✅ Tier-based limits with performance scaling'
                )
                self.stdout.write(
                    f'   ✅ 20% scaling factor for good performance'
                )
                self.stdout.write(
                    f'   ✅ Original payday loan interest structure'
                )
                self.stdout.write(
                    f'   ✅ Starting amounts for each tier'
                )
                
                if not options['force']:
                    self.stdout.write(
                        self.style.WARNING(
                            '\n💡 Use --force to update existing configurations'
                        )
                    )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error setting up KCC loan configurations: {e}')
            )
            raise