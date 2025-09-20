# 🤖 CURSOR AI WORKFLOW README
## **COMPREHENSIVE REFERENCE GUIDE FOR ALL CHAT SESSIONS**

---

## 🎯 **CRITICAL WORKFLOW PRINCIPLES**

### **🚨 MANDATORY PROCESS (NEVER SKIP):**
1. **📚 READ DOCUMENTATION FIRST** - Always start by understanding existing docs
2. **🔍 ANALYZE EXISTING CODE** - Check current structure and implementations
3. **📋 CREATE ANALYSIS DOCUMENT** - Document findings and gaps
4. **📝 CREATE IMPLEMENTATION DOC** - Plan the approach with options
5. **🧪 FOLLOW TDD PRINCIPLES** - Test-Driven Development for all changes
6. **✅ TEST LOCALLY COMPREHENSIVELY** - Use enhanced local settings
7. **🚀 DEPLOY TO UAT ONLY** - `codamakutano` first, NEVER production without permission
8. **⏳ WAIT FOR APPROVAL** - Get explicit permission before production deployment

---

## 📁 **PROJECT STRUCTURE OVERVIEW**

### **🏗️ Architecture:**
- **Modular Monolith** - Django-based with service layers
- **Apps**: `accounts`, `ai_services`, `finance`, `investing`, `management`, `marketing`, `professional_services`, `main`, `core`
- **Service Layer**: Centralized services in `core/services/`, `ai_services/services/`, `mail/services/`

### **📂 Key Directories:**
```
app/
├── core/                    # Core functionality & monitoring
├── ai_services/            # AI integration & services
├── mail/                   # Email services & templates
├── docs/                   # Comprehensive documentation
│   ├── optimization/       # Code optimization docs
│   ├── deployment/         # Deployment guides
│   ├── testing/           # Testing documentation
│   └── development/       # Development guides
├── scripts/               # Utility scripts
└── tests/                # Test files
```

---

## 🔧 **DEVELOPMENT ENVIRONMENT SETUP**

### **Local Settings (Enhanced):**
- **File**: `app/coda_project/local_settings.py`
- **Features**: More rigorous than production
- **Logging**: Comprehensive file + console logging
- **Monitoring**: Enhanced performance monitoring
- **Testing**: All production checks PLUS additional validation

### **Key Commands:**
```bash
# Local testing
python manage.py check --settings=coda_project.local_settings
python manage.py test --settings=coda_project.local_settings

# UAT deployment
git push heroku 25.10_CODA_STG_CM:main --app codamakutano

# Production deployment (ONLY with permission)
git push heroku 25.10_CODA_STG_CM:main --app codatrainingapp
```

---

## 📋 **STANDARD WORKFLOW TEMPLATE**

### **Phase 1: Discovery & Analysis**
1. **Read existing documentation** in `app/docs/`
2. **Analyze current codebase** structure
3. **Identify existing implementations** to avoid duplication
4. **Create gap analysis** document

### **Phase 2: Planning & Documentation**
1. **Create analysis document** (`ANALYSIS.md`)
2. **Create implementation options** (`IMPLEMENTATION_OPTIONS.md`)
3. **Create TDD plan** (`TDD_PLAN.md`)
4. **Get approval** for approach before coding

### **Phase 3: Implementation**
1. **Follow TDD principles**
2. **Use existing service layers** where possible
3. **Avoid duplication** - check for existing functions
4. **Maintain code organization**

### **Phase 4: Testing & Deployment**
1. **Test locally** with comprehensive settings
2. **Deploy to UAT** (`codamakutano`) only
3. **Wait for approval** before production
4. **Document results**

---

## 🚨 **CRITICAL RULES (NEVER VIOLATE)**

### **Deployment Process:**
- ✅ **UAT First**: Always deploy to `codamakutano` first
- ❌ **No Direct Production**: Never deploy to production without explicit permission
- ⏳ **Wait for Approval**: Get user approval before any production deployment

### **Code Quality:**
- 🔍 **Check for Duplicates**: Always search for existing implementations
- 📚 **Use Service Layers**: Leverage existing `core/services/`, `ai_services/services/`
- 🧪 **Test Everything**: Use comprehensive local testing
- 📝 **Document Changes**: Create proper documentation

### **Slug Size Optimization:**
- 🗑️ **Remove Unused Files**: Delete duplicate/unused templates, functions
- 🔄 **Consolidate Functions**: Use centralized services
- 📊 **Monitor Size**: Keep Heroku slug under 300MB

---

## 📊 **OPTIMIZATION OPPORTUNITIES**

### **Known Duplications to Check:**
- **Footer Templates**: Multiple footer files (consolidate if possible)
- **Utility Functions**: `random_string_generator`, `unique_slug_generator` (use centralized services)
- **Email Functions**: Multiple email sending implementations
- **AI Functions**: Duplicate AI implementations across apps

### **Service Consolidation:**
- **Email**: Use `mail/services/email_service.py`
- **AI**: Use `ai_services/services/ai_service_facade.py`
- **Utilities**: Use `core/services/utility_service.py`

---

## 🧪 **TESTING STRATEGY**

### **Local Testing (Enhanced):**
- **Settings**: `coda_project.local_settings` (more rigorous than production)
- **Logging**: Comprehensive file + console logging
- **Monitoring**: All production checks PLUS additional validation
- **Debug Tools**: Django Debug Toolbar enabled

### **Test Coverage:**
- **Unit Tests**: Individual function testing
- **Integration Tests**: Service layer testing
- **User Flow Tests**: Complete user journey testing
- **Performance Tests**: Load and response time testing

---

## 📚 **DOCUMENTATION STANDARDS**

### **Required Documents for Each Feature:**
1. **`ANALYSIS.md`** - Current state analysis
2. **`IMPLEMENTATION_OPTIONS.md`** - Implementation approaches with pros/cons
3. **`TDD_PLAN.md`** - Test-driven development plan
4. **`TESTING_RESULTS.md`** - Test results and validation

### **Documentation Structure:**
```
app/docs/
├── optimization/          # Code optimization documentation
├── deployment/           # Deployment guides and procedures
├── testing/             # Testing documentation and results
├── development/         # Development guides and procedures
├── architecture/        # System architecture documentation
└── apps/               # Individual app documentation
```

---

## 🔄 **CONTINUATION PROTOCOL**

### **When Resuming a Chat:**
1. **Read this README** first
2. **Check current TODO status**
3. **Review recent commits**
4. **Continue from last completed task**
5. **Follow standard workflow**

### **When Starting New Feature:**
1. **Read existing documentation**
2. **Analyze current implementation**
3. **Create analysis document**
4. **Get approval for approach**
5. **Follow TDD implementation**

---

## ⚡ **QUICK REFERENCE COMMANDS**

### **Local Development:**
```bash
cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV/app
python manage.py check --settings=coda_project.local_settings
python manage.py test --settings=coda_project.local_settings
python manage.py runserver --settings=coda_project.local_settings
```

### **UAT Deployment:**
```bash
git add .
git commit -m "Feature description"
git push heroku 25.10_CODA_STG_CM:main --app codamakutano
```

### **Production Deployment (WITH PERMISSION ONLY):**
```bash
git push heroku 25.10_CODA_STG_CM:main --app codatrainingapp
```

---

## 🎯 **SUCCESS METRICS**

### **Code Quality:**
- ✅ No duplicate functions
- ✅ Proper service layer usage
- ✅ Comprehensive testing
- ✅ Clear documentation

### **Deployment:**
- ✅ UAT testing successful
- ✅ User approval obtained
- ✅ Production deployment successful
- ✅ No critical issues

### **Performance:**
- ✅ Slug size < 300MB
- ✅ Response times < 2 seconds
- ✅ No memory leaks
- ✅ Proper error handling

---

## 🚀 **NEXT STEPS TEMPLATE**

When completing a task, always provide:
1. **Summary** of what was accomplished
2. **Options** for next steps
3. **Recommendations** for optimal approach
4. **Clear next action** to take

### **📋 STANDARD WORKFLOW SEQUENCE:**
1. **Fix UAT configuration** - Resolve any deployment issues
2. **Run comprehensive test suite** - Validate all functionality
3. **Commit and deploy to UAT** - Deploy to Heroku UAT
4. **Run test suite in UAT** - Ensure app works in UAT environment
5. **Organize documentation** - Consolidate .md files into proper folders
6. **Analyze slug size** - Break down 186MB slug composition
7. **Find optimization opportunities** - Templates, models, duplicate fields
8. **Create analysis doc** - Document findings
9. **Create implementation doc** - Plan optimization approach
10. **Follow TDD approach** - Test-driven development
11. **Run tests locally** - Validate changes
12. **Deploy to UAT** - Test in staging environment
13. **Run tests in UAT** - Final validation
14. **Fix any issues** - Address problems found

---

**📝 This README should be referenced at the start of every chat session to ensure consistent, efficient workflow and avoid repetitive explanations.**
