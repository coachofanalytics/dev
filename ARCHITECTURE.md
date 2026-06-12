# DC48K Project Architecture Documentation

**Project Name**: DC48K (Diaspora County 48 Kenya)  
**Framework**: Django 3.0.7  
**Python Version**: 3.8+  
**Database**: PostgreSQL (Production/Staging), SQLite (Development)  
**Version**: 26.05_DC48K_UAT_NF  
**Last Updated**: 2026-05-26

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Directory Structure](#directory-structure)
3. [Application Architecture](#application-architecture)
4. [Models & Database Design](#models--database-design)
5. [Views Architecture](#views-architecture)
6. [URL Routing](#url-routing)
7. [Templates Structure](#templates-structure)
8. [Forms System](#forms-system)
9. [Admin Configuration](#admin-configuration)
10. [Static Files & Media](#static-files--media)
11. [Middleware & Utilities](#middleware--utilities)
12. [Feature Modules](#feature-modules)
13. [Authentication System](#authentication-system)
14. [Email System](#email-system)
15. [Development Guidelines](#development-guidelines)
16. [Deployment Architecture](#deployment-architecture)
17. [Future Expansion Plan](#future-expansion-plan)

---

## Project Overview

### Purpose
DC48K is a comprehensive Django web application serving the Kenyan diaspora community globally. It provides multiple services including:
- Governance & Leadership Management
- Healthcare Information & Support
- Education & Scholarship Programs
- Financial Services & Investment Guidance
- Crisis Management & Support
- Community Engagement & Networking
- News & Content Management
- User Accounts & Membership Management
- Donation & Payment Processing

### Architecture Philosophy
- **Modular Design**: Separate apps for distinct domains (main, accounts, finance)
- **Django Best Practices**: MVC pattern with clear separation of concerns
- **Scalability**: Multi-app structure allows independent feature scaling
- **Extensibility**: Feature-based URL namespacing enables future feature additions
- **Security**: Custom authentication backend with django-allauth integration

### Key Technologies
```
Backend:
- Django 3.0.7 (Web Framework)
- PostgreSQL (Database)
- Gunicorn (WSGI Server)
- WhiteNoise (Static Files)

Frontend:
- HTML5 / CSS3
- Bootstrap 4 & 5
- Tailwind CSS (CDN)
- JavaScript (Vanilla + jQuery)
- Swiper.js (Carousels)
- FontAwesome (Icons)

Third-party Services:
- Stripe (Payments)
- Google OAuth (Authentication)
- Facebook OAuth (Authentication)
- AllAuth (Social Authentication)
- SendGrid/SMTP (Email)
- AWS S3 (Media Storage in Production)

Development:
- Django Debug Toolbar
- Coverage.py (Testing)
- Black (Code Formatting)
```

---

## Directory Structure

```
coda_project/
├── coda_project/                    # Project Configuration
│   ├── __init__.py
│   ├── settings.py                  # Main Django settings
│   ├── urls.py                      # Root URL configuration
│   ├── wsgi.py                      # WSGI entry point
│   └── media/                       # Project-level media storage
│
├── main/                            # Core Application (1583 lines)
│   ├── migrations/                  # Database migrations
│   │   ├── 0001_initial.py
│   │   ├── 0006_category_subscriber_newsarticle.py    # News feature
│   │   ├── 0010_legalservice.py
│   │   ├── 0012_communitymember...py                  # Community feature
│   │   ├── 0013_healthcare_models.py                  # Healthcare feature
│   │   ├── 0014_crisis_safety_alert...py              # Crisis management
│   │   ├── 0015_education_scholarship...py            # Education feature
│   │   └── 0016_community_support.py                  # Community support
│   │
│   ├── templates/main/
│   │   ├── base_templates/
│   │   │   ├── base.html                              # Master template
│   │   │   └── new_base.html                          # Alternative base
│   │   │
│   │   ├── navbar_templates/
│   │   │   └── navbar.html                            # Navigation component
│   │   │
│   │   ├── footer_templates/
│   │   │   └── new_footer.html                        # Footer component
│   │   │
│   │   ├── news/                                      # News feature templates (16 files)
│   │   │   ├── home.html
│   │   │   ├── news_listing.html
│   │   │   ├── article_detail.html
│   │   │   ├── article_form.html
│   │   │   ├── dashboard.html
│   │   │   ├── category_*.html
│   │   │   └── ...
│   │   │
│   │   ├── communities/                               # Community feature (25+ files)
│   │   │   ├── home.html
│   │   │   ├── forum_home.html
│   │   │   ├── forum_category.html
│   │   │   ├── view_post.html
│   │   │   ├── create_post.html
│   │   │   ├── event_calendar.html
│   │   │   ├── event_detail.html
│   │   │   ├── directory.html
│   │   │   └── ...
│   │   │
│   │   ├── consular/                                  # Consular service templates (10+ files)
│   │   ├── healthcare/                                # Healthcare templates (8+ files)
│   │   ├── education/                                 # Education templates (12+ files)
│   │   ├── crisis/                                    # Crisis management templates (6+ files)
│   │   ├── financial/                                 # Financial services templates (7+ files)
│   │   │
│   │   └── generic_pages/
│   │       ├── about.html
│   │       ├── about_templates/
│   │       └── ...
│   │
│   ├── static/main/
│   │   ├── css/
│   │   │   ├── main.css
│   │   │   ├── navbar.css
│   │   │   ├── governance.css
│   │   │   ├── messages.css
│   │   │   └── ...
│   │   ├── js/
│   │   │   ├── main.js
│   │   │   ├── messages.js
│   │   │   └── ...
│   │   └── img/
│   │       ├── dc48k_logo.png
│   │       ├── favicon.png
│   │       └── ...
│   │
│   ├── templatetags/
│   │   ├── __init__.py
│   │   └── custom_filters.py                          # Custom template filters
│   │
│   ├── models.py                    # 1583 lines - Core data models
│   ├── views.py                     # 2746 lines - View logic
│   ├── forms.py                     # Form definitions
│   ├── urls.py                      # Main app URL routes
│   ├── urls_communities.py          # Community feature URLs
│   ├── news_urls.py                 # News feature URLs
│   ├── admin.py                     # Django admin configuration
│   ├── apps.py                      # App configuration
│   ├── signals.py                   # Django signals
│   ├── context_processors.py        # Template context processors
│   ├── filters.py                   # Django filters for views
│   ├── ai_services.py               # AI integration (Groq)
│   ├── utils.py                     # Utility functions
│   ├── db.py                        # Database utilities
│   └── tests.py                     # Unit tests
│
├── accounts/                        # Authentication & User Management
│   ├── migrations/                  # User model migrations
│   ├── templates/accounts/
│   │   ├── registration/
│   │   │   ├── login.html
│   │   │   ├── signup.html / joins.html
│   │   │   ├── password_reset.html
│   │   │   ├── password_reset_confirm.html
│   │   │   ├── password_reset_done.html
│   │   │   ├── logout.html
│   │   │   └── ...
│   │   └── profile/
│   │       └── profile.html
│   │
│   ├── models.py                    # CustomerUser model (255 lines)
│   ├── views.py                     # Auth views
│   ├── forms.py                     # Auth forms
│   ├── urls.py                      # Auth routes
│   ├── admin.py                     # User admin config
│   ├── choices.py                   # User category choices
│   ├── decorators.py                # Custom decorators
│   ├── signals.py                   # User signals
│   ├── modelmanager.py              # Custom managers
│   ├── utils.py                     # Auth utilities
│   ├── tests/
│   │   ├── test_forms.py
│   │   ├── test_models.py
│   │   └── test_views.py
│   └── tests.py
│
├── finance/                         # Payment & Donation Management
│   ├── migrations/                  # Finance model migrations
│   ├── management/
│   │   └── commands/                # Custom Django commands
│   │
│   ├── templates/finance/
│   │   ├── donation.html
│   │   ├── pay_online.html
│   │   ├── partial_payment.html
│   │   ├── payment_success.html
│   │   └── ...
│   │
│   ├── static/finance/css/
│   │   ├── donation.css
│   │   ├── pay_online.css
│   │   ├── partial_payment.css
│   │   └── ...
│   │
│   ├── models.py                    # Payment models (493 lines)
│   ├── views.py                     # Payment views
│   ├── forms.py                     # Payment forms
│   ├── urls.py                      # Finance routes
│   ├── admin.py                     # Finance admin
│   ├── signals.py                   # Payment signals
│   ├── modelmanager.py              # Custom managers
│   ├── utils.py                     # Finance utilities
│   └── tests.py
│
├── mail/                            # Email Service (Optional)
│   └── __init__.py
│
├── media/                           # User-uploaded Media
│   ├── news_images/
│   ├── gallery/
│   ├── people/                      # Team member images
│   ├── history_images/
│   ├── img/
│   ├── background/
│   └── ...
│
├── static/                          # Project-level static files
│   ├── admin/
│   ├── community/
│   ├── facebook/
│   ├── finance/
│   ├── flags/
│   ├── main/
│   └── mppt/
│
├── staticfiles/                     # Collected static files (Production)
│   └── [Compiled static assets]
│
├── templates/                       # Project-level templates
│   ├── email/
│   │   └── [Email templates]
│   └── [Shared templates]
│
├── venv/                            # Python virtual environment
│   ├── Include/
│   ├── Lib/
│   ├── Scripts/
│   └── pyvenv.cfg
│
├── manage.py                        # Django management script
├── requirements.txt                 # Python dependencies
├── .gitignore                       # Git ignore rules
├── .env / .env.example              # Environment variables
├── README.md                        # Project README
├── ARCHITECTURE.md                  # This file
└── REQUIREMENT_*.md                 # Feature requirements
```

---

## Application Architecture

### Three-Tier Application Structure

```
┌─────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                    │
│  (Templates, Static Files, JavaScript, CSS)             │
├─────────────────────────────────────────────────────────┤
│                    BUSINESS LOGIC LAYER                  │
│  (Views, Forms, ViewSets, Signal Handlers)              │
├─────────────────────────────────────────────────────────┤
│                      DATA ACCESS LAYER                   │
│  (Models, QuerySets, Custom Managers)                   │
├─────────────────────────────────────────────────────────┤
│                  PERSISTENCE LAYER                       │
│  (PostgreSQL Database)                                  │
└─────────────────────────────────────────────────────────┘
```

### App Dependency Graph

```
coda_project (Settings & URLs)
    │
    ├── main (CORE APP)
    │   ├── Models: Page, Description, Content, Assets, Feedback, Service, SubService
    │   ├── News Feature: Category, NewsArticle, Subscriber (1 app, 3 models)
    │   ├── Community Feature: CommunityMember, DirectoryProfile, CommunityPost, 
    │   │                      CommentP, EventCalendar, ForumCategory, ContactMessage
    │   ├── Healthcare Feature: HealthcareProvider, HealthcareResource, 
    │   │                       HealthcareAppointment, HealthcareFAQ
    │   ├── Education Feature: Scholarship, TrainingCourse, EducationResource
    │   ├── Crisis Feature: SafetyAlert, CrisisSafetyAlertSubscription
    │   ├── Financial Feature: LegalService
    │   ├── Governance: Governance, Governance model links to CustomUser
    │   └── Gallery, Donations, Feedback, ContactUs
    │
    ├── accounts (AUTH APP)
    │   ├── Extends: CustomUser (AbstractUser)
    │   ├── Dependencies: Region, Chapter (from accounts)
    │   └── Related: django.contrib.auth Groups, Permissions
    │
    └── finance (PAYMENTS APP)
        ├── Models: Donation, PartialPayment, MembershipPayment
        ├── Depends on: CustomUser (FK)
        └── Integrates: Stripe API
```

---

## Models & Database Design

### Main App Models (1583 lines)

#### 1. **Foundational Models**
```python
Page
├── page_name (CharField)
└── descriptions (OneToMany) → Description

Description
├── page (FK → Page)
├── name (CharField)
└── content (TextField)

Content
├── section (ChoiceField: Our Story, Newsletter, Blog)
├── title (CharField)
├── description (TextField)
└── link (URLField)

Assets
├── name (CharField)
├── category (CharField: background, etc)
├── description (TextField)
└── image_url (CharField)
```

#### 2. **Contact & Feedback Models**
```python
Feedback
├── user (FK → CustomUser, null=True)
├── topic (CharField)
├── description (TextField)
└── is_active (BooleanField)

ContactUs
├── name (CharField)
├── email (EmailField)
├── phone_number (CharField)
├── message (TextField)
├── submitted_at (DateTimeField, auto_now_add)
└── is_resolved (BooleanField)

ContactMessage
├── name (CharField)
├── email (EmailField)
├── message (TextField)
└── submitted_at (DateTimeField)
```

#### 3. **Service Models**
```python
Service
├── title (CharField)
└── description (TextField)

SubService
├── service (FK → Service)
├── title (CharField)
└── description (TextField)
```

#### 4. **News & Content Models**
```python
Category
├── name (CharField, unique)
├── slug (SlugField, auto-generated, unique)
├── description (TextField)
└── created_at (DateTimeField)

NewsArticle
├── category (FK → Category)
├── title (CharField)
├── slug (SlugField, unique)
├── author (CharField)
├── featured_image (ImageField)
├── content (TextField)
├── status (ChoiceField: DRAFT, PUBLISHED)
├── ai_summary (TextField, auto-generated)
├── is_breaking (BooleanField)
├── created_at (DateTimeField)
├── updated_at (DateTimeField)
└── views (PositiveBigIntegerField)

Subscriber
├── email (EmailField, unique)
├── is_active (BooleanField)
├── conf_token (CharField, UUID)
├── confirmed (BooleanField)
└── subscribed_at (DateTimeField)
```

#### 5. **Team & Leadership Models**
```python
Team
├── name (CharField)
├── leadership (ChoiceField: Local, Global)
├── facebook_link (URLField)
├── role (ChoiceField: Governor, Deputy, Regional Coordinator, Team Member)
├── region (CharField)
├── image (ImageField)
└── bio (TextField)

Governance
├── governance_category (ChoiceField: Global Executive, Regional, County Assembly)
├── title (CharField)
├── description (TextField)
├── members (FK → CustomUser)
├── region (FK → Region)
├── chapter (FK → Chapter)
├── image (ImageField)
├── slug (SlugField, unique, auto-generated)
├── created_at (DateTimeField)
├── updated_at (DateTimeField)
└── ui_order (IntegerField, for sorting)
```

#### 6. **Gallery Models**
```python
Gallery
├── title (CharField)
├── description (TextField)
├── image (ImageField)
├── uploaded_at (DateTimeField)
└── event_date (DateField)

Gallery_image (duplicate/alternate)
├── title (CharField)
├── description (TextField)
├── image (ImageField)
├── uploaded_at (DateTimeField)
└── event_date (DateField)
```

#### 7. **Donation Models**
```python
Donation_organisation
├── user (FK → CustomUser)
├── donor_name (CharField)
├── email (EmailField)
├── amount (DecimalField)
├── message (TextField)
└── created_at (DateTimeField)

Donation_organization (alternate/newer)
├── donor_name (CharField)
├── email (EmailField)
├── amount (DecimalField)
├── message (TextField)
└── created_at (DateTimeField)
```

#### 8. **Healthcare Feature Models**
```python
HealthcareProvider
├── name (CharField)
├── specialization (CharField)
├── region (FK → Region)
├── contact_info (TextField)
└── verified (BooleanField)

HealthcareResource
├── title (CharField)
├── description (TextField)
├── resource_type (ChoiceField)
├── link (URLField)
└── created_at (DateTimeField)

HealthcareAppointment
├── user (FK → CustomUser)
├── provider (FK → HealthcareProvider)
├── date (DateTimeField)
├── status (ChoiceField)
└── notes (TextField)

HealthcareFAQ
├── question (CharField)
├── answer (TextField)
└── category (CharField)
```

#### 9. **Community Feature Models**
```python
CommunityMember
├── user (FK → CustomUser)
├── join_date (DateTimeField)
├── role (ChoiceField)
└── is_active (BooleanField)

DirectoryProfile
├── user (FK → CustomUser)
├── bio (TextField)
├── skills (TextField)
├── location (CharField)
├── image (ImageField)
├── is_public (BooleanField)
└── updated_at (DateTimeField)

ForumCategory
├── name (CharField)
├── description (TextField)
├── order (IntegerField)
└── is_active (BooleanField)

CommunityPost
├── author (FK → CustomUser)
├── category (FK → ForumCategory)
├── title (CharField)
├── content (TextField)
├── created_at (DateTimeField)
├── updated_at (DateTimeField)
└── is_pinned (BooleanField)

CommentP (Post Comments)
├── author (FK → CustomUser)
├── post (FK → CommunityPost)
├── content (TextField)
├── created_at (DateTimeField)
└── updated_at (DateTimeField)

EventCalendar
├── title (CharField)
├── description (TextField)
├── date (DateTimeField)
├── location (CharField)
├── organizer (FK → CustomUser)
├── attendees (ManyToMany → CustomUser)
├── image (ImageField)
└── status (ChoiceField)
```

#### 10. **Education Feature Models**
```python
Scholarship
├── title (CharField)
├── description (TextField)
├── amount (DecimalField)
├── deadline (DateField)
├── requirements (TextField)
├── category (CharField)
└── is_active (BooleanField)

TrainingCourse
├── title (CharField)
├── description (TextField)
├── duration (CharField)
├── instructor (CharField)
├── start_date (DateField)
├── end_date (DateField)
├── capacity (IntegerField)
├── enrolled_count (IntegerField)
└── is_active (BooleanField)

EducationResource
├── title (CharField)
├── description (TextField)
├── resource_type (ChoiceField)
├── link (URLField)
└── category (CharField)
```

#### 11. **Crisis Management Models**
```python
SafetyAlert
├── title (CharField)
├── description (TextField)
├── severity (ChoiceField: Low, Medium, High, Critical)
├── region (FK → Region)
├── created_by (FK → CustomUser)
├── created_at (DateTimeField)
└── is_active (BooleanField)

CrisisSafetyAlertSubscription
├── user (FK → CustomUser)
├── region (FK → Region)
├── is_active (BooleanField)
└── subscribed_at (DateTimeField)
```

#### 12. **Financial Models**
```python
LegalService
├── title (CharField)
├── description (TextField)
├── provider (CharField)
└── region (CharField)
```

### Accounts App Models (255 lines)

#### CustomUser (extends AbstractUser)
```python
CustomerUser (AbstractUser)
├── Base fields from AbstractUser:
│   ├── username, password, email
│   ├── first_name, last_name
│   ├── is_staff, is_active, last_login
│   └── date_joined
│
├── Custom fields:
│   ├── category (IntegerField, choices)
│   ├── is_admin (BooleanField)
│   ├── is_member (BooleanField)
│   ├── email_verified (BooleanField)
│   ├── verification_token (UUIDField)
│   ├── phone (CharField, unique)
│   ├── country (CountryField)
│   ├── state (CharField)
│   ├── city (CharField)
│   └── groups (M2M → Group)
│
├── Methods:
│   ├── get_category_display_name()
│   ├── get_subcategory_display_name()
│   ├── full_name (property)
│   ├── user_details (property)
│   ├── is_recent (property)
│   └── member_number (property)
│
└── Meta:
    ├── verbose_name_plural = "Users"
    └── ordering = ["-id"]
```

#### Region (from accounts context)
```python
Region
├── name (CharField)
├── description (TextField)
└── code (CharField, optional)
```

#### Chapter (from accounts context)
```python
Chapter
├── name (CharField)
├── region (FK → Region)
└── code (CharField, optional)
```

### Finance App Models (493 lines)

```python
Donation
├── user (FK → CustomUser)
├── amount (DecimalField)
├── payment_method (CharField)
├── status (ChoiceField)
├── transaction_id (CharField)
├── created_at (DateTimeField)
└── updated_at (DateTimeField)

PartialPayment
├── user (FK → CustomUser)
├── amount (DecimalField)
├── balance (DecimalField)
├── status (ChoiceField)
├── created_at (DateTimeField)
└── due_date (DateField)

MembershipPayment
├── user (FK → CustomUser)
├── amount (DecimalField)
├── payment_date (DateField)
├── status (ChoiceField)
├── transaction_id (CharField)
└── next_renewal_date (DateField)
```

---

## Views Architecture

### View Organization (2746 lines in views.py)

#### 1. **Generic Page Views**
```python
layout                          # Homepage/Landing page
about                          # About page
governance_list                # List all governance members
governance_detail              # Single governance member detail
contact_us                     # Contact form handling
get_help                       # Get help page
```

#### 2. **News Feature Views**
```python
LandingPageView (TemplateView)
├── Displays news landing page

ArticleHomeView (ListView)
├── List all articles with pagination (7 per page)
├── Filtering by status (PUBLISHED only)

ArticleDetailView (DetailView)
├── Show single article with related articles
├── Increment view counter

ArticleCreateView (LoginRequiredMixin, CreateView)
├── Create new article

ArticleEditView (UpdateView)
├── Edit existing article

ArticleDeleteView (DeleteView)
├── Delete article with confirmation

CategoryArticleListView (ListView)
├── List articles by category (6 per page)

CategoryCreateView, CategoryEditView, CategoryDeleteView
├── CRUD operations for categories

AdminDashboardView (TemplateView)
├── Dashboard with article stats

subscribe (Function View)
├── POST-only: Create subscriber
├── Send verification email

confirm_email (Function View)
├── Confirm email subscription via token
```

#### 3. **Community Feature Views** (main/views.py)
```python
communities_home                # Community home page
communities_forum_home          # Forum listing
communities_forum_category      # Forum posts by category
communities_view_post           # Single post detail
communities_create_post         # Create new post
communities_delete_post         # Delete post
communities_comment_post        # Comment on post
communities_directory           # Member directory
communities_directory_detail    # Single member profile
communities_join_directory      # Join directory
communities_event_calendar      # Event listing
communities_event_detail        # Single event detail
communities_create_event        # Create event
communities_edit_event          # Edit event
communities_delete_event        # Delete event
communities_contact_form        # Contact form
```

#### 4. **Service Feature Views**
```python
consular_service               # Consular services page
healthcare_service            # Healthcare page
healthcare_details            # Healthcare details
education_service             # Education page
education_details             # Education details
education_scholarship         # Scholarship listing
scholarship_apply             # Apply for scholarship
crisis_management             # Crisis management page
crisis_alerts                 # Safety alerts
financial_service            # Financial services
financial_legal_service      # Legal services
```

#### 5. **Error Handling Views**
```python
hendler400 (sic)              # Bad Request
hendler403                    # Forbidden
hendler300                    # Multiple Choices (?)
hendler500                    # Server Error
```

### View Patterns Used

#### Class-Based Views (CBV)
```python
from django.views.generic import (
    TemplateView, ListView, DetailView,
    CreateView, UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin

class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = NewsArticle
    form_class = ArticleForm
    template_name = 'main/news/article_form.html'
    success_url = reverse_lazy('news:dashboard')
    
    def form_valid(self, form):
        form.instance.author = self.request.user.username
        return super().form_valid(form)
```

#### Function-Based Views
```python
def subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        subscriber, created = Subscriber.objects.get_or_create(email=email)
        if created:
            # Send verification email
            send_mail(...)
        return redirect('news:home')
```

#### Mixins Used
- `LoginRequiredMixin` - Require authenticated users
- `UserPassesTestMixin` - Custom permission checks

---

## URL Routing

### URL Structure Hierarchy

```
coda_project/urls.py (ROOT)
├── /admin/                          → Django admin
├── /static/                         → Static files
├── /media/                          → User uploads
│
├── Password Reset URLs:
│   ├── /otp-reset/
│   ├── /password-reset/
│   ├── /password-reset-email/
│   ├── /password-reset-confirm/<uidb64>/<token>/
│   ├── /password-reset/done
│   └── /reset/done/
│
├── Social/Account URLs:
│   ├── /accounts/social/custom_login/
│   ├── /social_accounts/signup/
│   ├── /social_accounts/login/
│   └── /social_accounts/                            → AllAuth
│
├── Feature URLs:
│   ├── "" → main.news_urls (namespace='news')
│   │   ├── /news/                           → LandingPageView
│   │   ├── /news/details/                   → ArticleHomeView (list)
│   │   ├── /news/details/<slug>/            → ArticleDetailView
│   │   ├── /news/subscribe/                 → subscribe (POST)
│   │   ├── /confirm/<token>/                → confirm_email
│   │   ├── /news/dashboard/                 → AdminDashboardView
│   │   ├── /dashboard/article<id>/edit/     → ArticleEditView
│   │   ├── /dashboard/article/add/          → ArticleCreateView
│   │   ├── /article/<id>/delete/            → ArticleDeleteView
│   │   └── /category/<slug>/                → CategoryArticleListView
│   │
│   ├── "" → main.urls (namespace='main')
│   │   ├── /                                → layout (homepage)
│   │   ├── /about/                          → about
│   │   ├── /governance/                     → governance_list
│   │   ├── /governance/<slug>/              → governance_detail
│   │   ├── /contact-us/                     → contact_us
│   │   ├── /get-help/                       → get_help
│   │   ├── /consular/                       → consular_service
│   │   ├── /healthcare/                     → healthcare_service
│   │   ├── /education/                      → education_service
│   │   ├── /crisis/                         → crisis_management
│   │   ├── /financial/                      → financial_service
│   │   └── [More routes...]
│   │
│   ├── /communities/ → main.urls_communities
│   │   ├── /communities/                    → communities_home
│   │   ├── /communities/forum/              → communities_forum_home
│   │   ├── /communities/forum/<category>/   → communities_forum_category
│   │   ├── /communities/post/<id>/          → communities_view_post
│   │   ├── /communities/post/create/        → communities_create_post
│   │   ├── /communities/directory/          → communities_directory
│   │   ├── /communities/events/             → communities_event_calendar
│   │   ├── /communities/event/<id>/         → communities_event_detail
│   │   └── [More routes...]
│   │
│   ├── /accounts/ → accounts.urls
│   │   ├── /accounts/login/                 → login
│   │   ├── /accounts/signup/                → join / signup
│   │   ├── /accounts/logout/                → logout
│   │   ├── /accounts/profile/               → profile
│   │   └── [More routes...]
│   │
│   └── /finance/ → finance.urls
│       ├── /finance/donation/               → donation
│       ├── /finance/pay-online/             → pay_online
│       ├── /finance/payment-success/        → payment_success
│       └── [More routes...]
```

### URL Namespacing

```python
# news_urls.py: app_name = 'news'
# Usage: {% url 'news:home' %}

# urls_communities.py: (no namespace defined)
# Usage: {% url 'communities:home' %}

# urls.py (main): namespace='main'
# Usage: {% url 'main:layout' %}

# urls.py (accounts): (no namespace)
# Usage: {% url 'accounts:login' %}

# urls.py (finance): name='finance'
# Usage: {% url 'finance:donation' %}
```

---

## Templates Structure

### Template Hierarchy

```
templates/
├── email/                                   # Email templates
│   ├── verification_email.html
│   ├── subscription_confirmed.html
│   └── ...
│
└── [Shared project templates]

main/templates/main/
├── base_templates/
│   ├── base.html                            # Master template
│   │   ├── {% load static %}
│   │   ├── <head>: CSS, metadata, Tailwind CDN
│   │   ├── {% include navbar %}
│   │   ├── {% block content %}
│   │   └── {% include footer %}
│   │
│   └── new_base.html                        # Alternative base
│
├── navbar_templates/
│   └── navbar.html
│       ├── Brand logo
│       ├── Navigation links (HOME, ABOUT, SERVICES, etc)
│       ├── Dropdown menus for multi-level nav
│       └── Auth-dependent links (LOGIN/LOGOUT)
│
├── footer_templates/
│   └── new_footer.html
│       ├── Quick links
│       ├── Contact info
│       ├── Social media
│       └── Copyright
│
├── news/                                    # News feature (16 templates)
│   ├── home.html                            # Landing page
│   ├── news_listing.html                    # Articles list
│   ├── article_detail.html                  # Single article
│   ├── article_form.html                    # Create/edit form
│   ├── article_confirm_delete.html
│   ├── category_form.html                   # Create/edit category
│   ├── category_articles.html               # Articles by category
│   ├── category_confirm_delete.html
│   ├── dashboard.html                       # Admin dashboard
│   ├── news_form.html                       # Alternative form
│   ├── news_list.html                       # Alternative list
│   └── ...
│
├── communities/                             # Community feature (25+ templates)
│   ├── home.html                            # Community home
│   ├── forum_home.html                      # Forum listing
│   ├── forum_category.html                  # Posts by category
│   ├── view_post.html                       # Single post
│   ├── create_post.html
│   ├── directory.html                       # Member directory
│   ├── member_directory.html
│   ├── event_calendar.html                  # Events listing
│   ├── event_detail.html
│   ├── create_event.html
│   ├── edit_event.html
│   ├── delete_event.html
│   ├── contact_form.html
│   ├── contact_response.html
│   └── ...
│
├── consular/                                # Consular service (10+ templates)
│   ├── consular_service.html
│   ├── book_consultation.html
│   ├── all_updates.html
│   └── ...
│
├── healthcare/                              # Healthcare feature (8+ templates)
│   ├── healthcare_service.html
│   ├── healthcare_details.html
│   └── ...
│
├── education/                               # Education feature (12+ templates)
│   ├── education_service.html
│   ├── scholarship_list.html
│   ├── scholarship_detail.html
│   ├── scholarship_apply.html
│   └── ...
│
├── crisis/                                  # Crisis management (6+ templates)
│   ├── crisis_management.html
│   ├── safety_alerts.html
│   └── ...
│
├── financial/                               # Financial services (7+ templates)
│   ├── financial_service.html
│   ├── legal_services.html
│   └── ...
│
└── generic_pages/
    ├── about.html                           # About page
    ├── about_templates/
    │   ├── history.html
    │   └── service.html
    └── [Other pages]
```

### Template Inheritance Strategy

```html
<!-- base.html -->
<!DOCTYPE html>
<html>
  <head>
    <title>{% block title %}DC48K{% endblock %}</title>
    {% block extra_css %}{% endblock %}
  </head>
  <body>
    {% include 'main/navbar_templates/navbar.html' %}
    <main>
      {% block content %}{% endblock %}
    </main>
    {% include 'main/footer_templates/new_footer.html' %}
    {% block extra_js %}{% endblock %}
  </body>
</html>

<!-- news/home.html -->
{% extends "main/base_templates/base.html" %}
{% block title %}News - DC48K{% endblock %}
{% block content %}
  <!-- News-specific content -->
{% endblock %}
```

### Template Context Processors

```python
# main/context_processors.py

def images(request):
    # Provide image context to all templates
    return {
        'logo_url': '/static/main/img/dc48k_logo.png',
        # ...
    }

def googledriveurl(request):
    # Provide Google Drive URLs for embedded content
    return {
        'drive_folder_url': 'https://drive.google.com/...',
        # ...
    }

# Usage in settings.py:
# TEMPLATES[0]['OPTIONS']['context_processors'] += [
#     'main.context_processors.images',
#     'main.context_processors.googledriveurl',
# ]
```

---

## Forms System

### Form Organization (forms.py)

```python
from django import forms
from .models import (
    Feedback, GetHelp, Governance, NewsArticle,
    CommunityMember, DirectoryProfile, CommunityPost,
    CommentP, EventCalendar, ContactMessage,
    Scholarship, TrainingCourse, HealthcareAppointment
)

class ContactForm(forms.ModelForm):
    # Contact form for Feedback model
    class Meta:
        model = Feedback
        fields = ['user', 'topic', 'description']
        labels = {
            'user': 'Staff/Employee',
            'topic': 'Type your topic',
            'description': 'Describe your issue',
        }

class GetHelpForm(forms.ModelForm):
    # Help resource form
    class Meta:
        model = GetHelp
        fields = ['title', 'content', 'link']

class GovernanceForm(forms.ModelForm):
    # Governance member form
    class Meta:
        model = Governance
        fields = [
            'governance_category', 'title', 'description',
            'members', 'region', 'chapter'
        ]

class ArticleForm(forms.ModelForm):
    # News article creation/editing
    class Meta:
        model = NewsArticle
        fields = [
            'category', 'title', 'slug', 'author',
            'featured_image', 'content', 'ai_summary',
            'is_breaking', 'status', 'views'
        ]
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
            'ai_summary': forms.Textarea(attrs={'rows': 3}),
        }

class CommunityJoinForm(forms.ModelForm):
    # Join community
    class Meta:
        model = CommunityMember
        fields = ['role']

class DirectoryProfileForm(forms.ModelForm):
    # Member directory profile
    class Meta:
        model = DirectoryProfile
        fields = ['bio', 'skills', 'location', 'image', 'is_public']

class CommunityPostForm(forms.ModelForm):
    # Create community post
    class Meta:
        model = CommunityPost
        fields = ['category', 'title', 'content']

class CommunityCommentForm(forms.ModelForm):
    # Comment on post
    class Meta:
        model = CommentP
        fields = ['content']

class CommunityEventForm(forms.ModelForm):
    # Create/edit event
    class Meta:
        model = EventCalendar
        fields = [
            'title', 'description', 'date',
            'location', 'image', 'status'
        ]
    
    def clean_date(self):
        # Validation: date must be in future
        date = self.cleaned_data['date']
        if date < timezone.now():
            raise forms.ValidationError("Event date must be in the future")
        return date

class CommunityContactForm(forms.ModelForm):
    # Contact through community
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']
```

### Form Features

- **ModelForm** integration with Django ORM models
- **Custom widgets**: TextArea sizing, date pickers
- **Validation**: Field-level and form-level validation
- **Error handling**: User-friendly error messages
- **CSRF protection**: Automatic via Django middleware

---

## Admin Configuration

### Django Admin Setup (admin.py)

```python
from django.contrib import admin
from .models import *

class DescriptionAdmin(admin.ModelAdmin):
    list_display = ("page", "name", "content")
    search_fields = ("page", "name")
    list_filter = ("name",)
    ordering = ("name",)

class DescriptionGovernance(admin.ModelAdmin):
    list_display = (
        "governance_category", "members", "title", "ui_order"
    )
    list_filter = ("governance_category",)

# Register all models
admin.site.register(Description, DescriptionAdmin)
admin.site.register(News)
admin.site.register(Gallery)
admin.site.register(ContactUs)
admin.site.register(GetHelp)
admin.site.register(Governance, DescriptionGovernance)
admin.site.register(Category)
admin.site.register(NewsArticle)
admin.site.register(Subscriber)

# Community models
admin.site.register(CommunityMember)
admin.site.register(DirectoryProfile)
admin.site.register(ForumCategory)
admin.site.register(CommunityPost)
admin.site.register(CommentP)
admin.site.register(EventCalendar)
admin.site.register(ContactMessage)

# Healthcare models
admin.site.register(HealthcareProvider)
admin.site.register(HealthcareResource)
admin.site.register(HealthcareAppointment)

# Education models
admin.site.register(Scholarship)
admin.site.register(TrainingCourse)

# Finance models (from finance app)
admin.site.register(Donation)
admin.site.register(PartialPayment)
admin.site.register(MembershipPayment)
```

### Admin Customization Features

- **list_display**: Columns shown in list view
- **search_fields**: Searchable fields
- **list_filter**: Filterable fields
- **ordering**: Default sort order
- **readonly_fields**: Read-only in edit form
- **fieldsets**: Organize form fields

---

## Static Files & Media

### Static Files Organization

```
main/static/main/
├── css/
│   ├── main.css                 # Main stylesheet
│   ├── navbar.css               # Navigation styles
│   ├── governance.css           # Governance page styles
│   ├── messages.css             # Message display styles
│   ├── communities.css          # Community section styles
│   ├── news.css                 # News page styles
│   └── [Feature-specific CSS]
│
└── js/
    ├── main.js                  # Main JavaScript
    ├── messages.js              # Message handling
    ├── communities.js           # Community interactions
    └── [Feature-specific JS]

finance/static/finance/css/
├── donation.css
├── pay_online.css
├── partial_payment.css
└── ...
```

### Media Files (User Uploads)

```
media/
├── news_images/                 # Article featured images
├── gallery/                     # Gallery images
├── people/                      # Team member photos
├── history_images/              # History timeline images
├── background/                  # Background images
├── img/                         # Miscellaneous images
└── [Feature-specific uploads]
```

### Static Files Collection

```bash
# Collect static files for production
python manage.py collectstatic --noinput

# Output directory: staticfiles/
# Used by WhiteNoise middleware for serving in production
```

---

## Middleware & Utilities

### Middleware Stack (settings.py)

```python
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',      # Static file serving
    'django.middleware.security.SecurityMiddleware',   # Security headers
    'django.contrib.sessions.middleware.SessionMiddleware',  # Sessions
    'django.middleware.common.CommonMiddleware',       # Common utilities
    'django.middleware.csrf.CsrfViewMiddleware',       # CSRF protection
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Auth
    'django.contrib.messages.middleware.MessageMiddleware',  # Messages
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # Clickjacking
    'allauth.account.middleware.AccountMiddleware',    # Social auth
]
```

### Utility Modules

#### main/utils.py
```python
# Email utilities
send_verification_email(user, token)
send_welcome_email(user)

# Data processing
generate_article_summary(content)
process_upload_image(file)

# Query helpers
get_featured_articles(count=5)
get_governance_by_region(region_id)
```

#### main/ai_services.py
```python
# AI integration (Groq API)
def generate_article_summary(content):
    """Generate AI summary using Groq API"""
    try:
        from groq import Groq
        # Generate summary
        return summary
    except ImportError:
        # Fallback: return first 200 chars
        return content[:200] + "..."
```

#### main/signals.py
```python
# Django signals for post-processing
from django.db.models.signals import post_save

@receiver(post_save, sender=NewsArticle)
def generate_summary_on_save(sender, instance, **kwargs):
    """Auto-generate AI summary when article is saved"""
    if not instance.ai_summary:
        instance.ai_summary = generate_article_summary(instance.content)
        instance.save()
```

#### main/filters.py
```python
# Django filters for querysets
class NewsArticleFilter(django_filters.FilterSet):
    class Meta:
        model = NewsArticle
        fields = ['category', 'status', 'is_breaking']
```

#### main/context_processors.py
```python
def images(request):
    """Provide image URLs to all templates"""
    return {'logo': '/static/main/img/dc48k_logo.png'}

def googledriveurl(request):
    """Provide Google Drive links"""
    return {'drive_url': 'https://drive.google.com/...'}
```

---

## Feature Modules

### Feature Architecture (7 Major Features)

Each feature is self-contained with:
- Models (stored in main/models.py)
- Views (main/views.py)
- Templates (main/templates/main/[feature]/)
- Forms (main/forms.py)
- URLs (main/urls.py or main/urls_communities.py)
- Migrations (main/migrations/)

#### Feature 1: **News Management**
```
URLs: /news/ → news_urls.py (namespace='news')
Models: Category, NewsArticle, Subscriber
Views: 13 views (CRUD, listing, subscription)
Templates: 16 template files
Forms: ArticleForm
Migration: 0006_category_subscriber_newsarticle.py
```

#### Feature 2: **Community Support**
```
URLs: /communities/ → urls_communities.py
Models: CommunityMember, DirectoryProfile, ForumCategory,
        CommunityPost, CommentP, EventCalendar, ContactMessage
Views: 16+ community views
Templates: 25+ template files
Forms: CommunityJoinForm, DirectoryProfileForm, CommunityPostForm,
       CommunityCommentForm, CommunityEventForm, CommunityContactForm
Migration: 0012_communitymember_communitypost_eventcalendar_and_more.py
           0016_community_support.py
```

#### Feature 3: **Healthcare Services**
```
URLs: /healthcare/ → urls.py
Models: HealthcareProvider, HealthcareResource, HealthcareAppointment, HealthcareFAQ
Views: Healthcare-specific views
Templates: 8+ template files
Migration: 0013_healthcare_models.py
```

#### Feature 4: **Education & Training**
```
URLs: /education/ → urls.py
Models: Scholarship, TrainingCourse, EducationResource
Views: Education-specific views (scholarship listing, apply, etc)
Templates: 12+ template files
Forms: ScholarshipApplyForm, TrainingCourseEnrollForm
Migration: 0015_education_scholarship_trainingcourse.py
```

#### Feature 5: **Crisis Management**
```
URLs: /crisis/ → urls.py
Models: SafetyAlert, CrisisSafetyAlertSubscription
Views: Crisis management views (alert listing, subscription)
Templates: 6+ template files
Migration: 0014_crisis_safety_alert_subscription.py
```

#### Feature 6: **Financial Services**
```
URLs: /financial/ → urls.py
Models: LegalService
Views: Financial/legal service views
Templates: 7+ template files
Migration: 0010_legalservice.py
```

#### Feature 7: **Consular Assistance**
```
URLs: /consular/ → urls.py
Views: Consular service views (consultation booking, updates)
Templates: 10+ template files
No dedicated models (uses generic contact forms)
```

---

## Authentication System

### Custom User Model (accounts/models.py)

```python
class CustomerUser(AbstractUser):
    """Extended user model for DC48K"""
    
    # Additional fields
    category = IntegerField(choices=CategoryChoices.choices)
    is_admin = BooleanField(default=False)
    is_member = BooleanField(default=False)
    email_verified = BooleanField(default=False)
    verification_token = UUIDField(unique=True)
    phone = CharField(unique=True)
    country = CountryField()
    state = CharField()
    city = CharField()
    
    # Custom manager
    objects = DepartmentManager()
```

### Authentication Backends

```python
# settings.py
AUTH_USER_MODEL = "accounts.CustomerUser"

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # Default
    'allauth.account.auth_backends.AuthenticationMiddleware',  # Social auth
)
```

### Social Authentication (AllAuth)

```python
# Installed apps
INSTALLED_APPS = [
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
]

# URLs
path('social_accounts/', include('allauth.urls')),

# Features
- OAuth login (Google, Facebook)
- Email verification
- Password reset
- Social account linking
```

### Login/Registration Flow

```
User Registration:
1. User clicks "Register" → accounts/joins.html
2. Fill registration form (username, email, password)
3. Submit → accounts.join (POST)
4. Create CustomUser
5. Send verification email
6. Redirect to login or auto-login

User Login:
1. User clicks "Login" → accounts/registration/login.html
2. Enter username/email + password
3. Submit → Django auth backend
4. Create session
5. Redirect to homepage or next=parameter

Social Login:
1. User clicks "Google" or "Facebook" button
2. Redirect to OAuth provider
3. User authorizes
4. Callback to /accounts/google/login/callback/
5. AllAuth creates/links CustomUser
6. Create session
7. Redirect to homepage
```

---

## Email System

### Email Configuration

```python
# settings.py (environment-dependent)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'noreply@dc48k.org'
```

### Email Templates

```
templates/email/
├── verification_email.html
├── subscription_confirmed.html
├── password_reset_email.html
├── welcome_email.html
└── ...
```

### Email Sending Patterns

```python
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# Simple email
send_mail(
    subject='Verify Your Email',
    message='Click link to verify',
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=['user@example.com'],
    fail_silently=False,
)

# HTML email with template
html_message = render_to_string('email/verification_email.html', {
    'user': user,
    'token': token,
})
text_message = strip_tags(html_message)

send_mail(
    subject='Verify Your Email',
    message=text_message,
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=[user.email],
    html_message=html_message,
    fail_silently=False,
)
```

---

## Development Guidelines

### Code Organization Principles

1. **Separation of Concerns**
   - Models: Data logic only
   - Views: Request/response handling
   - Forms: Data validation
   - Templates: Presentation logic

2. **DRY (Don't Repeat Yourself)**
   - Use base templates and includes
   - Create reusable utility functions
   - Use template tags for common patterns

3. **Naming Conventions**
   - Views: `feature_action` (e.g., `news_list`, `article_detail`)
   - Templates: `app_model_action.html`
   - URLs: lowercase with underscores
   - Models: PascalCase

4. **Testing**
   - Unit tests in app/tests.py
   - Test models, views, forms separately
   - Use Django TestCase for database tests
   - Aim for >80% code coverage

### Adding a New Feature

1. **Create Models** (main/models.py)
   ```python
   class NewFeature(models.Model):
       title = CharField(max_length=255)
       description = TextField()
       created_at = DateTimeField(auto_now_add=True)
   ```

2. **Create Migration**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Create Views** (main/views.py)
   ```python
   class NewFeatureListView(ListView):
       model = NewFeature
       template_name = 'main/newfeature/list.html'
       paginate_by = 10
   ```

4. **Create Forms** (main/forms.py)
   ```python
   class NewFeatureForm(ModelForm):
       class Meta:
           model = NewFeature
           fields = ['title', 'description']
   ```

5. **Create URLs** (main/urls.py)
   ```python
   path('newfeature/', views.NewFeatureListView.as_view(), name='newfeature_list'),
   ```

6. **Create Templates** (main/templates/main/newfeature/)
   ```html
   {% extends "main/base_templates/base.html" %}
   {% block content %}
       <!-- Feature content -->
   {% endblock %}
   ```

7. **Register in Admin** (main/admin.py)
   ```python
   admin.site.register(NewFeature)
   ```

8. **Update Navbar** (navbar.html) if needed
   ```html
   <li><a href="{% url 'main:newfeature_list' %}">New Feature</a></li>
   ```

### Common Code Patterns

```python
# Redirect with message
from django.contrib import messages

def save_view(request):
    form = MyForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Saved successfully!')
        return redirect('success_page')
    return render(request, 'form.html', {'form': form})

# Get object or 404
from django.shortcuts import get_object_or_404

def detail_view(request, pk):
    obj = get_object_or_404(Model, pk=pk)
    return render(request, 'detail.html', {'obj': obj})

# Pagination in ListView
class ListView(ListView):
    paginate_by = 10

# Multiple filters
def filtered_list(request):
    queryset = Article.objects.all()
    
    category = request.GET.get('category')
    if category:
        queryset = queryset.filter(category__name=category)
    
    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(status=status)
    
    return render(request, 'list.html', {'articles': queryset})
```

---

## Deployment Architecture

### Environment Configuration

```
Development (.env):
- DEBUG = True
- ENVIRONMENT = 'development'
- DATABASE: SQLite (db.sqlite3)
- SECRET_KEY = (development key)
- ALLOWED_HOSTS = ['localhost', '127.0.0.1']

Staging (.env):
- DEBUG = False
- ENVIRONMENT = 'staging'
- DATABASE: PostgreSQL (Heroku)
- SECRET_KEY = (secure key)
- ALLOWED_HOSTS = ['staging.dc48k.org']

Production (.env):
- DEBUG = False
- ENVIRONMENT = 'production'
- DATABASE: PostgreSQL (Production)
- SECRET_KEY = (secure key)
- ALLOWED_HOSTS = ['dc48k.org', 'www.dc48k.org']
- CDN: AWS S3 for media
```

### Deployment Stack

```
Architecture:
┌─────────────────────────────────────┐
│     Nginx (Reverse Proxy)           │
├─────────────────────────────────────┤
│  Gunicorn (WSGI Application Server) │
├─────────────────────────────────────┤
│     Django Application              │
├─────────────────────────────────────┤
│   PostgreSQL Database               │
├─────────────────────────────────────┤
│   AWS S3 (Media Storage)            │
│   CDN (Static Files)                │
└─────────────────────────────────────┘

Deployment Process:
1. Push code to GitHub
2. CI/CD Pipeline (GitHub Actions / Travis)
3. Run tests
4. Build Docker image
5. Push to container registry
6. Deploy to Heroku / AWS / DigitalOcean
7. Run migrations
8. Collect static files
9. Restart application

Static Files Strategy:
- WhiteNoise middleware for local serving
- AWS S3 for production media
- CDN caching for static assets
- collectstatic command for compilation
```

### Deployment Checklist

```
Pre-deployment:
☐ All tests passing
☐ Code review completed
☐ Security audit passed
☐ Database migration tested
☐ Environment variables configured
☐ Static files optimized
☐ Media backup created

Deployment:
☐ Pull latest code
☐ Install dependencies: pip install -r requirements.txt
☐ Migrate database: python manage.py migrate
☐ Collect static: python manage.py collectstatic --noinput
☐ Create superuser (if needed): python manage.py createsuperuser
☐ Start application: gunicorn coda_project.wsgi
☐ Verify health endpoint
☐ Run smoke tests

Post-deployment:
☐ Monitor error logs
☐ Test all features
☐ Verify email sending
☐ Check API endpoints
☐ Monitor performance
☐ Update status page
```

---

## Future Expansion Plan

### Planned Features

1. **Volunteer Management**
   - VolunteerOpportunity model
   - VolunteerApplication model
   - VolunteerProfile model
   - Volunteer matching algorithm
   - Volunteer hours tracking

2. **Marketplace**
   - Product/Service listing
   - Shopping cart
   - Order management
   - Vendor dashboard

3. **Live Events & Streaming**
   - Event management
   - Live streaming integration
   - Attendance tracking
   - Q&A functionality

4. **Mobile App**
   - React Native app
   - iOS/Android platforms
   - Offline capabilities
   - Push notifications

5. **AI Enhancements**
   - Chatbot for support
   - Content recommendation
   - Sentiment analysis
   - Predictive analytics

6. **Advanced Analytics**
   - User behavior tracking
   - Cohort analysis
   - Retention metrics
   - Revenue analytics

### Scalability Improvements

- **Caching Strategy**
  - Redis for session/cache layer
  - Django cache framework
  - Query optimization

- **Database Optimization**
  - Read replicas
  - Indexing strategy
  - Query analysis and optimization
  - Archival strategy for old data

- **API Development**
  - Django REST Framework
  - API versioning
  - Authentication (JWT tokens)
  - Rate limiting

- **Asynchronous Tasks**
  - Celery for background jobs
  - Email queuing
  - Report generation
  - Data processing

### Performance Optimization

```python
# Database optimization
from django.db.models import Prefetch

# Use select_related for ForeignKey
articles = NewsArticle.objects.select_related('category').all()

# Use prefetch_related for M2M
events = EventCalendar.objects.prefetch_related('attendees').all()

# Use only() and values() to reduce fields
users = CustomUser.objects.only('username', 'email')

# Database indexing
class NewsArticle(models.Model):
    slug = SlugField(db_index=True)
    created_at = DateTimeField(db_index=True)
```

---

## Quick Reference

### Important Files

| File | Purpose | Lines |
|------|---------|-------|
| coda_project/settings.py | Configuration | ~150 |
| coda_project/urls.py | Root routing | ~112 |
| main/models.py | Core data models | 1583 |
| main/views.py | Business logic | 2746 |
| main/forms.py | Data validation | ~200 |
| main/urls.py | App routing | ~100 |
| accounts/models.py | User model | 255 |
| finance/models.py | Payment models | 493 |

### Useful Commands

```bash
# Development
python manage.py runserver

# Database
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations

# Admin
python manage.py createsuperuser
python manage.py changepassword username

# Static files
python manage.py collectstatic --noinput

# Testing
python manage.py test
coverage run --source='.' manage.py test
coverage report

# Shell
python manage.py shell

# Database dump
python manage.py dumpdata > backup.json
python manage.py loaddata backup.json
```

### Git Branching Strategy

```
Main branches:
- main: Production-ready code
- develop: Integration branch
- 25.10_DC48K_UAT_EM: Parent/stable branch
- 26.05_DC48K_UAT_NF: Current development (combined features)

Feature branches:
- 26.05_DC48K_UAT_CONSULAR_NF
- 26.05_DC48K_UAT_HEALTHCARE_NF
- 26.05_DC48K_UAT_CRISIS_MANAGEMENT_NF
- 26.05_DC48K_UAT_EDUCATION_TRAINING_NF
- 26.05_DC48K_UAT_FINANCIAL_SERVICES_NF
- 26.05_DC48K_UAT_COMMUNITY_SUPPORT_NF
- 26.05_DC48K_UAT_NEWS_NF

Workflow:
feature → develop → main (production)
```

---

## Support & Resources

### Documentation Links
- [Django Official Docs](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Bootstrap 4 Docs](https://getbootstrap.com/docs/4.0/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)

### Team Contact
- Backend Lead: [Team Lead]
- Frontend Lead: [Team Lead]
- DevOps: [Team Lead]
- Project Manager: [PM Name]

### Common Issues & Solutions

**Issue**: Migrations not applying
```bash
# Solution: Check migration dependencies
python manage.py showmigrations
python manage.py migrate app_name --no-input
```

**Issue**: Static files not loading in production
```bash
# Solution: Collect static files
python manage.py collectstatic --noinput --clear
```

**Issue**: CustomUser not found
```bash
# Solution: Ensure AUTH_USER_MODEL is set in settings.py
AUTH_USER_MODEL = "accounts.CustomerUser"
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-05-26  
**Status**: Active  
**Maintained By**: Development Team

---

*This architecture document serves as the source of truth for the DC48K project structure and should be updated whenever significant architectural changes are made.*
