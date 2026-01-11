# Option: Move Training Model to professional_services

**Date:** January 3, 2026  
**Question:** If Training is the only model using FeaturedCategory, why not move Training to professional_services?  
**Current Issue:** `Training` model in `management` app depends on `FeaturedCategory` models from `professional_services`

---

## 🔍 Analysis Results

### Current Situation

**Training Model Location:**
- ✅ **Exists in:** `coda/management/models.py` (line 26)
- ❌ **Does NOT exist in:** `coda/professional_services/models.py`
- **Note:** professional_services has `TrainingService` but not `Training` model

**Training Usage:**
- **Management app:** 95 references to Training
- **Professional services:** 27 references to Training (views, templates, services)
- **Key finding:** `TrainingAdmin` in management creates Tasks automatically when training sessions >= 35

---

## 📊 Training Model Usage Analysis

### In Management App

**Files using Training:**
- `coda/management/models.py` - Model definition
- `coda/management/admin.py` - `TrainingAdmin` (creates Tasks automatically)
- `coda/management/legacy_views.py` - Import only (note about dependency)
- Various services/tests - References to Training model

**Key Integration: `TrainingAdmin.save_model()`**

The `TrainingAdmin` in management has special logic that:
1. Creates Tasks automatically when training sessions >= 35
2. Promotes user to staff (`is_staff = True`)
3. Creates default tasks (General Meeting, BI Session, One on One, etc.)

**This is INTEGRATED with task management!**

### In Professional Services App

**Training functionality exists:**
- `coda/professional_services/services/training/training_service.py` - TrainingService
- `coda/professional_services/views.py` - Training views (training, TrainingView, CourseView, etc.)
- `coda/professional_services/templates/.../training/` - Training templates
- `coda/professional_services/urls.py` - Training URLs (training/, train/, bitraining/, etc.)

**But:** No `Training` model in professional_services - they likely use management's Training model!

---

## 💡 Recommendation: Move Training to professional_services ✅

### Why This Makes Sense

1. **Domain Alignment:**
   - ✅ Training is professional services domain (HR/training/employee development)
   - ✅ FeaturedCategory models are in professional_services
   - ✅ professional_services already has training views/templates/services
   - ✅ Natural grouping (all training-related code together)

2. **Solves Dependency Issue:**
   - ✅ No cross-app ForeignKey dependency
   - ✅ Training and FeaturedCategory in same app
   - ✅ Management app no longer depends on professional_services models
   - ✅ Cleaner architecture

3. **Simpler Than Other Options:**
   - ✅ No nullable fields needed
   - ✅ No model duplication
   - ✅ No shared_core moves
   - ✅ Just move the model and related code

### Challenge: TrainingAdmin Integration with Task Creation

**Issue:** `TrainingAdmin.save_model()` creates Tasks automatically - this integrates Training with task management.

**Solutions:**

**Option A: Keep TrainingAdmin in management (Recommended)**
- Move Training model to professional_services
- Keep `TrainingAdmin` in management/admin.py
- Import Training from professional_services: `from professional_services.models import Training`
- This keeps task creation logic in management (where Tasks are)
- Training model moves to its natural home (professional_services)

**Option B: Move TrainingAdmin to professional_services**
- Move Training model to professional_services
- Move `TrainingAdmin` to professional_services/admin.py
- Create Tasks via interface/helper (management interface or shared service)
- More complex - need to handle task creation across apps

**Option C: Split functionality**
- Move Training model to professional_services
- Keep TrainingAdmin in management but make it optional (conditional import)
- Use interface pattern for task creation (can use NoOp if management not installed)

---

## 📋 Implementation Plan: Move Training to professional_services

### Step 1: Move Model

```python
# From: coda/management/models.py (line 26-107)
# To: coda/professional_services/models.py

class Training(models.Model):
    # Move entire class definition
    # ... all fields and methods ...
```

### Step 2: Update Imports

**In management/admin.py:**
```python
# OLD: from management.models import Training
# NEW: from professional_services.models import Training

from professional_services.models import Training

class TrainingAdmin(admin.ModelAdmin):
    # ... existing code unchanged ...
    # Still creates Tasks in management (good - tasks belong in management)
```

**In management/legacy_views.py:**
```python
# OLD: from management.models import Training
# NEW: from professional_services.models import Training
```

**In other files that use Training:**
- Update imports to `from professional_services.models import Training`

### Step 3: Create Migration

```bash
# Django will create migration to move model from management to professional_services
python manage.py makemigrations management professional_services
```

**Migration will:**
- Remove Training table from management app
- Add Training table to professional_services app
- Preserve all data (table structure stays same, just ownership changes)

### Step 4: Update Code References

**Files to update:**
- `coda/management/admin.py` - Update import
- `coda/management/legacy_views.py` - Update import
- Any other files that import Training from management

### Step 5: Test

- Test Training model works in professional_services
- Test TrainingAdmin still creates Tasks correctly
- Test training views/templates still work
- Test management app doesn't break

---

## ✅ Pros

1. **Domain Alignment:**
   - ✅ Training belongs with FeaturedCategory (same domain)
   - ✅ professional_services already has training functionality
   - ✅ Natural grouping

2. **Solves Dependency Issue:**
   - ✅ No cross-app ForeignKey dependency
   - ✅ Management app no longer depends on professional_services models
   - ✅ Cleaner architecture

3. **Simpler:**
   - ✅ No nullable fields needed
   - ✅ No model duplication
   - ✅ Just move model and update imports

4. **TrainingAdmin Integration:**
   - ✅ Can keep TrainingAdmin in management (imports Training from pro_services)
   - ✅ Task creation logic stays in management (where Tasks are)
   - ✅ Clean separation: Training model in pro_services, Task creation in management

---

## ⚠️ Cons / Considerations

1. **TrainingAdmin Integration:**
   - ⚠️ TrainingAdmin creates Tasks (integrated with task management)
   - ⚠️ Need to decide: Keep TrainingAdmin in management or move it?
   - ✅ **Recommended:** Keep TrainingAdmin in management, import Training from pro_services

2. **Code Movement:**
   - ⚠️ Need to move model
   - ⚠️ Need to update imports
   - ⚠️ Need to create migration
   - ✅ **Benefit:** Cleaner than other options

3. **Breaking Changes:**
   - ⚠️ Any code importing `management.models.Training` breaks
   - ⚠️ Need to update all imports
   - ✅ **Mitigation:** Django migration preserves data, imports are straightforward to update

4. **Training Usage:**
   - ⚠️ 95 references in management app
   - ⚠️ Need to update all imports
   - ✅ **Benefit:** Most are just imports (easy to update)

---

## 🎯 Recommendation: MOVE TRAINING TO professional_services ✅

### Why This Is The Best Option

1. **Makes Domain Sense:**
   - Training is professional services domain (HR/training)
   - FeaturedCategory is professional services domain
   - They belong together

2. **Solves The Problem:**
   - No cross-app dependency
   - Management app no longer depends on professional_services models
   - Clean architecture

3. **Simpler Than Alternatives:**
   - No nullable fields
   - No model duplication
   - No shared_core moves
   - Just move model and update imports

4. **TrainingAdmin Can Stay in Management:**
   - Import Training from professional_services
   - Task creation logic stays in management (where Tasks are)
   - Clean separation of concerns

### Implementation Approach

**Recommended: Option A - Keep TrainingAdmin in Management**

- ✅ Move Training model to professional_services
- ✅ Keep TrainingAdmin in management/admin.py
- ✅ Import: `from professional_services.models import Training`
- ✅ TrainingAdmin creates Tasks (stays in management - tasks belong in management)
- ✅ Clean separation: Training model in pro_services, Task logic in management

**This approach:**
- ✅ Solves dependency issue (Training in pro_services with FeaturedCategory)
- ✅ Keeps task creation logic in management (where Tasks are)
- ✅ Clean domain boundaries (Training in pro_services, Tasks in management)
- ✅ Minimal disruption (just move model, update imports)

---

## 📋 Files That Need Updates

### Must Update (Import Changes)

1. `coda/management/admin.py` - Update Training import
2. `coda/management/legacy_views.py` - Update Training import
3. Any other files that import Training from management

### Migration

1. Django migration to move model from management to professional_services
2. Migration preserves all data (table structure unchanged)

### Optional (Can Keep TrainingAdmin in Management)

- `coda/management/admin.py` - Keep TrainingAdmin, just update import
- Task creation logic stays in management (good - tasks belong in management)

---

## 🎯 Final Recommendation

**✅ MOVE TRAINING MODEL TO professional_services**

**Approach:**
1. Move Training model from `management/models.py` to `professional_services/models.py`
2. Keep `TrainingAdmin` in `management/admin.py` (imports Training from pro_services)
3. Update all imports to `from professional_services.models import Training`
4. Create migration
5. Test

**Benefits:**
- ✅ Solves dependency issue (Training with FeaturedCategory in same app)
- ✅ Domain alignment (training is professional services)
- ✅ Simpler than other options
- ✅ Clean separation (Training in pro_services, Task creation in management)

**This is the cleanest solution!** 🎯

---

**Status:** Recommended - Move Training to professional_services  
**Last Updated:** January 3, 2026
