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

### **Advanced Heroku Log Filtering** 🎯
```bash
# Filter by source (most useful for debugging)
heroku logs --app codamakutano --source app --num 100          # App logs only
heroku logs --app codamakutano --source heroku --num 50        # System logs only
heroku logs --app codamakutano --source api --num 20           # API/deployment logs

# Filter by process type
heroku logs --app codamakutano --process-type web --num 100    # Web process only
heroku logs --app codamakutano --process-type worker --num 50  # Worker process only

# Filter by specific dyno instance
heroku logs --app codamakutano --dyno-name web.1 --num 50

# Combination filters (most powerful)
heroku logs --app codamakutano --source app --process-type web --num 100

# Real-time streaming with filters
heroku logs --app codamakutano --tail --source app             # Stream app logs
heroku logs --app codamakutano --tail --process-type web       # Stream web logs
```

**Log Filtering Recommendations:**
- Use `--source app` for application-specific issues
- Use `--num 100` or higher for comprehensive debugging
- Use `--tail` for real-time monitoring during deployments
- Combine filters for targeted debugging

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

### **Slug Size Optimization** 🚀
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

### **Advanced Optimization Strategies** ⚡
```bash
# 1. Remove heavy packages from requirements.txt
# Remove: chromedriver, google-api-python-client, selenium, etc.
# Keep only essential packages

# 2. Optimize virtual environment
rm -rf venv/lib/python*/site-packages/*/tests/
rm -rf venv/lib/python*/site-packages/*/test/
find venv -name "*.pyc" -delete
find venv -name "__pycache__" -type d -exec rm -rf {} +

# 3. Clean static files
find . -name "*.jpg" -size +500k -exec ls -lh {} \;  # Find large images
find . -name "*.png" -size +500k -exec ls -lh {} \;  # Find large images
find . -name "*.gif" -size +500k -exec ls -lh {} \;  # Find large images

# 4. Remove development files
rm -rf .git/hooks/
rm -rf node_modules/  # If using Node.js
rm -rf .vscode/
rm -rf .idea/

# 5. Use optimized requirements file
cp requirements-optimized.txt requirements.txt
```

**Optimization Results Achieved:**
- **Before**: 956MB slug size
- **After**: 163.1MB slug size
- **Reduction**: 83% (793MB saved)
- **Virtual Environment**: 727MB → 159MB (78% reduction)

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

### **Cursor AI Assistant Best Practices**
- **Be Specific**: Provide detailed context and requirements
- **Iterative Development**: Break complex tasks into smaller steps
- **Test-Driven**: Always request testing after implementing features
- **Documentation-First**: Ask Cursor to document changes and lessons learned
- **Error Analysis**: When errors occur, ask Cursor to analyze and provide solutions
- **Performance Focus**: Always consider performance implications of changes

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

## 📖 Documentation & Lessons Learned

### **Documentation Update Protocol** 📝
**IMPORTANT**: Always update documentation when implementing changes or learning new lessons.

#### **When to Update Documentation:**
- After fixing bugs or errors
- After implementing new features
- After optimizing performance
- After resolving deployment issues
- After learning new debugging techniques
- After successful problem-solving sessions

#### **What to Document:**
```markdown
## Lessons Learned - [Date]

### Issue/Challenge:
- Brief description of the problem

### Root Cause:
- Technical explanation of why it occurred

### Solution Applied:
- Step-by-step resolution process
- Code changes made
- Configuration updates

### Prevention Measures:
- How to avoid this issue in the future
- Best practices to implement
- Monitoring recommendations

### Performance Impact:
- Before/after metrics
- Optimization results

### Files Modified:
- List of files changed
- Key changes made
```

### **Cursor AI Documentation Commands**
When working with Cursor AI, always request documentation updates:

```bash
# Request documentation update after completing tasks
"Please update the documentation with the lessons learned from this session"

# Request specific documentation sections
"Please add this solution to the troubleshooting guide"

# Request performance documentation
"Please document the performance improvements achieved"
```

### **Documentation Files to Maintain:**
1. **CURSOR_WORKFLOW.md** - This file (workflow and best practices)
2. **README.md** - Project overview and setup
3. **FIXES_APPLIED_SUMMARY.md** - Bug fixes and resolutions
4. **COMPREHENSIVE_TEST_ANALYSIS.md** - Test results and analysis
5. **SLUG_SIZE_OPTIMIZATION_ANALYSIS.md** - Performance optimization records

### **Recent Lessons Learned** (Updated: September 21, 2025)

#### **Slug Size Optimization Success**
- **Issue**: Heroku slug size was 956MB, exceeding limits
- **Solution**: Removed heavy packages, optimized virtual environment, cleaned static files
- **Result**: Reduced to 163.1MB (83% reduction)
- **Lesson**: Always monitor slug size and implement optimization strategies

#### **Heroku Log Filtering Best Practices**
- **Issue**: Difficult to find relevant logs among continuous log generation
- **Solution**: Use `--source app` and `--process-type` filters
- **Lesson**: `heroku logs --app codamakutano --source app --num 100` is most effective for debugging

#### **Database Migration Conflicts**
- **Issue**: Multiple migration conflicts during deployment
- **Solution**: Use `--fake` flag for existing fields, proper field defaults
- **Lesson**: Always check existing database schema before creating migrations

#### **UI/UX Button Visibility**
- **Issue**: Login buttons were dark on blue background, invisible to users
- **Solution**: Applied golden-orange background (#e7ad4a) with white text
- **Lesson**: Always test UI visibility and contrast ratios

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

## 🎯 Quick Reference Commands

### **Most Used Commands**
```bash
# Deploy to UAT
git push heroku master:main --force

# Check UAT logs (filtered)
heroku logs --app codamakutano --source app --num 100

# Run comprehensive tests
python coda/tests/run_comprehensive_tests.py

# Check app status
heroku ps --app codamakutano

# Optimize slug size
python optimize_slug_size.py
```

### **Emergency Commands**
```bash
# Rollback deployment
heroku rollback --app codamakutano

# Restart app
heroku restart --app codamakutano

# Check critical errors
heroku logs --app codamakutano --source app --num 50 | grep -E "(ERROR|CRITICAL|Exception)"
```

---

**Last Updated**: September 21, 2025  
**Version**: 2.0  
**Status**: Production Ready ✅  
**UAT Environment**: codamakutano.herokuapp.com ✅  
**Slug Size**: 163.1MB (83% optimized) ✅

