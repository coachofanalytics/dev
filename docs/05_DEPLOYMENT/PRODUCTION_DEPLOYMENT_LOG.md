# Production Deployment Log

**Environment:** Production (codatrainingapp.herokuapp.com)  
**Last Updated:** October 21, 2025  
**Current Version:** v1746

---

## Recent Deployments (October 2025)

### October 20-21, 2025: Budget System Implementation

**Versions:** v1739 → v1746 (7 deployments)  
**Branch:** `25.10_CODA_DEV_v2_CM`  
**Status:** ✅ Successfully Deployed

**Major Changes:**
- Implemented AI-powered budget system
- Auto-categorized 276 transactions (48% → 97.1%)
- Generated 2026 budget projections ($766K)
- Fixed 10 critical issues
- Organized production scripts

**Deployment Commands:**
```bash
git push production 25.10_CODA_DEV_v2_CM:main
```

**Post-Deployment:**
- Ran migrations: `migrate finance --fake-initial`
- Applied `0002_budgetcategory_tier_fields`
- Verified data quality: 97.1% categorized
- Generated budget projections

### October 18, 2025: Merge & Stabilization

**Status:** Merged branches, resolved conflicts  
**Files Changed:** Portfolio templates, payment views  
**Deployed:** Successfully

---

## Infrastructure Setup

### HTTPS Configuration (Complete)

**Status:** ✅ Configured for local development  
**Certificate:** Self-signed for localhost  
**Port:** 8000 (HTTPS)

**Files:**
- SSL certificate: Generated
- Configuration: Updated
- Browser cache: Cleared

**Guide:** `HTTPS_SETUP_COMPLETE.md` → Archived

### Database Switching

**Environments:**
- **Development:** SQLite (local)
- **UAT:** PostgreSQL (codamakutano)
- **Production:** PostgreSQL (codatrainingapp)

**Switching Command:**
```bash
# Set in environment
export DJANGO_ENV=production  # or staging, development
```

**Settings Files:**
- `coda/coda_project/coda_settings/local_settings.py`
- `coda/coda_project/coda_settings/heroku_settings.py`
- `coda/coda_project/settings.py` (loader)

**Guide:** `DATABASE_SWITCHING_GUIDE.md` → Consolidated here

### Local Development Setup

**Status:** ✅ Ready  
**Python:** 3.12.6  
**Django:** 3.2.6

**Quick Start:**
```bash
cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV
source venv/bin/activate
cd coda
python manage.py runserver
```

**HTTPS (Optional):**
```bash
./scripts/run_https_local.sh
```

---

## Deployment Procedures

### To UAT (codamakutano):

```bash
git push heroku BRANCH_NAME:main
# Or using remote name:
git push uat BRANCH_NAME
```

**Post-Deploy Checks:**
```bash
# Verify URLs
heroku run "cd coda && python manage.py show_urls | grep finance" --app codamakutano

# Test critical path
curl https://codamakutano.herokuapp.com/finance/budget-dashboard/coda/
```

### To Production (codatrainingapp):

```bash
git push production BRANCH_NAME:main
```

**Post-Deploy Checks:**
```bash
# Run migrations if needed
heroku run "cd coda && python manage.py migrate" --app codatrainingapp

# Check data quality
heroku run "cd coda && python manage.py shell -c \"from finance.models import Transaction; print(f'Categorized: {Transaction.objects.filter(category__isnull=False).count()}/{Transaction.objects.count()}')\"" --app codatrainingapp

# Verify version
heroku releases --app codatrainingapp | head -5
```

### To GitHub UAT:

```bash
git push uat BRANCH_NAME
```

---

## Deployment Checklist

### Pre-Deployment:

- [ ] All tests pass locally
- [ ] No linter errors
- [ ] Migrations created (if models changed)
- [ ] Environment variables configured
- [ ] Dependencies in requirements.txt
- [ ] .slugignore updated (exclude docs/tests from Heroku)
- [ ] Changes documented

### During Deployment:

- [ ] Git branch up to date
- [ ] Commit message descriptive
- [ ] Push to correct remote
- [ ] Monitor build log for errors
- [ ] Note deployed version number

### Post-Deployment:

- [ ] Run migrations if needed
- [ ] Test critical URLs
- [ ] Check logs for errors: `heroku logs --tail`
- [ ] Verify data integrity
- [ ] Update documentation
- [ ] Notify team of changes

---

## Configuration Files

### Required Files:
- `Procfile` - Heroku process types
- `runtime.txt` - Python version (deprecated, use .python-version)
- `requirements.txt` - Python dependencies
- `.slugignore` - Files to exclude from Heroku
- `.gitignore` - Files to exclude from Git

### Environment Variables:

**Production (codatrainingapp):**
```
DATABASE_URL (auto-set by Heroku)
DJANGO_ENV=production
SECRET_KEY (configured)
DISABLE_COLLECTSTATIC=1
```

**UAT (codamakutano):**
```
DATABASE_URL (auto-set by Heroku)
DJANGO_ENV=staging
SECRET_KEY (configured)
DISABLE_COLLECTSTATIC=1
```

---

## Git Configuration

### Remotes:

```bash
origin     git@github.com:CODA-PROD/dev.git
uat        git@github.com:CODA-PROD/uat.git
heroku     https://git.heroku.com/codamakutano.git (UAT)
production https://git.heroku.com/codatrainingapp.git (Production)
```

### Active Branches:
- `25.10_CODA_DEV_v2_CM` - Main development (current)
- `25.10_UAT_DEPLOYMENT_FIX_CM` - UAT fixes
- Other feature branches as needed

---

## Heroku Stack Information

**Current:** Heroku-22  
**Available:** Heroku-24 (newer)  
**Recommendation:** Upgrade to Heroku-24 in next maintenance window

**Python Version:**
- **Current:** 3.12.6
- **Available:** 3.12.12
- **Recommendation:** Update to 3.12 (auto-patches)

**Migration Path:**
```bash
# Create .python-version file
echo "3.12" > .python-version

# Remove runtime.txt
git rm runtime.txt

# Deploy
git commit -m "migrate: Use .python-version instead of runtime.txt"
git push production main
```

---

## Monitoring & Logs

### View Logs:
```bash
# Real-time
heroku logs --tail --app codatrainingapp

# Last 100 lines
heroku logs -n 100 --app codatrainingapp

# Specific dyno
heroku logs --dyno web --app codatrainingapp

# Filter by level
heroku logs --tail --app codatrainingapp | grep ERROR
```

### Common Issues:

**Slow Performance:**
- Check dyno usage: `heroku ps --app codatrainingapp`
- Review query efficiency
- Add database indexes

**Memory Issues:**
- Check memory usage
- Optimize queries (select_related, prefetch_related)
- Consider upgrading dyno type

**Database Errors:**
- Check migration status: `heroku run "python manage.py showmigrations"`
- Verify schema matches models
- Review connection pooling

---

## Backup & Recovery

### Database Backups:

**Automatic:** Heroku PostgreSQL auto-backups (depends on plan)

**Manual Backup:**
```bash
heroku pg:backups:capture --app codatrainingapp
heroku pg:backups:download --app codatrainingapp
```

**Restore:**
```bash
heroku pg:backups:restore BACKUP_ID --app codatrainingapp
```

### Code Backups:

**Git is the source of truth:**
- GitHub: CODA-PROD/uat (full history)
- GitHub: CODA-PROD/dev (development)
- Local: All branches preserved

---

## Performance Optimization

### Database:
- Use `.select_related()` for ForeignKeys
- Use `.prefetch_related()` for Many-to-Many
- Add indexes on frequently queried fields
- Use `.only()` to limit field loading

### Heroku:
- Enable caching where appropriate
- Use CDN for static files (if applicable)
- Monitor dyno metrics
- Consider upgrading plan for better performance

---

## Security Considerations

### Sensitive Data:
- Real financial data ($2.3M)
- User information
- Department budgets

### Best Practices:
- ✅ Environment variables for secrets
- ✅ HTTPS enforced
- ✅ Authentication required
- ✅ Permission-based views
- ✅ Audit logging (signals track changes)

### Regular Tasks:
- Review user access quarterly
- Update dependencies monthly
- Security patches immediately
- Password rotation annually

---

## Related Documentation

- **Budget Implementation:** `docs/apps/finance/Budget/PRODUCTION_IMPLEMENTATION.md`
- **Testing Strategy:** `docs/04_TESTING/`
- **Integration Guide:** `docs/06_INTEGRATION/`
- **Technical Docs:** `docs/TECHNICAL_DOCS.md`

---

*Maintained by: CODA Development Team*  
*Last Review: October 21, 2025*  
*Next Review: December 2025*

