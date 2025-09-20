# 🚀 CURSOR AI QUICK REFERENCE CARD

## **⚡ IMMEDIATE WORKFLOW CHECKLIST**

### **🔍 START EVERY CHAT:**
1. ✅ Read `CURSOR_AI_WORKFLOW_README.md`
2. ✅ Check current TODO status
3. ✅ Review recent commits
4. ✅ Follow standard workflow

---

## **📋 STANDARD WORKFLOW:**
```
📚 Read Docs → 🔍 Analyze Code → 📝 Create Analysis → 📋 Plan Implementation → 
🧪 TDD Development → ✅ Local Testing → 🚀 UAT Deploy → ⏳ Get Approval → 🎯 Production
```

---

## **🚨 CRITICAL RULES:**
- ❌ **NEVER deploy to production without permission**
- ✅ **ALWAYS deploy to UAT (`codamakutano`) first**
- 🔍 **ALWAYS check for existing implementations**
- 📚 **ALWAYS read documentation first**
- 🧪 **ALWAYS use comprehensive local testing**

---

## **⚡ QUICK COMMANDS:**
```bash
# Local Testing
python manage.py check --settings=coda_project.local_settings

# UAT Deployment
git push heroku 25.10_CODA_STG_CM:main --app codamakutano

# Production (WITH PERMISSION ONLY)
git push heroku 25.10_CODA_STG_CM:main --app codatrainingapp
```

---

## **📊 CURRENT STATUS:**
- **Branch**: `25.10_CODA_STG_CM`
- **UAT App**: `codamakutano`
- **Production App**: `codatrainingapp`
- **Local Settings**: Enhanced (more rigorous than production)
- **Slug Size**: ~187MB (optimized from 396MB)

---

## **🎯 NEXT ACTIONS:**
1. Remove duplicate function implementations
2. Deploy optimized changes to UAT
3. Get approval for production deployment

---

**📝 Reference this card at the start of every session for immediate context.**

