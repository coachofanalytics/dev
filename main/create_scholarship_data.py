import random
from datetime import timedelta
from django.utils import timezone
from main.models import Scholarship  

titles = [
    "Excellence Scholarship", "Global Arts Grant", "Business Leadership Award",
    "Humanities Research Fellowship", "Vocational Skills Fund", "Innovation Scholarship",
    "Tech Leaders Award", "Creative Minds Grant", "Science Pioneer Fund", "Future Leaders Scholarship",
    "Diversity in STEM Scholarship", "Women in Leadership Grant", "Entrepreneurship Fund",
    "Climate Change Research Grant", "Public Health Fellowship", "Data Science Excellence Award"
]

providers = ["UNESCO", "World Bank", "Local University", "Tech Foundation", "Arts Council", 
             "Global Scholars Org", "Mastercard Foundation", "Chevening", "Fulbright", 
             "DAAD", "Commonwealth Scholarships", "Rotary International", "Google.org"]

amount_descriptions = [
    "Full tuition", "Partial tuition", "Full scholarship", "Full tuition + stipend",
    "Tuition waiver", "Research grant", "Varies by need", "Up to full cost",
    "Includes accommodation", "Full ride", "Merit-based", "Need-based"
]

def create_readable_scholarships(n=50):
    """Create n scholarships with random but realistic data using the new currency fields"""
    
    created_count = 0
    
    for i in range(n):
        has_numeric = random.choice([True, False])  
        
        deadline = timezone.now().date() + timedelta(days=random.randint(-30, 365))
        
        scholarship_data = {
            'title': f"{random.choice(titles)} #{i+1}",
            'provider': random.choice(providers),
            'level': random.choice(list(Scholarship.Level.values)),
            'field': random.choice(list(Scholarship.Field.values)),
            'location': random.choice(list(Scholarship.Location.values)),
            'deadline': deadline,
        }
        
        if has_numeric:
            scholarship_data.update({
                'amount_value': round(random.uniform(500, 50000), 2), 
                'amount_currency': random.choice(list(Scholarship.Currency.values)),
                'amount_description': ''  
            })
        else:
            scholarship_data.update({
                'amount_value': None,  
                'amount_currency': Scholarship.Currency.USD, 
                'amount_description': random.choice(amount_descriptions)
            })
        
        scholarship = Scholarship.objects.create(**scholarship_data)
        created_count += 1
        
        if (i + 1) % 10 == 0:
            print(f"Created {i + 1} scholarships...")
    
    print(f"Successfully created {created_count} scholarships!")
    return created_count

def create_targeted_scholarships():
    """Create specific scholarship examples with realistic amounts"""
    
    us_scholarships = [
        {
            'title': 'Fulbright Foreign Student Program',
            'provider': 'Fulbright',
            'level': Scholarship.Level.MASTERS,
            'field': Scholarship.Field.HUMANITIES,
            'location': Scholarship.Location.USA,
            'amount_value': 40000.00,
            'amount_currency': Scholarship.Currency.USD,
            'amount_description': 'Full tuition + stipend',
            'deadline': timezone.now().date() + timedelta(days=60)
        },
        {
            'title': 'Stanford University Knight-Hennessy Scholars',
            'provider': 'Stanford University',
            'level': Scholarship.Level.PHD,
            'field': Scholarship.Field.STEM,
            'location': Scholarship.Location.USA,
            'amount_value': 85000.00,
            'amount_currency': Scholarship.Currency.USD,
            'amount_description': 'Full funding',
            'deadline': timezone.now().date() + timedelta(days=45)
        }
    ]
    
    kenyan_scholarships = [
        {
            'title': 'Equity Group Foundation Scholarship',
            'provider': 'Equity Bank',
            'level': Scholarship.Level.UNDERGRADUATE,
            'field': Scholarship.Field.STEM,
            'location': Scholarship.Location.KENYA,
            'amount_value': 250000.00,
            'amount_currency': Scholarship.Currency.KES,
            'amount_description': 'Full tuition - Kenyan Universities',
            'deadline': timezone.now().date() + timedelta(days=30)
        },
        {
            'title': 'KCB Foundation Scholarship',
            'provider': 'KCB Bank',
            'level': Scholarship.Level.UNDERGRADUATE,
            'field': Scholarship.Field.BUSINESS,
            'location': Scholarship.Location.KENYA,
            'amount_value': 200000.00,
            'amount_currency': Scholarship.Currency.KES,
            'amount_description': 'Partial tuition',
            'deadline': timezone.now().date() + timedelta(days=15) 
        }
    ]
    
    uk_scholarships = [
        {
            'title': 'Chevening Scholarships',
            'provider': 'UK Government',
            'level': Scholarship.Level.MASTERS,
            'field': Scholarship.Field.HUMANITIES,
            'location': Scholarship.Location.UK,
            'amount_value': 30000.00,
            'amount_currency': Scholarship.Currency.GBP,
            'amount_description': 'Full tuition + living costs',
            'deadline': timezone.now().date() + timedelta(days=90)
        },
        {
            'title': 'Rhodes Scholarship',
            'provider': 'Rhodes Trust',
            'level': Scholarship.Level.MASTERS,
            'field': Scholarship.Field.HUMANITIES,
            'location': Scholarship.Location.UK,
            'amount_value': 45000.00,
            'amount_currency': Scholarship.Currency.GBP,
            'amount_description': 'Full funding',
            'deadline': timezone.now().date() + timedelta(days=120)
        }
    ]
    
    europe_scholarships = [
        {
            'title': 'Erasmus Mundus Joint Masters',
            'provider': 'European Union',
            'level': Scholarship.Level.MASTERS,
            'field': Scholarship.Field.STEM,
            'location': Scholarship.Location.GLOBAL,
            'amount_value': 24000.00,
            'amount_currency': Scholarship.Currency.EUR,
            'amount_description': 'Full scholarship',
            'deadline': timezone.now().date() + timedelta(days=75)
        },
        {
            'title': 'DAAD Scholarships',
            'provider': 'DAAD',
            'level': Scholarship.Level.PHD,
            'field': Scholarship.Field.STEM,
            'location': Scholarship.Location.GLOBAL,
            'amount_value': 1200.00,
            'amount_currency': Scholarship.Currency.EUR,
            'amount_description': 'Monthly stipend',
            'deadline': timezone.now().date() + timedelta(days=5) 
        }
    ]
    
    all_scholarships = us_scholarships + kenyan_scholarships + uk_scholarships + europe_scholarships
    
    for schol in all_scholarships:
        Scholarship.objects.create(**schol)
        print(f"Created: {schol['title']}")
    
    print(f"Created {len(all_scholarships)} targeted scholarships!")
    return len(all_scholarships)

def create_bulk_scholarships_with_currency_mix(n=100):
    """Create a mix of scholarships with various currency types"""
    
    currencies = list(Scholarship.Currency.values)
    currency_weights = [0.4, 0.3, 0.2, 0.1] 
    
    created_count = 0
    
    for i in range(n):

        currency = random.choices(currencies, weights=currency_weights)[0]
        
        if currency == Scholarship.Currency.KES:
            min_amount, max_amount = 50000, 1000000  
        elif currency == Scholarship.Currency.USD:
            min_amount, max_amount = 1000, 80000     
        elif currency == Scholarship.Currency.EUR:
            min_amount, max_amount = 1000, 60000    
        elif currency == Scholarship.Currency.GBP:
            min_amount, max_amount = 1000, 50000     
        
        if random.random() < 0.7:
            amount_value = round(random.uniform(min_amount, max_amount), 2)
            amount_description = ''
        else:
            amount_value = None
            amount_description = random.choice(amount_descriptions)
        
        scholarship = Scholarship.objects.create(
            title=f"{random.choice(titles)} #{i+1}",
            provider=random.choice(providers),
            level=random.choice(list(Scholarship.Level.values)),
            field=random.choice(list(Scholarship.Field.values)),
            location=random.choice(list(Scholarship.Location.values)),
            deadline=timezone.now().date() + timedelta(days=random.randint(-30, 365)),
            amount_value=amount_value,
            amount_currency=currency,
            amount_description=amount_description
        )
        created_count += 1
        
        if (i + 1) % 20 == 0:
            print(f"Created {i + 1} scholarships...")
    
    total = Scholarship.objects.count()
    print(f"\nTotal scholarships: {total}")
    print("\nCurrency breakdown:")
    for currency in currencies:
        count = Scholarship.objects.filter(amount_currency=currency).count()
        percentage = (count / total) * 100
        print(f"  {currency}: {count} ({percentage:.1f}%)")
    
    print(f"\nSuccessfully created {created_count} new scholarships!")
    return created_count

