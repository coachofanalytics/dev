# Dynamic URL System - Usage Examples

## **How to Use the New Dynamic URL System**

### **1. In Python Views:**

```python
from coda_project.url_config import get_app_url, get_role_url

# Instead of hardcoded URLs:
success_url = "/professional_services/bitraining"

# Use dynamic URLs:
success_url = get_role_url('data', 'training', 'base')  # → /professional_services/bitraining
success_url = get_app_url('data', 'prepquestions')      # → /professional_services/prepquestions
success_url = get_role_url('data', 'interview', 'prep') # → /professional_services/prepquestions
```

### **2. In HTML Templates:**

```html
<!-- Load the template tags -->
{% load url_tags %}

<!-- Instead of hardcoded URLs: -->
<a href="/professional_services/bitraining">Training</a>

<!-- Use dynamic URLs: -->
<a href="{% app_url 'data' 'bitraining' %}">Training</a>
<a href="{% role_url 'data' 'training' 'base' %}">Training</a>
<a href="{% role_url 'data' 'interview' 'prep' %}">Interview Prep</a>
```

### **3. In JavaScript:**

```javascript
// Instead of hardcoded URLs:
window.location.href = "/professional_services/bitraining";

// Use dynamic URLs (pass from Django):
window.location.href = "{{ role_url 'data' 'training' 'base' }}";
```

### **4. Changing App Names (The Magic!):**

To change from `data` to `professional_services`, just update ONE file:

**File: `uat/coda_project/url_config.py`**
```python
APP_URLS = {
    'professional_services': 'professional_services',
    'ai_services': 'ai_services', 
    'data': 'professional_services',  # ← Change this line!
    'get_data': 'ai_services',
}
```

**That's it!** All URLs automatically update:
- `{% app_url 'data' 'bitraining' %}` → `/professional_services/bitraining`
- `get_role_url('data', 'training')` → `/professional_services/bitraining`

### **5. Available Role URLs:**

```python
# Training URLs
get_role_url('data', 'training', 'base')      # → /professional_services/bitraining
get_role_url('data', 'training', 'progress')  # → /professional_services/training_progress
get_role_url('data', 'training', 'schedule')  # → /professional_services/schedule
get_role_url('data', 'training', 'courses')   # → /professional_services/courses

# Interview URLs  
get_role_url('data', 'interview', 'base')     # → /professional_services/interview
get_role_url('data', 'interview', 'prep')     # → /professional_services/prepquestions
get_role_url('data', 'interview', 'uploads')  # → /professional_services/iuploads
get_role_url('data', 'interview', 'roles')    # → /professional_services/roles

# Project URLs
get_role_url('data', 'projects', 'base')      # → /professional_services/project_story
get_role_url('data', 'projects', 'updates')   # → /professional_services/updatelist

# Job URLs
get_role_url('data', 'jobs', 'tracker')       # → /professional_services/job_tracker
get_role_url('data', 'jobs', 'market')        # → /professional_services/job_market
```

### **6. Migration Strategy:**

1. **Phase 1:** Update `url_config.py` with current mappings
2. **Phase 2:** Replace hardcoded URLs in views with dynamic functions
3. **Phase 3:** Replace hardcoded URLs in templates with template tags
4. **Phase 4:** Test everything works
5. **Phase 5:** Change app names in `url_config.py` - everything updates automatically!

### **7. Benefits:**

✅ **Single Source of Truth:** Change app names in one place
✅ **Type Safety:** IDE autocomplete for role/action combinations  
✅ **Maintainable:** No more hunting for hardcoded URLs
✅ **Flexible:** Easy to add new roles and actions
✅ **Backward Compatible:** Legacy URLs still work via redirects
✅ **Future-Proof:** New developers can't accidentally hardcode URLs

### **8. Quick Start:**

1. Add this to your view imports:
```python
from coda_project.url_config import get_app_url, get_role_url
```

2. Add this to your template:
```html
{% load url_tags %}
```

3. Replace hardcoded URLs:
```python
# Old:
success_url = "/professional_services/bitraining"

# New:
success_url = get_role_url('data', 'training', 'base')
```

**That's it! Your URLs are now dynamic and maintainable!** 🎉
