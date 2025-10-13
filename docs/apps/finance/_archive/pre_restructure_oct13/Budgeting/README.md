# CODA BUDGET SYSTEM - DOCUMENTATION

**Last Updated:** October 2, 2025

---

## 📚 **CORE DOCUMENTS** (Read These)

### 1. **MASTER_REFERENCE.md** 📘
**Complete technical documentation**
- System architecture, models, APIs
- Critical fixes and debugging guides
- Development workflow
- **Read this for:** Technical questions, bug fixes, architecture

### 2. **CURRENT_STATE_AND_ROADMAP.md** 📊
**Project status and planning**
- What's done (Phases 1-2), what's in progress (Phase 3), what's next
- Known issues and blockers
- Key metrics
- **Read this for:** Project status, priorities, next steps

### 3. **GETTING_STARTED_PROMPTS.md** 🤖
**Cursor AI prompt templates**
- Copy-paste prompts for new chat sessions
- Task-specific templates
- **Use this when:** Starting new Cursor chat

### 4. **.cursorrules** (at project root)
**AI behavior rules**
- Context for Cursor AI
- Code patterns and practices
- **Auto-loaded by Cursor**

---

## 🎯 **QUICK NAVIGATION**

**I want to...**

| Task | Document | Section |
|------|----------|---------|
| Understand the system | MASTER_REFERENCE.md | Quick Context + Architecture |
| Know current status | CURRENT_STATE_AND_ROADMAP.md | Executive Dashboard |
| Fix a bug | MASTER_REFERENCE.md | Debugging Guide |
| Add a feature | MASTER_REFERENCE.md | Development Workflow |
| Deploy changes | MASTER_REFERENCE.md | Deployment |
| Start Cursor chat | GETTING_STARTED_PROMPTS.md | Standard Prompts |
| See data insights | MASTER_REFERENCE.md | Data Analysis |

---

## 📂 **FILE STRUCTURE**

```
Budgeting/
├── README.md                          # ← You are here
├── MASTER_REFERENCE.md                # Technical docs (~700 lines)
├── CURRENT_STATE_AND_ROADMAP.md       # Status & roadmap (~600 lines)
├── 01_PRODUCTION_ROADMAP.md           # Historical reference
└── ARCHIVE_OLD_DOCS/                  # 20+ old docs (consolidated)
```

---

## ✅ **DOCUMENTATION CONSOLIDATION**

**Before:** 24 scattered markdown files  
**After:** 4 core documents  
**Result:** 83% reduction, easier to navigate

**Old docs archived** in `ARCHIVE_OLD_DOCS/` for reference.

---

## 🚀 **QUICK LINKS**

### Live System:
- UAT: https://codamakutano.herokuapp.com
- Dashboard: https://codamakutano.herokuapp.com/finance/budget-dashboard/coda/
- Smart Form: https://codamakutano.herokuapp.com/finance/transaction/smart-entry/

### Code:
- Main: `coda/finance/`
- Models: `coda/finance/models.py`
- Views: `coda/finance/views_*.py`

---

**Start with MASTER_REFERENCE.md for technical info.**  
**Start with CURRENT_STATE_AND_ROADMAP.md for project status.**

*Last Updated: October 2, 2025*

