# OptionPlay Sample Data

Sample exports of OptionPlayRawData for quality filter analysis.

## Quick Export

```bash
cd coda
python manage.py export_optionplay_sample --limit 50 --output samples/optionplay/latest.csv
```

## Why Export?

When you see "250 filtered out", export your data to see WHY:

```bash
python manage.py export_optionplay_sample --active-only --limit 100
```

This shows you:
- ✅ **Average Premium**: Is your filter too high? (e.g., avg $7 but filter $2 ✅ good)
- ⚠️ **Average IV Rank**: Common issue! (e.g., avg 0.3% but filter 40% ❌ bad)
- ✅ **Average DTE**: Is your range realistic? (e.g., avg 27 days, filter 60 days ✅ good)

## Example Output

```
📊 DATA QUALITY STATISTICS:
--------------------------------------------------------------------------------
💰 Premium: $7.30 avg ($1.50 - $25.00)
📊 IV Rank: 0.3% avg (0.1% - 85.0%)      ⚠️ Most are VERY LOW!
📅 DTE: 27 days avg (1 - 90)
--------------------------------------------------------------------------------

💡 Use this data to set realistic quality filters!
   Example: If avg IV Rank is 5%, don't filter at 40%
```

## Fix Common Issues

### Problem: All 250 positions filtered out

**Solution:**
1. Export your data: `python manage.py export_optionplay_sample`
2. Look at the statistics
3. Adjust filters on the import page:
   - If avg IV Rank is 0.3%, set filter to 0% (not 40%!)
   - If avg Premium is $7, a $2 filter is fine
   - If avg DTE is 27 days, a 60-day max is fine

### Problem: Filter says "Your average: 0.3%" but I want higher IV

**Solution:**
- The "Your average" is from your CURRENT database
- If you're uploading NEW data with better IV, ignore the old average
- Or use **Smart Cleanup mode** to archive old low-quality data

## Files in This Directory

- `latest.csv` - Most recent export (git-ignored)
- `active_positions.csv` - Non-expired only (git-ignored)
- `full_dump.csv` - Complete database dump (git-ignored)

All CSV files are git-ignored to avoid repository bloat.
Only run exports locally for analysis.

