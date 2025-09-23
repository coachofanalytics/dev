# 🧪 CODA Manual User Testing Guide

## 🚀 **QUICK START**

### **Start Local Development Server**
```bash
cd /Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV/app
python3 start_server.py
```

### **Access Application**
- **Main Application**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/v1/schema/swagger-ui/

---

## 👥 **USER CATEGORIES TO TEST**

### **1. Admin Users**
- **Access Level**: Full system access
- **Test Pages**:
  - `/admin/` - Django admin panel
  - `/admin/dashboard/` - Admin dashboard
  - `/admin/users/` - User management
  - `/finance/` - Financial management
  - `/investing/` - Investment management
  - `/management/` - HR management
  - `/ai-services/` - AI services

### **2. Regular Users**
- **Access Level**: Personal finance management
- **Test Pages**:
  - `/user/dashboard/` - User dashboard
  - `/finance/dashboard/` - Financial overview
  - `/finance/loans/` - Loan applications
  - `/finance/payments/` - Payment management
  - `/investing/portfolio/` - Investment portfolio

### **3. Loan Officers**
- **Access Level**: Loan processing and approval
- **Test Pages**:
  - `/loan/dashboard/` - Loan officer dashboard
  - `/loan/applications/` - Loan applications list
  - `/loan/approve/` - Loan approval process
  - `/finance/loans/` - Loan management

### **4. Financial Advisors**
- **Access Level**: Investment management
- **Test Pages**:
  - `/advisor/dashboard/` - Financial advisor dashboard
  - `/investing/portfolio/` - Investment portfolio
  - `/investing/rates/` - Investment rates
  - `/investing/analytics/` - Investment analytics

### **5. HR Managers**
- **Access Level**: Employee and payroll management
- **Test Pages**:
  - `/hr/dashboard/` - HR dashboard
  - `/hr/employees/` - Employee list
  - `/hr/payroll/` - Payroll management
  - `/management/` - Management tools

### **6. Analysts**
- **Access Level**: Data analysis and reporting
- **Test Pages**:
  - `/analytics/dashboard/` - Analytics dashboard
  - `/analytics/reports/` - Analytics reports
  - `/analytics/data/` - Data analysis tools
  - `/ai-services/analytics/` - AI analytics

---

## 🔍 **TESTING PROCEDURES**

### **Step 1: Server Startup**
1. Start the local development server
2. Verify server is running at http://localhost:8000
3. Check for any startup errors in terminal

### **Step 2: Basic Page Access**
1. **Home Page**: Visit http://localhost:8000
   - ✅ Should load without errors
   - ✅ Should display CODA branding
   - ✅ Should have navigation menu

2. **Admin Panel**: Visit http://localhost:8000/admin/
   - ✅ Should redirect to login if not authenticated
   - ✅ Should show Django admin login form

3. **API Documentation**: Visit http://localhost:8000/api/v1/schema/swagger-ui/
   - ✅ Should load API documentation
   - ✅ Should show available endpoints

### **Step 3: User Registration/Login**
1. **Registration**: Visit http://localhost:8000/accounts/signup/
   - ✅ Should show registration form
   - ✅ Should allow user creation

2. **Login**: Visit http://localhost:8000/accounts/login/
   - ✅ Should show login form
   - ✅ Should authenticate users

### **Step 4: User Category Testing**
For each user category, test:

1. **Login Process**
   - Create user with appropriate category
   - Login with credentials
   - Verify successful authentication

2. **Dashboard Access**
   - Access user-specific dashboard
   - Verify correct content is displayed
   - Check for any permission errors

3. **Feature Access**
   - Test access to category-specific features
   - Verify proper redirects
   - Check for forbidden access to other categories

4. **Navigation**
   - Test navigation menu items
   - Verify correct page redirects
   - Check for broken links

---

## 🐛 **COMMON ISSUES TO LOOK FOR**

### **Authentication Issues**
- ❌ Login form not loading
- ❌ Invalid credentials not handled
- ❌ Session not maintained
- ❌ Logout not working

### **Permission Issues**
- ❌ Users accessing unauthorized pages
- ❌ Admin features visible to regular users
- ❌ Category-specific features not restricted

### **Navigation Issues**
- ❌ Broken links
- ❌ Incorrect redirects
- ❌ Missing navigation items
- ❌ 404 errors on valid pages

### **Page Loading Issues**
- ❌ Pages not loading (500 errors)
- ❌ Missing static files
- ❌ Database connection errors
- ❌ Template rendering errors

### **API Issues**
- ❌ API endpoints not accessible
- ❌ Authentication required for API
- ❌ Rate limiting not working
- ❌ Documentation not loading

---

## 📋 **TESTING CHECKLIST**

### **✅ Server Functionality**
- [ ] Server starts without errors
- [ ] Home page loads correctly
- [ ] Static files served properly
- [ ] Database connections working
- [ ] Cache system functional

### **✅ User Authentication**
- [ ] Registration form works
- [ ] Login form works
- [ ] Logout functionality works
- [ ] Session management works
- [ ] Password reset works

### **✅ User Categories**
- [ ] Admin users can access admin features
- [ ] Regular users can access user features
- [ ] Loan officers can access loan features
- [ ] Financial advisors can access investment features
- [ ] HR managers can access HR features
- [ ] Analysts can access analytics features

### **✅ Page Redirects**
- [ ] Login redirects to appropriate dashboard
- [ ] Unauthorized access redirects to login
- [ ] Category-specific pages accessible
- [ ] Navigation links work correctly
- [ ] Breadcrumbs display correctly

### **✅ API Functionality**
- [ ] API endpoints accessible
- [ ] Authentication required for protected endpoints
- [ ] Rate limiting working
- [ ] Documentation accessible
- [ ] Error handling working

---

## 🎯 **TESTING RESULTS**

### **Expected Results**
- All user categories should be able to login
- Each category should access appropriate features
- Page redirects should work correctly
- No unauthorized access to restricted features
- API should be functional with proper authentication

### **Error Reporting**
When you find errors, note:
1. **User Category**: Which user type experienced the issue
2. **Page/Feature**: What page or feature had the problem
3. **Error Message**: Exact error message or behavior
4. **Steps to Reproduce**: How to recreate the issue
5. **Expected Behavior**: What should have happened

---

## 🚀 **READY FOR TESTING**

The CODA application is now ready for comprehensive manual testing. Use this guide to systematically test all user categories and identify any issues before deploying to Heroku.

**Start the server and begin testing!** 🧪
