import os
import django
import requests
import sys

# Set UTF-8 encoding for output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.urls import reverse
from marketplace.models import BusinessProfile, InvestmentOpportunity, JobOpportunity

base_url = "http://127.0.0.1:8000"

# Get sample data for detail pages
try:
    sample_business = BusinessProfile.objects.first()
    sample_opportunity = InvestmentOpportunity.objects.first()
    sample_job = JobOpportunity.objects.first()
except:
    sample_business = None
    sample_opportunity = None
    sample_job = None

pages_to_test = [
    ("Home", "/"),
    ("Register", "/register/"),
    ("Login", "/login/"),
    ("Browse Businesses", "/marketplace/businesses/"),
    ("Browse Opportunities", "/marketplace/opportunities/"),
    ("Browse Jobs", "/marketplace/jobs/"),
]

# Add detail pages if sample data exists
if sample_business:
    pages_to_test.append(("Business Detail", f"/marketplace/business/{sample_business.user.id}/"))
if sample_opportunity:
    pages_to_test.append(("Opportunity Detail", f"/marketplace/opportunity/{sample_opportunity.slug}/"))
if sample_job:
    pages_to_test.append(("Job Detail", f"/marketplace/job/{sample_job.slug}/"))

print("\n" + "="*60)
print("Testing Platform Pages")
print("="*60 + "\n")

all_passed = True

for page_name, url_path in pages_to_test:
    full_url = base_url + url_path
    try:
        response = requests.get(full_url, timeout=5)
        status = response.status_code
        
        if status == 200:
            status_icon = "[OK]"
            status_text = "200 OK"
        elif status in [301, 302]:
            status_icon = "[>>]"
            status_text = f"REDIRECT to {response.headers.get('Location', 'unknown')}"
        else:
            status_icon = "[!!]"
            status_text = f"ERROR {status}"
            all_passed = False
            
        print(f"{status_icon} {page_name:25} | {status_text}")
        
    except requests.exceptions.ConnectionError:
        print(f"[!!] {page_name:25} | CONNECTION ERROR - Server may not be running")
        all_passed = False
    except Exception as e:
        print(f"[!!] {page_name:25} | ERROR: {str(e)}")
        all_passed = False

print("\n" + "="*60)
if all_passed:
    print("[OK] All pages are accessible!")
else:
    print("[!!] Some pages have issues - see above for details")
print("="*60 + "\n")
