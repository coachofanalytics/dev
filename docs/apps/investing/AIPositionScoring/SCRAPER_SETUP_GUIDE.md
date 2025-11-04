# OptionPlay Scraper Setup Guide

## Overview

The CODA managed trading system automatically fetches high-probability options positions from **OptionPlay.com** using a Playwright-based web scraper.

This document explains how to configure and use the scraper.

---

## Why Scraping Instead of API?

- ❌ **OptionPlay doesn't have a public API** (as of Nov 2024)
- ✅ **Working scraper** already developed and tested (from `Opions_play_automation` repo)
- ✅ **Fetches real positions** from OptionPlay's website tables
- ✅ **Fallback mechanism** in place if scraping fails

---

## 📦 Installation

### 1. Install Required Packages

```bash
cd coda
pip install playwright beautifulsoup4 pandas lxml
```

### 2. Install Playwright Browsers

```bash
playwright install chromium
```

This downloads the Chromium browser needed for scraping (~150MB).

---

## 🔐 Configuration

### 1. OptionPlay Account

You need an **active OptionPlay account**:
- Visit: https://www.optionsplay.com
- Sign up for a plan (they have free trials)
- Note your **username** and **password**

### 2. Environment Variables

Add these to your environment (`.env` file or Heroku config vars):

```bash
# OptionPlay Credentials
OPTIONPLAY_USERNAME=your_username_here
OPTIONPLAY_PASSWORD=your_password_here
```

**For Heroku:**

```bash
heroku config:set OPTIONPLAY_USERNAME=your_username --app codamakutano
heroku config:set OPTIONPLAY_PASSWORD=your_password --app codamakutano
```

---

## 🧪 Testing the Scraper

### Manual Test (Django Shell)

```bash
cd coda
python manage.py shell
```

```python
from investing.services.optionplay_scraper import OptionPlayScraperService

# Initialize scraper
scraper = OptionPlayScraperService()

# Check if configured
print(f"Configured: {scraper.is_configured}")

# Fetch positions
positions = scraper.fetch_all_positions({
    'min_probability': 70,
    'min_premium': 100,
    'dte_min': 30,
    'dte_max': 60,
    'max_positions': 5
})

# View results
print(f"Fetched {len(positions)} positions")
for pos in positions:
    print(f"  {pos['symbol']} {pos['strategy']} - PoP: {pos['probability_of_profit']}%")
```

### Using Management Command

```bash
cd coda
python manage.py fetch_positions --source optionplay
```

Expected output:
```
🕸️  Using OptionPlay web scraper (Playwright)...
✅ OptionPlay scraper configured
🔍 Fetching Credit Spreads from OptionPlay...
✅ Fetched 12 credit spreads
🔍 Fetching Short Puts from OptionPlay...
✅ Fetched 8 short puts
🔍 Fetching Covered Calls from OptionPlay...
✅ Fetched 5 covered calls
📊 Total positions fetched: 25
📊 After filters: 5 positions (from 25)
```

---

## 📊 What Gets Scraped?

The scraper fetches **3 types of positions** from OptionPlay:

| Strategy Type | URL | Table ID |
|--------------|-----|----------|
| **Credit Spreads** | https://www.optionsplay.com/hub/credit-spread-file | `#CreditSpreadFile` |
| **Short Puts** | https://www.optionsplay.com/hub/short-puts | `#shortPuts` |
| **Covered Calls** | https://www.optionsplay.com/hub/covered-calls | `#coveredCalls` |

Each position includes:
- Symbol, Strategy Type
- Strike prices, Expiration date, DTE
- Premium, Capital Required
- Max Profit, Max Loss, Breakeven
- Probability of Profit, Greeks (Delta, Theta, Gamma, Vega)

---

## 🔄 Automated Fetching

### Celery Beat Schedule

Positions are auto-fetched **daily at 9 AM EST**:

```python
# coda/celeryapp.py
'daily-position-fetch': {
    'task': 'investing.tasks.daily_position_fetch_task',
    'schedule': crontab(hour=9, minute=0),  # 9 AM daily
}
```

### Manual Trigger

Staff can manually trigger via UI:
1. Go to: `/investing/managed/staff/suggestions/`
2. Click **"Fetch New Positions"**
3. Choose filters (or use defaults)
4. Click **"Fetch Now"**

---

## 🚨 Troubleshooting

### Error: "Playwright not installed"

```bash
pip install playwright
playwright install chromium
```

### Error: "OptionPlay credentials not configured"

Set environment variables:
```bash
export OPTIONPLAY_USERNAME=your_username
export OPTIONPLAY_PASSWORD=your_password
```

### Error: "Timeout waiting for selector"

OptionPlay's page structure may have changed. Check:
1. Login credentials are correct
2. OptionPlay website is accessible
3. Table IDs haven't changed (`#CreditSpreadFile`, etc.)

### Error: "No positions returned"

Possible causes:
1. OptionPlay has no positions matching your filters
2. Market is closed (OptionPlay updates during market hours)
3. Filters are too strict (try lowering `min_probability` to 65%)

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| **Scrape Time** | ~60-90 seconds (all 3 strategies) |
| **Positions Returned** | 15-30 positions typical |
| **After Filtering** | 5-10 positions (70%+ PoP, $100+ premium, 30-60 DTE) |
| **Success Rate** | ~95% (when credentials configured) |

---

## 🔐 Security Notes

1. **Credentials Storage**:
   - ✅ Store in environment variables (NOT in code)
   - ✅ Use Heroku config vars for production
   - ❌ Never commit credentials to Git

2. **Rate Limiting**:
   - Scraper runs once daily (safe)
   - Manual fetches limited to staff only
   - No aggressive scraping

3. **OptionPlay Terms**:
   - Ensure your OptionPlay subscription allows programmatic access
   - This is for internal use only (not reselling data)

---

## 🆘 Support

If the scraper fails consistently:

1. **Check OptionPlay website manually** - Login and verify you can see the tables
2. **Test credentials** - Ensure username/password are correct
3. **Review logs** - Check `coda/logs/` for detailed error messages
4. **Fallback to mock data** - System automatically uses mock data if scraper fails

---

## 📝 File Locations

| File | Purpose |
|------|---------|
| `investing/services/optionplay_scraper.py` | Main scraper service |
| `investing/services/position_fetcher_service.py` | Integration with position automation |
| `investing/management/commands/fetch_positions.py` | Manual fetch command |
| `investing/tasks.py` | Celery tasks for automated fetching |

---

## ✅ Verification Checklist

Before deploying to production:

- [ ] Playwright installed (`playwright install chromium`)
- [ ] Environment variables set (`OPTIONPLAY_USERNAME`, `OPTIONPLAY_PASSWORD`)
- [ ] Test scraper in Django shell (see above)
- [ ] Manual fetch command works (`python manage.py fetch_positions --source optionplay`)
- [ ] Staff UI shows fetched positions (`/investing/managed/staff/suggestions/`)
- [ ] Celery Beat task configured (check `celeryapp.py`)

---

**Last Updated**: November 1, 2025
**Maintainer**: CODA Development Team

