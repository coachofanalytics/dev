# 🔗 Dependency Management Strategy for Sharing Apps

## 🎯 Problem
When sharing the `investing` app with external developers, we need to handle:
- **Required dependencies**: `main` and `accounts` (base models, utils, credential store)
- **Optional dependencies**: `finance`, `ai_services` (already handled with try/except)
- **Security**: Don't expose other apps or sensitive code from `main`/`accounts`

---

## 📊 Current Dependencies Analysis

### ✅ Required Dependencies (Must Include)

#### From `main.models`:
```python
from main.models import TimeStampedModel, ContractBase, DocumentMixin, StatusMixin
```
- **Base model mixins** - Used by all investing models
- **Solution**: Extract only these base classes to `shared-core`

#### From `main.utils`:
```python
from main.utils import (
    path_values,
    dates_functionality,
    generate_chatbot_response,
    today_date,
    date_converter,
)
```
- **Utility functions** - Used by investing views
- **Solution**: Extract only these functions

#### From `main.filters`:
```python
from main.filters import ReturnsFilter
```
- **Django filters** - Used for filtering
- **Solution**: Extract to `shared-core`

#### From `accounts.models`:
```python
from accounts.models import CustomerUser
from accounts.choices import UserCategory
```
- **User model** - Core user functionality
- **Solution**: Extract minimal user model to `shared-core`

#### From `accounts.mixins`:
```python
from accounts.mixins import FilteredListViewMixin
```
- **View mixin** - Used by investing views
- **Solution**: Extract to `shared-core`

#### From `accounts.services.credential_store`:
```python
from accounts.services.credential_store import credential_store
```
- **API credential management** - Critical for investing (OptionPlay, Unusual Whales)
- **Solution**: Extract credential store service

### ⚠️ Optional Dependencies (Already Handled)

#### From `finance`:
```python
try:
    from finance.models import Payment_Information, Transaction
except ImportError:
    Payment_Information = None
    Transaction = None
```
- **Already optional** ✅

#### From `ai_services`:
```python
try:
    from ai_services.services.token_encryption_service import TokenEncryptionService
except ImportError:
    # Stub implementation
    class TokenEncryptionService: ...
```
- **Already optional** ✅

---

## 🏗️ Solution Architecture: Shared Core Package

### Option 1: Extract to `coda-shared-core` Package (RECOMMENDED) ⭐

Create a minimal shared package containing only what `investing` needs:

```
coda-investing/                    # Public repo
├── coda/
│   ├── investing/                # Investing app (full)
│   └── shared_core/              # Minimal shared dependencies
│       ├── models.py             # Only base mixins from main
│       ├── utils.py              # Only needed utils
│       ├── filters.py            # ReturnsFilter
│       ├── users.py              # Minimal user model
│       ├── mixins.py             # FilteredListViewMixin
│       └── services/
│           └── credential_store.py
├── requirements.txt
└── setup.py
```

### Implementation Steps

#### Step 1: Create `shared_core` Module

```python
# coda/shared_core/models.py
"""
Shared core models extracted from main.models
Contains only base model mixins needed by investing app
"""
from django.db import models
from django.utils import timezone

class TimeStampedModel(models.Model):
    """Abstract base model with created_at and updated_at timestamps"""
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    class Meta:
        abstract = True

class ContractBase(TimeStampedModel):
    """Base model for contract-related fields"""
    client_signature = models.ImageField(
        upload_to="signatures/", blank=True, null=True
    )
    company_rep = models.CharField(max_length=255, blank=True, null=True)
    contract_submitted_date = models.DateTimeField(default=timezone.now)
    client_date = models.CharField(max_length=100, null=True, blank=True)
    rep_date = models.CharField(max_length=100, null=True, blank=True)
    contract_signed = models.BooleanField(default=False)
    contract_signed_date = models.DateField(null=True, blank=True)
    
    class Meta:
        abstract = True

class DocumentMixin(models.Model):
    """Mixin for document storage"""
    documents = models.JSONField(default=list, blank=True)
    
    class Meta:
        abstract = True

class StatusMixin(models.Model):
    """Mixin for status fields"""
    status = models.CharField(max_length=50, default='pending')
    
    class Meta:
        abstract = True
```

```python
# coda/shared_core/users.py
"""
Minimal user model extracted from accounts.models
Contains only what investing app needs
"""
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomerUser(AbstractUser):
    """Minimal user model for investing app"""
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'accounts_customeruser'  # Match existing table name
```

```python
# coda/shared_core/utils.py
"""
Utility functions extracted from main.utils
Contains only functions used by investing app
"""
from django.utils import timezone
from datetime import datetime

def path_values(path):
    """Extract values from path"""
    # Implementation from main.utils
    pass

def dates_functionality(date_obj):
    """Date utility function"""
    # Implementation from main.utils
    pass

def today_date():
    """Get today's date"""
    return timezone.now().date()

def date_converter(date_str):
    """Convert date string to date object"""
    # Implementation from main.utils
    pass

def generate_chatbot_response(message):
    """Generate chatbot response"""
    # Implementation from main.utils (if needed)
    pass
```

```python
# coda/shared_core/services/credential_store.py
"""
Credential store service extracted from accounts.services.credential_store
Used for managing API keys (OptionPlay, Unusual Whales, etc.)
"""
import os
from typing import Dict, Optional
from django.conf import settings
# Minimal credential store implementation
```

#### Step 2: Update Investing Imports

```python
# coda/investing/models.py
# Before:
# from main.models import TimeStampedModel, ContractBase, DocumentMixin, StatusMixin

# After:
from shared_core.models import TimeStampedModel, ContractBase, DocumentMixin, StatusMixin
```

```python
# coda/investing/views_legacy.py
# Before:
# from main.utils import path_values, dates_functionality, ...
# from accounts.models import CustomerUser
# from accounts.mixins import FilteredListViewMixin

# After:
from shared_core.utils import path_values, dates_functionality, ...
from shared_core.users import CustomerUser
from shared_core.mixins import FilteredListViewMixin
```

#### Step 3: Update Settings

```python
# coda/coda_project/coda_settings/base_settings.py
INSTALLED_APPS = [
    "shared_core",  # Shared core package
    "investing.apps.InvestingConfig",
    # ... other apps
]

AUTH_USER_MODEL = 'shared_core.CustomerUser'  # Or keep accounts.CustomerUser if compatible
```

---

## 🎯 Option 2: Copy Minimal Dependencies (Alternative)

Instead of extracting, copy only needed code to `investing` app:

```
coda-investing/
├── coda/
│   └── investing/
│       ├── models.py
│       ├── utils.py
│       ├── base_models.py      # Copied base models
│       ├── base_utils.py       # Copied utils
│       └── ...
```

**Pros**: No external dependencies  
**Cons**: Code duplication, harder to maintain

---

## 🎯 Option 3: Submodule/Subtree (Advanced)

Use Git subtrees/submodules to include minimal `main` and `accounts`:

```
coda-investing/
├── coda/
│   ├── investing/
│   ├── main/        # Git subtree - only needed files
│   └── accounts/    # Git subtree - only needed files
```

**Pros**: Keeps code in original locations  
**Cons**: Complex setup, harder for external developers

---

## ✅ Recommended Implementation: Option 1 (Shared Core)

### Complete Structure

```
coda-investing/                          # Public repo for external developers
├── coda/
│   ├── investing/                       # Full investing app
│   │   ├── models.py                    # Updated imports
│   │   ├── views/
│   │   ├── services/
│   │   └── ...
│   └── shared_core/                     # Minimal shared dependencies
│       ├── __init__.py
│       ├── models.py                    # Base model mixins only
│       ├── utils.py                     # Needed utils only
│       ├── filters.py                   # ReturnsFilter
│       ├── users.py                     # Minimal user model
│       ├── mixins.py                    # View mixins
│       ├── choices.py                   # UserCategory choices
│       └── services/
│           └── credential_store.py      # Credential management
├── requirements.txt
├── setup.py
└── README.md
```

### Implementation Script

```bash
#!/bin/bash
# extract-investing-app.sh

# 1. Create new repo structure
mkdir -p coda-investing/coda/{investing,shared_core/services}

# 2. Copy investing app
cp -r coda/investing coda-investing/coda/

# 3. Extract shared core components
# Extract base models
grep -A 50 "class TimeStampedModel" coda/main/models.py > coda-investing/coda/shared_core/models.py
grep -A 50 "class ContractBase" coda/main/models.py >> coda-investing/coda/shared_core/models.py
# ... extract other needed classes

# 4. Extract utils
# Extract only needed functions from main.utils

# 5. Extract credential store
cp coda/accounts/services/credential_store.py coda-investing/coda/shared_core/services/

# 6. Update imports in investing app
find coda-investing/coda/investing -name "*.py" -exec sed -i '' \
    's/from main.models import/from shared_core.models import/g' {} \;
find coda-investing/coda/investing -name "*.py" -exec sed -i '' \
    's/from accounts.models import CustomerUser/from shared_core.users import CustomerUser/g' {} \;
# ... update other imports

# 7. Create setup.py
cat > coda-investing/setup.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name='coda-investing',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'Django>=3.2',
        # Only public dependencies
    ],
)
EOF

# 8. Initialize git repo
cd coda-investing
git init
git add .
git commit -m "Initial: Investing app with shared core dependencies"
```

---

## 🔒 Security Considerations

### Before Extracting Shared Core:

1. **Review all code** in shared core:
   - [ ] No references to other apps
   - [ ] No sensitive configuration
   - [ ] No database connection strings
   - [ ] No API keys hardcoded

2. **Minimize shared core**:
   - [ ] Only include what's absolutely needed
   - [ ] Remove any business logic unrelated to investing
   - [ ] Remove references to finance, management, etc.

3. **Sanitize credential store**:
   - [ ] Remove any hardcoded credentials
   - [ ] Ensure all credentials come from environment variables
   - [ ] Document required environment variables

---

## 📝 Migration Checklist

### Phase 1: Create Shared Core
- [ ] Extract base models to `shared_core/models.py`
- [ ] Extract utils to `shared_core/utils.py`
- [ ] Extract user model to `shared_core/users.py`
- [ ] Extract credential store to `shared_core/services/credential_store.py`
- [ ] Create `shared_core/__init__.py`

### Phase 2: Update Investing Imports
- [ ] Update `investing/models.py` imports
- [ ] Update `investing/views/` imports
- [ ] Update `investing/services/` imports
- [ ] Test all imports work correctly

### Phase 3: Create Separate Repo
- [ ] Create new `coda-investing` repo
- [ ] Copy investing app + shared core
- [ ] Update settings.py
- [ ] Test app works standalone

### Phase 4: Documentation
- [ ] Document shared core dependencies
- [ ] Create README for external developers
- [ ] Document required environment variables
- [ ] Create setup instructions

---

## 🎯 Final Structure Example

```
coda-investing/                          # Public GitHub repo
├── .gitignore
├── README.md                            # Setup instructions for external devs
├── requirements.txt                     # Only public dependencies
├── setup.py                            # Installable package
├── coda/
│   ├── __init__.py
│   ├── investing/                      # Full investing app
│   │   ├── __init__.py
│   │   ├── models.py                   # Uses shared_core.models
│   │   ├── views/
│   │   ├── services/
│   │   └── ...
│   └── shared_core/                    # Minimal dependencies
│       ├── __init__.py
│       ├── models.py                   # TimeStampedModel, ContractBase, etc.
│       ├── utils.py                    # path_values, dates_functionality, etc.
│       ├── filters.py                  # ReturnsFilter
│       ├── users.py                    # CustomerUser (minimal)
│       ├── mixins.py                   # FilteredListViewMixin
│       ├── choices.py                  # UserCategory
│       └── services/
│           └── credential_store.py     # API credential management
└── docs/
    └── SHARED_CORE.md                  # Documentation for shared core
```

---

## ✅ Benefits of This Approach

1. **Security**: External developers only see investing + minimal shared core
2. **Isolation**: No access to finance, management, ai_services, etc.
3. **Maintainability**: Shared core can be versioned independently
4. **Flexibility**: Can update shared core without affecting main repo
5. **Clean Dependencies**: Clear separation of what's needed vs. optional

---

**Created:** November 22, 2025  
**Status:** 📋 Implementation strategy - Ready to implement


