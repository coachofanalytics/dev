"""
Management command to populate standard loan products
"""
from django.core.management.base import BaseCommand
from finance.models import LoanProduct


class Command(BaseCommand):
    help = 'Populate standard loan products for the system'

    def handle(self, *args, **options):
        # Standard loan products to create
        loan_products = [
            {
                'name': 'Staff Emergency Loan',
                'description': 'Emergency loan for staff members in urgent need of funds',
                'min_amount': 100.00,
                'max_amount': 2000.00,
                'interest_rate': 8.00,
                'term_months': 12,
                'fees': 25.00,
                'product_type': 'staff_emergency',
                'requirements': 'Active staff member, minimum 3 months employment, no outstanding loans',
                'is_active': True
            },
            {
                'name': 'Staff Development Loan',
                'description': 'Loan for staff professional development and training',
                'min_amount': 500.00,
                'max_amount': 5000.00,
                'interest_rate': 6.00,
                'term_months': 24,
                'fees': 50.00,
                'product_type': 'staff_development',
                'requirements': 'Active staff member, approved training/development plan',
                'is_active': True
            },
            {
                'name': 'KCC Premium Loan',
                'description': 'Premium loan product for Karen Country Club members',
                'min_amount': 200.00,
                'max_amount': 10000.00,
                'interest_rate': 5.00,
                'term_months': 36,
                'fees': 75.00,
                'product_type': 'kcc_premium',
                'requirements': 'Active KCC membership, valid membership number',
                'is_active': True
            },
            {
                'name': 'Business Startup Loan',
                'description': 'Loan for new business ventures and startups',
                'min_amount': 1000.00,
                'max_amount': 25000.00,
                'interest_rate': 12.00,
                'term_months': 48,
                'fees': 200.00,
                'product_type': 'business_startup',
                'requirements': 'Business plan, guarantor required, proof of income',
                'is_active': True
            },
            {
                'name': 'Education Loan',
                'description': 'Loan for educational expenses and training programs',
                'min_amount': 300.00,
                'max_amount': 15000.00,
                'interest_rate': 7.00,
                'term_months': 36,
                'fees': 100.00,
                'product_type': 'education',
                'requirements': 'Enrollment proof, guarantor required',
                'is_active': True
            },
            {
                'name': 'Home Improvement Loan',
                'description': 'Loan for home renovation and improvement projects',
                'min_amount': 500.00,
                'max_amount': 20000.00,
                'interest_rate': 9.00,
                'term_months': 60,
                'fees': 150.00,
                'product_type': 'home_improvement',
                'requirements': 'Property ownership proof, guarantor required',
                'is_active': True
            },
            {
                'name': 'Medical Emergency Loan',
                'description': 'Loan for urgent medical expenses and healthcare',
                'min_amount': 200.00,
                'max_amount': 10000.00,
                'interest_rate': 6.50,
                'term_months': 24,
                'fees': 50.00,
                'product_type': 'medical_emergency',
                'requirements': 'Medical documentation, guarantor required',
                'is_active': True
            },
            {
                'name': 'Vehicle Purchase Loan',
                'description': 'Loan for vehicle purchase and transportation needs',
                'min_amount': 1000.00,
                'max_amount': 30000.00,
                'interest_rate': 10.00,
                'term_months': 72,
                'fees': 300.00,
                'product_type': 'vehicle_purchase',
                'requirements': 'Vehicle details, guarantor required, proof of income',
                'is_active': True
            },
            {
                'name': 'Debt Consolidation Loan',
                'description': 'Loan to consolidate multiple debts into one manageable payment',
                'min_amount': 1000.00,
                'max_amount': 50000.00,
                'interest_rate': 11.00,
                'term_months': 60,
                'fees': 250.00,
                'product_type': 'debt_consolidation',
                'requirements': 'Debt statements, guarantor required, credit check',
                'is_active': True
            },
            {
                'name': 'Wedding & Events Loan',
                'description': 'Loan for wedding expenses and special events',
                'min_amount': 500.00,
                'max_amount': 15000.00,
                'interest_rate': 8.50,
                'term_months': 36,
                'fees': 125.00,
                'product_type': 'wedding_events',
                'requirements': 'Event details, guarantor required',
                'is_active': True
            },
            {
                'name': 'General Purpose Loan',
                'description': 'Flexible loan for various personal and business needs',
                'min_amount': 200.00,
                'max_amount': 10000.00,
                'interest_rate': 9.50,
                'term_months': 36,
                'fees': 100.00,
                'product_type': 'general',
                'requirements': 'Guarantor required, proof of income',
                'is_active': True
            }
        ]

        created_count = 0
        updated_count = 0

        for product_data in loan_products:
            product, created = LoanProduct.objects.get_or_create(
                name=product_data['name'],
                defaults=product_data
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created: {product.name}')
                )
            else:
                # Update existing product with new data
                for field, value in product_data.items():
                    setattr(product, field, value)
                product.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated: {product.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created {created_count} new products, updated {updated_count} existing products.'
            )
        )

