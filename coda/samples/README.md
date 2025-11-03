# Sample Data Exports

This directory contains sample data exports for analysis and debugging.

## Purpose
- Analyze data quality before setting import filters
- Understand distribution of premiums, IV ranks, DTE
- Debug why positions are being filtered out
- Test new features with realistic data

## Directories

### `optionplay/`
Sample exports of OptionPlay raw data for quality filter analysis.

**Export Command:**
```bash
cd coda
python manage.py export_optionplay_sample --limit 50 --output samples/optionplay/latest.csv
```

**Options:**
- `--limit 50` - Number of records (default: 50)
- `--active-only` - Export only non-expired positions
- `--output <file>` - Output filename

**Example:**
```bash
# Export 100 active positions
python manage.py export_optionplay_sample --limit 100 --active-only --output samples/optionplay/active_positions.csv

# Export all current data
python manage.py export_optionplay_sample --limit 1000 --output samples/optionplay/full_dump.csv
```

## Usage Tips

1. **Before Setting Filters:**
   - Export current data: `python manage.py export_optionplay_sample`
   - Open CSV in Excel/Google Sheets
   - Look at IV Rank, Premium, DTE distributions
   - Set filters based on actual data ranges

2. **When All Positions Filter Out:**
   - Check the command output for statistics
   - Look for averages vs your filter settings
   - Common issue: IV Rank avg is 5%, but filter set to 40%

3. **Regular Analysis:**
   - Export monthly to track data quality trends
   - Compare before/after cleanup operations
   - Verify AI scoring results

## Git Ignore
Sample CSVs are git-ignored to avoid bloating the repository.
Only the README files are tracked.

