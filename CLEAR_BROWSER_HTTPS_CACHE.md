# Fix: Browser Auto-Redirecting HTTP to HTTPS

## Problem
When you visit `http://127.0.0.1:8000/` or `http://localhost:8000/`, your browser automatically changes it to `https://` causing SSL errors.

## Why This Happens
Your browser cached HTTPS settings from earlier when we tried to set up SSL. Browsers remember this via HSTS (HTTP Strict Transport Security).

## Solutions

### Option 1: Clear HSTS Settings (Recommended)

**Chrome/Edge:**
1. Visit: `chrome://net-internals/#hsts`
2. Scroll to "Delete domain security policies"
3. Enter: `localhost` and click Delete
4. Also delete: `127.0.0.1`
5. Restart browser
6. Try: `http://localhost:8000/`

**Firefox:**
1. Close Firefox completely
2. Find your Firefox profile folder:
   - Mac: `~/Library/Application Support/Firefox/Profiles/`
   - Delete file: `SiteSecurityServiceState.txt`
3. Restart Firefox
4. Try: `http://localhost:8000/`

**Safari:**
1. Safari → Settings → Privacy
2. Click "Manage Website Data"
3. Search for "localhost"
4. Remove all localhost entries
5. Restart Safari
6. Try: `http://localhost:8000/`

### Option 2: Use Incognito/Private Mode

Quickest solution:
1. Open Incognito/Private window (Cmd+Shift+N or Cmd+Shift+P)
2. Visit: `http://localhost:8000/`
3. Browser won't have cached HTTPS preference

### Option 3: Use Different Port

Change your local server to a different port that browser hasn't cached:

```bash
cd coda
DJANGO_SETTINGS_MODULE=coda_project.coda_settings.local_settings \
python manage.py runserver 0.0.0.0:8080
```

Then visit: `http://localhost:8080/`

### Option 4: Clear All Browser Cache

**Chrome/Edge:**
1. Cmd+Shift+Delete
2. Select "All time"
3. Check all boxes
4. Clear data

**Firefox:**
1. Cmd+Shift+Delete
2. Select "Everything"
3. Check all boxes
4. Clear now

**Safari:**
1. Safari → Clear History
2. Select "all history"
3. Clear history

## Verify It's Fixed

After clearing cache, test:
```
http://localhost:8000/
```

Should stay as HTTP (not change to HTTPS).

## Quick Test URLs

Try these URLs in order:
1. `http://localhost:8000/` - Main site
2. `http://localhost:8000/portfolio/` - Portfolio hub
3. `http://localhost:8000/interview/` - Interview mode
4. `http://localhost:8000/dashboard/` - Dashboard

## Prevent This in Future

Don't visit these with HTTPS:
- ❌ `https://localhost:8000/` 
- ✅ `http://localhost:8000/`

Use bookmarks with HTTP:// to avoid typing https:// by mistake.

---

**Quick Fix:** Just use Incognito/Private mode for now!
