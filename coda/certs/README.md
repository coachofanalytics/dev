# SSL Certificates for Local Development

This directory contains self-signed SSL certificates for running the Django development server with HTTPS.

## Files

- `cert.pem` - SSL certificate (self-signed)
- `key.pem` - Private key

## Security Note

⚠️ **These certificates are for LOCAL DEVELOPMENT ONLY**

- Self-signed certificates are NOT secure for production
- Files are excluded from git (see `.gitignore`)
- Your browser will show security warnings - this is expected
- Never use these certificates in production

## Usage

### Option 1: Run HTTPS Server (Recommended)

From project root:
```bash
./run_https_local.sh
```

### Option 2: Manual Command

From project root:
```bash
cd coda
python manage.py runsslserver --certificate certs/cert.pem --key certs/key.pem 0.0.0.0:8000
```

Then access: https://localhost:8000/

## Browser Security Warning

When you first access https://localhost:8000/, your browser will show a warning:

**Chrome/Edge:**
1. Click "Advanced"
2. Click "Proceed to localhost (unsafe)"

**Firefox:**
1. Click "Advanced"
2. Click "Accept the Risk and Continue"

**Safari:**
1. Click "Show Details"
2. Click "visit this website"

This is normal and expected for self-signed certificates.

## Regenerating Certificates

If you need to regenerate the certificates:

```bash
cd coda/certs
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/C=KE/ST=Nairobi/L=Nairobi/O=CODA Development/OU=Dev/CN=localhost"
```

## Production SSL

For production, use:
- Let's Encrypt (free)
- Commercial SSL certificates
- Cloud provider SSL (AWS Certificate Manager, etc.)
- Never use self-signed certificates

## Troubleshooting

### Server won't start
- Check that `cert.pem` and `key.pem` exist
- Check that `django-sslserver` is installed: `pip install django-sslserver`
- Check that `sslserver` is in INSTALLED_APPS

### Browser still shows HTTP errors
- Make sure you're using `https://` not `http://`
- Clear browser cache
- Try incognito/private window

### "Bad request version" errors
- This happens when something tries to access HTTP server with HTTPS protocol
- The HTTPS server fixes this
- No action needed

---

**Last Updated:** October 17, 2025  
**Certificate Validity:** 365 days from generation

