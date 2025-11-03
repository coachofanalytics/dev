# QUICK START: Test AI Scoring on UAT
## November 2, 2025

## 🎯 **CURRENT STATUS**

✅ **LOCAL** (Working perfectly):
- 509 OptionPlay raw data entries
- 499 AI-scored positions
- UI showing scores with stars ⭐⭐⭐⭐⭐

❌ **UAT** (Needs data upload):
- 0 OptionPlay raw data
- 5 old positions (not AI-scored)
- **System uses mock data** (that's why you see it defaulting to mock!)

---

## 🚀 **3 WAYS TO UPLOAD DATA TO UAT**

### **Option 1: Test Locally First** ⭐ **RECOMMENDED**

**You Already Have Everything Working Locally!**

**View it now**:
1. Make sure dev server is running:
   ```bash
   cd C:\Users\admin\Desktop\project\coda\stg\coda
   python manage.py runserver 8080
   ```

2. **Open in browser**:
   ```
   http://localhost:8080/investing/managed/staff/suggestions/
   ```

3. **You'll See**:
   - 504 pending positions
   - AI scores (44-74/100)
   - Star ratings (⭐ to ⭐⭐⭐)
   - Color-coded rows
   - Statistics cards with "🤖 Avg AI Score: 48.3"

4. **Click "👁️" on RENT (top scored)**:
   - See large "74" score
   - See ⭐⭐⭐ stars
   - See 6-factor breakdown
   - See AI recommendation

**THIS IS WHAT UAT WILL LOOK LIKE** once we upload data!

---

### **Option 2: Upload via Django Admin on UAT** ⭐ **EASIEST FOR DEMO**

**URL**: https://codamakutano.herokuapp.com/admin/investing/optionplayrawdata/

**Steps**:
1. **Login to admin**
2. **Click "Add Option Play Raw Data"**
3. **Enter ONE position manually** (test):
   ```
   Strategy Type: short_put
   Symbol: AAPL
   Stock Price: 175.50
   Sell Strike: 170.00
   Expiry: 2024-12-20
   Days to Expiry: 45
   Premium: 2.50
   IV Rank: 65.00
   Raw Return: 1.5
   Annualized Return: 12.0
   ```
4. **Click "Save"**
5. **Go back to list**, select the entry (checkbox)
6. **Actions dropdown**: "Convert selected to SuggestedPositions"
7. **Click "Go"**
8. **Navigate to**: https://codamakutano.herokuapp.com/investing/managed/staff/suggestions/
9. **See AI-scored AAPL position!** 🎉

---

### **Option 3: Bulk Import from CSV**

**Copy CSV to Heroku** (if file is small):

```bash
# 1. Create a small sample CSV (10 best positions)
cd C:\Users\admin\Desktop\project\coda\stg\coda

# 2. Export top 10 from local
python manage.py dumpdata investing.OptionPlayRawData --pks 1,2,3,4,5,6,7,8,9,10 > sample_data.json

# 3. Add to git (temporary)
git add sample_data.json
git commit -m "Sample positions for UAT"
git push heroku 25.10_CODA_UAT_CM:main

# 4. Load on Heroku
heroku run "cd coda && python manage.py loaddata sample_data.json" --app codamakutano

# 5. Convert to scored positions
heroku run "cd coda && python manage.py verify_ai_scoring_uat" --app codamakutano
```

---

## 🎬 **RECOMMENDED: 5-MINUTE DEMO**

### **Do This NOW to See AI Scoring on UAT**:

1. **Open UAT Admin**:
   ```
   https://codamakutano.herokuapp.com/admin/investing/optionplayrawdata/
   ```

2. **Add 3 positions manually** (5 min):

**Position 1: RENT (Will score ~74/100 - AVERAGE)**
```
Strategy Type: short_put
Symbol: RENT
Sell Strike: 25.00
Premium: 1.50
Expiry: 2024-12-20
Days to Expiry: 48
IV Rank: 100.00
Raw Return: 6.0
Annualized Return: 45.0
```

**Position 2: TSLA (Will score ~57/100 - BELOW_AVG)**
```
Strategy Type: short_put
Symbol: TSLA
Sell Strike: 240.00
Premium: 3.80
Expiry: 2024-12-20
Days to Expiry: 45
IV Rank: 30.00
Raw Return: 4.3
Annualized Return: 35.0
```

**Position 3: MUNI (Will score ~44/100 - POOR)**
```
Strategy Type: short_put
Symbol: MUNI
Sell Strike: 100.00
Premium: 0.20
Expiry: 2024-12-20
Days to Expiry: 45
IV Rank: 11.00
Raw Return: 0.2
Annualized Return: 1.6
```

3. **After adding all 3**:
   - Go to list: https://codamakutano.herokuapp.com/admin/investing/optionplayrawdata/
   - Select all 3 (checkboxes)
   - Actions: "Convert selected to SuggestedPositions"
   - Click "Go"

4. **View Results**:
   ```
   https://codamakutano.herokuapp.com/investing/managed/staff/suggestions/
   ```

5. **You'll See**:
   - RENT at top (74/100) ⭐⭐⭐ AVERAGE (green row)
   - TSLA middle (57/100) ⭐⭐ BELOW_AVG (yellow)
   - MUNI bottom (44/100) ⭐ POOR (red row)

**AI SCORING WORKING!** 🎉

---

## 📊 **LOCAL VS UAT COMPARISON**

| Environment | URL | Raw Data | Scored | Status |
|-------------|-----|----------|--------|--------|
| **Local** | http://localhost:8080 | 509 | 499 | ✅ Working |
| **UAT** | https://codamakutano.herokuapp.com | 0 | 0 | ⚠️ Needs upload |

---

## ✅ **WHAT TO DO NOW**

### **Quick Test (5 minutes)**:
1. Upload 3 positions via admin (see above)
2. Convert to SuggestedPositions
3. View in staff UI
4. ✅ Confirm AI scoring works!

### **Full Test (20 minutes)**:
1. Upload 10-20 positions via admin
2. Or export from local and import
3. Test all UI features
4. Test admin filtering/sorting

### **Production Ready (Later)**:
1. Wait for OptionPlay API access
2. OR upload weekly CSVs
3. OR use TD Ameritrade API

---

## 📞 **WHERE TO GO**

### **To Upload Data**:
**https://codamakutano.herokuapp.com/admin/investing/optionplayrawdata/**

### **To View AI Scores**:
**https://codamakutano.herokuapp.com/investing/managed/staff/suggestions/**

### **To Test Locally** (Already Working!):
**http://localhost:8080/investing/managed/staff/suggestions/**

---

## 🎯 **SUMMARY**

**Issue**: UAT shows mock data  
**Cause**: No OptionPlay data uploaded to UAT database  
**Solution**: Upload 3-10 positions manually via admin (5-10 min)  
**Result**: AI scoring will work immediately!  

**Local**: ✅ Perfect (499 AI-scored positions ready to view!)  
**UAT**: ⚠️ Ready for data upload  

**Next**: Upload a few positions to UAT and test! 🚀

---

*Created: November 2, 2025*  
*AI Position Scoring System - v976*

