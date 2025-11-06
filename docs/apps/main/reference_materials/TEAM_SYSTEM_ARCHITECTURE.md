# TEAM SYSTEM - Architecture & Data Flow

**Last Updated:** November 5, 2025

---

## SYSTEM ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TEAM DISPLAY SYSTEM                                │
└─────────────────────────────────────────────────────────────────────────────┘

                              USER REQUEST
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            URL ROUTING                                      │
│                         (coda/main/urls.py)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  /about/                    → views.about()                                 │
│  /members/team_profiles     → views.team(title='team')                      │
│  /members/client_profiles   → views.team(title='clients')                   │
│  /members/future_talents    → views.team(title='future')                    │
│  /members/board             → views.team(title='board')                     │
└────────────────┬────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           VIEW LAYER                                        │
│                      (coda/main/views.py)                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐              ┌──────────────────────┐
│   views.about()      │              │   views.team()       │
│   Lines 986-1017     │              │   Lines 739-928      │
├──────────────────────┤              ├──────────────────────┤
│ 1. Get Assets        │              │ 1. Point Calculation │
│ 2. Get UserProfiles  │              │ 2. Categorization    │
│ 3. Filter by         │              │ 3. AI Description    │
│    img_category      │              │ 4. Template Render   │
│ 4. Render Template   │              │                      │
└──────────┬───────────┘              └──────────┬───────────┘
           │                                     │
           │                                     │
           ▼                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER - MODELS                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   CustomerUser      │    │   UserProfile       │    │   Team_Members      │
│  (accounts.models)  │◄───┤  (accounts.models)  │    │  (accounts.models)  │
├─────────────────────┤    ├─────────────────────┤    ├─────────────────────┤
│ • username          │    │ • user (FK)         │    │ • category          │
│ • first_name        │    │ • position          │    │ • title             │
│ • last_name         │    │ • description       │    │ • description       │
│ • email             │    │ • education         │    └─────────────────────┘
│ • category          │    │ • linkedin          │
│ • sub_category      │    │ • image             │
│ • is_active         │    │ • image2 (FK)       │
│ • is_staff          │    │ • performance_tier  │
│ • is_superuser      │    │ • staff_level       │
└─────────────────────┘    └──────────┬──────────┘
                                      │
                                      │ Linked to
                                      ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Assets            │◄───┤   (image2 field)    │    │   Editable          │
│  (main.models)      │    └─────────────────────┘    │  (ai_services)      │
├─────────────────────┤                               ├─────────────────────┤
│ • name              │                               │ • name              │
│ • category          │                               │ • value (JSON)      │
│ • image_url         │                               └─────────────────────┘
│ • service_image     │                                         │
└─────────────────────┘                                         │
                                                                │
                                    ┌───────────────────────────┘
                                    │ 'team_profile_value_json'
                                    ▼
                              ┌──────────────┐
                              │  Thresholds  │
                              ├──────────────┤
                              │ lead_team    │
                              │ support_team │
                              │ delta        │
                              │ percentage   │
                              └──────────────┘
```

---

## POINT CALCULATION DATA FLOW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     POINT CALCULATION SYSTEM                                │
└─────────────────────────────────────────────────────────────────────────────┘

                        UserProfile Query
                               │
                               ▼
        ┌──────────────────────────────────────────┐
        │  all_member = UserProfile.objects.filter │
        │     user__is_active=True,                │
        │     user__category=2                     │
        │  ).annotate(...)                         │
        └──────────────────┬───────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
            ▼                             ▼
┌─────────────────────┐      ┌─────────────────────┐
│  SUBQUERY 1:        │      │  SUBQUERY 2:        │
│  Education Points   │      │  Task History       │
├─────────────────────┤      ├─────────────────────┤
│ Source: UserProfile │      │ Source: TaskHistory │
│ Field: education    │      │ Field: point        │
│                     │      │                     │
│ Calculation:        │      │ Calculation:        │
│ • Level 1 = 250     │      │ • SUM(point)        │
│ • Level 2 = 1,000   │      │                     │
│ • Level 3 = 3,000   │      │ Filter:             │
│ • Level 4 = 6,000   │      │ • employee_id =     │
│ • Level 5 = 10,000  │      │   OuterRef(pk)      │
└─────────────────────┘      └─────────────────────┘
            │                             │
            └──────────────┬──────────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
            ▼                             ▼
┌─────────────────────┐      ┌─────────────────────┐
│  SUBQUERY 3:        │      │  SUBQUERY 4:        │
│  Requirement Points │      │  Training Points    │
├─────────────────────┤      ├─────────────────────┤
│ Source: Requirement │      │ Source: Training    │
│ Field: duration     │      │ Field: level        │
│                     │      │                     │
│ Calculation:        │      │ Calculation:        │
│ • SUM(duration)     │      │ • Level 1 = 5       │
│                     │      │ • Level 2 = 20      │
│ Filter:             │      │ • Level 3 = 45      │
│ • assigned_to =     │      │ • Level 4 = 80      │
│   OuterRef(pk)      │      │ • Level 5 = 125     │
│                     │      │                     │
│                     │      │ Filter:             │
│                     │      │ • presenter =       │
│                     │      │   OuterRef(pk)      │
└─────────────────────┘      └─────────────────────┘
            │                             │
            └──────────────┬──────────────┘
                           │
                           ▼
            ┌──────────────────────────┐
            │  SUBQUERY 5:             │
            │  Client Assessment       │
            ├──────────────────────────┤
            │ Source: ClientAssessment │
            │ Field: totalpoints       │
            │                          │
            │ Calculation:             │
            │ • Latest record only     │
            │                          │
            │ Filter:                  │
            │ • email =                │
            │   OuterRef(user__email)  │
            │ • order_by('-rating_date')│
            └──────────────┬───────────┘
                           │
                           ▼
            ┌──────────────────────────┐
            │    TOTAL POINTS          │
            │                          │
            │  education_points +      │
            │  taskhistory_points +    │
            │  requirement_points +    │
            │  training_points +       │
            │  clientassesment_points  │
            └──────────────┬───────────┘
                           │
                           ▼
            ┌──────────────────────────┐
            │  TEAM CATEGORIZATION     │
            │                          │
            │  if total_points > 8000: │
            │    → Lead Team           │
            │  elif 7000-8000:         │
            │    → Senior Analysts     │
            │  elif 6000-7000:         │
            │    → Junior Analysts     │
            │  etc...                  │
            └──────────────────────────┘
```

---

## AI DESCRIPTION GENERATION FLOW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   AI DESCRIPTION GENERATION                                 │
└─────────────────────────────────────────────────────────────────────────────┘

                    Team Member Loop
                           │
                           ▼
            ┌──────────────────────────┐
            │  Check: description      │
            │  exists?                 │
            └──────────┬───────────────┘
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
        [EXISTS]            [MISSING]
        Skip                     │
                                 ▼
                  ┌──────────────────────────┐
                  │ Get ClientAssessment     │
                  │ by email                 │
                  └──────────┬───────────────┘
                             │
                             ▼
                  ┌──────────────────────────┐
                  │ Extract Data:            │
                  │ • first_name             │
                  │ • experience (it_exp)    │
                  │ • IT skills with ratings │
                  └──────────┬───────────────┘
                             │
                             ▼
                  ┌──────────────────────────┐
                  │ Rank IT Skills:          │
                  │ 1. Non-IT Experience     │
                  │ 2. IT Experience         │
                  │ 3. Project Charter       │
                  │ 4. Requirements Analysis │
                  │ 5. Reporting             │
                  │ 6. ETL                   │
                  │ 7. Database              │
                  │ 8. Testing               │
                  │ 9. Deployment            │
                  │ 10. Frontend             │
                  │ 11. Backend              │
                  │                          │
                  │ Sort by rating DESC      │
                  │ Take top 2               │
                  └──────────┬───────────────┘
                             │
                             ▼
                  ┌──────────────────────────┐
                  │ Build Prompt:            │
                  │                          │
                  │ "Generate a description  │
                  │ for {first_name}, a      │
                  │ professional with        │
                  │ {experience} years of    │
                  │ experience in {skill1},  │
                  │ {skill2}."               │
                  └──────────┬───────────────┘
                             │
                             ▼
                  ┌──────────────────────────┐
                  │ Call OpenAI API:         │
                  │ generate_chatbot_response│
                  └──────────┬───────────────┘
                             │
                             ▼
                  ┌──────────────────────────┐
                  │ Response Example:        │
                  │                          │
                  │ "John is a seasoned      │
                  │ professional with 5      │
                  │ years of experience      │
                  │ specializing in ETL      │
                  │ and Database management. │
                  │ He has demonstrated...   │
                  └──────────┬───────────────┘
                             │
                             ▼
                  ┌──────────────────────────┐
                  │ Save to UserProfile:     │
                  │ user_profile.description │
                  │ user_profile.save()      │
                  └──────────────────────────┘
```

---

## IMAGE RENDERING FLOW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       IMAGE RENDERING SYSTEM                                │
└─────────────────────────────────────────────────────────────────────────────┘

                    Template Renders
                           │
                           ▼
            ┌──────────────────────────┐
            │ <img src=                │
            │   "{{ googledriveurl }}  │
            │   {{ member.img_url }}"  │
            │   onerror=               │
            │   "handleImageError()"/> │
            └──────────┬───────────────┘
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
    [IMAGE LOADS]        [IMAGE FAILS]
    Display                    │
                               ▼
                ┌──────────────────────────┐
                │ JavaScript:              │
                │ handleImageError()       │
                └──────────┬───────────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
            ▼                             ▼
    [src includes '/static/']   [External URL]
            │                             │
            ▼                             ▼
┌──────────────────────┐      ┌──────────────────────┐
│ Set to default:      │      │ Try profile image:   │
│ /static/main/img/    │      │ /static/main/img/    │
│ service-1.jpg        │      │ profile/{name}.jpeg  │
└──────────────────────┘      └──────────┬───────────┘
                                         │
                              ┌──────────┴──────────┐
                              │                     │
                              ▼                     ▼
                          [EXISTS]            [NOT FOUND]
                          Display             Use default


┌─────────────────────────────────────────────────────────────────────────────┐
│                      GOOGLE DRIVE UPLOAD FLOW                               │
└─────────────────────────────────────────────────────────────────────────────┘

        UserProfileUpdateView.form_valid()
                       │
                       ▼
        ┌──────────────────────────┐
        │ User uploads new image?  │
        └──────────┬───────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
    [NO IMAGE]           [IMAGE UPLOADED]
    Skip                     │
                             ▼
              ┌──────────────────────────┐
              │ Extract image data:      │
              │ • image_name             │
              │ • image_path             │
              │ • folder_id (hardcoded)  │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │ upload_image_to_drive()  │
              │ (utils.py)               │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │ Google Drive API:        │
              │ • Authenticate           │
              │ • Upload file            │
              │ • Return file_id         │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │ Create Assets record:    │
              │ Assets.objects.create(   │
              │   image_url = file_id    │
              │ )                        │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │ Link to UserProfile:     │
              │ instance.image2 =        │
              │   assets_instance        │
              └──────────────────────────┘
```

---

## TEMPLATE RENDERING FLOW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TEMPLATE RENDERING FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

                views.team(title='team_profiles')
                              │
                              ▼
               ┌──────────────────────────┐
               │ Calculate Points         │
               │ Categorize Members       │
               │ Generate Descriptions    │
               └──────────┬───────────────┘
                          │
                          ▼
               ┌──────────────────────────┐
               │ Build Context:           │
               │ {                        │
               │   'team_categories': {   │
               │     'Lead Team': [...],  │
               │     'Support Team': [...],│
               │     ...                  │
               │   },                     │
               │   'team_members': [...]  │
               │   'title': "..."         │
               │ }                        │
               └──────────┬───────────────┘
                          │
                          ▼
               ┌──────────────────────────┐
               │ Render Template:         │
               │ team_profiles.html       │
               └──────────┬───────────────┘
                          │
                          ▼
               ┌──────────────────────────┐
               │ Extends:                 │
               │ main/base_templates/     │
               │ new_base.html            │
               └──────────┬───────────────┘
                          │
                          ▼
               ┌──────────────────────────┐
               │ Includes:                │
               │ snippets_templates/      │
               │ cards/team_card.html     │
               └──────────┬───────────────┘
                          │
                          ▼
        ┌─────────────────┴─────────────────┐
        │                                   │
        ▼                                   ▼
┌────────────────┐               ┌────────────────┐
│ Loop through   │               │ For each       │
│ team_categories│               │ category:      │
└────────┬───────┘               └────────┬───────┘
         │                                │
         ▼                                ▼
┌────────────────┐               ┌────────────────┐
│ Left Column:   │               │ Right Column:  │
│ • Category     │               │ Loop through   │
│   name         │               │ members:       │
│ • Category     │               │ • Image        │
│   description  │               │ • Name         │
│   (from        │               │ • Position     │
│   Team_Members)│               │ • Points       │
└────────────────┘               │ • LinkedIn     │
                                 │ • Description  │
                                 │ • Edit link    │
                                 └────────────────┘
```

---

## DATABASE SCHEMA RELATIONSHIPS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DATABASE RELATIONSHIPS                                │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │  CustomerUser   │
                    │  (auth table)   │
                    ├─────────────────┤
                    │ PK: id          │
                    │ • username      │
                    │ • email         │
                    │ • category      │
                    │ • sub_category  │
                    │ • is_active     │
                    └────────┬────────┘
                             │ 1
                             │
                             │ has one
                             │
                             ▼ 1
                    ┌─────────────────┐
                    │  UserProfile    │
                    ├─────────────────┤
                    │ PK: id          │
                    │ FK: user_id     │◄───────┐
                    │ FK: image2_id   │        │
                    │ • position      │        │
                    │ • description   │        │
                    │ • education     │        │
                    │ • linkedin      │        │
                    └────────┬────────┘        │
                             │                 │
                 ┌───────────┼───────────┐     │ points from
                 │           │           │     │
                 │           │           │     │
        ┌────────▼──┐  ┌────▼─────┐  ┌──▼─────▼───┐
        │TaskHistory│  │Requirement│  │ClientAssess│
        ├───────────┤  ├───────────┤  ├────────────┤
        │FK:employee│  │FK:assigned│  │email (match│
        │• point    │  │• duration │  │  user.email│
        └───────────┘  └───────────┘  │• totalpoint│
                                      │• it_exp    │
                                      │• etl       │
        ┌───────────┐                 │• database  │
        │  Training │                 │• etc...    │
        ├───────────┤                 └────────────┘
        │FK:presenter                        
        │• level    │                        
        └───────────┘                        
                             │
                             │ links to
                             │
                             ▼
                    ┌─────────────────┐
                    │     Assets      │
                    ├─────────────────┤
                    │ PK: id          │
                    │ • name          │
                    │ • category      │
                    │ • image_url     │◄─── Google Drive
                    │ • service_image │     File ID
                    └─────────────────┘

                    ┌─────────────────┐
                    │  Team_Members   │
                    ├─────────────────┤
                    │ PK: id          │
                    │ • category      │
                    │ • title         │
                    │ • description   │◄─── Used for
                    └─────────────────┘     category
                                            descriptions

                    ┌─────────────────┐
                    │    Editable     │
                    ├─────────────────┤
                    │ PK: id          │
                    │ • name          │
                    │ • value (JSON)  │◄─── Thresholds
                    └─────────────────┘     config
```

---

## REQUEST/RESPONSE CYCLE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FULL REQUEST/RESPONSE CYCLE                              │
└─────────────────────────────────────────────────────────────────────────────┘

1. USER REQUEST
   │
   └─► GET /members/team_profiles HTTP/1.1
       Host: codamakutano.herokuapp.com

2. URL ROUTING (urls.py)
   │
   └─► path('members/<str:title>', views.team, name='members')
       │
       └─► title = 'team_profiles'

3. VIEW EXECUTION (views.py:team)
   │
   ├─► Parse title: 'team_profiles'
   │
   ├─► IF NOT client_profiles:
   │   │
   │   ├─► Query UserProfile with annotations
   │   │   │
   │   │   ├─► Education subquery
   │   │   ├─► TaskHistory subquery
   │   │   ├─► Requirement subquery
   │   │   ├─► Training subquery
   │   │   └─► ClientAssessment subquery
   │   │
   │   ├─► Calculate total_points for each member
   │   │
   │   ├─► Get thresholds from Editable model
   │   │
   │   ├─► Categorize members:
   │   │   │
   │   │   ├─► elite_team (superuser only)
   │   │   ├─► lead_team (> 8000)
   │   │   ├─► senior_analysts (7000-8000)
   │   │   ├─► junior_analysts (6000-7000)
   │   │   └─► etc...
   │   │
   │   └─► Generate AI descriptions (if missing)
   │
   ├─► Build team_categories dict
   │
   └─► Build context = {
           'team_categories': {...},
           'team_members': [...],
           'title': 'THE BEST TEAM...'
       }

4. TEMPLATE RENDERING
   │
   ├─► Load: team_profiles.html
   │   │
   │   └─► Extends: base_templates/new_base.html
   │       │
   │       └─► Includes: snippets_templates/cards/team_card.html
   │
   ├─► Loop through team_categories
   │   │
   │   └─► For each category:
   │       │
   │       ├─► Render category name
   │       ├─► Render category description
   │       │
   │       └─► Loop through members:
   │           │
   │           ├─► Render image
   │           ├─► Render name
   │           ├─► Render position
   │           ├─► Render points (if admin)
   │           ├─► Render LinkedIn
   │           └─► Render description
   │
   └─► Generate HTML

5. HTTP RESPONSE
   │
   └─► HTTP/1.1 200 OK
       Content-Type: text/html; charset=utf-8
       
       <!DOCTYPE html>
       <html>
       ...
       </html>

6. BROWSER RENDERING
   │
   ├─► Parse HTML
   ├─► Load CSS (team_card.css)
   ├─► Load JavaScript (Read More/Less)
   ├─► Fetch images
   │   │
   │   ├─► Try Google Drive URL
   │   │   │
   │   │   ├─► [SUCCESS] → Display
   │   │   │
   │   │   └─► [FAIL] → Call handleImageError()
   │   │       │
   │   │       └─► Try static profile image
   │   │           │
   │   │           ├─► [SUCCESS] → Display
   │   │           │
   │   │           └─► [FAIL] → Default image
   │   │
   │   └─► Render page
   │
   └─► Attach event listeners (Read More/Less)
```

---

## PERFORMANCE PROFILE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PERFORMANCE ANALYSIS                                │
└─────────────────────────────────────────────────────────────────────────────┘

QUERY COMPLEXITY (for 20 team members):
│
├─► Main Query: 1
│   └─► SELECT * FROM accounts_userprofile WHERE ...
│
├─► Subqueries per member: 5 × 20 = 100 subqueries
│   ├─► Education calculation (annotation)
│   ├─► TaskHistory aggregation
│   ├─► Requirement aggregation
│   ├─► Training calculation (annotation)
│   └─► ClientAssessment lookup
│
├─► Threshold lookup: 1
│   └─► SELECT value FROM ai_services_editable WHERE name='...'
│
├─► AI Description generation: 0-20 (only if missing)
│   └─► OpenAI API calls (varies)
│
└─► Total Database Queries: ~102-122

OPTIMIZATION OPPORTUNITIES:
│
├─► Cache total_points
│   └─► Reduce 100 subqueries to 1 field lookup
│       Savings: ~99% query reduction
│
├─► Pre-generate descriptions
│   └─► Reduce 0-20 API calls to 0
│       Savings: API cost + latency
│
├─► Add select_related / prefetch_related
│   └─► Reduce N+1 queries for user data
│       Savings: 20-40 additional queries
│
└─► Page caching
    └─► Cache rendered HTML for 1 hour
        Savings: All queries for cached period

ESTIMATED CURRENT LOAD TIME:
│
├─► Database queries: 100-120 × ~10ms = 1-1.2s
├─► AI generation: 0-20 × ~2s = 0-40s (if needed)
├─► Image loading: 20 × ~100ms = 2s
└─► Total: ~3-43s (worst case), ~1-3s (typical)

ESTIMATED OPTIMIZED LOAD TIME:
│
├─► Database queries: 2-3 × ~10ms = 20-30ms
├─► Cached HTML: ~5ms
├─► Image loading: 20 × ~100ms = 2s (CDN)
└─► Total: ~2s (best case)
```

---

## ERROR HANDLING FLOW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ERROR HANDLING                                      │
└─────────────────────────────────────────────────────────────────────────────┘

POTENTIAL ERRORS:

1. UserProfile.DoesNotExist
   │
   ├─► Cause: User has no profile
   ├─► Handler: Signal auto-creates on user creation
   └─► Fallback: Skip member in loop

2. ClientAssessment.DoesNotExist
   │
   ├─► Cause: No assessment completed
   ├─► Handler: Return 0 points for assessment
   └─► Fallback: Description = 'null'

3. OpenAI API Error
   │
   ├─► Cause: API timeout, rate limit, key issue
   ├─► Handler: try/except block
   └─► Fallback: Description = 'null'

4. Image Load Error
   │
   ├─► Cause: Invalid Google Drive ID
   ├─► Handler: onerror="handleImageError()"
   └─► Fallback: Static profile image → default image

5. Editable.DoesNotExist
   │
   ├─► Cause: 'team_profile_value_json' not in DB
   ├─► Handler: Hardcoded defaults
   └─► Fallback: {lead_team: 8000, support_team: 1000, ...}

6. No team members found
   │
   ├─► Cause: No active category=2 users
   ├─► Handler: Check in template {% if members %}
   └─► Fallback: Display "Check back soon" message
```

---

## SECURITY CONSIDERATIONS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SECURITY MODEL                                     │
└─────────────────────────────────────────────────────────────────────────────┘

AUTHENTICATION:
│
├─► About page: PUBLIC (no login required)
├─► Team profiles: PUBLIC (no login required)
└─► Update profile: @login_required + ownership check

AUTHORIZATION:
│
├─► View total points:
│   └─► if request.user.is_admin OR is_superuser OR is_staff
│
├─► Edit profile:
│   └─► if request.user.is_superuser OR user == profile.user
│
└─► View descriptions:
    └─► PUBLIC (all descriptions visible)

DATA EXPOSURE:
│
├─► Public data:
│   ├─► Name (first, last)
│   ├─► Position
│   ├─► Description
│   ├─► LinkedIn URL
│   └─► Profile image
│
├─► Restricted data (admin only):
│   └─► Total points
│
└─► Private data (not displayed):
    ├─► Email
    ├─► National ID
    ├─► Emergency contacts
    ├─► Account numbers
    └─► Personal documents

FILE UPLOAD SECURITY:
│
├─► Image validation:
│   ├─► File type check
│   ├─► Size limit
│   └─► Virus scan (recommended)
│
└─► Google Drive upload:
    ├─► Authenticated API
    ├─► Specific folder only
    └─► File ID stored (not raw file)

XSS PREVENTION:
│
├─► Description field:
│   ├─► AI-generated (controlled input)
│   └─► |safe filter (should be reviewed)
│
└─► User input:
    ├─► Django auto-escapes
    └─► CSRF protection enabled

RECOMMENDATIONS:
│
├─► 1. Remove |safe from descriptions (use auto-escape)
├─► 2. Add rate limiting to AI generation
├─► 3. Implement audit logging for profile changes
├─► 4. Add image virus scanning
└─► 5. Review Google Drive permissions regularly
```

---

**End of Architecture Documentation**

*For implementation details, see `ABOUT_AND_TEAM_PAGES.md`*  
*For quick reference, see `TEAM_SYSTEM_QUICK_REFERENCE.md`*

