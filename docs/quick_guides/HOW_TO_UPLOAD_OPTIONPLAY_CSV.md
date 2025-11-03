# How to Upload OptionPlay CSV Data
## Quick Guide for UAT Testing

## 🎯 **WHERE TO UPLOAD CSV FILES**

### **Option 1: Django Admin (Easiest)** ⭐ **RECOMMENDED**

**URL**: https://codamakutano.herokuapp.com/admin/investing/optionplayrawdata/

**Steps**:
1. **Login to Django Admin**
   - URL: https://codamakutano.herokuapp.com/admin/
   - Use staff credentials

2. **Navigate to OptionPlay Raw Data**
   - Click "Investing" → "Option play raw datas"
   - OR direct URL: `/admin/investing/optionplayrawdata/`

3. **Add New Entry (One at a time)**
   - Click "Add Option Play Raw Data" button (top right)
   - Fill in fields manually:
     * Strategy Type: credit_spread / short_put / covered_call
     * Symbol: AAPL, TSLA, etc.
     * Sell Strike, Buy Strike, Premium, Expiry, etc.
   - Click "Save"

4. **Bulk Convert to Scored Positions**
   - Select multiple raw data entries (checkboxes)
   - From "Actions" dropdown: "Convert selected to SuggestedPositions"
   - Click "Go"
   - Positions will be AI-scored automatically!

5. **View Scored Positions**
   - Navigate to: https://codamakutano.herokuapp.com/investing/managed/staff/suggestions/
   - See AI scores with star ratings ⭐⭐⭐⭐⭐

---

### **Option 2: Management Command (Bulk Upload)** ⭐ **FOR LOCAL TESTING**

**Prerequisites**:
- Have OptionPlay CSV file downloaded
- CSV must be one of these types:
  * `credit_spreads.csv`
  * `short_puts.csv`
  * `covered_calls.csv`

**Command**:
```bash
# Local testing
cd coda
python manage.py import_optionplay_csv short_puts path/to/short_puts.csv --convert --max-positions 20 --min-premium 1.0

# On Heroku (if you can upload file)
heroku run "cd coda && python manage.py import_optionplay_csv short_puts /app/yourfile.csv --convert" --app codamakutano
```

**Parameters**:
- `short_puts` = strategy type (or credit_spreads, covered_calls)
- `path/to/file.csv` = your CSV file
- `--convert` = Auto-convert to SuggestedPosition with AI scoring
- `--max-positions 20` = Limit to top 20
- `--min-premium 1.0` = Only positions with $1+ premium
- `--min-iv 30` = Only high IV positions (30%+)
- `--symbols "AAPL,MSFT,GOOGL"` = Filter to specific symbols

---

### **Option 3: Sample CSV Files from OptionPlay Repo**

**Location**: You have OptionPlay CSV samples at:
```
C:\Users\admin\Desktop\project\coda\Opions_play_automation\*.csv
```

**Available Files**:
1. `credit_spreads.csv` (~100-200 positions)
2. `short_puts.csv` (~200-300 positions)
3. `covered_calls.csv` (~100-150 positions)

**To Upload to UAT**:

**Method A: Copy CSV content, paste in admin**
1. Open CSV in Excel/Notepad
2. Copy a few rows
3. Manually add via Django admin (Option 1 above)

**Method B: Upload locally, then migrate**
1. Upload CSVs to local database:
   ```bash
   cd C:\Users\admin\Desktop\project\coda\stg\coda
   python manage.py import_optionplay_csv short_puts C:\Users\admin\Desktop\project\coda\Opions_play_automation\short_puts.csv --convert --max-positions 50 --min-premium 1.5
   ```

2. Export SuggestedPositions:
   ```bash
   python manage.py dumpdata investing.SuggestedPosition --indent 2 > suggested_positions.json
   ```

3. Load on UAT:
   ```bash
   heroku run "cd coda && python manage.py loaddata suggested_positions.json" --app codamakutano
   ```

**Method C: Direct database import (Advanced)**
- Use Heroku dataclips
- Import CSV to Postgres directly
- Trigger conversion

---

## 🚀 **QUICK START: TEST LOCALLY FIRST**

### **Step 1: Check Data Sources**
```bash
cd coda
python manage.py check_data_sources
```

**Expected Output**:
```
📊 OPTIONPLAY RAW DATA:
  Total Entries: 509
  Unprocessed: 509
  Processed: 0

📋 SUGGESTED POSITIONS:
  Total Positions: 499
  AI Scored: 499
```

---

### **Step 2: Upload CSV Locally (If No Data)**

**Find CSV Files**:
```powershell
# Navigate to OptionPlay repo
cd C:\Users\admin\Desktop\project\coda\Opions_play_automation

# List CSV files
dir *.csv
```

**Upload Short Puts**:
```bash
cd C:\Users\admin\Desktop\project\coda\stg\coda

python manage.py import_optionplay_csv short_puts "C:\Users\admin\Desktop\project\coda\Opions_play_automation\short_puts.csv" --convert --max-positions 20 --min-premium 2.0 --min-iv 40
```

**What This Does**:
1. Reads CSV file
2. Creates OptionPlayRawData entries (509 rows)
3. Filters to top quality (min premium $2, IV 40%+)
4. Converts to SuggestedPosition (top 20)
5. **AI scores each position automatically!**
6. Ready for staff review

---

### **Step 3: Verify AI Scoring Worked**
```bash
python manage.py verify_ai_scoring_uat
```

**Expected Output**:
```
Total Positions: 20
AI Scored: 20
Percentage: 100.0%

TOP 5 SCORED POSITIONS:
  1. AAPL   74.0/100 (AVERAGE        ) ⭐⭐⭐
  2. TSLA   63.5/100 (BELOW_AVERAGE ) ⭐⭐
  ...
```

---

### **Step 4: Test in Browser**

**Navigate to**:
```
http://localhost:8080/investing/managed/staff/suggestions/
```

**You Should See**:
- Statistics cards with "🤖 Avg AI Score"
- Table with AI Score column (first column)
- Star ratings (⭐ to ⭐⭐⭐⭐⭐)
- Color-coded badges (EXCELLENT/GOOD/AVERAGE/BELOW_AVERAGE/POOR)
- Positions sorted by score (best first)

**Click "👁️ Review" on any position**:
- See AI Analysis card at top
- Large score display
- 6-factor breakdown
- AI recommendation

---

## 📁 **CSV FILE LOCATIONS**

### **On Your Computer**:
```
C:\Users\admin\Desktop\project\coda\Opions_play_automation\
├── credit_spreads.csv       (~100-200 positions)
├── short_puts.csv           (~200-300 positions)
└── covered_calls.csv        (~100-150 positions)
```

### **CSV Format Examples**:

**Short Puts CSV**:
```csv
Symbol,Price,Strike,Expiry,Premium,DTE,IV Rank,%Return,Ann %Return,Dist to Strike,Earnings,E
AAPL,175.50,170.00,2024-12-20,$2.50,45,65%,1.5%,12.1%,-3.1%,2024-12-31,N
TSLA,245.00,240.00,2024-12-20,$3.80,45,72%,1.6%,13.0%,-2.0%,2025-01-15,N
```

**Credit Spreads CSV**:
```csv
Symbol,Strategy,Type,Price,Sell Strike,Buy Strike,Expiry,Premium,Width,Prem/Width,IV Rank,%Return,Ann %Return,Dist to Strike,Earnings,E
AAPL,Bullish,Put,175.50,170.00,165.00,2024-12-20,$2.30,$5.00,46%,65%,46.0%,372%,-3.1%,2024-12-31,N
```

---

## 🐛 **TROUBLESHOOTING**

### **Problem: "Mock data is being used"**

**Cause**: No real OptionPlay data in database

**Solution**:
1. **Check if data exists**:
   ```bash
   python manage.py check_data_sources
   ```

2. **If no data, upload CSV**:
   ```bash
   python manage.py import_optionplay_csv short_puts "path/to/file.csv" --convert --max-positions 20
   ```

3. **Verify conversion**:
   ```bash
   python manage.py verify_ai_scoring_uat
   ```

---

### **Problem: "CSV file not found"**

**Solution**:
```powershell
# Use full path with quotes
python manage.py import_optionplay_csv short_puts "C:\Users\admin\Desktop\project\coda\Opions_play_automation\short_puts.csv" --convert
```

---

### **Problem: "All positions filtered out"**

**Cause**: Quality filters too strict (min premium, min IV, etc.)

**Solution**: Lower filters
```bash
# More lenient filters
python manage.py import_optionplay_csv short_puts file.csv --convert --min-premium 0.5 --min-iv 20 --max-positions 50
```

---

### **Problem: "Positions not showing in UI"**

**Checklist**:
1. Check if SuggestedPositions exist:
   ```bash
   python manage.py check_data_sources
   ```

2. Check review status:
   - Only `status='pending'` shows in Pending tab
   - Check database: Most should be pending

3. Check URL:
   - Correct: `/investing/managed/staff/suggestions/`
   - Incorrect: `/investing/managed/suggestions/` (missing staff)

---

## 📊 **RECOMMENDED WORKFLOW FOR UAT**

### **For Testing on codamakutano.herokuapp.com**:

**Step 1**: Upload CSV locally first (test data quality)
```bash
cd C:\Users\admin\Desktop\project\coda\stg\coda

python manage.py import_optionplay_csv short_puts "C:\Users\admin\Desktop\project\coda\Opions_play_automation\short_puts.csv" --convert --max-positions 10 --min-premium 2.0 --min-iv 50
```

**Step 2**: Verify locally
```bash
python manage.py verify_ai_scoring_uat
```

**Step 3**: View in browser
```
http://localhost:8080/investing/managed/staff/suggestions/
```

**Step 4**: Export for UAT (if looks good)
```bash
python manage.py dumpdata investing.SuggestedPosition investing.OptionPlayRawData --indent 2 > uat_positions.json
```

**Step 5**: Load on UAT
```bash
# Upload file to Heroku (if small enough)
heroku run "cd coda && python manage.py loaddata uat_positions.json" --app codamakutano

# Or manually add via admin (smaller dataset)
```

---

## 🎯 **CURRENT STATUS**

### **Local Database** (coda_prod_clone):
- ✅ 509 OptionPlay raw data entries
- ✅ 499 AI-scored SuggestedPositions
- ✅ All test commands working
- ✅ UI showing scores correctly

### **UAT Database** (codamakutano):
- ❌ 0 OptionPlay raw data
- ❌ 0 SuggestedPositions
- ✅ Migrations applied (models exist)
- ✅ AI scoring service deployed
- ⚠️ **Needs data upload!**

---

## ✅ **ACTION ITEMS**

**To Get AI Scoring Working on UAT**:

1. **Upload CSV Data**:
   ```bash
   # Test locally first
   cd coda
   python manage.py import_optionplay_csv short_puts "C:\Users\admin\Desktop\project\coda\Opions_play_automation\short_puts.csv" --convert --max-positions 20 --min-premium 2.0
   ```

2. **Verify Locally**:
   ```bash
   python manage.py verify_ai_scoring_uat
   python manage.py check_data_sources
   ```

3. **View in Browser**:
   ```
   http://localhost:8080/investing/managed/staff/suggestions/
   ```

4. **If Good, Export/Upload to UAT**:
   - Option A: Manual entry via admin (small dataset)
   - Option B: Export JSON, load on Heroku
   - Option C: Upload CSV directly on Heroku (if file accessible)

---

## 📞 **QUICK COMMANDS**

```bash
# Check what data exists
python manage.py check_data_sources

# Upload & score 10 best positions
python manage.py import_optionplay_csv short_puts "C:\path\to\file.csv" --convert --max-positions 10 --min-premium 2.0 --min-iv 50

# Verify AI scoring
python manage.py verify_ai_scoring_uat

# View top scores
python manage.py shell -c "from investing.models import SuggestedPosition; [print(f'{p.symbol}: {p.ai_score}/100') for p in SuggestedPosition.objects.filter(ai_score__isnull=False).order_by('-ai_score')[:10]]"
```

---

## 🌐 **ADMIN URLS**

**Local**:
- Admin: http://localhost:8080/admin/
- Raw Data: http://localhost:8080/admin/investing/optionplayrawdata/
- Suggestions: http://localhost:8080/admin/investing/suggestedposition/
- Staff UI: http://localhost:8080/investing/managed/staff/suggestions/

**UAT**:
- Admin: https://codamakutano.herokuapp.com/admin/
- Raw Data: https://codamakutano.herokuapp.com/admin/investing/optionplayrawdata/
- Suggestions: https://codamakutano.herokuapp.com/admin/investing/suggestedposition/
- Staff UI: https://codamakutano.herokuapp.com/investing/managed/staff/suggestions/

---

## 🎯 **RECOMMENDED: Upload 10 High-Quality Positions for Demo**

**Command**:
```bash
cd C:\Users\admin\Desktop\project\coda\stg\coda

python manage.py import_optionplay_csv short_puts "C:\Users\admin\Desktop\project\coda\Opions_play_automation\short_puts.csv" --convert --max-positions 10 --min-premium 2.50 --min-iv 60 --symbols "AAPL,MSFT,GOOGL,META,NVDA,TSLA,AMZN"
```

**This Will**:
- Read short_puts.csv (300+ positions)
- Filter to FAANG stocks only
- Filter to premium $2.50+ (good edge)
- Filter to IV 60%+ (high volatility)
- Take top 10 positions
- **AI score each one** (expect scores 65-85)
- Create SuggestedPosition entries

**Result**: 10 high-quality, AI-scored positions ready for demo!

---

*Created: November 2, 2025*  
*Part of: AI Position Scoring System*

