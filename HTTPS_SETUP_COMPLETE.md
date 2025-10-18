# HTTPS/SSL Local Development - Setup Complete! 🔒

**Completed:** October 17, 2025  
**Status:** ✅ Ready to use

## What Was Configured

### 1. SSL Certificates Generated ✅
- Self-signed SSL certificate created
- Location: `coda/certs/cert.pem` and `coda/certs/key.pem`
- Valid for: 365 days
- Excluded from git repository

### 2. Django SSL Server Installed ✅
- Package: `django-sslserver` (v0.22)
- Added to: `local_settings.py` INSTALLED_APPS
- SSL paths configured

### 3. Convenience Script Created ✅
- File: `run_https_local.sh`
- Executable and ready to use
- Checks for certificates automatically

### 4. Documentation Created ✅
- SSL certificate README in `coda/certs/README.md`
- Browser security warning guidance
- Troubleshooting guide

## 🚀 How to Run HTTPS Server

### Method 1: Using the Script (Easiest)

From project root:
```bash
./run_https_local.sh
```

### Method 2: Manual Command

```bash
cd coda
export DJANGO_SETTINGS_MODULE=coda_project.coda_settings.local_settings
python manage.py runsslserver --certificate certs/cert.pem --key certs/key.pem 0.0.0.0:8000
```

### Method 3: Using manage.py directly

```bash
cd coda
python manage.py runsslserver --settings=coda_project.coda_settings.local_settings --certificate certs/cert.pem --key certs/key.pem 0.0.0.0:8000
```

## 📱 Accessing Your HTTPS Server

Once running, access at:
```
https://localhost:8000/
https://127.0.0.1:8000/
```

### Portfolio URLs (HTTPS)
```
Portfolio Hub:        https://localhost:8000/portfolio/
Interview Mode:       https://localhost:8000/interview/
Budget Tier (Tech):   https://localhost:8000/interview/budget-tier/technical/
Dashboard:            https://localhost:8000/dashboard/
```

## ⚠️ Browser Security Warning (Expected!)

Your browser WILL show a security warning. This is **normal and expected** for self-signed certificates.

### How to Proceed:

**Chrome/Edge:**
1. Click "Advanced"
2. Click "Proceed to localhost (unsafe)"

**Firefox:**
1. Click "Advanced"
2. Click "Accept the Risk and Continue"

**Safari:**
1. Click "Show Details"
2. Click "visit this website"

This is safe because:
- You generated the certificate yourself
- It's only for local development
- Traffic stays on your machine
- Never used in production

## 🔧 Troubleshooting

### Issue: "Unknown command: 'runsslserver'"

**Cause:** Wrong settings module loaded  
**Fix:** Use one of these methods:

```bash
# Option 1: Set environment variable
export DJANGO_SETTINGS_MODULE=coda_project.coda_settings.local_settings
python manage.py runsslserver --certificate certs/cert.pem --key certs/key.pem

# Option 2: Specify settings in command
python manage.py runsslserver --settings=coda_project.coda_settings.local_settings --certificate certs/cert.pem --key certs/key.pem

# Option 3: Use the script (handles this automatically)
./run_https_local.sh
```

### Issue: Port 8000 already in use

**Cause:** Another server is running  
**Fix:**

```bash
# Find process on port 8000
lsof -i :8000

# Kill it (replace PID with actual process ID)
kill <PID>

# Or use a different port
python manage.py runsslserver --certificate certs/cert.pem --key certs/key.pem 0.0.0.0:8443
```

### Issue: Certificate not found

**Cause:** Certificates weren't generated  
**Fix:**

```bash
cd coda/certs
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/C=KE/ST=Nairobi/L=Nairobi/O=CODA Development/OU=Dev/CN=localhost"
```

### Issue: Still getting "Bad request version" errors

**Cause:** Old HTTP server still running  
**Fix:**

```bash
# Kill all Python processes on port 8000
lsof -ti :8000 | xargs kill

# Then start HTTPS server
./run_https_local.sh
```

## 📁 Files Created/Modified

### New Files:
- `coda/certs/cert.pem` (SSL certificate) - **NOT in git**
- `coda/certs/key.pem` (Private key) - **NOT in git**
- `coda/certs/README.md` (Documentation)
- `run_https_local.sh` (Convenience script)
- `HTTPS_SETUP_COMPLETE.md` (This file)

### Modified Files:
- `coda/coda_project/coda_settings/local_settings.py` - Added SSL server config
- `.gitignore` - Excluded certificate files

### Installed Packages:
- `django-sslserver==0.22`

## 🔐 Security Notes

### ✅ Safe for Local Development
- Self-signed certificates are PERFECT for local development
- No security risk on localhost
- Allows testing HTTPS features locally

### ❌ NEVER Use in Production
- Self-signed certificates will break in production
- Browsers will block your site
- Users will see big security warnings

### Production SSL Options
For production, use:
- **Let's Encrypt** (free, auto-renewing)
- **Commercial SSL** (from providers like DigiCert)
- **Cloud SSL** (AWS Certificate Manager, Cloudflare)
- **Heroku SSL** (built-in for paid dynos)

## 🎯 Why HTTPS Locally?

### Benefits:
1. **Test HTTPS-only features** (Service Workers, Geolocation API, etc.)
2. **Match production environment** (avoid HTTP/HTTPS issues)
3. **Test SSL-specific code** (secure cookies, HSTS headers)
4. **Modern browser features** (many require HTTPS)
5. **Portfolio presentations** (no SSL handshake errors)

### No More Errors:
- ❌ "You're accessing the development server over HTTPS, but it only supports HTTP"
- ❌ "Bad request version" SSL handshake errors
- ✅ Clean, professional HTTPS URLs

## 📊 Quick Reference

| What | Command |
|------|---------|
| Start HTTPS server | `./run_https_local.sh` |
| Access portfolio | `https://localhost:8000/portfolio/` |
| Interview mode | `https://localhost:8000/interview/` |
| Stop server | `Ctrl+C` or `kill <PID>` |
| Check port 8000 | `lsof -i :8000` |
| Regenerate certs | See `coda/certs/README.md` |

## ✅ Testing Checklist

- [ ] Run `./run_https_local.sh`
- [ ] Server starts without errors
- [ ] Access `https://localhost:8000/`
- [ ] Accept security warning
- [ ] Portfolio hub loads: `https://localhost:8000/portfolio/`
- [ ] Interview mode works: `https://localhost:8000/interview/`
- [ ] No SSL handshake errors in logs
- [ ] Dashboard accessible: `https://localhost:8000/dashboard/`

## 🎉 Success!

Your local development environment now supports HTTPS! You can:

✅ Run presentations over HTTPS  
✅ Test SSL-specific features  
✅ Match production environment  
✅ No more SSL handshake errors  
✅ Professional HTTPS URLs for demos

---

**Next Steps:**
1. Run `./run_https_local.sh` to start HTTPS server
2. Access https://localhost:8000/portfolio/
3. Accept browser security warning (one-time)
4. Enjoy SSL-enabled local development!

**Questions?** See `coda/certs/README.md` for detailed instructions.

**Last Updated:** October 17, 2025  
**Certificate Expires:** October 17, 2026 (regenerate annually)

