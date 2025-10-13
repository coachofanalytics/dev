# CODA Development - Documentation Index
**Last Updated:** October 13, 2025  
**Purpose:** Single source of truth for finding documentation

---

## 📖 **START HERE**

### For Finance/Budget System:
→ **[coda/docs/apps/finance/README.md](coda/docs/apps/finance/README.md)**  
   Complete index of all finance documentation

### For Deployment Information:
→ **[coda/docs/05_DEPLOYMENT/OCT13_SESSION_SUMMARY.md](coda/docs/05_DEPLOYMENT/OCT13_SESSION_SUMMARY.md)**  
   Latest deployment session summary

### For Current Issues:
→ **[coda/docs/05_DEPLOYMENT/KNOWN_ISSUES.md](coda/docs/05_DEPLOYMENT/KNOWN_ISSUES.md)**  
   Known bugs and workarounds

---

## 🗂️ DOCUMENTATION STRUCTURE

```
coda/docs/
│
├── apps/                           # App-specific documentation
│   ├── finance/
│   │   ├── README.md              ⭐ Finance app index
│   │   ├── BUDGET_APPROVAL_SYSTEM.md  ⭐ Main reference
│   │   ├── planning/              # Future implementation plans
│   │   ├── features/              # Feature documentation
│   │   └── [subsystems]/          # Budgeting, Loans, Payments
│   │
│   ├── management/
│   ├── investing/
│   └── [other apps]/
│
├── 01_GETTING_STARTED/            # Setup guides
├── 05_DEPLOYMENT/                 # Deployment documentation
│   ├── OCT13_SESSION_SUMMARY.md   # Latest session
│   ├── KNOWN_ISSUES.md            # Current issues
│   ├── SCHEMA_ALIGNMENT_FIXES.md  # Schema fixes
│   └── archive/                   # Old session docs
│
├── project_management/            # PM docs
└── [other directories]/
```

---

## 📋 DOCUMENTATION STANDARDS

### ✅ DO:
- **One document per topic** (system, feature, or major plan)
- **Update existing docs** instead of creating new ones
- **Use clear hierarchical structure** (app → subsystem → feature)
- **Link related docs** for easy navigation
- **Archive old versions** instead of deleting

### ❌ DON'T:
- Create random .md files in project root
- Duplicate information across files
- Create session-specific docs (consolidate into summaries)
- Let docs go stale (update as you go)

---

## 🎯 WHEN TO CREATE NEW DOCS

### Create New Doc When:
1. **New major feature** → `coda/docs/apps/{app}/features/FEATURE_NAME.md`
2. **New implementation plan** → `coda/docs/apps/{app}/planning/PLAN_NAME.md`
3. **Deployment session** → `coda/docs/05_DEPLOYMENT/DATE_SESSION_SUMMARY.md`

### Update Existing Doc When:
1. **Bug fix** → Update Known Issues + main system doc
2. **Feature enhancement** → Update feature doc
3. **Status change** → Update system doc status section
4. **Business requirements change** → Update requirements doc

---

## 📊 CURRENT DOCUMENTATION HEALTH

### Finance App: ✅ EXCELLENT
- Clear index (README.md)
- Consolidated main reference (BUDGET_APPROVAL_SYSTEM.md)
- Organized planning docs (planning/ directory)
- Feature docs separated (features/ directory)

### Deployment: ✅ GOOD
- Latest session documented
- Known issues tracked
- Archive system in place

### Other Apps: ⚠️ NEEDS REVIEW
- Some apps have good structure
- Others need consolidation
- Future cleanup task

---

## 🔍 FINDING INFORMATION

### "How do I...?"

**Set up development environment?**  
→ `coda/docs/01_GETTING_STARTED/README.md`

**Understand budget approvals?**  
→ `coda/docs/apps/finance/BUDGET_APPROVAL_SYSTEM.md`

**Deploy to UAT/Production?**  
→ `coda/docs/05_DEPLOYMENT/OCT13_SESSION_SUMMARY.md`

**Know current bugs?**  
→ `coda/docs/05_DEPLOYMENT/KNOWN_ISSUES.md`

**Plan Phase 2 implementation?**  
→ `coda/docs/apps/finance/planning/PHASE2_DATA_DRIVEN_APPROVAL_PLAN.md`

**Use theme switcher?**  
→ `coda/docs/apps/finance/features/THEME_SWITCHER.md`

---

## 🔄 MAINTENANCE SCHEDULE

### After Each Session:
- [ ] Update deployment summary
- [ ] Update known issues
- [ ] Update relevant system docs
- [ ] Archive any temporary docs

### Monthly:
- [ ] Review all docs for accuracy
- [ ] Consolidate duplicate information
- [ ] Update status sections
- [ ] Clean up archive

### Quarterly:
- [ ] Major documentation review
- [ ] Reorganize if structure changed
- [ ] Update standards
- [ ] Archive obsolete docs

---

## 📞 DOCUMENTATION HELP

**Questions about docs?**
- Check this index first
- Check app-specific README
- Check deployment summaries

**Want to add new docs?**
- Follow the structure above
- One doc per topic
- Link from relevant READMEs
- Update this index if adding new category

---

## 🎯 GOALS

1. **Easy to Find** - Clear hierarchy, good index
2. **Easy to Update** - One place per topic
3. **Stay Current** - Update as you go
4. **No Duplication** - Consolidate ruthlessly
5. **Quality over Quantity** - Fewer, better docs

---

**Total Organized Docs:** ~10 active (down from 14+ scattered)  
**Archive:** 6 files (old session docs)  
**Structure:** ✅ Clean and navigable  
**Next Review:** After Phase 2 implementation

