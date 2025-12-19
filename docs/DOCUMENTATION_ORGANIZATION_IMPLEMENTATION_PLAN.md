# Documentation Organization - Implementation Plan

**Date:** December 2025  
**Status:** Approved - Ready for Implementation  
**Based on:** Feedback from DOCUMENTATION_ORGANIZATION_PROPOSAL.md

---

## ✅ Approved Changes Summary

### 1. Document Lifecycle Management ✅
- **Active documents:** Keep current versions only
- **Archive old versions:** Move `*_v1.md`, `*_v2.md`, `*_OLD.md` to `docs/_archive/`
- **Use Git for versioning:** No more file-based versioning

### 2. Master Document Consolidation ✅
- **Use existing 7-doc structure** instead of creating new subdirectories
- Consolidate `MASTER_CODA_TASK_PAY_CAREER_DAF_SYSTEM_v2.md` into:
  - `01_ANALYSIS.md` (analysis sections)
  - `02_REQUIREMENTS.md` (requirements sections)
  - `03_ARCHITECTURE.md` (architecture sections)
  - `04_IMPLEMENTATION.md` (implementation sections)
- Archive master doc after consolidation verified

### 3. Analysis Report Consolidation ✅
- Merge analysis reports into `01_ANALYSIS.md`
- Archive original reports after consolidation
- Keep consolidated version as single source of truth

### 4. Organize by Concern Type ✅
- Group implementation docs by infrastructure, architecture, development
- **Keep app-specific docs in app directories** (for easy sharing)
- Keep cross-cutting concerns in `docs/03_IMPLEMENTATION/`

### 5. Storage Optimization ✅
- Archive old versions (30-40 files)
- Consolidate duplicates
- Use references instead of duplication
- Compress large historical documents

---

## 📋 Implementation Phases

### Phase 1: Archive Old Versions (Immediate - Day 1)

#### Tasks:
1. Create `docs/_archive/` directory structure
   ```bash
   docs/_archive/
   ├── 2024/
   ├── 2025/
   └── deprecated/
   ```

2. Identify versioned files:
   ```bash
   find docs -name "*_v*.md" -o -name "*_OLD.md" -o -name "*old*.md"
   ```

3. Verify latest versions are current:
   - `MASTER_CODA_TASK_PAY_CAREER_DAF_SYSTEM_v2.md` → verify `v2` is latest
   - Check for any `*_v1.md` files

4. Move old versions to archive:
   - Move `MASTER_CODA_TASK_PAY_CAREER_DAF_SYSTEM.md` (old version) to `_archive/2025/`
   - Move any `*_v1.md` files to `_archive/`

5. Update references in active docs

**Expected Reduction:** 2-5 files moved to archive

---

### Phase 2: Consolidate Master Document into 7-Doc Structure (Week 1)

#### Target: `MASTER_CODA_TASK_PAY_CAREER_DAF_SYSTEM_v2.md` (2807 lines)

#### Tasks:

1. **Analyze master document structure:**
   - Map sections to 7-doc categories:
     - Analysis sections → `01_ANALYSIS.md`
     - Requirements sections → `02_REQUIREMENTS.md`
     - Architecture sections → `03_ARCHITECTURE.md`
     - Implementation sections → `04_IMPLEMENTATION.md`

2. **Consolidate into existing files:**
   - **01_ANALYSIS.md** (currently 164 lines):
     - Add: Domain Overview & Current State
     - Add: High-Level Goals
     - Add: Analysis from TASK_SYSTEM_ANALYSIS_REPORT.md
     - Add: Analysis from PAYSLIP_PAYROLL_ANALYSIS_REPORT.md
   
   - **02_REQUIREMENTS.md** (currently 559 lines):
     - Add: Policy Knobs & Default Values
     - Add: Business Rules from Think-Ahead Rounds
     - Add: Requirements from master doc
   
   - **03_ARCHITECTURE.md** (currently 774 lines):
     - Add: Target Architecture sections
     - Add: Service Layers
     - Add: Career Ladder structures
     - Add: Pay Philosophy & Safety Nets
     - Add: DAF UX Expectations
   
   - **04_IMPLEMENTATION.md** (currently 994 lines):
     - Add: Implementation Status
     - Add: Key Files and Locations
     - Add: Technical Patterns and Constraints
     - Add: Implementation Roadmap

3. **Verify consolidation:**
   - Check all sections are covered
   - Verify no information loss
   - Test that consolidated docs are complete

4. **Archive master document:**
   - Move `MASTER_CODA_TASK_PAY_CAREER_DAF_SYSTEM_v2.md` to `_archive/2025/`
   - Update README to reference 7-doc structure instead

**Expected Result:** 
- Master doc archived
- 7-doc structure contains all information
- Better organization and navigation

---

### Phase 3: Consolidate Analysis Reports (Week 1-2)

#### Target Files:
- `TASK_SYSTEM_ANALYSIS_REPORT.md` (1000 lines)
- `PAYSLIP_PAYROLL_ANALYSIS_REPORT.md` (1400 lines)

#### Tasks:

1. **Review analysis reports:**
   - Identify unique content in each report
   - Map to appropriate 7-doc sections

2. **Consolidate into 01_ANALYSIS.md:**
   - Extract Task System Analysis → `01_ANALYSIS.md`
   - Extract Payroll System Analysis → `01_ANALYSIS.md`
   - Organize by system component

3. **Archive original reports:**
   - Move to `_archive/2025/` after consolidation verified
   - Keep for reference if needed

**Expected Reduction:** 2 files archived

---

### Phase 4: Organize Implementation Docs (Week 2)

#### Tasks:

1. **Create subdirectories in `docs/03_IMPLEMENTATION/`:**
   ```
   docs/03_IMPLEMENTATION/
   ├── Infrastructure/
   │   ├── Branch_Management.md (from BRANCH_MANAGEMENT_STRATEGY.md)
   │   └── Shared_Core_Migration.md (from SHARED_CORE_MIGRATION_COMPLETE.md)
   ├── Architecture/
   │   └── Management_Decoupling.md (from PROMPTS.md)
   └── Development/
       └── Quick_Start_Guides.md (consolidate QUICK_START_PROMPT.md)
   ```

2. **Move and rename files:**
   - `BRANCH_MANAGEMENT_STRATEGY.md` → `Infrastructure/Branch_Management.md`
   - `SHARED_CORE_MIGRATION_COMPLETE.md` → `Infrastructure/Shared_Core_Migration.md`
   - `PROMPTS.md` → `Architecture/Management_Decoupling.md`

3. **Update README files:**
   - Update `docs/03_IMPLEMENTATION/README.md` with new structure
   - Update cross-references in other docs

**Expected Result:** Better organization, easier navigation

---

### Phase 5: Clean Up and Optimize (Week 3)

#### Tasks:

1. **Remove truly redundant documents:**
   - Identify duplicates
   - Verify information is preserved elsewhere
   - Archive or remove

2. **Update all cross-references:**
   - Search for references to moved files
   - Update links and paths
   - Verify all links work

3. **Create documentation index:**
   - Update main `docs/README.md` (if exists)
   - Create navigation guide

4. **Final verification:**
   - Check file count reduction
   - Verify storage reduction
   - Test documentation navigation

**Expected Reduction:** 5-10 additional files

---

## 📊 Expected Results

### File Count
- **Before:** 216 files
- **After:** ~180-190 files (12-17% reduction)
- **Archived:** ~25-30 files

### Storage
- **Before:** ~2.3 MB
- **After:** ~1.8-2.0 MB (13-22% reduction)
- **Archived:** ~0.3-0.5 MB

### Organization
- ✅ Master documents consolidated into 7-doc structure
- ✅ Analysis reports merged
- ✅ Implementation docs organized by concern
- ✅ Old versions archived
- ✅ Better navigation and maintainability

---

## 🔍 Verification Checklist

After each phase:
- [ ] All information preserved
- [ ] No broken links
- [ ] README files updated
- [ ] Cross-references updated
- [ ] Git history maintained
- [ ] Archive structure created

---

## 🚀 Quick Start Commands

### Create Archive Structure
```bash
mkdir -p docs/_archive/{2024,2025,deprecated}
```

### Find Versioned Files
```bash
find docs -name "*_v*.md" -o -name "*_OLD.md" -o -name "*old*.md"
```

### Find Large Files (>1500 lines)
```bash
find docs -name "*.md" -exec wc -l {} \; | awk '$1 > 1500 {print}'
```

### Check File Sizes
```bash
find docs -name "*.md" -exec du -k {} \; | sort -rn | head -20
```

---

## 📝 Notes

- **Information Integrity:** All information will be preserved (archived, not deleted)
- **Git History:** Use Git for versioning, not file versions
- **7-Doc Structure:** Use existing framework, don't create new structures
- **App Sharing:** Keep app-specific docs in app directories for easy sharing
- **Gradual Migration:** Phases can be done incrementally

---

**Status:** Ready for Implementation  
**Next Step:** Begin Phase 1 - Archive Old Versions



