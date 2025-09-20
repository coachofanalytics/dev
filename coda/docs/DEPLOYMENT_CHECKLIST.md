# 🚀 Production Deployment Checklist

**Purpose**: Comprehensive checklist to ensure successful deployments to Heroku production environment.

## 📋 Pre-Deployment Checklist

### ✅ Code Quality
- [ ] All tests pass locally
- [ ] No linting errors
- [ ] Code reviewed and approved
- [ ] Database migrations tested
- [ ] Static files optimized (images compressed, CSS minified)

### ✅ Environment Configuration
- [ ] Environment variables configured correctly
- [ ] Database credentials updated
- [ ] API keys and secrets configured
- [ ] Email settings configured
- [ ] SSL/HTTPS settings verified

### ✅ Static Files Configuration
- [ ] `STATIC_ROOT` points to correct directory
- [ ] `STATIC_URL` configured properly
- [ ] `STATICFILES_STORAGE` set for production
- [ ] `DISABLE_COLLECTSTATIC` unset (if using collectstatic)
- [ ] Static files collected and tested locally

## 🚀 Deployment Process

### ✅ Git & Repository
- [ ] All changes committed to git
- [ ] No uncommitted files
- [ ] Branch merged to main/master
- [ ] Remote repositories configured correctly

### ✅ Heroku Configuration
- [ ] Heroku CLI authenticated
- [ ] Correct app selected (production vs UAT)
- [ ] Environment variables set on Heroku
- [ ] Buildpack configured correctly
- [ ] Dyno configuration verified

### ✅ Deployment Commands
```bash
# 1. Check current status
heroku ps --app codatrainingapp

# 2. Deploy to production
git push production master:main --force

# 3. Check deployment status
heroku ps --app codatrainingapp

# 4. Run collectstatic (if needed)
heroku run "cd coda && python manage.py collectstatic --noinput" --app codatrainingapp
```

## 🧪 Post-Deployment Testing

### ✅ Application Health
- [ ] Application starts successfully
- [ ] No crashed dynos
- [ ] HTTP 200 response from homepage
- [ ] Database connections working
- [ ] No critical errors in logs

### ✅ Static Files Testing
- [ ] CSS files load correctly
- [ ] JavaScript files load correctly
- [ ] Images display properly
- [ ] Fonts load correctly
- [ ] Static file URLs return 200 OK

**CSS Testing Commands:**
```bash
# Test main CSS file
curl -I https://codatrainingapp.herokuapp.com/static/main/css/new_main.css

# Test other CSS files
curl -I https://codatrainingapp.herokuapp.com/static/admin/css/base.css
curl -I https://codatrainingapp.herokuapp.com/static/main/css/timer.css

# Test JavaScript files
curl -I https://codatrainingapp.herokuapp.com/static/admin/js/core.js

# Test images
curl -I https://codatrainingapp.herokuapp.com/static/main/image/logo.png
```

### ✅ Functional Testing
- [ ] User registration works
- [ ] User login works
- [ ] Core application features function
- [ ] Forms submit correctly
- [ ] Database operations work
- [ ] Email functionality works (if applicable)

### ✅ Performance Testing
- [ ] Page load times acceptable
- [ ] No memory leaks
- [ ] Database queries optimized
- [ ] Static files cached properly

## 🔍 Troubleshooting Common Issues

### ❌ CSS Not Loading
**Symptoms**: Pages load without styling, 404 errors for CSS files

**Diagnosis Steps:**
1. Check if static files were collected:
   ```bash
   heroku run "ls -la /app/coda/staticfiles/" --app codatrainingapp
   ```

2. Verify STATIC_ROOT configuration:
   ```bash
   heroku run "cd coda && python manage.py shell -c 'from django.conf import settings; print(settings.STATIC_ROOT)'" --app codatrainingapp
   ```

3. Check STATICFILES_STORAGE setting:
   ```bash
   heroku run "cd coda && python manage.py shell -c 'from django.conf import settings; print(settings.STATICFILES_STORAGE)'" --app codatrainingapp
   ```

**Solutions:**
- Run collectstatic manually: `heroku run "cd coda && python manage.py collectstatic --noinput" --app codatrainingapp`
- Verify STATIC_ROOT points to correct directory
- Ensure STATICFILES_STORAGE is configured for production
- Check if DISABLE_COLLECTSTATIC is set incorrectly

### ❌ Application Crashes
**Symptoms**: Dyno shows "crashed" status

**Diagnosis Steps:**
1. Check logs for errors:
   ```bash
   heroku logs --app codatrainingapp --num 50 | grep -E "(ERROR|CRITICAL|Exception|Traceback)"
   ```

2. Check for missing modules:
   ```bash
   heroku logs --app codatrainingapp --num 20 | grep -E "(ModuleNotFoundError|ImportError)"
   ```

**Solutions:**
- Fix missing imports
- Ensure all dependencies in requirements.txt
- Check Python path configuration
- Verify Procfile configuration

### ❌ Database Issues
**Symptoms**: Database connection errors, migration failures

**Diagnosis Steps:**
1. Check database configuration:
   ```bash
   heroku config --app codatrainingapp | grep -E "(DATABASE|DB)"
   ```

2. Run migrations:
   ```bash
   heroku run "cd coda && python manage.py migrate" --app codatrainingapp
   ```

**Solutions:**
- Update database credentials
- Run pending migrations
- Check database connection settings

## 📊 Monitoring & Maintenance

### ✅ Post-Deployment Monitoring
- [ ] Monitor application logs for 24 hours
- [ ] Check error rates and response times
- [ ] Monitor database performance
- [ ] Verify all integrations working
- [ ] Check user feedback and reports

### ✅ Regular Maintenance
- [ ] Update dependencies regularly
- [ ] Monitor security advisories
- [ ] Backup database regularly
- [ ] Review and optimize performance
- [ ] Update documentation

## 🚨 Emergency Procedures

### ❌ Rollback Process
1. Identify the last working commit
2. Deploy previous version:
   ```bash
   git push production <previous-commit-hash>:main --force
   ```
3. Verify rollback success
4. Investigate and fix issues
5. Plan re-deployment

### ❌ Critical Issues
- [ ] Application completely down
- [ ] Data corruption detected
- [ ] Security breach suspected
- [ ] Performance severely degraded

**Immediate Actions:**
1. Assess impact and severity
2. Notify stakeholders
3. Implement emergency fixes or rollback
4. Document incident
5. Post-mortem analysis

## 📝 Documentation Updates

### ✅ Post-Deployment Documentation
- [ ] Update deployment notes
- [ ] Document any configuration changes
- [ ] Update troubleshooting guides
- [ ] Record performance metrics
- [ ] Update user documentation if needed

---

## 🎯 Success Criteria

A successful deployment is achieved when:
- ✅ Application is running and accessible
- ✅ All static files (CSS, JS, images) load correctly
- ✅ Core functionality works as expected
- ✅ No critical errors in logs
- ✅ Performance metrics are acceptable
- ✅ User experience is not degraded

---

**Last Updated**: September 20, 2025  
**Version**: 1.0  
**Maintained By**: Development Team
