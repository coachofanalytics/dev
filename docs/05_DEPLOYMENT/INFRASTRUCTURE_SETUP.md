# Infrastructure Setup & Configuration

**Last Updated:** October 21, 2025  
**Environments:** Development, UAT, Production

---

## Environment Configuration

### Development (Local)
- **Database:** SQLite
- **URL:** http://localhost:8000 or https://localhost:8000
- **SSL:** Self-signed certificate
- **Python:** 3.12.6
- **Django:** 3.2.6

**Setup:**
```bash
cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV
source venv/bin/activate
cd coda
python manage.py runserver  # HTTP on 8000
# OR
./scripts/run_https_local.sh  # HTTPS on 8000
```

### UAT (Staging)
- **Platform:** Heroku
- **App:** codamakutano
- **Database:** PostgreSQL (Heroku)
- **URL:** https://codamakutano.herokuapp.com
- **Branch:** Usually deployed from feature branches

### Production
- **Platform:** Heroku
- **App:** codatrainingapp  
- **Database:** PostgreSQL (Heroku)
- **URL:** https://codatrainingapp.herokuapp.com
- **Branch:** Main deployment branch

---

## HTTPS Setup (Local Development)

### Status: ✅ Configured

**Certificate:** Self-signed SSL certificate generated  
**Port:** 8000 (HTTPS)  
**Browser:** Clear cache after first use

**Clear Browser Cache:**
1. Chrome: Chrome menu → Clear browsing data
2. Firefox: Preferences → Privacy → Clear data
3. Safari: Safari menu → Clear history

**Run HTTPS Server:**
```bash
./scripts/run_https_local.sh
```

**Note:** Browser will show security warning - click "Advanced" → "Proceed to localhost"

---

## Database Configuration

### Switching Between Environments:

The system auto-detects environment based on `DJANGO_ENV` variable:

```bash
# Development (SQLite)
unset DJANGO_ENV
python manage.py runserver

# Staging (Heroku UAT)
export DJANGO_ENV=staging
# Uses DATABASE_URL from Heroku

# Production (Heroku Production)
export DJANGO_ENV=production
# Uses DATABASE_URL from Heroku
```

### Settings Structure:

```
coda/coda_project/
├── settings.py (loader - detects environment)
└── coda_settings/
    ├── base_settings.py (common settings)
    ├── local_settings.py (development)
    └── heroku_settings.py (staging & production)
```

### Database URLs:

**Development:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**Production/UAT:**
```python
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(conn_max_age=600)
}
```

---

## Git & Deployment Flow

### Git Remotes:

```bash
origin      git@github.com:CODA-PROD/dev.git
uat         git@github.com:CODA-PROD/uat.git
heroku      https://git.heroku.com/codamakutano.git (UAT)
production  https://git.heroku.com/codatrainingapp.git (Prod)
```

### Deployment Flow:

1. **Development:**
   ```bash
   # Work on feature branch
   git checkout -b feature/new-feature
   # Make changes
   git add -A
   git commit -m "feat: description"
   ```

2. **Deploy to UAT:**
   ```bash
   git push heroku feature/new-feature:main
   # Test on codamakutano
   ```

3. **Deploy to Production:**
   ```bash
   # After UAT testing
   git push production feature/new-feature:main
   # Verify on codatrainingapp
   ```

4. **Push to GitHub:**
   ```bash
   git push uat feature/new-feature
   # Creates backup on GitHub
   ```

---

## File Exclusion Strategy

### .gitignore (Git-level):

**Excluded from Git:**
- `venv/` - Virtual environment
- `__pycache__/` - Python cache
- `*.pyc` - Compiled Python
- `db.sqlite3` - Local database
- `archive/` - Archived docs
- `backups/` - Database backups
- `.env` - Environment variables

**Included in Git:**
- `docs/` - All documentation
- `scripts/` - Development scripts
- `tests/` - Test files
- `coda/` - All application code
- `requirements.txt` - Dependencies

### .slugignore (Heroku-level):

**Excluded from Heroku (but in Git):**
- `docs/` - Documentation (not needed on server)
- `tests/` - Test files
- `scripts/` - Local development scripts
- `archive/` - Archives
- `backups/` - Backups
- `*.md` - Markdown docs

**Deployed to Heroku:**
- `coda/` - Application code
- `requirements.txt` - Dependencies
- `Procfile` - Process definition
- `runtime.txt` or `.python-version` - Python version

**Result:**
- **GitHub:** Full codebase with docs (version control)
- **Heroku:** Only essential code (~80MB vs 214MB)

---

## Dependencies Management

### requirements.txt (Frozen Versions):

**Core:**
- Django==3.2.6
- gunicorn==20.1.0 (production server)
- whitenoise==5.2.0 (static files)
- psycopg2==2.9.5 (PostgreSQL)

**Extensions:**
- django-crispy-forms, django-countries, django-filter
- django-allauth (authentication)
- celery, redis (async tasks)
- google-api-python-client (Google services)

**Update Dependencies:**
```bash
# Check for updates
pip list --outdated

# Update specific package
pip install --upgrade PACKAGE_NAME

# Freeze
pip freeze > requirements.txt

# Test locally before deploying
```

---

## Deployment Size Optimization

### Before Optimization:
- **Size:** 214.9MB compressed
- **Included:** venv/, docs/, tests/, archive/, backups/

### After Optimization:
- **Size:** 79.9MB compressed (63% reduction!)
- **Excluded:** All unnecessary files via .slugignore

### Optimization Steps Applied:

1. Created `.slugignore` file
2. Excluded docs/, tests/, scripts/ from Heroku
3. Removed venv/ from git tracking
4. Kept only essential code for deployment

---

## Recent Infrastructure Changes

### October 20, 2025:
- ✅ Updated .gitignore to properly exclude archive/ and backups/
- ✅ Created .slugignore for Heroku-specific exclusions
- ✅ Reduced deployment size by 63%
- ✅ Organized production scripts into scripts/production/

### October 18, 2025:
- ✅ Merged deployment branches
- ✅ Resolved git conflicts
- ✅ Stabilized deployment process

---

## Troubleshooting

### Deployment Fails:

**Check:**
1. Build logs for errors
2. requirements.txt has all dependencies
3. Migrations are up to date
4. Environment variables set

**Common Fixes:**
```bash
# Clear build cache
heroku repo:purge_cache --app APP_NAME

# Rebuild
git commit --allow-empty -m "rebuild: Force rebuild"
git push production main
```

### Database Connection Issues:

**Check:**
```bash
heroku pg:info --app APP_NAME
heroku config:get DATABASE_URL --app APP_NAME
```

### Migration Issues:

**Fix:**
```bash
# Fake initial if tables exist
heroku run "python manage.py migrate APP_NAME --fake-initial" --app APP_NAME

# Force specific migration
heroku run "python manage.py migrate APP_NAME MIGRATION_NUMBER" --app APP_NAME
```

---

## Maintenance Windows

### Recommended Schedule:

**Weekly:**
- Review error logs
- Check performance metrics
- Monitor data quality

**Monthly:**
- Update dependencies
- Review user access
- Backup database manually

**Quarterly:**
- Security audit
- Performance optimization
- User training refresher
- Budget vs. actual review

---

## Support & Resources

### Heroku Documentation:
- https://devcenter.heroku.com/
- https://devcenter.heroku.com/articles/django-app-configuration

### Django Documentation:
- https://docs.djangoproject.com/en/3.2/

### Internal Documentation:
- Getting Started: `docs/01_GETTING_STARTED/`
- Testing: `docs/04_TESTING/`
- Apps: `docs/apps/`

---

*Maintained by: CODA Development Team*  
*Infrastructure Lead: System Admin*  
*Last Review: October 21, 2025*

