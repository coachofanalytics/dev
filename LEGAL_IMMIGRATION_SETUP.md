# Legal & Immigration Guidance Setup Guide

## Overview
This guide provides instructions for setting up and managing the Legal & Immigration Guidance system with integrated Consular Assistance Services in your DC48K Django application.

## What's New

### New Models
1. **ConsularService** - Stores information about government agencies, legal aid organizations, and consultation services
2. **LegalImmigrationResource** - Stores legal immigration information organized by category

### New Views
- `legal_immigration_guidance()` - Main immigration guidance page with tabs
- `consular_services_list()` - Searchable/filterable list of consular services
- `consular_service_detail()` - Detailed view of a single consular service
- `legal_resources()` - Searchable/filterable list of legal resources
- `legal_resource_detail()` - Detailed view of a single legal resource

### New Templates
- `legal_immigration.html` - Main guidance page with 4 tabs (Immigration Basics, Legal Rights, Consular Services, FAQ)
- `consular_services_list.html` - List view with search and filtering
- `consular_service_detail.html` - Service detail page
- `legal_resources.html` - Resources list with search and filtering
- `legal_resource_detail.html` - Resource detail page

## Setup Instructions

### Step 1: Apply Database Migrations

Create and apply migrations for the new models:

```bash
# Create migration files
python manage.py makemigrations communities

# Apply migrations to database
python manage.py migrate communities
```

### Step 2: Create Consular Services via Django Admin

1. Go to `http://your-domain/admin/`
2. Navigate to **Communities > Consular Services**
3. Click **Add Consular Service** and fill in the form:

**Example 1: USCIS**
```
Name: USCIS (U.S. Citizenship & Immigration Services)
Service Type: Government Agency
Description: Official agency handling all immigration applications and benefits including visas, green cards, and citizenship.
Website: https://www.uscis.gov
Phone: 1-800-375-5283
Email: (leave blank)
Address: Multiple locations nationwide
Country Coverage: USA
Services Offered: Green card applications, visa processing, citizenship applications, employment authorization, biometrics
Is Featured: ✓ (checked)
```

**Example 2: State Department**
```
Name: U.S. State Department - Consular Affairs
Service Type: Government Agency
Description: Provides diplomatic services and visa issuance through U.S. embassies and consulates worldwide.
Website: https://travel.state.gov
Phone: 1-888-874-7875
Email: (leave blank)
Address: Multiple locations in U.S. embassies worldwide
Country Coverage: Global
Services Offered: Visa interviews, passport services, emergency assistance, immigrant visa processing
Is Featured: ✓ (checked)
```

**Example 3: RAICES (Legal Aid)**
```
Name: RAICES (Refugee and Immigrant Center for Education and Legal Services)
Service Type: Legal Aid Organization
Description: Nonprofit providing legal services and immigration assistance to refugees and immigrants.
Website: https://www.raicestexas.org
Phone: Contact via website
Email: info@raicestexas.org
Address: Texas locations
Country Coverage: Texas, USA
Services Offered: Legal representation, asylum cases, family reunification, bond hearings, detention support
Is Featured: ✓ (checked)
```

### Step 3: Add Legal Resources via Django Admin

1. Go to `http://your-domain/admin/`
2. Navigate to **Communities > Legal Immigration Resources**
3. Click **Add Legal Immigration Resource** and fill in examples:

**Example 1: Green Card Basics**
```
Title: Understanding Green Cards and Permanent Residency
Category: Green Card & Permanent Residency
Content: [Comprehensive content about green cards, eligibility, application process, etc.]
External URL: https://www.uscis.gov/green-card
Related Service: USCIS (U.S. Citizenship & Immigration Services)
Keywords: green card, permanent residency, immigrant visa, employment-based, family-based
Is Critical: Not checked
```

**Example 2: Your Rights**
```
Title: Know Your Rights as an Immigrant
Category: Legal Rights
Content: [Content about constitutional rights, right to remain silent, legal representation, etc.]
External URL: (blank)
Related Service: (any legal aid organization)
Keywords: rights, constitution, legal representation, due process
Is Critical: ✓ (checked)
```

### Step 4: Update Navigation Menu

Add links to the new pages in your base template (`base.html`):

```html
<!-- In your main navigation menu -->
<li class="nav-item dropdown">
    <a class="nav-link dropdown-toggle" href="#" id="immigrationDropdown" role="button">
        Immigration & Legal
    </a>
    <div class="dropdown-menu" aria-labelledby="immigrationDropdown">
        <a class="dropdown-item" href="{% url 'legal_immigration' %}">
            <i class="fas fa-book"></i> Immigration Guidance
        </a>
        <a class="dropdown-item" href="{% url 'consular_services' %}">
            <i class="fas fa-building"></i> Consular Services
        </a>
        <a class="dropdown-item" href="{% url 'legal_resources' %}">
            <i class="fas fa-file-alt"></i> Legal Resources
        </a>
    </div>
</li>
```

## URL Structure

Once set up, the following URLs will be available:

| URL | Purpose |
|-----|---------|
| `/community/legal-immigration/` | Main immigration guidance page with tabs |
| `/community/consular-services/` | Searchable list of all consular services |
| `/community/consular-services/<id>/` | Detail page for a specific service |
| `/community/legal-resources/` | Searchable list of legal resources |
| `/community/legal-resources/<id>/` | Detail page for a specific resource |

## Features

### Legal Immigration Guidance Page
- **4 Tabs:**
  1. Immigration Basics - Visa types, green cards, citizenship, employment
  2. Legal Rights - Constitutional rights, asylum, family sponsorship, deportation defense
  3. Consular Services - Links to all major government services and agencies
  4. FAQs - Frequently asked questions with expandable answers

### Consular Services
- Search by name or service type
- Filter by service category (Government, Legal Aid, Non-Profit, Consultation)
- Filter by country coverage
- Direct contact information (phone, email, website)
- Links to related legal resources
- Pagination (10 per page)

### Legal Resources
- Search by title and keywords
- Filter by category (Visa, Green Card, Citizenship, Employment, Asylum, Deportation, Family, Rights)
- Mark critical information prominently
- Link resources to related consular services
- Related resources suggestions
- Pagination (15 per page)

## Admin Dashboard Features

### Managing Consular Services
- **List View:** See all services with their type, coverage, and featured status
- **Filters:** Quick filter by service type or featured status
- **Search:** Find services by name, description, or services offered
- **Add/Edit:** Organized form with sections for basic info, contact details, and settings

### Managing Legal Resources
- **List View:** See all resources with category and critical status
- **Filters:** Quick filter by category or critical status
- **Search:** Find resources by title, content, or keywords
- **Add/Edit:** Form organized by content sections

## Search and Filter Capabilities

### Consular Services
```
Search: Name, description, services offered
Filters: Service Type, Country Coverage
Sorting: Featured first, then by update date
```

### Legal Resources
```
Search: Title, keywords
Filters: Category
Sorting: Critical first, then by update date
```

## Database Schema

### ConsularService Fields
```python
- name (CharField, max_length=255)
- service_type (CharField, choices: government, legal_aid, nonprofit, consultation)
- description (TextField)
- website (URLField, optional)
- phone (CharField, optional)
- email (EmailField, optional)
- address (TextField, optional)
- country_coverage (CharField, max_length=255)
- services_offered (TextField)
- is_featured (BooleanField, default=False)
- created_at (DateTimeField, auto_now_add=True)
- updated_at (DateTimeField, auto_now=True)
```

### LegalImmigrationResource Fields
```python
- title (CharField, max_length=255)
- category (CharField, choices: visa, green_card, citizenship, employment, asylum, deportation, family, rights)
- content (TextField)
- external_url (URLField, optional)
- related_service (ForeignKey to ConsularService, optional)
- keywords (CharField, max_length=255)
- is_critical (BooleanField, default=False)
- created_at (DateTimeField, auto_now_add=True)
- updated_at (DateTimeField, auto_now=True)
```

## Customization

### Styling
All templates use Bootstrap 5. Customize by modifying:
- Color scheme in card headers
- Badge colors for categories
- Button styles

### Adding More Services
1. Log in to Django admin
2. Go to Consular Services
3. Click "Add Consular Service"
4. Fill in all fields
5. Click "Save"

### Adding More Resources
1. Log in to Django admin
2. Go to Legal Immigration Resources
3. Click "Add Legal Immigration Resource"
4. Fill in the content and metadata
5. Optionally link to a consular service
6. Click "Save"

## Troubleshooting

### Migration Issues
If you get migration errors:
```bash
# Reset migrations (careful - only in development)
python manage.py migrate communities zero
python manage.py migrate communities
```

### Missing URLs
Make sure your `communities/urls.py` is included in your main `urls.py`:
```python
path('community/', include('communities.urls')),
```

### Template Not Found
Ensure templates are in the correct location:
```
communities/templates/
├── legal_immigration.html
├── consular_services_list.html
├── consular_service_detail.html
├── legal_resources.html
└── legal_resource_detail.html
```

### Search Not Working
Ensure `django.db.models` is imported in `views.py`:
```python
from django.db.models import Q
```

## Next Steps

1. **Add More Content:** Use Django admin to add comprehensive consular service listings and legal resources
2. **Localization:** Translate content for multiple languages
3. **Email Integration:** Set up email notifications for resource updates
4. **Statistics:** Track which resources are most accessed
5. **User Feedback:** Add rating/review system for resources

## Support

For questions or issues with setup, contact your Django administrator or consult the main project documentation.
