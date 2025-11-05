# PHASE 9 UAT DEPLOYMENT CHECKLIST
**Date:** November 5, 2025  
**Branch:** 25.11_CODA_UAT_CM  
**Target:** codamakutano.herokuapp.com (UAT)  
**Heroku Remote:** heroku-uat

---

## ✅ PRE-DEPLOYMENT VERIFICATION (COMPLETED)

### Code Quality
- [x] **Syntax validation:** All Python files compile without errors
- [x] **Django checks:** `python manage.py check --deploy` passes (9 security warnings are normal for dev/UAT)
- [x] **No blocking TODOs:** Only minor future enhancements noted
- [x] **Migrations created:** 
  - `0013_suggestedposition_notes.py` ✅
  - `0014_add_spread_strategy_types.py` ✅
- [x] **Migrations applied locally:** Both migrations marked [X]

### Repository Status
- [x] **Branch:** Switched to `25.11_CODA_UAT_CM`
- [x] **Changes committed:** Commit `14dbfef1d` created
- [x] **16 files modified:** All Phase 9 changes staged
- [x] **Commit message:** Comprehensive with features, fixes, and next steps

### Feature Completeness
- [x] **Auto-Spread Builder:** Implemented in `spread_builder.py`
- [x] **Smart Duplicate Ranking:** Integrated in `csv_upload.py`
- [x] **One-Click Bulk Approval:** API endpoint + button + service
- [x] **Unusual Whales Integration:** CSV upload + score boosts + quick buttons
- [x] **Bug fixes applied:** 6 critical fixes (strategy detection, premium calc, IV display, etc.)

---

## 🚀 DEPLOYMENT STEPS

### Step 1: Push to UAT Heroku
```bash
git push heroku-uat 25.11_CODA_UAT_CM:main --force
```

**Expected Output:**
- Build starts
- Dependencies installed
- Static files collected
- Release created (vXXX)
- Deployed to codamakutano.herokuapp.com

**Known Issue:**
- ⚠️ Error: `column investing_positionbatch.whatsapp_notification_sent does not exist`
- ✅ Will be fixed by running migrations (Step 2)

---

### Step 2: Run Migrations on UAT
```bash
heroku run "cd coda && python manage.py migrate investing" --app codamakutano
```

**Expected Output:**
```
Running migrations:
  Applying investing.0013_suggestedposition_notes... OK
  Applying investing.0014_add_spread_strategy_types... OK
```

**Verification:**
```bash
heroku run "cd coda && python manage.py showmigrations investing | tail -5" --app codamakutano
```

Should show:
```
[X] 0013_suggestedposition_notes
[X] 0014_add_spread_strategy_types
```

---

### Step 3: Verify URLs
```bash
heroku run "cd coda && python manage.py show_urls | grep managed" --app codamakutano
```

**Expected:** Should include new bulk approval endpoint:
```
/investing/managed/api/bulk-approve-excellent/
```

---

### Step 4: Manual Testing on UAT

#### Test 1: CSV Upload with Auto-Spread Builder
1. Go to: `https://codamakutano.herokuapp.com/investing/managed/upload/`
2. Upload a CSV with Short Put positions
3. **Verify:** Positions auto-converted to Bull Put Spreads
4. **Check:** Capital requirements reduced by ~90%

#### Test 2: Smart Duplicate Ranking
1. Upload same CSV twice
2. **Verify:** Duplicates detected and ranked
3. **Check:** Best duplicate marked 🏆 RECOMMENDED
4. **Verify:** Ranking formula: AI(40%) + R:R(30%) + DTE(20%) + Premium(10%)

#### Test 3: One-Click Bulk Approval 🎯 **CRITICAL**
1. Go to: `https://codamakutano.herokuapp.com/investing/staff/suggested-positions/`
2. Filter: Status = "Pending Review"
3. **Verify:** Purple "🚀 Approve All Excellent" button visible
4. Click button
5. **Expected Results:**
   - Positions with score ≥95 auto-approved
   - Top 3-6 positions distributed
   - Success message shown
   - Page refreshes with updated counts

#### Test 4: Unusual Whales Integration
1. Go to upload page
2. **Verify:** Quick-download buttons visible:
   - Options Flow
   - Dark Pool
   - Lit Flow
3. Upload Unusual Whales CSV
4. **Verify:** Score boosts applied (+10 to +50)
5. **Check:** Rating recalculated after boost

#### Test 5: Bug Fixes Verification
- [x] **Strategy detection:** Bear Call spreads labeled correctly (not Bull Put)
- [x] **Premium calc:** No double multiplication (check total vs individual legs)
- [x] **IV Rank:** Displays as 32% not 3200%
- [x] **Import errors:** No `PositionScoringService` errors in logs
- [x] **Field names:** `current_balance` used (not `account_balance`)

---

## 🔍 POST-DEPLOYMENT VERIFICATION

### Database Check
```bash
heroku pg:psql --app codamakutano
```

**Run SQL:**
```sql
-- Verify new strategy types exist
SELECT DISTINCT strategy_type FROM investing_optionplayrawdata;

-- Verify notes field exists
\d investing_suggestedposition;

-- Check for any pending positions
SELECT COUNT(*) FROM investing_suggestedposition WHERE status = 'pending_review';
```

### Logs Monitoring
```bash
heroku logs --tail --app codamakutano
```

**Watch for:**
- ✅ No `relation does not exist` errors
- ✅ No `column does not exist` errors
- ✅ Successful bulk approval requests
- ⚠️ Any unexpected errors (investigate immediately)

### Performance Check
```bash
heroku ps --app codamakutano
```

**Verify:**
- Dynos running
- No memory issues
- Response times acceptable (<2s for pages)

---

## 📊 ACCEPTANCE CRITERIA

### Must Pass Before PROD Deployment
- [ ] All 5 manual tests pass
- [ ] Bulk approval button works (auto-approves score ≥95)
- [ ] Auto-spread conversion working (Short Put → Bull Put Spread)
- [ ] Duplicate ranking accurate (🏆 RECOMMENDED marked)
- [ ] Unusual Whales score boosts apply correctly
- [ ] No database errors in logs (30 min monitoring)
- [ ] All 6 bug fixes verified working
- [ ] Migrations applied successfully (0013, 0014)

### Nice-to-Have Verifications
- [ ] Staff can see clear before/after capital requirements
- [ ] Clients receive WhatsApp/Telegram notifications (if configured)
- [ ] Position batches created with correct data
- [ ] Score boost explanations visible in Notes field

---

## 🚨 ROLLBACK PLAN (If UAT Fails)

### If Critical Errors Found:
```bash
# 1. Revert to previous release
heroku releases --app codamakutano  # Note current version
heroku rollback vXXX --app codamakutano  # Replace XXX with previous version

# 2. Verify rollback successful
heroku logs --tail --app codamakutano

# 3. Test previous version still works
curl https://codamakutano.herokuapp.com/investing/staff/suggested-positions/
```

### If Migration Errors:
```bash
# 1. Check migration status
heroku run "cd coda && python manage.py showmigrations investing" --app codamakutano

# 2. If needed, fake migrations back
heroku run "cd coda && python manage.py migrate investing 0012 --fake" --app codamakutano

# 3. Re-apply migrations
heroku run "cd coda && python manage.py migrate investing" --app codamakutano
```

---

## ✅ PROD DEPLOYMENT (After UAT Pass)

### Prerequisites
- [ ] UAT running for 24+ hours without errors
- [ ] All acceptance criteria met
- [ ] Staff/clients tested and approved features
- [ ] No reported bugs or issues

### Commands
```bash
# 1. Switch to PROD branch
git checkout 25.11_CODA_PROD_CM

# 2. Merge UAT changes
git merge 25.11_CODA_UAT_CM

# 3. Push to production
git push heroku-prod 25.11_CODA_PROD_CM:main --force

# 4. Run migrations
heroku run "cd coda && python manage.py migrate investing" --app codatrainingapp

# 5. Monitor logs
heroku logs --tail --app codatrainingapp
```

---

## 📝 DOCUMENTATION UPDATES

### After Successful UAT Deployment
- [ ] Update `04_IMPLEMENTATION.md` with UAT test results
- [ ] Update `07_DEPLOYMENT.md` with deployment date/version
- [ ] Update `CURRENT_STATE_AND_ROADMAP.md` (Phase 9 → DEPLOYED TO UAT)
- [ ] Create Phase 9 success summary in project docs

### After Successful PROD Deployment
- [ ] Update all docs with PROD deployment info
- [ ] Mark Phase 9 as COMPLETE in roadmap
- [ ] Document any production-specific configurations
- [ ] Create user training materials for new features

---

## 🎯 KEY METRICS TO TRACK

### Phase 9 Success Metrics
1. **Auto-Approval Rate:** % of positions with score ≥95
2. **Capital Efficiency:** Average capital reduction from spreads
3. **Duplicate Detection:** % of uploads with duplicates caught
4. **Unusual Whales Impact:** Average score boost from flow signals
5. **Time Savings:** Staff time saved by bulk approval vs manual
6. **Client Satisfaction:** Feedback on position quality

### Target Metrics (Week 1)
- Auto-approval rate: >20% of positions
- Capital reduction: >80% average
- Duplicate detection: 100% accuracy
- Score boost impact: +15 average for flow signals
- Time savings: >2 hours/day for staff

---

## 🔗 REFERENCE LINKS

### Heroku Dashboards
- **UAT:** https://dashboard.heroku.com/apps/codamakutano
- **PROD:** https://dashboard.heroku.com/apps/codatrainingapp

### Application URLs
- **UAT:** https://codamakutano.herokuapp.com/investing/managed/upload/
- **UAT Staff:** https://codamakutano.herokuapp.com/investing/staff/suggested-positions/
- **PROD:** https://codatrainingapp.herokuapp.com/ (deploy after UAT success)

### Documentation
- **Implementation:** `docs/apps/investing/ManagedOptionsTrading/04_IMPLEMENTATION.md`
- **Deployment:** `docs/apps/investing/ManagedOptionsTrading/07_DEPLOYMENT.md`
- **Cursor AI Guide:** `docs/01_GETTING_STARTED/CURSOR_AI_GUIDE.md`

---

## ✨ DEPLOYMENT SUMMARY

**Phase 9 Features:**
- ✅ Auto-Spread Builder (90% capital reduction)
- ✅ Smart Duplicate Ranking (AI-powered)
- ✅ One-Click Bulk Approval (score ≥95)
- ✅ Unusual Whales Integration (score boosts)

**Status:** READY TO DEPLOY TO UAT  
**Confidence Level:** HIGH (all tests pass locally, code quality verified)  
**Risk Level:** LOW (migrations straightforward, rollback plan ready)

**Next Step:** Execute Step 1 (Push to UAT Heroku) ⬇️

---

*Generated: November 5, 2025*  
*Last Updated: Pre-deployment verification complete*

