# Deployment Guide

## Environments

### Local Development
```bash
# Setup
cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV
source venv/bin/activate
cd coda
python manage.py runserver 0.0.0.0:8000

# Access
http://127.0.0.1:8000
```

### UAT (User Acceptance Testing)
```bash
# Deploy
git add -A
git commit -m "Clear description of changes"
git push heroku 25.10_CODA_DEV_CM:main

# Access
https://codamakutano.herokuapp.com

# Verify
heroku run "cd coda && python manage.py show_urls | grep finance" --app codamakutano
```

### Production (Future)
```bash
# Not yet deployed
# Will be: https://codatrainingapp.herokuapp.com
```

## Deployment Process

### Pre-Deployment Checklist
- [ ] All tests pass locally
- [ ] No console errors
- [ ] Database migrations up to date
- [ ] Environment variables set
- [ ] Documentation updated

### Deployment Steps
1. **Test Locally**
   ```bash
   python manage.py check
   python manage.py test
   ```

2. **Commit Changes**
   ```bash
   git add -A
   git commit -m "Descriptive commit message"
   ```

3. **Deploy to UAT**
   ```bash
   git push heroku 25.10_CODA_DEV_CM:main
   ```

4. **Verify Deployment**
   ```bash
   heroku logs --tail --app codamakutano
   curl https://codamakutano.herokuapp.com/finance/budget-dashboard/coda/
   ```

5. **User Testing**
   - Test critical workflows
   - Verify all buttons work
   - Check calculations
   - Report any issues

## Environment Configuration

### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql://...

# Email
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...

# Google API (optional)
GOOGLE_API_CREDENTIALS=...

# Django
SECRET_KEY=...
DEBUG=False  # for production
```

### Heroku Configuration
```bash
# Set environment variables
heroku config:set SECRET_KEY=... --app codamakutano
heroku config:set DEBUG=False --app codamakutano

# Check configuration
heroku config --app codamakutano
```

## Database Management

### Migrations
```bash
# Create migration
python manage.py makemigrations

# Apply migration
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

### Data Management
```bash
# Backup database
heroku pg:backups:capture --app codamakutano

# Restore database
heroku pg:backups:restore BACKUP_ID --app codamakutano

# Access database
heroku pg:psql --app codamakutano
```

## Monitoring

### Health Checks
```bash
# Check app status
heroku ps --app codamakutano

# Check logs
heroku logs --tail --app codamakutano

# Check database
heroku pg:info --app codamakutano
```

### Performance Monitoring
- **Response Times:** Monitor page load times
- **Error Rates:** Check for 500 errors
- **Database Performance:** Monitor query times
- **Memory Usage:** Check dyno memory

## Troubleshooting

### Common Issues

#### Deployment Fails
```bash
# Check build logs
heroku logs --tail --app codamakutano

# Common fixes
git push heroku 25.10_CODA_DEV_CM:main --force
heroku restart --app codamakutano
```

#### Database Errors
```bash
# Reset database (DANGER: loses data)
heroku pg:reset --app codamakutano
heroku run "cd coda && python manage.py migrate" --app codamakutano
```

#### Memory Issues
```bash
# Check memory usage
heroku logs --tail --app codamakutano | grep "Memory usage"

# Restart dynos
heroku restart --app codamakutano
```

### Emergency Procedures

#### Rollback Deployment
```bash
# Rollback to previous release
heroku rollback --app codamakutano

# Or rollback to specific release
heroku rollback vXXX --app codamakutano
```

#### Emergency Maintenance
```bash
# Put app in maintenance mode
heroku maintenance:on --app codamakutano

# Take out of maintenance mode
heroku maintenance:off --app codamakutano
```

## Security

### SSL/HTTPS
- Heroku provides free SSL certificates
- Custom domains need SSL configuration
- Force HTTPS in production

### Access Control
- All views require authentication
- Company-based data isolation
- User permission checks

### Data Protection
- Regular backups
- Secure environment variables
- No sensitive data in code

## Performance Optimization

### Database
- Use proper indexes
- Optimize queries
- Regular maintenance

### Static Files
- Use CDN for static files
- Compress images
- Minify CSS/JS

### Caching
- Enable Django caching
- Cache expensive calculations
- Use Redis for sessions

## Backup Strategy

### Database Backups
```bash
# Daily automated backups (Heroku handles this)
# Manual backup before major changes
heroku pg:backups:capture --app codamakutano
```

### Code Backups
- Git repository is the backup
- Tag releases for easy rollback
- Keep multiple branches

## Release Notes

### Current Version
- **Version:** v880+
- **Date:** October 11, 2025
- **Changes:** Fixed budget buttons, login redirect, consolidated docs
- **Status:** Stable, ready for testing

### Previous Versions
- **v880:** Initial organization and fixes
- **v879:** Phase 2 completion
- **v878:** Phase 1 completion

---

**Remember:** Always test locally before deploying to UAT, and test in UAT before production!
