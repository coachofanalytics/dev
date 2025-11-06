# ABOUT US & TEAM PAGES - Complete Documentation

**Last Updated:** November 5, 2025  
**Status:** Active System  
**Location:** `coda/main/` app

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [URL Routing](#url-routing)
3. [Views & Functions](#views--functions)
4. [Models & Data Structure](#models--data-structure)
5. [Templates](#templates)
6. [Team Categorization Logic](#team-categorization-logic)
7. [Image Management](#image-management)
8. [AI-Generated Descriptions](#ai-generated-descriptions)
9. [Related Features](#related-features)
10. [Technical Details](#technical-details)

---

## OVERVIEW

The **About Us** and **Team Pages** system displays CODA's company information, team members, and organizational structure. The system includes:

- **About Page**: Company mission, vision, services, and team overview
- **Team Profiles**: Categorized display of all team members with detailed profiles
- **Client Profiles**: Display of client success stories
- **Future Talents**: Junior team members and trainees
- **Board Members**: Board of Governors display

### Key Features:
✅ Dynamic team categorization based on performance points  
✅ AI-generated member descriptions  
✅ Google Drive image integration  
✅ Responsive design with "Read More" functionality  
✅ LinkedIn profile integration  
✅ Real-time point calculation system  

---

## URL ROUTING

### Main URLs (`coda/main/urls.py`)

```python
urlpatterns = [
    # About page
    path('about/', views.about, name='about'),
    
    # Team profiles (categorized)
    path('members/<str:title>', views.team, name='members'),
    
    # Related pages
    path('why-coda/', views.why_coda, name='why_coda'),
    path('careers/', views.careers, name='careers'),
    path('student-support-Page/', views.student_support, name='student_support'),
    path('contact/', views.contact, name='contact'),
]
```

### URL Examples:
- `/about/` - Main about page
- `/members/team_profiles` - Internal team display
- `/members/client_profiles` - Client showcase
- `/members/future_talents` - Junior team members
- `/members/board` - Board of Governors

---

## VIEWS & FUNCTIONS

### 1. About View (`views.about()`)

**Location:** `coda/main/views.py` (Lines 986-1017)

**Purpose:** Renders the main About Us page with team overview

**Key Logic:**
```python
def about(request):
    # Get all active images/assets
    images = Assets.objects.all()
    image_names = Assets.objects.values_list('name', flat=True)
    
    # Get all active team members (category=2 = Employee)
    team_members = UserProfile.objects.filter(
        user__category=2,
        user__is_active=True
    )
    
    # Filter to only display employees with images
    staff = [member for member in team_members if member.img_category=='employee']
    img_urls = [member.img_url for member in team_members if member.img_category=='employee']
    
    context = {
        "active_employees": staff,
        "img_urls": img_urls,
        "title_about": "about",
    }
    return render(request, "main/about.html", context)
```

**Template:** `coda/main/templates/main/about.html`

**Features:**
- Hero section with company tagline
- Mission & Vision statements
- Core values display
- Services overview cards
- Team member grid (filtered by `img_category='employee'`)
- Statistics section
- Call-to-action buttons

---

### 2. Team View (`views.team()`)

**Location:** `coda/main/views.py` (Lines 739-928)

**Purpose:** Dynamic team categorization with performance-based tiers

**Key Logic Flow:**

#### Step 1: Point Calculation System

The system calculates total points for each team member from multiple sources:

```python
# 1. Education Points
user_education_subquery = (
    When(education=1, then=F('education') * 250.0),   # High School
    When(education=2, then=F('education') * 500.0),   # Some College
    When(education=3, then=F('education') * 1000.0),  # Bachelor's
    When(education=4, then=F('education') * 1500.0),  # Master's
    When(education=5, then=F('education') * 2000.0),  # Doctorate
)

# 2. Task History Points (from TaskHistory model)
employee_taskhistory_subquery = Sum('point')

# 3. Requirement Points (from Requirement model - task duration)
employee_requiremet_subquery = Sum('duration')

# 4. Training Points (from Training model)
employee_training_subquery = (
    When(level=1, then=F('level') * 5.0),
    When(level=2, then=F('level') * 10.0),
    When(level=3, then=F('level') * 15.0),
    When(level=4, then=F('level') * 20.0),
    When(level=5, then=F('level') * 25.0),
)

# 5. Client Assessment Points (from ClientAssessment model)
employee_clientassesment_points = latest totalpoints

# TOTAL POINTS = Sum of all above
total_points = (
    education_points + 
    taskhistory_points + 
    requirement_points + 
    training_points + 
    clientassesment_points
)
```

#### Step 2: Team Categorization

Teams are categorized dynamically based on total points:

```python
# Default thresholds (stored in Editable model: 'team_profile_value_json')
team_member_value_json = {
    "lead_team": 8000,      # Lead Team threshold
    "support_team": 1000,   # Support Team threshold
    "delta": 1000,          # Point reduction per tier
    "percentage": 10        # Percentage reduction when delta exhausted
}

# Calculate thresholds for each tier
threshold_dict = {
    'lead_team': 8000,           # > 8000 points
    'senior_analysts': 7000,     # 7000-8000 points
    'junior_analysts': 6000,     # 6000-7000 points
    'senior_trainee': 5000,      # 5000-6000 points
    'junior_trainee': 4000,      # 4000-5000 points
    'elementry': 0,              # < 4000 points
}

# Categorize team members
elite_team_member = UserProfile.objects.filter(
    user__is_superuser=True, 
    user__username='c_maghas'
)

lead_team = filter(lambda v: v.total_points > 8000, all_staff_member)
senior_analysts = filter(lambda v: 7000 < v.total_points <= 8000, all_staff_member)
# ... etc
```

#### Step 3: Team Categories by Page

**Team Profiles Page (`/members/team_profiles`):**
```python
team_categories = {
    'Elite Team': [c_maghas],          # Superuser only
    'Lead Team': [...],                 # > 8000 points
    'Support Team': [...],              # Contractors > 1000 points
    'Senior Analysts': [...],           # 7000-8000 points
}
```

**Client Profiles Page (`/members/client_profiles`):**
```python
team_categories = {
    'Job Seekers': [...],               # Non job-support clients
    'Job Support': [...],               # sub_category=4 clients
}
```

**Future Talents Page (`/members/future_talents`):**
```python
team_categories = {
    'Junior Analysts': [...],           # 6000-7000 points
    'Senior Trainee Team': [...],       # 5000-6000 points
    'Junior Trainee Team': [...],       # 4000-5000 points
    'Elementary': [...],                # < 4000 points
}
```

**Board Page (`/members/board`):**
```python
team_categories = {
    'Board Members': [...],             # sub_category=0
}
```

---

## MODELS & DATA STRUCTURE

### 1. UserProfile Model

**Location:** `coda/accounts/models.py` (Lines 186-336+)

**Key Fields:**
```python
class UserProfile(models.Model):
    # Core Fields
    user = OneToOneField(CustomerUser, related_name="profile")
    
    # Professional Info
    position = CharField(max_length=255)        # Job title
    company = CharField(max_length=254)         # Employer
    description = TextField()                   # Bio (AI-generated)
    linkedin = URLField(max_length=500)         # LinkedIn URL
    
    # Education & Skills
    education = IntegerField(choices=Education.choices)
    skills = JSONField(default=list)
    
    # Images
    image = ImageField(upload_to="Application_Profile_pics")
    image2 = ForeignKey(Assets, related_name="profile_image")
    
    # Identification
    national_id_no = CharField(max_length=254)
    id_file = ImageField(upload_to='id_files/')
    
    # Emergency Contact
    emergency_name = CharField(max_length=254)
    emergency_phone = CharField(max_length=254)
    emergency_email = EmailField(max_length=254)
    
    # KCC Membership
    is_karen_country_club_member = BooleanField(default=False)
    kcc_membership_number = CharField(max_length=100)
    kcc_membership_date = DateField()
    kcc_membership_expiry = DateField()
    
    # Performance Tracking
    performance_tier = CharField(
        max_length=20,
        choices=PerformanceTier.choices,
        default=PerformanceTier.NEW
    )
    staff_level = CharField(
        max_length=20,
        choices=StaffLevel.choices
    )
    
    # Loan Eligibility
    monthly_income = DecimalField(max_digits=10, decimal_places=2)
    employment_start_date = DateField()
    credit_score = IntegerField()
    
    # Preferences
    preferred_contact_method = CharField(
        max_length=20,
        choices=[('email', 'Email'), ('phone', 'Phone'), ...]
    )
```

**Education Choices:**
- 1: High School (250 points)
- 2: Some College (500 points)
- 3: Bachelor's Degree (1000 points)
- 4: Master's Degree (1500 points)
- 5: Doctorate (2000 points)

**Performance Tiers:**
- NEW
- BRONZE
- SILVER
- GOLD
- PLATINUM

**Staff Levels:**
- JUNIOR
- SENIOR
- MANAGER
- EXECUTIVE

---

### 2. Team_Members Model

**Location:** `coda/accounts/models.py` (Lines 796-826)

**Purpose:** Store team category descriptions

```python
class Team_Members(models.Model):
    CAT_CHOICES = [
        ("board", "Board Members"),
        ("analytics_team", "Analytics Team"),
        ("future_talent", "Future Talent"),
        ("support_team", "Support Team"),
        ("clients", "Clients"),
        ("other", "other"),
    ]
    
    category = CharField(max_length=25, choices=CAT_CHOICES)
    title = CharField(max_length=255, default="Project Manager")
    description = TextField()
```

**Usage:**
- Stores descriptive text for each team category
- Displayed on the left side of team profile pages
- Helps explain what each team tier represents

---

### 3. Assets Model

**Location:** `coda/main/models.py` (Lines 340-360)

**Purpose:** Manage images and media assets

```python
class Assets(TimeStampedModel):
    name = CharField(max_length=200)
    category = CharField(default='background', max_length=200)
    image_string = TextField()
    description = TextField(default='background')
    service_image = ImageField(upload_to="images/", default='background')
    image_url = CharField(max_length=1000, default='background')
    
    @property
    def split_name(self):
        # Splits name by underscore for processing
        image_1 = self.name.split("_")[0]
        image_2 = self.name.split("_")[1]
        return (image_1, image_2)
```

**Features:**
- Stores Google Drive image IDs
- Links to UserProfile via `image2` field
- Supports multiple image categories

---

### 4. Testimonials Model

**Location:** `coda/main/models.py` (Lines 317-337)

**Purpose:** Client testimonials and reviews

```python
class Testimonials(models.Model):
    title = CharField(max_length=100)
    slug = SlugField(max_length=255, unique=True)
    content = TextField()
    date_posted = DateTimeField(default=timezone.now)
    writer = ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to=(
            Q(is_staff=True) | 
            Q(category__in=[1, 3, 4, 5, 6, 7])  # Clients
        )
    )
```

**Features:**
- Displayed on homepage and about page
- Auto-slugification
- Filtered by user category

---

## TEMPLATES

### 1. About Page Template

**Location:** `coda/main/templates/main/about.html`

**Structure:**
```html
{% extends "main/base_templates/new_base.html" %}

<!-- Hero Section -->
<section class="hero-section">
    <h1>About CODA</h1>
    <p>Financial technology company...</p>
    <span class="badge">Financial Services</span>
    <span class="badge">Technology Training</span>
    <span class="badge">Investment Solutions</span>
</section>

<!-- Mission & Vision Section -->
<section class="mission-vision">
    <div>Mission...</div>
    <div>Vision...</div>
    <div>Core Values...</div>
</section>

<!-- Services Overview -->
<section class="services">
    <div class="card">Financial Services</div>
    <div class="card">Professional Training</div>
    <div class="card">AI Services</div>
</section>

<!-- Team Section -->
<section class="team">
    {% if active_employees %}
        {% for member in active_employees %}
            <div class="card">
                <img src="{{ member.img_url }}" />
                <h5>{{ member.user.get_full_name }}</h5>
                <p>{{ member.job_title }}</p>
            </div>
        {% endfor %}
    {% else %}
        <a href="{% url 'main:members' title='team' %}">View Team</a>
    {% endif %}
</section>

<!-- Statistics Section -->
<section class="statistics">
    <div>1000+ Clients Served</div>
    <div>50+ Projects Completed</div>
    <div>15+ Years Experience</div>
    <div>98% Client Satisfaction</div>
</section>

<!-- Call to Action -->
<section class="cta">
    <a href="{% url 'accounts:join' %}">Get Started Today</a>
    <a href="{% url 'main:contact' %}">Contact Us</a>
</section>
```

**CSS Styling:**
- Linear gradient background: `#667eea` to `#764ba2`
- Hover animations on cards
- Responsive grid layout
- Modern shadow effects

---

### 2. Team Profiles Template

**Location:** `coda/main/templates/main/team_profiles.html`

**Structure:**
```html
{% extends "main/base_templates/new_base.html" %}

<section id="testimonials-section">
    <div class="testimonials text-center">
        <h1>{{ title }}</h1>
        <hr />
        {% include 'main/snippets_templates/cards/team_card.html' %}
    </div>
</section>
```

**Simple wrapper that includes the team card component.**

---

### 3. Team Card Component

**Location:** `coda/main/templates/main/snippets_templates/cards/team_card.html`

**Structure:**
```html
{% load static %}

<div class="section">
  {% for category, members in team_categories.items %}
  <div class="row">
      <!-- Left Column: Category Description -->
      <div class="col-md-3">
        <div class="emp border-light">
          <h1>{{ category }}</h1>
          <p class="descriptionside">
            {% for team_member in team_members %}
              {% if team_member.title == category %}
                {{ team_member.description }}
              {% endif %}
            {% endfor %}
          </p>
        </div>
      </div>
      
      <!-- Right Column: Team Members -->
      <div class="col-md-9">
        <div class="emp">
          <div class="row text-center">
            {% for member in members %}
                {% if member.description %}
                    <div class="col-md-4">
                        <!-- Profile Image -->
                        <div class="img-div p-3">
                            <img 
                                src="{{ googledriveurl }}{{ member.img_url }}" 
                                onerror="handleImageError(this, '{{member.user.first_name}}')" 
                                class="team-img rounded-circle" 
                                width="120px" 
                                height="120px"
                            />
                        </div>
                        
                        <!-- Member Info -->
                        <div class="member-info">
                          <a href="#" class="member-link">
                            <h3>{{ member.user.first_name|capfirst }}, {{ member.user.last_name|capfirst }}</h3>
                            <h5>{{ member.position }}
                              {% if request.user.is_admin or request.user.is_superuser %}
                                {{ member.total_points }}
                              {% endif %}
                            </h5>
                            
                            {% if member.linkedin %}
                            <h5>
                              <a href="{{member.linkedin}}">LinkedIn Profile</a>
                            </h5>
                            {% endif %}
                          </a>
                          
                          <!-- Description with Read More/Less -->
                          <div class="responsive">
                            <p class="description" id="description{{ forloop.counter }}">
                              {% if member.description|length > 220 %}
                                <span class="truncated-text" id="truncatedText{{ forloop.counter }}">
                                  {{ member.description|safe|truncatechars:220 }}
                                </span>
                                <span class="remaining-text" id="remainingText{{ forloop.counter }}" style="display: none;">
                                  {{ member.description|safe }}
                                </span>
                                <a class="read-more-button" data-index="{{ forloop.counter }}">
                                  Read more
                                </a>
                                <a class="read-less-button" data-index="{{ forloop.counter }}" style="display: none;">
                                  Read less
                                </a>
                              {% else %}
                                {{ member.description|safe }}
                              {% endif %}
                            </p>
                          </div>                        
                        </div>
                        
                        <!-- Edit Link (Admin Only) -->
                        {% if member.is_admin or member.is_superuser or member == member.user %}
                            <a href="{% url 'main:update_profile' member.user.id %}">Update Profile</a>
                        {% endif %}
                    </div>
                {% endif %}
          {% endfor %}
          </div>
        </div>
      </div>
  </div>
  <hr />
  {% endfor %}
</div>

<!-- JavaScript for Read More/Less functionality -->
<script>
let currentlyOpenEmpSection = null;

document.querySelectorAll('.read-more-button, .read-less-button').forEach(button => {
  button.addEventListener('click', () => {
    const index = button.dataset.index;
    const truncatedText = document.getElementById(`truncatedText${index}`);
    const remainingText = document.getElementById(`remainingText${index}`);
    const readMoreButton = document.querySelector(`.read-more-button[data-index="${index}"]`);
    const readLessButton = document.querySelector(`.read-less-button[data-index="${index}"]`);
    
    // Toggle display
    if (truncatedText.style.display === 'none') {
      truncatedText.style.display = 'inline';
      remainingText.style.display = 'none';
      readMoreButton.style.display = 'inline';
      readLessButton.style.display = 'none';
    } else {
      truncatedText.style.display = 'none';
      remainingText.style.display = 'inline';
      readMoreButton.style.display = 'none';
      readLessButton.style.display = 'inline';
    }
    
    // Smooth scroll
    const empSection = button.closest('.member-info');
    const contentBelow = empSection.nextElementSibling;
    if (contentBelow) {
      contentBelow.scrollIntoView({ behavior: 'smooth' });
    }
  });
});

// Image error handling
function handleImageError(img, name) {
    img.style.height = '120px';
    img.style.width = '120px';
    
    if (img.src.includes('/static/')) {
      img.src = "{% static 'main/img/service-1.jpg' %}"
    } else {
      img.src = "{% static 'main/img/profile/' %}" + name.toLowerCase() + ".jpeg"
    }
}
</script>
```

**Features:**
- Responsive 3-column grid (col-md-4)
- Google Drive image integration
- Fallback to local images on error
- Read More/Less toggle for long descriptions
- LinkedIn profile links
- Admin-only total points display
- Edit profile link for authorized users

---

## TEAM CATEGORIZATION LOGIC

### Point Calculation Breakdown

Each team member's `total_points` is calculated from 5 sources:

#### 1. Education Points
```python
High School:          1 × 250  = 250 points
Some College:         2 × 500  = 1,000 points
Bachelor's Degree:    3 × 1,000 = 3,000 points
Master's Degree:      4 × 1,500 = 6,000 points
Doctorate:            5 × 2,000 = 10,000 points
```

#### 2. Task History Points
- From `TaskHistory` model
- Sum of all `point` values for tasks assigned to the user
- Example: Completed 10 tasks worth 50 points each = 500 points

#### 3. Requirement Points
- From `Requirement` model
- Sum of all `duration` values (task hours)
- Example: 100 hours of work = 100 points

#### 4. Training Points
```python
Level 1:    1 × 5  = 5 points
Level 2:    2 × 10 = 20 points
Level 3:    3 × 15 = 45 points
Level 4:    4 × 20 = 80 points
Level 5:    5 × 25 = 125 points
```

#### 5. Client Assessment Points
- From `ClientAssessment` model
- Latest `totalpoints` value for the user
- Based on IT skills assessment (ETL, Database, Testing, etc.)

### Example Calculation

**Team Member: John Doe**
```python
Education:           Bachelor's = 3,000 points
Task History:        50 tasks × 50 = 2,500 points
Requirements:        200 hours = 200 points
Training:            Level 4 = 80 points
Client Assessment:   2,500 points
─────────────────────────────────────────────
TOTAL:                         8,280 points

Category: LEAD TEAM (> 8,000 points)
```

### Team Tier Thresholds

These thresholds are stored in the `Editable` model under `team_profile_value_json`:

```python
{
    "lead_team": 8000,
    "support_team": 1000,
    "delta": 1000,
    "percentage": 10
}
```

**Calculated Tiers:**
- **Elite Team**: Superuser only (`c_maghas`)
- **Lead Team**: > 8,000 points
- **Senior Analysts**: 7,000 - 8,000 points
- **Junior Analysts**: 6,000 - 7,000 points
- **Senior Trainee**: 5,000 - 6,000 points
- **Junior Trainee**: 4,000 - 5,000 points
- **Elementary**: < 4,000 points
- **Support Team**: Contractors with > 1,000 points

### Dynamic Threshold Adjustment

The system can dynamically adjust thresholds:

```python
for team in staff_team:
    if team == 'lead_team':
        threshold_dict[team] = 8000
    else:
        if previous_threshold - delta > 0:
            # Subtract delta (1000)
            threshold_dict[team] = previous_threshold - delta
        else:
            # Subtract percentage (10%)
            threshold_dict[team] = previous_threshold - (previous_threshold * percentage / 100)
    
    previous_threshold = threshold_dict[team]
```

---

## IMAGE MANAGEMENT

### Google Drive Integration

**Image URL Structure:**
```
{{ googledriveurl }}{{ member.img_url }}
```

- `googledriveurl`: Base Google Drive URL (from settings)
- `member.img_url`: Google Drive file ID (stored in `Assets.image_url`)

### Image Fallback Logic

```javascript
function handleImageError(img, name) {
    img.style.height = '120px';
    img.style.width = '120px';
    
    // If image is from static folder, use default service image
    if (img.src.includes('/static/')) {
        img.src = "{% static 'main/img/service-1.jpg' %}"
    } else {
        // Otherwise, try to load profile image by first name
        img.src = "{% static 'main/img/profile/' %}" + name.toLowerCase() + ".jpeg"
    }
}
```

### Static Profile Images

**Location:** `coda/main/static/main/img/profile/`

**Available Images:**
- `amanda.jpeg`
- `brenda.jpeg`
- `caroline.jpeg`
- `ceo_profile_v1.png`
- `chris.jpeg`
- `edwin.jpeg`
- `erick.jpeg`
- `hashim.jpeg`
- `judy.jpeg`
- `kennedy.jpeg`
- `prachi.jpeg`
- `profile.jpeg` (default)
- `sylvia.jpeg`
- `victor.jpeg`

### Image Upload Process

When updating a profile via `UserProfileUpdateView`:

```python
def form_valid(self, form):
    instance = form.save()
    
    if form.cleaned_data.get('image') is not None:
        image_name = form.cleaned_data.get('image').name
        folder_id = "1qzO8GAa5jGRgFYsamGEmnrI_bHbJ6Zre"  # Google Drive folder
        image_path = instance.image.path
        
        # Upload to Google Drive
        image_id = upload_image_to_drive(image_path, folder_id, image_name)
        
        # Create Assets record
        assets_instance = Assets.objects.create(image_url=image_id)
        instance.image2 = assets_instance
    
    return super().form_valid(form)
```

---

## AI-GENERATED DESCRIPTIONS

### Function: `generate_openai_description()`

**Location:** `coda/main/views.py` (Lines 705-736)

**Purpose:** Auto-generate professional descriptions for team members

**Logic:**
```python
def generate_openai_description(user_profile):
    # Get client assessment data
    client_assessment = ClientAssessment.objects.filter(
        email=user_profile.user.email
    ).first()
    
    first_name = client_assessment.first_name
    total_points = client_assessment.totalpoints
    experience = client_assessment.it_exp
    
    # Get IT skills and ratings
    it_skills = [
        ('Non-IT Experience', client_assessment.non_it_exp),
        ('IT Experience', client_assessment.it_exp),
        ('Project Charter', client_assessment.projectcharter),
        ('Requirements Analysis', client_assessment.requirementsAnalysis),
        ('Reporting', client_assessment.reporting),
        ('ETL', client_assessment.etl),
        ('Database', client_assessment.database),
        ('Testing', client_assessment.testing),
        ('Deployment', client_assessment.deployment),
        ('Frontend', client_assessment.frontend),
        ('Backend', client_assessment.backend),
    ]
    
    # Sort by rating and take top 2 skills
    sorted_it_skills = sorted(it_skills, key=lambda x: x[1], reverse=True)
    top_it_skills = [skill[0] for skill in sorted_it_skills[:2]]
    
    # Generate description using AI
    user_message = f"Generate a description for {first_name}, a professional with {experience} years of experience in {', '.join(top_it_skills)}."
    
    response = generate_chatbot_response(user_message)
    return response.strip()
```

### When Descriptions Are Generated

In the `team()` view:

```python
for category, members in team_categories.items():
    for member in members:
        user_profile = member.user.profile
        
        # Only generate if description is missing
        if not user_profile.description:
            try:
                user_profile.description = generate_openai_description(user_profile)
            except:
                user_profile.description = 'null'
            
            user_profile.save()
```

### Example Generated Description

**Input:**
- Name: John Doe
- Experience: 5 years
- Top Skills: ETL, Database

**Output:**
> "John Doe is a seasoned professional with 5 years of experience specializing in ETL and Database management. He has demonstrated expertise in designing and implementing robust data pipelines, optimizing database performance, and ensuring data integrity across multiple enterprise systems. His technical proficiency and attention to detail make him a valuable asset to any data-driven organization."

---

## RELATED FEATURES

### 1. Testimonials System

**Function:** `get_testimonials()`  
**Location:** `coda/main/views.py` (Lines 95-117)

```python
def get_testimonials():
    count_to_class = {
        2: "col-md-6",
        3: "col-md-4",
        4: "col-md-3"
    }
    
    # Get latest testimonial from each writer
    latest_posts = Testimonials.objects.values('writer').annotate(
        latest=Max('date_posted')
    ).order_by('-latest')
    
    testimonials = []
    for post in latest_posts:
        writer = post['writer']
        
        # Filter to only client categories
        user_profile = UserProfile.objects.filter(
            user=writer, 
            user__category__in=[1, 3, 4, 5, 6, 7]  # Clients
        ).first()
        
        if user_profile:
            latest_post = Testimonials.objects.filter(
                writer=writer, 
                date_posted=post['latest']
            ).first()
            testimonials.append(latest_post)
    
    number_of_testimonials = len(testimonials)
    selected_class = count_to_class.get(number_of_testimonials, "default-class")
    
    return testimonials, selected_class
```

**Used On:**
- Homepage (`layout` view)
- Service pages
- About page

---

### 2. User Profile Update

**View:** `UserProfileUpdateView`  
**Location:** `coda/main/views.py` (Lines 1065-1096)

```python
class UserProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = UserProfile
    fields = [
        'position',
        'education',
        'description',
        'image',
        'image2',
        'is_active',
        'laptop_status'
    ]
    
    def form_valid(self, form):
        instance = form.save()
        
        # Upload to Google Drive if new image
        if form.cleaned_data.get('image'):
            image_name = form.cleaned_data.get('image').name
            folder_id = "1qzO8GAa5jGRgFYsamGEmnrI_bHbJ6Zre"
            image_path = instance.image.path
            
            image_id = upload_image_to_drive(image_path, folder_id, image_name)
            assets_instance = Assets.objects.create(image_url=image_id)
            instance.image2 = assets_instance
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('accounts:account-profile', kwargs={
            'username': self.object.user.username
        })
    
    def test_func(self):
        # Allow superusers and own profile
        return self.request.user.is_superuser or True
```

**URL:** `/updateprofile/<int:pk>/`

---

### 3. Contact Form

**View:** `contact()`  
**Location:** `coda/main/views.py` (Lines 1629-1649)

```python
@login_required
def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST, request.FILES)
        
        if form.is_valid():
            instance = form.save(commit=False)
            instance.task = 'NA'
            instance.plan = 'NA'
            instance.trained_by = request.user
            instance.save()
            
            message = 'Thank You, we will get back to you within 48 hours.'
            return render(request, "main/errors/generalerrors.html", {
                "message": message
            })
    else:
        form = ContactForm()
    
    return render(request, "main/contact/contact_message.html", {
        "form": form
    })
```

**URL:** `/contact/`

---

## TECHNICAL DETAILS

### Database Queries

#### Optimized Team Query

```python
all_member = UserProfile.objects.filter(
    user__is_active=True, 
    user__category=2
).annotate(
    education_points=Coalesce(user_education_subquery, Value(0)),
    training_points=Coalesce(employee_training_subquery, Value(0)),
    taskhistory_points=Coalesce(employee_taskhistory_subquery, Value(0)),
    requirement_points=Coalesce(employee_requiremet_subquery, Value(0)),
    clientassesment_points=Coalesce(employee_clientassesment.values('totalpoints'), Value(0)),
    total_points=(
        F('education_points') + 
        F('taskhistory_points') + 
        F('requirement_points') + 
        F('training_points') + 
        F('clientassesment_points')
    )
).order_by("user__date_joined")
```

**Features:**
- ✅ Single query with subqueries (efficient)
- ✅ Uses `Coalesce()` to handle NULL values
- ✅ Annotates calculated fields for filtering
- ✅ Orders by join date for seniority

---

### Performance Considerations

**Current Issues:**
1. **Multiple Subqueries:** 5 subqueries per team member
2. **AI Description Generation:** Happens on page load if missing
3. **Image Loading:** External Google Drive calls

**Potential Optimizations:**
1. **Cache Total Points:**
   - Add `total_points` field to `UserProfile`
   - Calculate daily via management command
   - Reduces real-time calculation overhead

2. **Pre-generate Descriptions:**
   - Run AI generation as background job
   - Store in `UserProfile.description`
   - Trigger on profile updates only

3. **Image Optimization:**
   - Serve from CDN instead of Google Drive
   - Use image thumbnails for profile cards
   - Lazy load images below fold

---

### Security Considerations

**Current Security:**
- ✅ `@login_required` on update views
- ✅ `UserPassesTestMixin` for edit permissions
- ✅ CSRF protection on forms
- ✅ File upload validation

**Potential Risks:**
- ⚠️ Total points visible to admins only (good)
- ⚠️ Profile descriptions may contain PII
- ⚠️ Image URLs are public (Google Drive)

**Recommendations:**
1. Add rate limiting to AI generation
2. Sanitize user-uploaded descriptions
3. Implement image access controls
4. Add audit logging for profile changes

---

## SUMMARY

### What We Have

**Pages:**
1. `/about/` - Company overview with team preview
2. `/members/team_profiles` - Internal team categorized by performance
3. `/members/client_profiles` - Client showcase
4. `/members/future_talents` - Junior team members
5. `/members/board` - Board of Governors

**Models:**
- `UserProfile` - Team member profiles
- `Team_Members` - Category descriptions
- `Assets` - Image management
- `Testimonials` - Client reviews

**Features:**
- ✅ Dynamic team categorization
- ✅ Performance-based point system
- ✅ AI-generated descriptions
- ✅ Google Drive image integration
- ✅ Responsive design
- ✅ LinkedIn integration
- ✅ Read More/Less functionality

**Dependencies:**
- `TaskHistory` model (points)
- `Requirement` model (points)
- `Training` model (points)
- `ClientAssessment` model (points, AI input)
- `Editable` model (thresholds)
- OpenAI API (description generation)
- Google Drive API (image storage)

---

## NEXT STEPS

**If improving this system, consider:**

1. **Performance:**
   - Cache total points calculation
   - Pre-generate AI descriptions
   - Implement CDN for images

2. **Features:**
   - Add team member search/filter
   - Implement pagination for large teams
   - Add skill-based filtering
   - Create individual member detail pages

3. **Maintenance:**
   - Document threshold adjustment process
   - Create management command for point recalculation
   - Add monitoring for AI generation failures

4. **Testing:**
   - Write tests for point calculation
   - Test team categorization logic
   - Test image fallback mechanisms
   - Test AI description generation

---

**End of Documentation**

*For questions or updates, contact the development team.*

