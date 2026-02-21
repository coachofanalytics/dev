# Legal & Immigration Guidance System - Architecture & Flow Diagram

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Frontend                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  /legal-immigration/          /consular-services/                  │
│  ┌────────────────────┐       ┌──────────────────┐                 │
│  │ Main Guidance Page │       │ Services List    │                 │
│  │                    │       │                  │                 │
│  │ - Immigration      │       │ - Search box     │                 │
│  │   Basics           │       │ - Filter by type │                 │
│  │ - Legal Rights     │       │ - Paginated      │                 │
│  │ - Consular Svcs    │       │ - Service cards  │                 │
│  │ - FAQs             │       │                  │                 │
│  └────────────────────┘       └──────────────────┘                 │
│          │                              │                           │
│          └──────────┬───────────────────┘                           │
│                     │                                               │
│  /consular-services/<id>/     /legal-resources/                    │
│  ┌────────────────────────┐   ┌──────────────────┐                │
│  │ Service Detail Page    │   │ Resources List   │                │
│  │                        │   │                  │                │
│  │ - Full description     │   │ - Search box     │                │
│  │ - Contact info         │   │ - Filter by cat. │                │
│  │ - Services offered     │   │ - Paginated      │                │
│  │ - Related Resources    │   │ - Resource cards │                │
│  └────────────────────────┘   └──────────────────┘                │
│                                       │                             │
│                   /legal-resources/<id>/                           │
│                   ┌──────────────────────┐                         │
│                   │ Resource Detail Page │                         │
│                   │                      │                         │
│                   │ - Full article       │                         │
│                   │ - Related service    │                         │
│                   │ - Similar resources  │                         │
│                   │ - External links     │                         │
│                   └──────────────────────┘                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

         │                              │
         ▼                              ▼

┌─────────────────────────────────────────────────────────────────────┐
│                    Django Views Layer                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  legal_immigration_guidance()          consular_services_list()    │
│  └─ Get featured services              └─ Get all services         │
│  └─ Get critical resources             └─ Apply filters            │
│  └─ Render 4-tab template              └─ Apply search             │
│                                         └─ Paginate                 │
│                                                                      │
│  consular_service_detail()             legal_resources()           │
│  └─ Get service by ID                  └─ Get all resources        │
│  └─ Get related resources              └─ Apply filters            │
│  └─ Render detail template             └─ Apply search             │
│                                         └─ Paginate                 │
│                                                                      │
│  legal_resource_detail()                                           │
│  └─ Get resource by ID                                             │
│  └─ Get related service                                            │
│  └─ Get similar resources                                          │
│  └─ Render detail template                                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

         │                              │
         ▼                              ▼

┌─────────────────────────────────────────────────────────────────────┐
│                   Django Models Layer                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────┐  ┌──────────────────────────────┐   │
│  │  ConsularService         │  │ LegalImmigrationResource     │   │
│  ├──────────────────────────┤  ├──────────────────────────────┤   │
│  │ - name                   │  │ - title                      │   │
│  │ - service_type (4 types) │  │ - category (8 categories)   │   │
│  │ - description            │  │ - content                    │   │
│  │ - website                │  │ - external_url               │   │
│  │ - phone                  │  │ - related_service (FK) ──┐  │   │
│  │ - email                  │  │ - keywords                   │   │
│  │ - address                │  │ - is_critical                │   │
│  │ - country_coverage       │  │ - created_at/updated_at      │   │
│  │ - services_offered       │  │                              │   │
│  │ - is_featured            │  │                              │   │
│  │ - created_at/updated_at  │  │                              │   │
│  └──────────────────────────┘  └──────────────────────────────┘   │
│        ▲                              │                             │
│        │                              │                             │
│        └──────── 1:Many ─────────────┘                             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

         │                              │
         ▼                              ▼

┌─────────────────────────────────────────────────────────────────────┐
│                    Database (SQLite/PostgreSQL)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  communities_consularservice                                        │
│  ├─ id (PRIMARY KEY)                                               │
│  ├─ name, service_type, description                                │
│  ├─ website, phone, email, address                                 │
│  ├─ country_coverage, services_offered                             │
│  ├─ is_featured, created_at, updated_at                            │
│  └─ Indexed: name, service_type, is_featured                       │
│                                                                      │
│  communities_legalimmigrationresource                              │
│  ├─ id (PRIMARY KEY)                                               │
│  ├─ title, category, content                                       │
│  ├─ external_url, keywords                                         │
│  ├─ is_critical, created_at, updated_at                            │
│  ├─ related_service_id (FOREIGN KEY) ──┐                          │
│  └─ Indexed: title, category, is_critical                          │
│                                         │                           │
│  └─ References ───────────────────────┘                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
USER INTERACTION FLOW
═══════════════════════════════════════════════════════════════════════

1. USER VISITS MAIN PAGE
   │
   └─► /community/legal-immigration/
       │
       ├─► Main Guidance Page (legal_immigration_guidance view)
       │   │
       │   ├─► Fetch featured ConsularServices
       │   ├─► Fetch critical LegalImmigrationResources
       │   └─► Render with 4 tabs
       │
       └─► Displays:
           ├─ Immigration Basics (hardcoded content)
           ├─ Legal Rights (hardcoded content)
           ├─ Consular Services (from database)
           └─ FAQs (hardcoded content)


2. USER CLICKS "Consular Services" TAB
   │
   └─► /community/consular-services/
       │
       ├─► Services List View (consular_services_list view)
       │   │
       │   ├─► Get all ConsularService objects
       │   ├─► Apply filters (service_type, country_coverage)
       │   ├─► Apply search (name, description, services_offered)
       │   ├─► Paginate (10 per page)
       │   └─► Render list template
       │
       └─► User sees:
           ├─ Search box
           ├─ Filter dropdowns
           ├─ Service cards (name, type, services, contact)
           └─ Pagination controls


3. USER CLICKS ON SERVICE CARD
   │
   └─► /community/consular-services/<service_id>/
       │
       ├─► Service Detail View (consular_service_detail view)
       │   │
       │   ├─► Get ConsularService by ID
       │   ├─► Get related LegalImmigrationResources
       │   └─► Render detail template
       │
       └─► User sees:
           ├─ Full service description
           ├─ Complete contact information
           ├─ Services offered list
           ├─ Coverage area
           └─ Related resources


4. USER CLICKS "Legal Resources" TAB
   │
   └─► /community/legal-resources/
       │
       ├─► Resources List View (legal_resources view)
       │   │
       │   ├─► Get all LegalImmigrationResource objects
       │   ├─► Apply category filter
       │   ├─► Apply search (title, keywords)
       │   ├─► Paginate (15 per page)
       │   └─► Render list template
       │
       └─► User sees:
           ├─ Search box
           ├─ Category filter dropdown
           ├─ Resource cards (title, category, preview)
           └─ Pagination controls


5. USER CLICKS ON RESOURCE CARD
   │
   └─► /community/legal-resources/<resource_id>/
       │
       ├─► Resource Detail View (legal_resource_detail view)
       │   │
       │   ├─► Get LegalImmigrationResource by ID
       │   ├─► Get related ConsularService (if any)
       │   ├─► Get similar resources (same category)
       │   └─► Render detail template
       │
       └─► User sees:
           ├─ Full article content
           ├─ Category badge
           ├─ Related consular service info
           ├─ Similar resources links
           ├─ External resource links
           └─ Legal disclaimer


ADMIN WORKFLOW
═════════════════════════════════════════════════════════════════════════

1. ADMIN GOES TO /admin/
   │
   ├─► ADDS NEW CONSULAR SERVICE
   │   │
   │   └─► /admin/communities/consularservice/add/
   │       │
   │       ├─► Fill in form (name, type, description, contact, etc.)
   │       ├─► Check "Is Featured" if applies
   │       └─► Save to database
   │           └─ Now visible in:
   │              ├─ Main page (if featured)
   │              └─ Services list (searchable/filterable)
   │
   │
   └─► ADDS NEW LEGAL RESOURCE
       │
       └─► /admin/communities/legalimmigrationresource/add/
           │
           ├─► Fill in form (title, category, content, etc.)
           ├─► Link to consular service (optional)
           ├─► Mark as critical (optional)
           └─► Save to database
               └─ Now visible in:
                  ├─ Resources list (searchable/filterable)
                  └─ Related to service (if linked)
```

## Search & Filter Architecture

```
CONSULAR SERVICES FILTERING
═════════════════════════════

GET /community/consular-services/?q=<search>&type=<type>

Query Logic:
─────────────
q = "USCIS"               → Filter by: name OR description OR services_offered
                          → Returns services matching "USCIS"

type = "government"       → Filter by: service_type = "government"
                          → Returns only government agencies

q + type combined         → Apply BOTH filters
                          → Returns government agencies matching search


LEGAL RESOURCES FILTERING
══════════════════════════

GET /community/legal-resources/?q=<search>&category=<cat>

Query Logic:
─────────────
q = "green card"          → Filter by: title OR keywords
                          → Returns resources matching "green card"

category = "green_card"   → Filter by: category = "green_card"
                          → Returns only green card resources

q + category combined     → Apply BOTH filters
                          → Returns green card resources matching search


SORTING & PAGINATION
═════════════════════

Services Sorting:
─────────────────
1. Featured (is_featured=True) FIRST
2. Then by update date (newest first)
3. Paginate 10 per page

Resources Sorting:
──────────────────
1. Critical (is_critical=True) FIRST
2. Then by update date (newest first)
3. Paginate 15 per page
```

## Database Relationships

```
One ConsularService ──────────► Many LegalImmigrationResources
                    (One-to-Many)

Example:
────────

ConsularService: "USCIS"
├─ LegalImmigrationResource: "Green Card Application Guide"
├─ LegalImmigrationResource: "Employment Authorization"
├─ LegalImmigrationResource: "Citizenship Path"
└─ LegalImmigrationResource: "Visa Types"

Each resource can be linked to at most ONE service
Each service can be linked to MANY resources
```

## URL Routing

```
Django URL Pattern Hierarchy
═════════════════════════════

Main Project urls.py:
  path('community/', include('communities.urls'))

Communities urls.py:
  path('legal-immigration/', views.legal_immigration_guidance, ...)
  path('consular-services/', views.consular_services_list, ...)
  path('consular-services/<int:service_id>/', views.consular_service_detail, ...)
  path('legal-resources/', views.legal_resources, ...)
  path('legal-resources/<int:resource_id>/', views.legal_resource_detail, ...)

Resulting URLs:
───────────────
http://domain/community/legal-immigration/
http://domain/community/consular-services/
http://domain/community/consular-services/5/
http://domain/community/legal-resources/
http://domain/community/legal-resources/23/
```

## Admin Interface Structure

```
Django Admin Hierarchy
══════════════════════

/admin/
├─ Communities
│  ├─ Community Members
│  ├─ Forum Categories
│  ├─ Posts
│  ├─ Comments
│  ├─ Event Calendars
│  ├─ Contact Messages
│  ├─ Consular Services ────────┐
│  │   ├─ Search: name, desc   │
│  │   ├─ Filter: type, featured│
│  │   └─ List: name, type,    │
│  │       coverage, featured,  │
│  │       updated_at           │
│  │                           │
│  └─ Legal Immigration Resources
│      ├─ Search: title, keywords
│      ├─ Filter: category, critical
│      └─ List: title, category,
│          critical, updated_at
│
└─ ... (other apps)
```

This architecture provides:
- ✅ Scalable data storage
- ✅ Efficient searching and filtering
- ✅ Related content discovery
- ✅ Admin-friendly interface
- ✅ User-friendly frontend
