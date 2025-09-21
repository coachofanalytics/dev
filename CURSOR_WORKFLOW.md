# 🚀 Cursor Workflow Guide - CODA Analytics

**Purpose**: Comprehensive workflow guide for efficient development and deployment using Cursor AI assistant.

## 📋 Table of Contents
1. [Development Workflow](#development-workflow)
2. [Deployment Workflow](#deployment-workflow)
3. [Testing Workflow](#testing-workflow)
4. [Debugging Workflow](#debugging-workflow)
5. [Optimization Workflow](#optimization-workflow)
6. [Best Practices](#best-practices)
7. [Troubleshooting Guide](#troubleshooting-guide)

---

## 🔧 Development Workflow

### **Phase 1: Project Setup**
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Navigate to project directory
cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV

# 3. Check Django status
python manage.py check

# 4. Run migrations if needed
python manage.py migrate
```

### **Phase 2: Feature Development**
1. **Create feature branch**: `git checkout -b feature/your-feature-name`
2. **Make changes**: Use Cursor AI for code generation and refactoring
3. **Test locally**: Run comprehensive tests before committing
4. **Commit changes**: Use descriptive commit messages

### **Phase 3: Code Quality**
```bash
# Run linting
python -m flake8 .

# Run type checking
python -m mypy .

# Run security checks
python -m bandit -r .
```

---

## 🚀 Deployment Workflow

### **Pre-Deployment Checklist**
- [ ] All tests pass locally
- [ ] Code reviewed and approved
- [ ] Database migrations tested
- [ ] Static files optimized
- [ ] Environment variables configured
- [ ] SSL/HTTPS settings verified

### **UAT Deployment (codamakutano)**
```bash
# 1. Commit changes
git add .
git commit -m "Feature: Your feature description"

# 2. Deploy to UAT
git push heroku master:main --force

# 3. Check deployment status
heroku logs --tail --app codamakutano

# 4. Test UAT functionality
curl -I https://codamakutano.herokuapp.com/
```

### **Production Deployment (codatrainingapp)**
```bash
# 1. Verify UAT is working
curl -I https://codamakutano.herokuapp.com/

# 2. Deploy to production
git push production master:main --force

# 3. Monitor deployment
heroku logs --tail --app codatrainingapp

# 4. Test production functionality
curl -I https://codatrainingapp.herokuapp.com/
```

### **Post-Deployment Verification**
- [ ] Application responds with HTTP 200
- [ ] CSS files load correctly (`/static/main/css/new_main.css`)
- [ ] Database connections working
- [ ] User authentication working
- [ ] All critical user flows functional

---

## 🧪 Testing Workflow

### **Local Testing**
```bash
# Run comprehensive test suite
python coda/tests/run_comprehensive_tests.py

# Run specific test categories
python manage.py test accounts.tests
python manage.py test finance.tests
python manage.py test ai_services.tests
```

### **Test Categories**
1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Service integration testing
3. **E2E Tests**: End-to-end user flow testing
4. **Performance Tests**: Load and performance testing
5. **Security Tests**: Security vulnerability testing

### **Test Coverage**
- Aim for 80%+ code coverage
- Test all critical user flows
- Test all API endpoints
- Test all database operations

---

## 🐛 Debugging Workflow

### **Local Debugging**
```bash
# 1. Check Django status
python manage.py check

# 2. Check database migrations
python manage.py showmigrations

# 3. Check static files
python manage.py collectstatic --dry-run

# 4. Run with debug logging
python manage.py runserver --verbosity=2
```

### **Heroku Debugging**
```bash
# 1. Check app status
heroku ps --app codatrainingapp

# 2. Check logs (filtered)
heroku logs --tail --app codatrainingapp | grep -E "(ERROR|CRITICAL|Exception)"

# 3. Run Django shell
heroku run "cd coda && python manage.py shell" --app codatrainingapp

# 4. Check environment variables
heroku config --app codatrainingapp
```

### **Common Issues & Solutions**

#### **CSS Not Loading**
```bash
# Check static files configuration
heroku run "cd coda && python manage.py collectstatic --noinput" --app codatrainingapp

# Verify STATIC_ROOT setting
heroku run "cd coda && python manage.py shell -c 'from django.conf import settings; print(settings.STATIC_ROOT)'" --app codatrainingapp
```

#### **Module Not Found Errors**
```bash
# Check Python path
heroku run "cd coda && python -c 'import sys; print(sys.path)'" --app codatrainingapp

# Verify file structure
heroku run "ls -la /app/coda/" --app codatrainingapp
```

#### **Database Connection Issues**
```bash
# Check database configuration
heroku run "cd coda && python manage.py shell -c 'from django.conf import settings; print(settings.DATABASES)'" --app codatrainingapp

# Test database connection
heroku run "cd coda && python manage.py dbshell" --app codatrainingapp
```

---

## ⚡ Optimization Workflow

### **Slug Size Optimization**
```bash
# 1. Analyze current slug size
heroku run "du -sh /app" --app codatrainingapp

# 2. Identify large files
heroku run "find /app -type f -size +1M -exec ls -lh {} \;" --app codatrainingapp

# 3. Optimize images
python coda/scripts/optimize_images.py

# 4. Remove unnecessary files
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
```

### **Performance Optimization**
```bash
# 1. Run performance tests
python coda/tests/performance/test_performance.py

# 2. Check database queries
python manage.py shell -c "from django.db import connection; print(connection.queries)"

# 3. Monitor memory usage
python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"
```

---

## 📚 Best Practices

### **Code Organization**
- Keep related functionality in the same app
- Use clear, descriptive variable and function names
- Follow Django conventions for models, views, and URLs
- Document complex business logic

### **Git Workflow**
- Use descriptive commit messages
- Create feature branches for new development
- Test thoroughly before merging to main
- Keep commits atomic and focused

### **Deployment**
- Always test in UAT before production
- Use environment-specific settings
- Monitor logs during and after deployment
- Have rollback plan ready

### **Testing**
- Write tests for new features
- Test edge cases and error conditions
- Maintain high test coverage
- Use meaningful test names

---

## 🔍 Troubleshooting Guide

### **Deployment Issues**

#### **ModuleNotFoundError**
- **Cause**: Missing Python path configuration
- **Solution**: Update Procfile with correct PYTHONPATH
- **Prevention**: Test deployment in UAT first

#### **Static Files Not Loading**
- **Cause**: Incorrect STATIC_ROOT or missing collectstatic
- **Solution**: Configure STATICFILES_DIRS and run collectstatic
- **Prevention**: Test static files in UAT

#### **Database Migration Errors**
- **Cause**: Incompatible migration files
- **Solution**: Reset migrations or fix conflicts
- **Prevention**: Test migrations in UAT

### **Performance Issues**

#### **Slow Page Loads**
- **Cause**: Unoptimized queries or large static files
- **Solution**: Add database indexes, optimize images
- **Prevention**: Regular performance testing

#### **High Memory Usage**
- **Cause**: Memory leaks or inefficient code
- **Solution**: Profile memory usage, optimize code
- **Prevention**: Monitor memory in production

---

## 📊 Monitoring & Maintenance

### **Daily Checks**
- [ ] Application health status
- [ ] Error logs review
- [ ] Performance metrics
- [ ] User feedback monitoring

### **Weekly Maintenance**
- [ ] Security updates
- [ ] Dependency updates
- [ ] Performance optimization
- [ ] Backup verification

### **Monthly Reviews**
- [ ] Code quality metrics
- [ ] Test coverage analysis
- [ ] Performance trends
- [ ] User satisfaction metrics

---

## 🎯 Success Metrics

### **Development Metrics**
- Code coverage: 80%+
- Test pass rate: 95%+
- Deployment success rate: 95%+
- Bug resolution time: <24 hours

### **Performance Metrics**
- Page load time: <3 seconds
- API response time: <500ms
- Uptime: 99.9%+
- Memory usage: <80%

---

**Last Updated**: September 20, 2025  
**Version**: 1.0  
**Status**: Production Ready ✅

