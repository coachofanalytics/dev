# UAT Testing Guide - AI Position Scoring System
## November 2, 2025 - Release v973

## 🎯 **TESTING SCENARIOS**

### **✅ DEPLOYMENT STATUS**

| Component | Status | Version |
|-----------|--------|---------|
| **GitHub UAT** | ✅ Pushed | 99273c833 |
| **Heroku** | ✅ Deployed | v973 |
| **Migrations** | ✅ Applied | 0008, 0009, 0010 |
| **Signals** | ✅ Loaded | Position history |
| **Services** | ✅ Ready | Scoring, collector |

---

## 📋 **TEST SCENARIOS**

### **Scenario 1: View AI Scores in Staff UI** ⭐ PRIORITY

**URL**: https://codamakutano.herokuapp.com/investing/managed/staff/suggestions/

**Steps**:
1. Login as staff user
2. Navigate to Position Suggestions page
3. Check statistics cards:
   - Should see "🤖 Avg AI Score" card (purple gradient)
   - Should see "⭐ Excellent" count card (pink gradient)
4. Check Pending tab table:
   - First column should be "🤖 AI Score"
   - Should see scores (44-74/100)
   - Should see gold star ratings (⭐ to ⭐⭐⭐⭐⭐)
   - Should see color-coded badges (EXCELLENT/GOOD/AVERAGE/BELOW_AVERAGE/POOR)
   - Rows should be highlighted (green for excellent, red for poor)
5. Check sorting:
   - Positions should be sorted by AI score (highest first)
   - RENT (74/100) should be at top if present

**Expected Results**:
- ✅ AI scores visible
- ✅ Star ratings displayed
- ✅ Color coding works
- ✅ Sorted correctly

---

### **Scenario 2: Review Position Detail with AI Breakdown** ⭐ PRIORITY

**URL**: Click "👁️" icon on any position

**Steps**:
1. From suggestions list, click "👁️ Review" on a position
2. Check for AI Analysis card at top:
   - Large score display (3em font, color-coded)
   - Star rating visualization
   - Rating badge (EXCELLENT/GOOD/etc.)
   - AI recommendation alert box (green/blue/yellow/red)
3. Check 6-Factor Breakdown:
   - Historical Win Rate (30% weight)
   - IV Rank Optimization (20% weight)
   - Greeks Profile (15% weight)
   - Risk/Reward Ratio (15% weight)
   - Earnings Safety (10% weight)
   - Liquidity Score (10% weight)
4. Check confidence level displayed

**Expected Results**:
- ✅ AI card displays at top
- ✅ All 6 factors shown with scores
- ✅ Recommendation text appropriate for score
- ✅ Color-coded based on rating

---

### **Scenario 3: Django Admin AI Scores** ⭐ PRIORITY

**URL**: https://codamakutano.herokuapp.com/admin/investing/suggestedposition/

**Steps**:
1. Login to Django admin
2. Navigate to Suggested Positions
3. Check list view:
   - "🤖 AI Score" column should show score + stars
   - Should be color-coded
   - Should be sortable (click column header)
4. Click on a position to edit
5. Check fieldsets:
   - Should see "AI Position Scoring (6-Factor Algorithm)" section
   - Should show: ai_score, ai_rating, ai_confidence_level, ai_recommendation, ai_breakdown
6. Filter by AI Rating:
   - Use filter on right side
   - Select "EXCELLENT" or "POOR"
   - List should update

**Expected Results**:
- ✅ AI scores in list view
- ✅ Sortable column
- ✅ Filter works
- ✅ Detail view shows breakdown

---

### **Scenario 4: Import CSV with Auto-Scoring** ⭐ CRITICAL

**Command**: 
```bash
heroku run "cd coda && python manage.py import_optionplay_csv short_puts /path/to/file.csv --convert --max-positions 10" --app codamakutano
```

**OR** (if CSV not available):
```bash
# Convert existing raw data
heroku run "cd coda && python manage.py test_ai_scoring_integration --count 10" --app codamakutano
```

**Expected Results**:
- ✅ Positions converted successfully
- ✅ Each position shows AI score in logs
- ✅ Scores range from 44-74 (based on quality)
- ✅ Top scores identified correctly

**Sample Output**:
```
1. RENT  - Score: 74.0/100 (AVERAGE)    ⭐⭐⭐
2. MSTR  - Score: 63.5/100 (BELOW_AVG)  ⭐⭐
3. ITM   - Score: 56.5/100 (BELOW_AVG)  ⭐⭐
...
```

---

### **Scenario 5: Verify Scoring Algorithm** ⭐ CRITICAL

**Command**:
```bash
heroku run "cd coda && python manage.py test_position_scoring" --app codamakutano
```

**Expected Results**:
- ✅ Test runs successfully
- ✅ Shows 3 sample positions scored
- ✅ AAPL scores higher than XYZ
- ✅ Breakdown shows all 6 factors
- ✅ Recommendations make sense

**Sample Output**:
```
Test 1: AAPL Bull Put Spread
Score: 77.2/100 (AVERAGE)
Breakdown:
  Historical Win Rate:   50/100 (no data yet)
  IV Rank Optimization:  80/100 (65% IV)
  Greeks Profile:        75/100 (estimated)
  Risk/Reward Ratio:    100/100 (50% ratio - excellent!)
  Earnings Safety:      100/100 (safe)
  Liquidity Score:      100/100 (highly liquid)
Recommendation: 🟡 REVIEW

Test 3: XYZ Credit Spread
Score: 35.8/100 (POOR)
Recommendation: 🔴 REJECT
```

---

### **Scenario 6: Historical Data Collection** (Future Test)

**When a position closes**:

**Steps**:
1. Close an open position (set status='closed')
2. Check that OptionsPositionHistory is created automatically
3. Verify fields populated:
   - was_profitable (True/False)
   - actual_return_percentage
   - days_held
   - performance_category

**Expected Results**:
- ✅ History created via signal
- ✅ All fields calculated correctly
- ✅ No manual intervention needed

**Command to Test**:
```bash
# Check signal loaded
heroku logs --tail --app codamakutano | grep "Position history"

# Should see:
# "📊 Position history auto-collection signals loaded"
```

---

### **Scenario 7: Check 499 Scored Positions** ⭐ DATA VERIFICATION

**URL**: https://codamakutano.herokuapp.com/admin/investing/suggestedposition/

**OR Command**:
```bash
heroku run "cd coda && python manage.py shell -c \"from investing.models import SuggestedPosition; total = SuggestedPosition.objects.count(); scored = SuggestedPosition.objects.filter(ai_score__isnull=False).count(); print(f'Total positions: {total}'); print(f'AI scored: {scored}'); print(f'Percentage: {scored/total*100:.1f}%')\"" --app codamakutano
```

**Expected Results**:
- ✅ ~499-500 SuggestedPositions exist
- ✅ All or most have ai_score populated
- ✅ Percentage close to 100%

---

### **Scenario 8: Score Distribution Analysis** ⭐ QUALITY CHECK

**Command**:
```bash
heroku run "cd coda && python manage.py shell -c \"from investing.models import SuggestedPosition; positions = SuggestedPosition.objects.filter(ai_score__isnull=False); excellent = positions.filter(ai_rating='EXCELLENT').count(); good = positions.filter(ai_rating='GOOD').count(); average = positions.filter(ai_rating='AVERAGE').count(); below_avg = positions.filter(ai_rating='BELOW_AVERAGE').count(); poor = positions.filter(ai_rating='POOR').count(); total = positions.count(); print(f'Score Distribution ({total} positions):'); print(f'EXCELLENT (95+): {excellent} ({excellent/total*100:.1f}%)'); print(f'GOOD (85-94): {good} ({good/total*100:.1f}%)'); print(f'AVERAGE (70-84): {average} ({average/total*100:.1f}%)'); print(f'BELOW_AVG (50-69): {below_avg} ({below_avg/total*100:.1f}%)'); print(f'POOR (0-49): {poor} ({poor/total*100:.1f}%)')\"" --app codamakutano
```

**Expected Distribution**:
```
EXCELLENT (95+):     0 ( 0.0%)  ← Expected: batch quality is poor
GOOD (85-94):        0 ( 0.0%)
AVERAGE (70-84):     1 ( 0.2%)  ← RENT
BELOW_AVG (50-69): ~150 (30.1%)
POOR (0-49):       ~348 (69.7%)  ← Correctly identified!
```

**Why This Is Correct**:
- OptionPlay batch had mostly low-premium positions (0.2%-4% risk/reward)
- Algorithm correctly identified them as POOR
- Only 1 position (RENT) broke into AVERAGE tier (high IV + good R/R)

---

### **Scenario 9: Test Top Performers** ⭐ QUALITY VERIFICATION

**Command**:
```bash
heroku run "cd coda && python manage.py shell -c \"from investing.models import SuggestedPosition; top_10 = SuggestedPosition.objects.filter(ai_score__isnull=False).order_by('-ai_score')[:10]; print('TOP 10 SCORED POSITIONS:'); for i, pos in enumerate(top_10, 1): print(f'{i}. {pos.symbol:6} Score: {pos.ai_score:5.1f}/100 ({pos.ai_rating:15}) Premium: \${pos.premium_collected or 0:6.2f}')\"" --app codamakutano
```

**Expected Output**:
```
TOP 10 SCORED POSITIONS:
1. RENT   Score:  74.0/100 (AVERAGE        ) Premium: $XXX.XX
2. MSTR   Score:  63.5/100 (BELOW_AVERAGE ) Premium: $XXX.XX
3. COST   Score:  60.5/100 (BELOW_AVERAGE ) Premium: $XXX.XX
...
```

**Verification**:
- ✅ Top positions have meaningful differences
- ✅ Higher scores correlate with better setups
- ✅ RENT at top (has 100% IV + 650% R/R)

---

## 🔍 **POST-DEPLOYMENT VERIFICATION**

### **1. Check Heroku Logs**
```bash
heroku logs --tail --app codamakutano
```

**Look for**:
- ✅ "Position history auto-collection signals loaded"
- ✅ "Investing app signals loaded successfully"
- ✅ No error messages
- ✅ App started successfully

---

### **2. Test Staff UI**

**Checklist**:
- [ ] Navigate to /investing/managed/staff/suggestions/
- [ ] See AI score statistics cards
- [ ] See AI score column in table
- [ ] See star ratings (⭐ to ⭐⭐⭐⭐⭐)
- [ ] See color-coded badges
- [ ] Click "👁️" on a position
- [ ] See AI Analysis card at top
- [ ] See 6-factor breakdown
- [ ] All data displays correctly

---

### **3. Test Django Admin**

**Checklist**:
- [ ] Login to admin (/admin/)
- [ ] Navigate to Suggested Positions
- [ ] See "🤖 AI Score" column with stars
- [ ] Click column header to sort
- [ ] Use "AI Rating" filter on right
- [ ] Open a position detail
- [ ] See "AI Position Scoring" section
- [ ] All AI fields populated

---

### **4. Test Management Commands**

**Test scoring algorithm**:
```bash
heroku run "cd coda && python manage.py test_position_scoring" --app codamakutano
```

**Expected**: Shows 3 sample positions scored, AAPL > TSLA > XYZ

**Test integration**:
```bash
heroku run "cd coda && python manage.py test_ai_scoring_integration --count 10" --app codamakutano
```

**Expected**: Converts 10 positions, shows AI scores, distribution stats

---

## 🐛 **TROUBLESHOOTING**

### **If AI scores not showing**:

**Check 1**: Verify migrations ran
```bash
heroku run "cd coda && python manage.py showmigrations investing" --app codamakutano
```
Should show [X] for migrations 0008, 0009, 0010

**Check 2**: Verify data exists
```bash
heroku run "cd coda && python manage.py shell -c \"from investing.models import SuggestedPosition; print(SuggestedPosition.objects.filter(ai_score__isnull=False).count())\"" --app codamakutano
```
Should show ~499

**Check 3**: Check logs for errors
```bash
heroku logs --tail --app codamakutano | grep -i error
```

---

### **If scores are all 50 (default)**:

**Cause**: Historical data not available yet (expected on Day 1)

**Solution**: This is normal! Scores will improve as:
1. Positions close (historical data collected)
2. Win rates calculated per symbol/strategy  
3. Historical Win Rate factor (30%) updates from 50 → 70-90

**Timeline**: 30-90 days for full dataset

---

### **If star ratings not showing**:

**Check**: Browser console (F12)
- Look for JavaScript errors
- Template rendering correctly

**Fix**: Clear browser cache, reload page

---

## ✅ **SUCCESS CRITERIA**

| Test | Expected Result | Status |
|------|-----------------|--------|
| **Migrations Applied** | All 3 OK | ✅ |
| **Signals Loaded** | Log shows loaded | ✅ |
| **AI Scores Visible** | Staff UI shows scores | ⏳ Test |
| **Star Ratings** | Gold stars ⭐ display | ⏳ Test |
| **Score Breakdown** | 6 factors shown | ⏳ Test |
| **Sorting Works** | Best scores at top | ⏳ Test |
| **Admin Updated** | AI column + filter | ⏳ Test |
| **Commands Work** | Test commands run | ⏳ Test |

---

## 📊 **EXPECTED DATA**

### **Current OptionPlay Batch (509 positions)**:

**Quality**: POOR overall (bond ETFs, low premiums)

**Distribution**:
- EXCELLENT: 0
- GOOD: 0
- AVERAGE: ~1 (RENT)
- BELOW_AVG: ~150 (30%)
- POOR: ~348 (70%)

**Why**: This validates the algorithm! These ARE poor positions.

**Next Steps**: 
- Import better quality CSVs (higher premiums, better symbols)
- OR wait for OptionPlay API access
- OR use TD Ameritrade API

---

## 🚀 **POST-TESTING ACTIONS**

### **After Successful UAT**:

1. **Announce to Staff**:
   - "AI Position Scoring is LIVE!"
   - "Look for star ratings ⭐⭐⭐⭐⭐"
   - "Approve positions scored 70+"
   - "Auto-reject positions scored <50"

2. **Monitor Usage**:
   - Watch Heroku logs for errors
   - Check staff feedback
   - Monitor performance

3. **Gather Feedback**:
   - Are scores helpful?
   - Is UI intuitive?
   - Any missing factors?

4. **Plan Next Phase**:
   - Week 4-5: WhatsApp alerts
   - Week 6-9: Performance dashboard
   - Week 10-12: Full launch

---

## 📞 **QUICK TESTING COMMANDS**

### **All-in-One Test Suite**:

```bash
# 1. Check deployment
heroku ps --app codamakutano

# 2. Run migrations (if not done)
heroku run "cd coda && python manage.py migrate investing" --app codamakutano

# 3. Test scoring algorithm
heroku run "cd coda && python manage.py test_position_scoring" --app codamakutano

# 4. Check data
heroku run "cd coda && python manage.py shell -c \"from investing.models import SuggestedPosition; print(f'Positions: {SuggestedPosition.objects.count()}'); print(f'Scored: {SuggestedPosition.objects.filter(ai_score__isnull=False).count()}')\"" --app codamakutano

# 5. View top scores
heroku run "cd coda && python manage.py shell -c \"from investing.models import SuggestedPosition; for p in SuggestedPosition.objects.filter(ai_score__isnull=False).order_by('-ai_score')[:5]: print(f'{p.symbol}: {p.ai_score}/100')\"" --app codamakutano

# 6. Check logs
heroku logs --tail --app codamakutano
```

---

## 🎯 **TESTING PRIORITIES**

| Priority | Scenario | Time Required |
|----------|----------|---------------|
| **P0** | View AI scores in UI | 5 min |
| **P0** | Review position detail | 5 min |
| **P0** | Test scoring algorithm | 5 min |
| **P1** | Admin interface | 10 min |
| **P1** | Import CSV test | 10 min |
| **P2** | Score distribution | 5 min |

**Total Testing Time**: ~40 minutes

---

## ✅ **SIGN-OFF CHECKLIST**

Before announcing to users:

- [ ] All P0 tests passing
- [ ] UI looks good (no layout issues)
- [ ] Star ratings displaying correctly
- [ ] Scores make sense (low quality → low score)
- [ ] No errors in Heroku logs
- [ ] Admin interface functional
- [ ] Staff can filter by AI rating
- [ ] Documentation updated

---

## 📝 **BUG REPORTING**

**If you find issues**:

1. **Capture**:
   - Screenshot of issue
   - Browser console log (F12)
   - URL where it occurred
   - Heroku logs (if backend error)

2. **Report**: Include all above in message

3. **Priority**:
   - P0 (Critical): UI not displaying, migrations failed
   - P1 (High): Scores wrong, sorting broken
   - P2 (Medium): Visual issues, minor bugs
   - P3 (Low): Nice-to-haves, enhancements

---

## 🎉 **READY FOR TESTING!**

**UAT Environment**: https://codamakutano.herokuapp.com/  
**Version**: v973  
**Status**: READY  
**Migrations**: APPLIED  
**Signals**: LOADED  

**GO TEST! 🚀**

---

*AI Position Scoring System - UAT Testing Guide*  
*Release v973*  
*November 2, 2025*

