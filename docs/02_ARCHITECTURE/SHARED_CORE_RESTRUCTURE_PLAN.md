# 🏗️ Shared Core Restructure Plan - Entire Application

## 🎯 Goal
Create a `shared_core` package that the **ENTIRE application** uses, then extracting apps for external sharing becomes trivial (no merge conflicts).

---

## 📊 Current State Analysis

### Current Import Patterns
```python
# Across the app:
from main.models import TimeStampedModel, ContractBase, DocumentMixin, StatusMixin
from main.utils import path_values, dates_functionality, ...
from accounts.models import CustomerUser
from accounts.services.credential_store import credential_store
```

### Problems with Current Approach
1. **Tight coupling** - Apps directly import from `main` and `accounts`
2. **Hard to extract** - When sharing apps, need to change imports (causes merge conflicts)
3. **Unclear dependencies** - Not clear what's shared vs. app-specific

---

## ✅ Proposed Solution: Create `shared_core` App

### Architecture

```
coda/
├── shared_core/                    # NEW: Shared package for entire app
│   ├── __init__.py
│   ├── models.py                   # Base model mixins (TimeStampedModel, etc.)
│   ├── utils.py                    # Shared utility functions
│   ├── mixins.py                   # Shared view mixins
│   ├── filters.py                  # Shared Django filters
│   ├── users.py                    # User model (re-export from accounts)
│   ├── choices.py                  # Shared choices/enums
│   └── services/
│       └── credential_store.py     # Credential management
├── main/                           # Main app (business logic)
├── accounts/                       # Accounts app (still has models, but shared_core re-exports)
├── investing/                      # Investing app (uses shared_core)
├── finance/                        # Finance app (uses shared_core)
└── ...
```

### Strategy: Re-export Pattern

Instead of moving code, **re-export** from original locations via `shared_core`:

```python
# coda/shared_core/models.py
"""
Shared core models - Re-exports base models for consistent imports
"""
from main.models import (
    TimeStampedModel,
    ContractBase,
    DocumentMixin,
    StatusMixin,
    UserReferenceMixin,
)
# Re-export so apps import from shared_core instead of main
__all__ = [
    'TimeStampedModel',
    'ContractBase',
    'DocumentMixin',
    'StatusMixin',
    'UserReferenceMixin',
]
```

```python
# coda/shared_core/users.py
"""
Shared user model - Re-export from accounts
"""
from accounts.models import CustomerUser
from accounts.choices import UserCategory

__all__ = ['CustomerUser', 'UserCategory']
```

**Benefits:**
- ✅ **No code duplication** - Original models stay in `main`/`accounts`
- ✅ **Backward compatible** - Old imports still work during transition
- ✅ **Easy migration** - Apps can migrate gradually
- ✅ **Clear structure** - `shared_core` is the official way to import shared code

---

## 📋 Implementation Plan

### Phase 1: Create `shared_core` App (No Breaking Changes)

#### Step 1.1: Create Package Structure
```bash
mkdir -p coda/shared_core/services
touch coda/shared_core/__init__.py
touch coda/shared_core/models.py
touch coda/shared_core/utils.py
touch coda/shared_core/mixins.py
touch coda/shared_core/filters.py
touch coda/shared_core/users.py
touch coda/shared_core/services/__init__.py
```

#### Step 1.2: Create Re-export Modules

```python
# coda/shared_core/models.py
"""
Shared core models - Re-exports from main.models
All apps should import from shared_core.models, not main.models
"""
from main.models import (
    TimeStampedModel,
    ContractBase,
    DocumentMixin,
    StatusMixin,
    UserReferenceMixin,
)

__all__ = [
    'TimeStampedModel',
    'ContractBase',
    'DocumentMixin',
    'StatusMixin',
    'UserReferenceMixin',
]
```

```python
# coda/shared_core/utils.py
"""
Shared utility functions - Re-exports from main.utils
"""
from main.utils import (
    path_values,
    dates_functionality,
    generate_chatbot_response,
    today_date,
    date_converter,
)

__all__ = [
    'path_values',
    'dates_functionality',
    'generate_chatbot_response',
    'today_date',
    'date_converter',
]
```

```python
# coda/shared_core/users.py
"""
Shared user models and choices - Re-exports from accounts
"""
from accounts.models import CustomerUser
from accounts.choices import UserCategory

__all__ = ['CustomerUser', 'UserCategory']
```

```python
# coda/shared_core/mixins.py
"""
Shared view mixins - Re-exports from accounts.mixins
"""
from accounts.mixins import FilteredListViewMixin

__all__ = ['FilteredListViewMixin']
```

```python
# coda/shared_core/filters.py
"""
Shared Django filters - Re-exports from main.filters
"""
from main.filters import ReturnsFilter, CredentialFilter

__all__ = ['ReturnsFilter', 'CredentialFilter']
```

```python
# coda/shared_core/services/credential_store.py
"""
Credential store service - Re-exports from accounts.services
"""
from accounts.services.credential_store import credential_store

__all__ = ['credential_store']
```

#### Step 1.3: Add to INSTALLED_APPS

```python
# coda/coda_project/coda_settings/base_settings.py
INSTALLED_APPS = [
    "shared_core.apps.SharedCoreConfig",  # NEW - Add before other apps
    "main.apps.MainConfig",
    "accounts.apps.AccountsConfig",
    # ... rest of apps
]
```

```python
# coda/shared_core/apps.py
from django.apps import AppConfig

class SharedCoreConfig(AppConfig):
    name = 'shared_core'
    verbose_name = 'Shared Core'
```

### Phase 2: Update Apps Gradually (Backward Compatible)

#### Step 2.1: Update `investing` App First

```python
# coda/investing/models.py
# BEFORE:
# from main.models import TimeStampedModel, ContractBase, DocumentMixin, StatusMixin

# AFTER:
from shared_core.models import TimeStampedModel, ContractBase, DocumentMixin, StatusMixin
```

```python
# coda/investing/views_legacy.py
# BEFORE:
# from main.utils import path_values, dates_functionality, ...
# from accounts.models import CustomerUser
# from accounts.mixins import FilteredListViewMixin

# AFTER:
from shared_core.utils import path_values, dates_functionality, ...
from shared_core.users import CustomerUser
from shared_core.mixins import FilteredListViewMixin
```

#### Step 2.2: Update Other Apps

- `finance/` - Update to use `shared_core`
- `management/` - Update to use `shared_core`
- `main/` - Can keep direct imports (it's the source) or use `shared_core` for consistency
- `accounts/` - Can keep direct imports or use `shared_core`

**Note:** During this phase, **both old and new imports work** (backward compatible).

### Phase 3: Migration Complete (All Apps Use `shared_core`)

At this point:
- ✅ All apps import from `shared_core` (not directly from `main`/`accounts`)
- ✅ Code is still in `main`/`accounts` (just re-exported)
- ✅ No breaking changes
- ✅ Ready for extraction

### Phase 4: Extract for External Sharing (No Merge Conflicts!)

When extracting `investing` app:
1. Copy `coda/investing/` to new repo
2. Copy `coda/shared_core/` to new repo
3. **That's it!** - No import changes needed (already use `shared_core`)

---

## 🔄 Migration Strategy: Gradual & Safe

### Approach: Support Both Imports During Transition

```python
# coda/shared_core/models.py
from main.models import (
    TimeStampedModel,
    ContractBase,
    DocumentMixin,
    StatusMixin,
)

# Re-export for new imports
__all__ = [
    'TimeStampedModel',
    'ContractBase',
    'DocumentMixin',
    'StatusMixin',
]

# Also make backward compatible (optional - can remove later)
import sys
import main.models as _main_models

# Add deprecation warnings (optional)
import warnings

def _deprecated_import(name):
    """Show warning for old import pattern"""
    warnings.warn(
        f"Importing {name} directly from main.models is deprecated. "
        f"Use 'from shared_core.models import {name}' instead.",
        DeprecationWarning,
        stacklevel=2
    )
```

### Migration Steps Per App

1. **Add imports** - Import from `shared_core` in addition to old imports
2. **Test** - Verify everything works
3. **Remove old imports** - Clean up old imports
4. **Test again** - Final verification

---

## 📊 Current Usage Count

Based on analysis:
- **14 files** import from `main.models` or `accounts.models`
- **Most used:** `TimeStampedModel`, `ContractBase`, `CustomerUser`
- **Gradual migration** possible (one app at a time)

---

## ✅ Benefits of This Approach

### 1. No Merge Conflicts
- Main repo already uses `shared_core`
- External repos copy `shared_core` (no changes needed)
- Both repos use same import pattern

### 2. Better Architecture
- Clear separation: shared vs. app-specific code
- Single source of truth: `shared_core` defines what's shared
- Easy to understand dependencies

### 3. Easy Extraction
- When extracting app: copy app + `shared_core` = done
- No import changes needed
- Works immediately

### 4. Future-Proof
- New apps automatically use `shared_core`
- Clear guidelines for developers
- Maintainable long-term

---

## 🚀 Quick Start Implementation

### Step 1: Create `shared_core` Package
```bash
# Create structure
mkdir -p coda/shared_core/services
touch coda/shared_core/{__init__.py,models.py,utils.py,mixins.py,filters.py,users.py}
touch coda/shared_core/services/__init__.py
touch coda/shared_core/apps.py
```

### Step 2: Create Re-export Files

I'll create these files for you with the re-export pattern.

### Step 3: Add to INSTALLED_APPS
```python
INSTALLED_APPS = [
    "shared_core.apps.SharedCoreConfig",  # Add first
    # ... rest
]
```

### Step 4: Update `investing` App First
- Update imports to use `shared_core`
- Test thoroughly
- Commit changes

### Step 5: Migrate Other Apps Gradually
- One app at a time
- Test after each migration
- No rush (both patterns work)

---

## 📝 Example: Before & After

### Before (Current)
```python
# coda/investing/models.py
from main.models import TimeStampedModel, ContractBase
from accounts.models import CustomerUser
```

### After (With shared_core)
```python
# coda/investing/models.py
from shared_core.models import TimeStampedModel, ContractBase
from shared_core.users import CustomerUser
```

### When Extracting
```bash
# Copy to external repo
cp -r coda/investing coda-external/
cp -r coda/shared_core coda-external/

# Imports already work! ✅
```

---

## 🎯 Next Steps

1. **Create `shared_core` package** - Re-export from existing code
2. **Update `investing` app first** - Test the pattern
3. **Gradually migrate other apps** - No rush, backward compatible
4. **Document the pattern** - For future developers
5. **Extract apps when ready** - No merge conflicts!

---

**Created:** November 22, 2025  
**Status:** 📋 Implementation plan - Ready to execute


