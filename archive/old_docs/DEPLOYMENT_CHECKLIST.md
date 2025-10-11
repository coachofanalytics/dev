# Heroku UAT Deployment Checklist

## Pre-Deployment Checklist

### 1. Environment Configuration
- [x] `.gitignore` updated to exclude SQLite databases and unnecessary files
- [x] `runtime.txt` specifies Python 3.12.6
- [x] `requirements.txt` optimized for Heroku (97 packages)
- [x] `Procfile` configured for gunicorn
- [x] Heroku settings configured in `heroku_settings.py`

### 2. Database Configuration
- [x] SQLite databases excluded from git (3.1MB `coda_dev.db` excluded)
- [x] Heroku PostgreSQL configuration ready
- [x] Database URL environment variable configured

### 3. Static Files
- [x] WhiteNoise configured for static file serving
- [x] Static files directory structure verified
- [x] Large media files excluded from deployment

### 4. Security Settings
- [x] SSL redirect enabled for production
- [x] Security headers configured
- [x] CSRF and session cookies secured
- [x] Allowed hosts configured for Heroku domain

### 5. Environment Variables Required
Set these in Heroku dashboard:
```
ENVIRONMENT=heroku
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://...
EMAIL_HOST=your-smtp-host
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USER=your-email
EMAIL_PASS=your-password
SITE_URL=https://codamakutano.herokuapp.com
```

### 6. Deployment Commands
```bash
# Deploy to Heroku
git add .
git commit -m "Prepare for UAT deployment"
git push heroku main

# Run migrations
heroku run python manage.py migrate --app codamakutano

# Collect static files
heroku run python manage.py collectstatic --noinput --app codamakutano

# Create superuser (if needed)
heroku run python manage.py createsuperuser --app codamakutano

# Check logs
heroku logs --tail --app codamakutano

# Check app status
heroku ps --app codamakutano
```

### 7. Post-Deployment Testing
- [ ] Verify app starts successfully
- [ ] Test database connectivity
- [ ] Verify static files are served correctly
- [ ] Test user authentication
- [ ] Test email functionality
- [ ] Verify SSL redirect works
- [ ] Check all major application features

### 8. Monitoring
- [ ] Set up Heroku metrics monitoring
- [ ] Configure error tracking
- [ ] Set up log aggregation
- [ ] Monitor database performance

## File Exclusions for Smaller Slug Size
The following files/directories are excluded to keep the Heroku slug size minimal:
- SQLite databases (*.db, *.sqlite*)
- Virtual environments (venv/, .venv/)
- Python cache files (__pycache__/, *.pyc)
- IDE files (.vscode/, .idea/)
- OS files (.DS_Store, Thumbs.db)
- Log files (*.log, logs/)
- Test files (tests/, test_*.py)
- Documentation (docs/, *.md except README)
- Large media files (*.mp4, *.psd, etc.)
- Backup files (*.bak, *.backup)

## Current Slug Size Optimization
- Requirements.txt: 97 packages (optimized)
- Database files: Excluded (3.1MB saved)
- Static files: Optimized with WhiteNoise
- Media files: Large files excluded

## Troubleshooting
If deployment fails:
1. Check Heroku logs: `heroku logs --tail --app codamakutano`
2. Verify environment variables are set
3. Check database connectivity
4. Verify static file collection
5. Check for missing dependencies in requirements.txt
