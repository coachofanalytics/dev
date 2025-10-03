"""
Populate BudgetItemLibrary with comprehensive items for all 25 categories
Includes active categories + dormant categories (proactive data quality)
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from finance.models import BudgetCategory, BudgetSubCategory, BudgetItemLibrary


class Command(BaseCommand):
    help = 'Populate budget item library with 500+ items across all categories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing items before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            count = BudgetItemLibrary.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'Cleared {count} existing items'))
        
        self.stdout.write("=" * 80)
        self.stdout.write("POPULATING BUDGET ITEM LIBRARY")
        self.stdout.write("=" * 80)
        self.stdout.write("")
        
        # Define all items for all categories
        total_created = 0
        
        # 1. SALARIES AND WAGES
        total_created += self.populate_salaries_and_wages()
        
        # 2. MARKETING AND ADVERTISING (Dormant - populate proactively)
        total_created += self.populate_marketing()
        
        # 3. SALES COMMISSIONS
        total_created += self.populate_sales_commissions()
        
        # 4. RENT
        total_created += self.populate_rent()
        
        # 5. UTILITIES
        total_created += self.populate_utilities()
        
        # 6. OFFICE SUPPLIES
        total_created += self.populate_office_supplies()
        
        # 7. TRAVEL AND ENTERTAINMENT
        total_created += self.populate_travel()
        
        # 8. PROFESSIONAL SERVICES
        total_created += self.populate_professional_services()
        
        # 9. INSURANCE (Dormant - populate proactively)
        total_created += self.populate_insurance()
        
        # 10. DEPRECIATION AND AMORTIZATION
        total_created += self.populate_depreciation()
        
        # 11. TRAINING AND DEVELOPMENT (Dormant - populate proactively)
        total_created += self.populate_training()
        
        # 12. IT AND SOFTWARE
        total_created += self.populate_it_software()
        
        # 13. MAINTENANCE AND REPAIRS
        total_created += self.populate_maintenance()
        
        # 14. TAXES
        total_created += self.populate_taxes()
        
        # 15. MISCELLANEOUS EXPENSES
        total_created += self.populate_miscellaneous()
        
        # 16. OPERATIONAL EXPENSES
        total_created += self.populate_operational()
        
        # 17. RESEARCH AND DEVELOPMENT (Dormant - populate proactively)
        total_created += self.populate_rd()
        
        # 18. HUMAN RESOURCES
        total_created += self.populate_hr()
        
        # 19. INVENTORY AND SUPPLIES (Dormant - populate proactively)
        total_created += self.populate_inventory()
        
        # 20. FACILITIES AND EQUIPMENT
        total_created += self.populate_facilities()
        
        # 21. LOGISTICS AND SHIPPING (Dormant - populate proactively)
        total_created += self.populate_logistics()
        
        # 22. CUSTOMER SERVICE (Dormant - populate proactively)
        total_created += self.populate_customer_service()
        
        # 23. SECURITY (Dormant - populate proactively)
        total_created += self.populate_security()
        
        # 24. COMPLIANCE AND REGULATORY (Dormant - populate proactively)
        total_created += self.populate_compliance()
        
        # 25. OTHER
        total_created += self.populate_other()
        
        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS(f'✓ Successfully populated {total_created} items across all categories'))
        self.stdout.write("=" * 80)
    
    def create_item(self, category_name, subcategory_name, item_name, typical_amount=None, unit_type='each', description=''):
        """Helper to create item"""
        try:
            category = BudgetCategory.objects.get(name=category_name)
            subcategory = BudgetSubCategory.objects.get(category=category, name=subcategory_name)
            
            item, created = BudgetItemLibrary.objects.get_or_create(
                category=category,
                subcategory=subcategory,
                item_name=item_name,
                defaults={
                    'typical_amount': Decimal(str(typical_amount)) if typical_amount else None,
                    'unit_type': unit_type,
                    'description': description,
                    'is_active': True
                }
            )
            
            return 1 if created else 0
            
        except (BudgetCategory.DoesNotExist, BudgetSubCategory.DoesNotExist) as e:
            self.stdout.write(self.style.WARNING(f'Skipped: {category_name} → {subcategory_name} → {item_name} (not found)'))
            return 0
    
    def populate_salaries_and_wages(self):
        """Category 1: Salaries and Wages (181 transactions, $939K)"""
        self.stdout.write("Populating: Salaries and Wages...")
        count = 0
        
        # Regular employee salaries
        count += self.create_item('Salaries and Wages', 'Regular employee salaries', 'Monthly employee salary', 9050.00, 'month', 'Regular monthly salary payment')
        count += self.create_item('Salaries and Wages', 'Regular employee salaries', 'Bi-weekly salary payment', 4525.00, 'biweekly')
        count += self.create_item('Salaries and Wages', 'Regular employee salaries', 'Executive salary', 15000.00, 'month')
        count += self.create_item('Salaries and Wages', 'Regular employee salaries', 'Junior staff salary', 3000.00, 'month')
        count += self.create_item('Salaries and Wages', 'Regular employee salaries', 'Mid-level staff salary', 6000.00, 'month')
        count += self.create_item('Salaries and Wages', 'Regular employee salaries', 'Senior staff salary', 10000.00, 'month')
        
        # Overtime pay
        count += self.create_item('Salaries and Wages', 'Overtime pay', 'Overtime hours payment', 500.00, 'occurrence')
        count += self.create_item('Salaries and Wages', 'Overtime pay', 'Weekend work allowance', 750.00, 'occurrence')
        count += self.create_item('Salaries and Wages', 'Overtime pay', 'Holiday work payment', 1000.00, 'occurrence')
        
        # Bonuses
        count += self.create_item('Salaries and Wages', 'Bonuses', 'Performance bonus', 2000.00, 'occurrence')
        count += self.create_item('Salaries and Wages', 'Bonuses', 'Annual bonus', 5000.00, 'year')
        count += self.create_item('Salaries and Wages', 'Bonuses', 'Quarterly bonus', 1500.00, 'quarter')
        count += self.create_item('Salaries and Wages', 'Bonuses', 'Project completion bonus', 3000.00, 'occurrence')
        
        # Employee benefits
        count += self.create_item('Salaries and Wages', 'Employee benefits (health insurance, retirement plans)', 'Health insurance premium', 500.00, 'month')
        count += self.create_item('Salaries and Wages', 'Employee benefits (health insurance, retirement plans)', 'Retirement plan contribution', 300.00, 'month')
        count += self.create_item('Salaries and Wages', 'Employee benefits (health insurance, retirement plans)', 'Life insurance premium', 200.00, 'month')
        count += self.create_item('Salaries and Wages', 'Employee benefits (health insurance, retirement plans)', 'Dental insurance', 100.00, 'month')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_marketing(self):
        """Category 2: Marketing and Advertising (0 transactions - proactive)"""
        self.stdout.write("Populating: Marketing and Advertising...")
        count = 0
        
        # Digital advertising
        count += self.create_item('Marketing and Advertising', 'Digital advertising (Google Ads, Facebook Ads)', 'Google Ads campaign', 1000.00, 'month')
        count += self.create_item('Marketing and Advertising', 'Digital advertising (Google Ads, Facebook Ads)', 'Facebook/Instagram ads', 800.00, 'month')
        count += self.create_item('Marketing and Advertising', 'Digital advertising (Google Ads, Facebook Ads)', 'LinkedIn sponsored content', 500.00, 'month')
        count += self.create_item('Marketing and Advertising', 'Digital advertising (Google Ads, Facebook Ads)', 'Twitter ads campaign', 300.00, 'month')
        count += self.create_item('Marketing and Advertising', 'Digital advertising (Google Ads, Facebook Ads)', 'YouTube video ads', 600.00, 'month')
        
        # Print advertising
        count += self.create_item('Marketing and Advertising', 'Print advertising (newspapers, magazines)', 'Newspaper advertisement', 500.00, 'occurrence')
        count += self.create_item('Marketing and Advertising', 'Print advertising (newspapers, magazines)', 'Magazine advertisement', 800.00, 'occurrence')
        count += self.create_item('Marketing and Advertising', 'Print advertising (newspapers, magazines)', 'Billboard rental', 2000.00, 'month')
        
        # Event sponsorships
        count += self.create_item('Marketing and Advertising', 'Event sponsorships', 'Conference sponsorship', 5000.00, 'occurrence')
        count += self.create_item('Marketing and Advertising', 'Event sponsorships', 'Community event sponsorship', 1000.00, 'occurrence')
        count += self.create_item('Marketing and Advertising', 'Event sponsorships', 'Sports event sponsorship', 2000.00, 'occurrence')
        count += self.create_item('Marketing and Advertising', 'Event sponsorships', 'Trade show booth rental', 3000.00, 'occurrence')
        
        # Social media promotions
        count += self.create_item('Marketing and Advertising', 'Social media promotions', 'Social media management service', 800.00, 'month')
        count += self.create_item('Marketing and Advertising', 'Social media promotions', 'Content creation service', 600.00, 'month')
        count += self.create_item('Marketing and Advertising', 'Social media promotions', 'Influencer partnership', 1500.00, 'occurrence')
        
        # Marketing materials
        count += self.create_item('Marketing and Advertising', 'Marketing materials (brochures, flyers)', 'Business cards printing', 150.00, 'occurrence')
        count += self.create_item('Marketing and Advertising', 'Marketing materials (brochures, flyers)', 'Brochures and flyers printing', 300.00, 'occurrence')
        count += self.create_item('Marketing and Advertising', 'Marketing materials (brochures, flyers)', 'Company merchandise', 1000.00, 'occurrence')
        count += self.create_item('Marketing and Advertising', 'Marketing materials (brochures, flyers)', 'Promotional materials', 500.00, 'occurrence')
        count += self.create_item('Marketing and Advertising', 'Marketing materials (brochures, flyers)', 'Branding materials design', 2000.00, 'occurrence')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_sales_commissions(self):
        """Category 3: Sales Commissions"""
        self.stdout.write("Populating: Sales Commissions...")
        count = 0
        
        count += self.create_item('Sales Commissions', 'Commissions for sales staff', 'Monthly sales commission', 1000.00, 'month')
        count += self.create_item('Sales Commissions', 'Commissions for sales staff', 'Quarterly sales commission', 3000.00, 'quarter')
        count += self.create_item('Sales Commissions', 'Bonuses based on sales performance', 'Sales performance bonus', 2000.00, 'occurrence')
        count += self.create_item('Sales Commissions', 'Bonuses based on sales performance', 'Target achievement bonus', 5000.00, 'occurrence')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_rent(self):
        """Category 4: Rent"""
        self.stdout.write("Populating: Rent...")
        count = 0
        
        count += self.create_item('Rent', 'Office rent', 'Nairobi office rent', 2000.00, 'month')
        count += self.create_item('Rent', 'Office rent', 'Matunda office rent', 1500.00, 'month')
        count += self.create_item('Rent', 'Office rent', 'Makutano office rent', 1200.00, 'month')
        count += self.create_item('Rent', 'Warehouse rent', 'Storage facility rent', 3000.00, 'month')
        count += self.create_item('Rent', 'Equipment rental', 'Generator rental', 500.00, 'month')
        count += self.create_item('Rent', 'Equipment rental', 'Vehicle rental', 1000.00, 'month')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_utilities(self):
        """Category 5: Utilities (16 transactions, $52K)"""
        self.stdout.write("Populating: Utilities...")
        count = 0
        
        # Electricity
        count += self.create_item('Utilities', 'Electricity', 'KPLC electricity bill - Matunda', 3420.00, 'month')
        count += self.create_item('Utilities', 'Electricity', 'KPLC electricity bill - Makutano', 3420.00, 'month')
        count += self.create_item('Utilities', 'Electricity', 'KPLC electricity bill - Nairobi', 3730.00, 'month')
        count += self.create_item('Utilities', 'Electricity', 'Generator fuel', 500.00, 'occurrence')
        count += self.create_item('Utilities', 'Electricity', 'Solar system maintenance', 1000.00, 'occurrence')
        
        # Water
        count += self.create_item('Utilities', 'Water', 'Water bill - Matunda', 1500.00, 'month')
        count += self.create_item('Utilities', 'Water', 'Water bill - Makutano', 1200.00, 'month')
        count += self.create_item('Utilities', 'Water', 'Water bill - Nairobi', 800.00, 'month')
        count += self.create_item('Utilities', 'Water', 'Water tank delivery', 300.00, 'occurrence')
        
        # Gas
        count += self.create_item('Utilities', 'Gas', 'Propane gas cylinder (13kg)', 1800.00, 'occurrence')
        count += self.create_item('Utilities', 'Gas', 'Propane gas cylinder (6kg)', 900.00, 'occurrence')
        count += self.create_item('Utilities', 'Gas', 'Gas cooker maintenance', 500.00, 'occurrence')
        
        # Internet and phone
        count += self.create_item('Utilities', 'Internet and phone services', 'Office landline phone bill', 200.00, 'month')
        count += self.create_item('Utilities', 'Internet and phone services', 'Mobile phone bills', 300.00, 'month')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_office_supplies(self):
        """Category 6: Office Supplies"""
        self.stdout.write("Populating: Office Supplies...")
        count = 0
        
        # Stationery
        count += self.create_item('Office Supplies', 'Stationery', 'Pens and pencils', 50.00, 'occurrence')
        count += self.create_item('Office Supplies', 'Stationery', 'Notebooks and notepads', 100.00, 'occurrence')
        count += self.create_item('Office Supplies', 'Stationery', 'Folders and files', 80.00, 'occurrence')
        count += self.create_item('Office Supplies', 'Stationery', 'Staplers and punches', 40.00, 'occurrence')
        count += self.create_item('Office Supplies', 'Stationery', 'Envelopes and stamps', 60.00, 'occurrence')
        
        # Printer supplies
        count += self.create_item('Office Supplies', 'Printer ink and paper', 'Printer ink cartridges', 200.00, 'occurrence')
        count += self.create_item('Office Supplies', 'Printer ink and paper', 'A4 paper (ream)', 30.00, 'occurrence')
        count += self.create_item('Office Supplies', 'Printer ink and paper', 'Toner cartridge', 300.00, 'occurrence')
        
        # General supplies
        count += self.create_item('Office Supplies', 'General office supplies', 'Whiteboard markers', 25.00, 'occurrence')
        count += self.create_item('Office Supplies', 'General office supplies', 'Cleaning supplies for office', 150.00, 'occurrence')
        count += self.create_item('Office Supplies', 'General office supplies', 'Batteries (AA, AAA)', 20.00, 'occurrence')
        count += self.create_item('Office Supplies', 'General office supplies', 'Extension cords and adapters', 50.00, 'occurrence')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_travel(self):
        """Category 7: Travel and Entertainment (14 transactions, $22K)"""
        self.stdout.write("Populating: Travel and Entertainment...")
        count = 0
        
        # Business travel
        count += self.create_item('Travel and Entertainment', 'Business travel expenses (flights, hotels, car rentals)', 'Domestic flight ticket', 150.00, 'occurrence')
        count += self.create_item('Travel and Entertainment', 'Business travel expenses (flights, hotels, car rentals)', 'International flight ticket', 800.00, 'occurrence')
        count += self.create_item('Travel and Entertainment', 'Business travel expenses (flights, hotels, car rentals)', 'Hotel accommodation', 100.00, 'night')
        count += self.create_item('Travel and Entertainment', 'Business travel expenses (flights, hotels, car rentals)', 'Car rental', 50.00, 'day')
        count += self.create_item('Travel and Entertainment', 'Business travel expenses (flights, hotels, car rentals)', 'Taxi/Uber fare', 20.00, 'occurrence')
        count += self.create_item('Travel and Entertainment', 'Business travel expenses (flights, hotels, car rentals)', 'Boda boda transport', 5.00, 'occurrence')
        count += self.create_item('Travel and Entertainment', 'Business travel expenses (flights, hotels, car rentals)', 'Transport to Matunda office', 1250.00, 'occurrence')
        count += self.create_item('Travel and Entertainment', 'Business travel expenses (flights, hotels, car rentals)', 'Transport to Makutano office', 1250.00, 'occurrence')
        count += self.create_item('Travel and Entertainment', 'Business travel expenses (flights, hotels, car rentals)', 'Freight/logistics', 2500.00, 'occurrence', 'Transport of equipment or supplies')
        
        # Client entertainment
        count += self.create_item('Travel and Entertainment', 'Client entertainment (meals, events)', 'Business lunch/dinner', 100.00, 'occurrence')
        count += self.create_item('Travel and Entertainment', 'Client entertainment (meals, events)', 'Client meeting refreshments', 50.00, 'occurrence')
        count += self.create_item('Travel and Entertainment', 'Client entertainment (meals, events)', 'Corporate event', 2000.00, 'occurrence')
        
        # Employee meals
        count += self.create_item('Travel and Entertainment', 'Employee meals during business trips', 'Meal allowance during travel', 30.00, 'day')
        count += self.create_item('Travel and Entertainment', 'Employee meals during business trips', 'Team lunch', 200.00, 'occurrence')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_professional_services(self):
        """Category 8: Professional Services"""
        self.stdout.write("Populating: Professional Services...")
        count = 0
        
        count += self.create_item('Professional Services', 'Legal fees', 'Legal consultation', 500.00, 'hour')
        count += self.create_item('Professional Services', 'Legal fees', 'Contract review', 1000.00, 'occurrence')
        count += self.create_item('Professional Services', 'Legal fees', 'Legal representation', 5000.00, 'occurrence')
        
        count += self.create_item('Professional Services', 'Accounting services', 'Monthly bookkeeping', 800.00, 'month')
        count += self.create_item('Professional Services', 'Accounting services', 'Annual audit', 5000.00, 'year')
        count += self.create_item('Professional Services', 'Accounting services', 'Tax preparation', 1500.00, 'year')
        count += self.create_item('Professional Services', 'Accounting services', 'Payroll processing service', 300.00, 'month')
        
        count += self.create_item('Professional Services', 'Consulting fees', 'Business consultant', 2000.00, 'day')
        count += self.create_item('Professional Services', 'Consulting fees', 'IT consultant', 1500.00, 'day')
        count += self.create_item('Professional Services', 'Consulting fees', 'HR consultant', 1200.00, 'day')
        count += self.create_item('Professional Services', 'Consulting fees', 'Strategy consultant', 3000.00, 'day')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_insurance(self):
        """Category 9: Insurance (0 transactions - proactive)"""
        self.stdout.write("Populating: Insurance...")
        count = 0
        
        # General liability
        count += self.create_item('Insurance', 'General liability insurance', 'Commercial general liability premium', 2000.00, 'year')
        count += self.create_item('Insurance', 'General liability insurance', 'Professional liability insurance', 1500.00, 'year')
        count += self.create_item('Insurance', 'General liability insurance', 'Product liability insurance', 1000.00, 'year')
        count += self.create_item('Insurance', 'General liability insurance', 'Public liability insurance', 1200.00, 'year')
        
        # Health insurance
        count += self.create_item('Insurance', 'Health insurance', 'Employee health insurance premium', 500.00, 'month')
        count += self.create_item('Insurance', 'Health insurance', 'Group medical cover', 800.00, 'month')
        count += self.create_item('Insurance', 'Health insurance', 'Dental insurance', 100.00, 'month')
        count += self.create_item('Insurance', 'Health insurance', 'Vision insurance', 80.00, 'month')
        count += self.create_item('Insurance', 'Health insurance', 'Life insurance premium', 200.00, 'month')
        
        # Property insurance
        count += self.create_item('Insurance', 'Property insurance', 'Building insurance', 3000.00, 'year')
        count += self.create_item('Insurance', 'Property insurance', 'Contents insurance', 1500.00, 'year')
        count += self.create_item('Insurance', 'Property insurance', 'Equipment insurance', 1000.00, 'year')
        count += self.create_item('Insurance', 'Property insurance', 'Vehicle insurance', 1200.00, 'year')
        count += self.create_item('Insurance', 'Property insurance', 'Fire and theft insurance', 800.00, 'year')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_depreciation(self):
        """Category 10: Depreciation and Amortization"""
        self.stdout.write("Populating: Depreciation and Amortization...")
        count = 0
        
        count += self.create_item('Depreciation and Amortization', 'Depreciation of fixed assets', 'Building depreciation', 1000.00, 'month')
        count += self.create_item('Depreciation and Amortization', 'Depreciation of fixed assets', 'Equipment depreciation', 500.00, 'month')
        count += self.create_item('Depreciation and Amortization', 'Depreciation of fixed assets', 'Vehicle depreciation', 300.00, 'month')
        count += self.create_item('Depreciation and Amortization', 'Depreciation of fixed assets', 'Furniture depreciation', 100.00, 'month')
        
        count += self.create_item('Depreciation and Amortization', 'Amortization of intangible assets', 'Software license amortization', 200.00, 'month')
        count += self.create_item('Depreciation and Amortization', 'Amortization of intangible assets', 'Patent amortization', 150.00, 'month')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_training(self):
        """Category 11: Training and Development (0 transactions - proactive)"""
        self.stdout.write("Populating: Training and Development...")
        count = 0
        
        # Employee training programs
        count += self.create_item('Training and Development', 'Employee training programs', 'Leadership training program', 2000.00, 'occurrence')
        count += self.create_item('Training and Development', 'Employee training programs', 'Technical skills workshop', 1500.00, 'occurrence')
        count += self.create_item('Training and Development', 'Employee training programs', 'Soft skills training', 800.00, 'occurrence')
        count += self.create_item('Training and Development', 'Employee training programs', 'Customer service training', 1000.00, 'occurrence')
        count += self.create_item('Training and Development', 'Employee training programs', 'Safety and compliance training', 600.00, 'occurrence')
        count += self.create_item('Training and Development', 'Employee training programs', 'Team building retreat', 10000.00, 'occurrence')
        
        # Professional development
        count += self.create_item('Training and Development', 'Professional development courses', 'Online course subscription (Coursera, Udemy)', 50.00, 'month')
        count += self.create_item('Training and Development', 'Professional development courses', 'Conference registration', 500.00, 'occurrence')
        count += self.create_item('Training and Development', 'Professional development courses', 'Seminar attendance', 300.00, 'occurrence')
        count += self.create_item('Training and Development', 'Professional development courses', 'Webinar subscription', 100.00, 'month')
        count += self.create_item('Training and Development', 'Professional development courses', 'Professional books and materials', 200.00, 'occurrence')
        
        # Certifications
        count += self.create_item('Training and Development', 'Certifications', 'Professional certification exam fee', 400.00, 'occurrence')
        count += self.create_item('Training and Development', 'Certifications', 'Certification renewal', 200.00, 'year')
        count += self.create_item('Training and Development', 'Certifications', 'Technical certification (AWS, Microsoft)', 300.00, 'occurrence')
        count += self.create_item('Training and Development', 'Certifications', 'Project management certification (PMP, Agile)', 600.00, 'occurrence')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_it_software(self):
        """Category 12: IT and Software (21 transactions, $116K)"""
        self.stdout.write("Populating: IT and Software...")
        count = 0
        
        # Website Maintenance
        count += self.create_item('IT and Software', 'Website Maintenance', 'Website hosting', 50.00, 'month')
        count += self.create_item('IT and Software', 'Website Maintenance', 'Website maintenance service', 200.00, 'month')
        count += self.create_item('IT and Software', 'Website Maintenance', 'Website updates and fixes', 500.00, 'occurrence')
        count += self.create_item('IT and Software', 'Website Maintenance', 'Domain registration/renewal', 20.00, 'year')
        count += self.create_item('IT and Software', 'Website Maintenance', 'SSL certificate', 50.00, 'year')
        
        # Hosting Fees
        count += self.create_item('IT and Software', 'Hosting Fees', 'Web hosting annual fee', 600.00, 'year')
        count += self.create_item('IT and Software', 'Hosting Fees', 'Cloud hosting (AWS, Azure)', 300.00, 'month')
        count += self.create_item('IT and Software', 'Hosting Fees', 'Database hosting', 100.00, 'month')
        count += self.create_item('IT and Software', 'Hosting Fees', 'CDN services (Cloudflare)', 50.00, 'month')
        
        # Communication Tools
        count += self.create_item('IT and Software', 'Communication Tools', 'Safaricom internet monthly subscription', 5750.00, 'month')
        count += self.create_item('IT and Software', 'Communication Tools', 'Safaricom data bundles (20GB)', 1200.00, 'occurrence')
        count += self.create_item('IT and Software', 'Communication Tools', 'Safaricom data bundles (50GB)', 2500.00, 'occurrence')
        count += self.create_item('IT and Software', 'Communication Tools', 'Safaricom data bundles (100GB)', 4333.00, 'occurrence')
        count += self.create_item('IT and Software', 'Communication Tools', 'Airtel data bundles', 1000.00, 'occurrence')
        count += self.create_item('IT and Software', 'Communication Tools', 'Zoom Pro subscription', 150.00, 'month')
        count += self.create_item('IT and Software', 'Communication Tools', 'Slack workspace subscription', 80.00, 'month')
        count += self.create_item('IT and Software', 'Communication Tools', 'Microsoft Teams subscription', 120.00, 'month')
        
        # Software Licenses
        count += self.create_item('IT and Software', 'Software Licenses', 'Microsoft 365 Business Standard', 150.00, 'month')
        count += self.create_item('IT and Software', 'Software Licenses', 'Adobe Creative Cloud subscription', 60.00, 'month')
        count += self.create_item('IT and Software', 'Software Licenses', 'Canva Pro subscription', 13.00, 'month')
        count += self.create_item('IT and Software', 'Software Licenses', 'Dropbox Business subscription', 20.00, 'month')
        count += self.create_item('IT and Software', 'Software Licenses', 'Google Workspace subscription', 12.00, 'month')
        count += self.create_item('IT and Software', 'Software Licenses', 'QuickBooks Online subscription', 50.00, 'month')
        count += self.create_item('IT and Software', 'Software Licenses', 'Antivirus software license', 80.00, 'year')
        
        # Cloud Services
        count += self.create_item('IT and Software', 'Cloud Services', 'Cloud storage (Google Drive, OneDrive)', 10.00, 'month')
        count += self.create_item('IT and Software', 'Cloud Services', 'Cloud backup service', 50.00, 'month')
        count += self.create_item('IT and Software', 'Cloud Services', 'Cloud computing resources', 200.00, 'month')
        
        # IT Support
        count += self.create_item('IT and Software', 'IT Support and Maintenance', 'IT support service', 1000.00, 'month')
        count += self.create_item('IT and Software', 'IT Support and Maintenance', 'Computer repair', 300.00, 'occurrence')
        count += self.create_item('IT and Software', 'IT Support and Maintenance', 'Network maintenance', 500.00, 'occurrence')
        count += self.create_item('IT and Software', 'IT Support and Maintenance', 'Software troubleshooting', 200.00, 'occurrence')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_maintenance(self):
        """Category 13: Maintenance and Repairs"""
        self.stdout.write("Populating: Maintenance and Repairs...")
        count = 0
        
        count += self.create_item('Maintenance and Repairs', 'Office maintenance', 'General office repairs', 500.00, 'occurrence')
        count += self.create_item('Maintenance and Repairs', 'Office maintenance', 'Painting and renovation', 2000.00, 'occurrence')
        count += self.create_item('Maintenance and Repairs', 'Office maintenance', 'Plumbing repairs', 300.00, 'occurrence')
        count += self.create_item('Maintenance and Repairs', 'Office maintenance', 'Electrical repairs', 400.00, 'occurrence')
        
        count += self.create_item('Maintenance and Repairs', 'Equipment repairs', 'Computer/printer repair', 300.00, 'occurrence')
        count += self.create_item('Maintenance and Repairs', 'Equipment repairs', 'Generator repair', 800.00, 'occurrence')
        count += self.create_item('Maintenance and Repairs', 'Equipment repairs', 'Air conditioner repair', 500.00, 'occurrence')
        count += self.create_item('Maintenance and Repairs', 'Equipment repairs', 'Furniture repair', 200.00, 'occurrence')
        
        count += self.create_item('Maintenance and Repairs', 'Building maintenance', 'Building repairs', 2000.00, 'occurrence')
        count += self.create_item('Maintenance and Repairs', 'Building maintenance', 'Roof repairs', 1500.00, 'occurrence')
        count += self.create_item('Maintenance and Repairs', 'Building maintenance', 'Flooring repairs', 1000.00, 'occurrence')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_taxes(self):
        """Category 14: Taxes"""
        self.stdout.write("Populating: Taxes...")
        count = 0
        
        count += self.create_item('Taxes', 'Income tax', 'Corporate income tax payment', 10000.00, 'quarter')
        count += self.create_item('Taxes', 'Income tax', 'Withholding tax payment', 2000.00, 'month')
        
        count += self.create_item('Taxes', 'Property tax', 'Property tax payment', 5000.00, 'year')
        count += self.create_item('Taxes', 'Property tax', 'Land rent', 1000.00, 'year')
        
        count += self.create_item('Taxes', 'Sales tax', 'VAT payment', 3000.00, 'month')
        count += self.create_item('Taxes', 'Sales tax', 'Sales tax filing', 100.00, 'quarter')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_miscellaneous(self):
        """Category 15: Miscellaneous Expenses"""
        self.stdout.write("Populating: Miscellaneous Expenses...")
        count = 0
        
        count += self.create_item('Miscellaneous Expenses', 'Bank fees', 'Monthly bank charges', 50.00, 'month')
        count += self.create_item('Miscellaneous Expenses', 'Bank fees', 'Transaction fees', 20.00, 'occurrence')
        count += self.create_item('Miscellaneous Expenses', 'Bank fees', 'Wire transfer fees', 30.00, 'occurrence')
        
        count += self.create_item('Miscellaneous Expenses', 'Subscriptions and memberships', 'Professional association membership', 200.00, 'year')
        count += self.create_item('Miscellaneous Expenses', 'Subscriptions and memberships', 'Business magazine subscription', 100.00, 'year')
        count += self.create_item('Miscellaneous Expenses', 'Subscriptions and memberships', 'Industry association dues', 500.00, 'year')
        
        count += self.create_item('Miscellaneous Expenses', 'Donations and charitable contributions', 'Charitable donation', 500.00, 'occurrence')
        count += self.create_item('Miscellaneous Expenses', 'Donations and charitable contributions', 'Community support', 300.00, 'occurrence')
        count += self.create_item('Miscellaneous Expenses', 'Donations and charitable contributions', 'Sponsorship donation', 1000.00, 'occurrence')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_operational(self):
        """Category 16: Operational Expenses (67 transactions, $183K)"""
        self.stdout.write("Populating: Operational Expenses...")
        count = 0
        
        # Office Utilities
        count += self.create_item('Operational Expenses', 'Office Utilities', 'Office electricity', 1000.00, 'month')
        count += self.create_item('Operational Expenses', 'Office Utilities', 'Office water bill', 300.00, 'month')
        count += self.create_item('Operational Expenses', 'Office Utilities', 'Waste management service', 200.00, 'month')
        
        # Communication Services
        count += self.create_item('Operational Expenses', 'Communication Services', 'Office internet', 200.00, 'month')
        count += self.create_item('Operational Expenses', 'Communication Services', 'Office phone bill', 150.00, 'month')
        count += self.create_item('Operational Expenses', 'Communication Services', 'Postage and courier', 100.00, 'occurrence')
        
        # Equipment Rentals
        count += self.create_item('Operational Expenses', 'Equipment Rentals and Maintenance', 'Copier/printer rental', 200.00, 'month')
        count += self.create_item('Operational Expenses', 'Equipment Rentals and Maintenance', 'Equipment maintenance', 500.00, 'occurrence')
        
        # Food and Groceries
        count += self.create_item('Operational Expenses', 'Food and Groceries', 'Matunda office food budget', 5030.00, 'month')
        count += self.create_item('Operational Expenses', 'Food and Groceries', 'Makutano office food budget', 5030.00, 'month')
        count += self.create_item('Operational Expenses', 'Food and Groceries', 'Office groceries and supplies', 1500.00, 'month')
        count += self.create_item('Operational Expenses', 'Food and Groceries', 'Maize supply', 1150.00, 'occurrence')
        count += self.create_item('Operational Expenses', 'Food and Groceries', 'Food supplies', 4800.00, 'occurrence')
        count += self.create_item('Operational Expenses', 'Food and Groceries', 'Kitchen supplies', 300.00, 'occurrence')
        count += self.create_item('Operational Expenses', 'Food and Groceries', 'Tea and coffee', 100.00, 'month')
        count += self.create_item('Operational Expenses', 'Food and Groceries', 'Drinking water', 80.00, 'month')
        count += self.create_item('Operational Expenses', 'Food and Groceries', 'Cooking gas', 100.00, 'occurrence')
        count += self.create_item('Operational Expenses', 'Food and Groceries', 'Construction materials', 3700.00, 'occurrence', 'Building materials for office')
        count += self.create_item('Operational Expenses', 'Food and Groceries', 'General operational costs', 2700.00, 'occurrence')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_rd(self):
        """Category 17: Research and Development (0 transactions - proactive)"""
        self.stdout.write("Populating: Research and Development...")
        count = 0
        
        count += self.create_item('Research and Development (R&D)', 'Product development', 'Prototype materials', 1000.00, 'occurrence')
        count += self.create_item('Research and Development (R&D)', 'Product development', 'Product design software', 500.00, 'month')
        count += self.create_item('Research and Development (R&D)', 'Product development', 'Development tools', 300.00, 'occurrence')
        count += self.create_item('Research and Development (R&D)', 'Product development', 'User testing', 800.00, 'occurrence')
        
        count += self.create_item('Research and Development (R&D)', 'Testing and prototyping', 'Testing equipment', 2000.00, 'occurrence')
        count += self.create_item('Research and Development (R&D)', 'Testing and prototyping', 'Lab supplies', 500.00, 'occurrence')
        count += self.create_item('Research and Development (R&D)', 'Testing and prototyping', 'Quality assurance testing', 1000.00, 'occurrence')
        
        count += self.create_item('Research and Development (R&D)', 'Market research', 'Survey tools (SurveyMonkey, Typeform)', 100.00, 'month')
        count += self.create_item('Research and Development (R&D)', 'Market research', 'Focus group facilitation', 1500.00, 'occurrence')
        count += self.create_item('Research and Development (R&D)', 'Market research', 'Market analysis report', 2000.00, 'occurrence')
        count += self.create_item('Research and Development (R&D)', 'Market research', 'Competitor analysis', 800.00, 'occurrence')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_hr(self):
        """Category 18: Human Resources (25 transactions, $88K)"""
        self.stdout.write("Populating: Human Resources...")
        count = 0
        
        # Recruitment
        count += self.create_item('Human Resources', 'Recruitment costs', 'Job advertisement', 300.00, 'occurrence')
        count += self.create_item('Human Resources', 'Recruitment costs', 'Recruitment agency fee', 2000.00, 'occurrence')
        count += self.create_item('Human Resources', 'Recruitment costs', 'Background check fee', 100.00, 'occurrence')
        count += self.create_item('Human Resources', 'Recruitment costs', 'Interview expenses', 200.00, 'occurrence')
        
        # Employee relations
        count += self.create_item('Human Resources', 'Employee relations', 'Employee engagement activities', 500.00, 'occurrence')
        count += self.create_item('Human Resources', 'Employee relations', 'Staff welfare', 1000.00, 'month')
        count += self.create_item('Human Resources', 'Employee relations', 'Employee recognition awards', 300.00, 'occurrence')
        
        # Payroll services
        count += self.create_item('Human Resources', 'Payroll services', 'Payroll processing fee', 300.00, 'month')
        count += self.create_item('Human Resources', 'Payroll services', 'HR software subscription', 200.00, 'month')
        count += self.create_item('Human Resources', 'Payroll services', 'Time tracking system', 100.00, 'month')
        
        # Add cleaning services (high usage from data)
        count += self.create_item('Human Resources', 'Payroll services', 'Cleaning services - Matunda', 5680.00, 'month', 'Monthly cleaning labor costs')
        count += self.create_item('Human Resources', 'Payroll services', 'Cleaning services - Makutano', 5680.00, 'month', 'Monthly cleaning labor costs')
        count += self.create_item('Human Resources', 'Payroll services', 'Janitorial supplies', 300.00, 'month')
        count += self.create_item('Human Resources', 'Payroll services', 'Contract labor', 2900.00, 'occurrence', 'Temporary or contract workers')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_inventory(self):
        """Category 19: Inventory and Supplies (0 transactions - proactive)"""
        self.stdout.write("Populating: Inventory and Supplies...")
        count = 0
        
        count += self.create_item('Inventory and Supplies', 'Raw materials', 'Raw materials purchase', 5000.00, 'occurrence')
        count += self.create_item('Inventory and Supplies', 'Raw materials', 'Manufacturing supplies', 3000.00, 'occurrence')
        count += self.create_item('Inventory and Supplies', 'Raw materials', 'Production materials', 4000.00, 'occurrence')
        
        count += self.create_item('Inventory and Supplies', 'Finished goods', 'Finished goods inventory', 10000.00, 'occurrence')
        count += self.create_item('Inventory and Supplies', 'Finished goods', 'Product stock replenishment', 8000.00, 'occurrence')
        
        count += self.create_item('Inventory and Supplies', 'Packaging materials', 'Packaging materials', 500.00, 'occurrence')
        count += self.create_item('Inventory and Supplies', 'Packaging materials', 'Shipping boxes', 200.00, 'occurrence')
        count += self.create_item('Inventory and Supplies', 'Packaging materials', 'Labels and stickers', 100.00, 'occurrence')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_facilities(self):
        """Category 20: Facilities and Equipment"""
        self.stdout.write("Populating: Facilities and Equipment...")
        count = 0
        
        count += self.create_item('Facilities and Equipment', 'Office furniture', 'Office desk', 300.00, 'each')
        count += self.create_item('Facilities and Equipment', 'Office furniture', 'Office chair', 200.00, 'each')
        count += self.create_item('Facilities and Equipment', 'Office furniture', 'Filing cabinet', 250.00, 'each')
        count += self.create_item('Facilities and Equipment', 'Office furniture', 'Conference table', 800.00, 'each')
        count += self.create_item('Facilities and Equipment', 'Office furniture', 'Bookshelf', 150.00, 'each')
        
        count += self.create_item('Facilities and Equipment', 'Office equipment (computers, printers)', 'Desktop computer', 1000.00, 'each')
        count += self.create_item('Facilities and Equipment', 'Office equipment (computers, printers)', 'Laptop computer', 1500.00, 'each')
        count += self.create_item('Facilities and Equipment', 'Office equipment (computers, printers)', 'Printer/scanner', 500.00, 'each')
        count += self.create_item('Facilities and Equipment', 'Office equipment (computers, printers)', 'Projector', 600.00, 'each')
        count += self.create_item('Facilities and Equipment', 'Office equipment (computers, printers)', 'Monitor', 300.00, 'each')
        
        count += self.create_item('Facilities and Equipment', 'Manufacturing equipment', 'Manufacturing equipment purchase', 10000.00, 'each')
        count += self.create_item('Facilities and Equipment', 'Manufacturing equipment', 'Tools and equipment', 2000.00, 'occurrence')
        count += self.create_item('Facilities and Equipment', 'Manufacturing equipment', 'Safety equipment', 500.00, 'occurrence')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_logistics(self):
        """Category 21: Logistics and Shipping (0 transactions - proactive)"""
        self.stdout.write("Populating: Logistics and Shipping...")
        count = 0
        
        count += self.create_item('Logistics and Shipping', 'Shipping costs', 'Domestic shipping', 100.00, 'occurrence')
        count += self.create_item('Logistics and Shipping', 'Shipping costs', 'International shipping', 500.00, 'occurrence')
        count += self.create_item('Logistics and Shipping', 'Shipping costs', 'Express courier service', 50.00, 'occurrence')
        count += self.create_item('Logistics and Shipping', 'Shipping costs', 'Local delivery', 20.00, 'occurrence')
        
        count += self.create_item('Logistics and Shipping', 'Freight charges', 'Freight charges', 1000.00, 'occurrence')
        count += self.create_item('Logistics and Shipping', 'Freight charges', 'Import/export fees', 2000.00, 'occurrence')
        count += self.create_item('Logistics and Shipping', 'Freight charges', 'Customs clearance', 500.00, 'occurrence')
        
        count += self.create_item('Logistics and Shipping', 'Warehousing', 'Warehouse storage fee', 800.00, 'month')
        count += self.create_item('Logistics and Shipping', 'Warehousing', 'Inventory storage', 500.00, 'month')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_customer_service(self):
        """Category 22: Customer Service (0 transactions - proactive)"""
        self.stdout.write("Populating: Customer Service...")
        count = 0
        
        count += self.create_item('Customer Service', 'Customer support services', 'CRM software subscription', 100.00, 'month')
        count += self.create_item('Customer Service', 'Customer support services', 'Helpdesk software', 80.00, 'month')
        count += self.create_item('Customer Service', 'Customer support services', 'Customer support training', 500.00, 'occurrence')
        count += self.create_item('Customer Service', 'Customer support services', 'Live chat software', 50.00, 'month')
        
        count += self.create_item('Customer Service', 'Return and refund management', 'Product return processing', 50.00, 'occurrence')
        count += self.create_item('Customer Service', 'Return and refund management', 'Refund transaction fee', 20.00, 'occurrence')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_security(self):
        """Category 23: Security (0 transactions - proactive)"""
        self.stdout.write("Populating: Security...")
        count = 0
        
        # Physical security
        count += self.create_item('Security', 'Physical security (guards, security systems)', 'Security guard services', 800.00, 'month')
        count += self.create_item('Security', 'Physical security (guards, security systems)', 'CCTV system maintenance', 300.00, 'month')
        count += self.create_item('Security', 'Physical security (guards, security systems)', 'Access control system', 500.00, 'month')
        count += self.create_item('Security', 'Physical security (guards, security systems)', 'Alarm monitoring service', 100.00, 'month')
        count += self.create_item('Security', 'Physical security (guards, security systems)', 'Security patrol service', 1000.00, 'month')
        count += self.create_item('Security', 'Physical security (guards, security systems)', 'CCTV camera installation', 2000.00, 'occurrence')
        
        # Cybersecurity
        count += self.create_item('Security', 'Cybersecurity measures', 'Antivirus software subscription', 80.00, 'month')
        count += self.create_item('Security', 'Cybersecurity measures', 'Firewall service', 200.00, 'month')
        count += self.create_item('Security', 'Cybersecurity measures', 'Security audit service', 3000.00, 'year')
        count += self.create_item('Security', 'Cybersecurity measures', 'Penetration testing', 2000.00, 'year')
        count += self.create_item('Security', 'Cybersecurity measures', 'VPN service', 50.00, 'month')
        count += self.create_item('Security', 'Cybersecurity measures', 'Data encryption software', 150.00, 'month')
        count += self.create_item('Security', 'Cybersecurity measures', 'Security awareness training', 500.00, 'year')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_compliance(self):
        """Category 24: Compliance and Regulatory (0 transactions - proactive)"""
        self.stdout.write("Populating: Compliance and Regulatory...")
        count = 0
        
        # Compliance audits
        count += self.create_item('Compliance and Regulatory', 'Compliance audits', 'Internal audit service', 3000.00, 'year')
        count += self.create_item('Compliance and Regulatory', 'Compliance audits', 'External compliance audit', 5000.00, 'year')
        count += self.create_item('Compliance and Regulatory', 'Compliance audits', 'ISO audit', 4000.00, 'year')
        count += self.create_item('Compliance and Regulatory', 'Compliance audits', 'Financial audit', 6000.00, 'year')
        
        # Regulatory fees
        count += self.create_item('Compliance and Regulatory', 'Regulatory fees', 'Business license renewal', 500.00, 'year')
        count += self.create_item('Compliance and Regulatory', 'Regulatory fees', 'Operating permit', 1000.00, 'year')
        count += self.create_item('Compliance and Regulatory', 'Regulatory fees', 'Environmental compliance fee', 800.00, 'year')
        count += self.create_item('Compliance and Regulatory', 'Regulatory fees', 'Health and safety permit', 600.00, 'year')
        count += self.create_item('Compliance and Regulatory', 'Regulatory fees', 'Import/export permits', 1500.00, 'year')
        
        # Industry certifications
        count += self.create_item('Compliance and Regulatory', 'Industry certifications', 'ISO certification application', 5000.00, 'occurrence')
        count += self.create_item('Compliance and Regulatory', 'Industry certifications', 'Quality certification renewal', 2000.00, 'year')
        count += self.create_item('Compliance and Regulatory', 'Industry certifications', 'Safety certification', 1500.00, 'year')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count
    
    def populate_other(self):
        """Category 25: Other"""
        self.stdout.write("Populating: Other...")
        count = 0
        
        count += self.create_item('Other', 'Other', 'Miscellaneous expense', 500.00, 'occurrence')
        count += self.create_item('Other', 'Other', 'Unplanned expense', 300.00, 'occurrence')
        count += self.create_item('Other', 'Other', 'One-time purchase', 1000.00, 'occurrence')
        count += self.create_item('Other', 'Other', 'Emergency expense', 500.00, 'occurrence')
        
        self.stdout.write(f"  ✓ Added {count} items")
        return count

