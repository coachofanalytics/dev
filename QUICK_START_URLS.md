# 🚀 Quick Start - Correct URLs to Test

**Server:** http://127.0.0.1:8000  
**Login:** `budget_manager` / `test123`

---

## ✅ CORRECT URLS TO USE

### 1. **Login First!**
```
http://127.0.0.1:8000/accounts/login/
```
- Use: `budget_manager` / `test123`
- This is **required** before accessing other pages

---

### 2. **Finance Budget Dashboard** ⭐ (Main one to test)
```
http://127.0.0.1:8000/finance/budget-dashboard/coda/
```
- This is the **main budget dashboard**
- Shows budget categories, totals, analytics
- **Start here after logging in!**

---

### 3. **Finance Home**
```
http://127.0.0.1:8000/finance/
```
- Finance app landing page
- Links to all finance sections

---

### 4. **Budget Requests**
```
http://127.0.0.1:8000/finance/budget-requests/
```
- Create new budget requests
- View pending requests
- Submit for approval

---

### 5. **Budget Approvals**
```
http://127.0.0.1:8000/finance/budget-approvals/
```
- View pending approvals
- Approve/reject requests
- See approval history

---

### 6. **Admin Interface**
```
http://127.0.0.1:8000/admin/
```
- Django admin panel
- Manage all models
- Login: `budget_manager` / `test123`

---

### 7. **Automation Dashboard**
```
http://127.0.0.1:8000/finance/automation/
```
- View automation rules
- Approval policies
- Audit logs

---

### 8. **Finance Dashboard** (Alternative)
```
http://127.0.0.1:8000/finance/finance-dashboard/coda/
```
- Another dashboard view
- More detailed analytics

---

## ❌ URLs THAT DON'T WORK (Yet)

### `/dashboard/` - Redirects to login
- This is the **unified dashboard** (separate app)
- Requires different setup
- **Use `/finance/budget-dashboard/coda/` instead!**

### `/finance/transactions/` - 404
- URL pattern may be different
- Check finance URLs for correct pattern

---

## 🎯 RECOMMENDED TEST SEQUENCE

1. **Login**
   ```
   http://127.0.0.1:8000/accounts/login/
   ```

2. **Budget Dashboard** (Main test!)
   ```
   http://127.0.0.1:8000/finance/budget-dashboard/coda/
   ```

3. **Create Budget Request**
   ```
   http://127.0.0.1:8000/finance/budget-requests/
   ```

4. **Approve Request**
   ```
   http://127.0.0.1:8000/finance/budget-approvals/
   ```

5. **Check Admin**
   ```
   http://127.0.0.1:8000/admin/
   ```

---

## 💡 TIPS

1. **Always login first** at `/accounts/login/`
2. **Use budget_manager** for testing (has staff permissions)
3. **Bookmark** `/finance/budget-dashboard/coda/` (main dashboard)
4. **Check browser console** (F12) for any JavaScript errors
5. **If page redirects to login**, your session expired - login again

---

## 🐛 IF YOU SEE ISSUES

### Page redirects to login:
- ✅ Expected - login required
- Login at `/accounts/login/`

### 404 Error:
- Check URL is exactly as shown above
- Some old URLs may have changed

### 500 Error:
- Check server logs
- Report the URL and what you clicked

---

## 📝 TESTING CHECKLIST

After logging in, test these in order:

- [ ] Budget Dashboard loads: `/finance/budget-dashboard/coda/`
- [ ] Can see budget categories
- [ ] Budget totals display
- [ ] Can click "Add Budget" (if button exists)
- [ ] Budget Requests page: `/finance/budget-requests/`
- [ ] Can create new request
- [ ] Budget Approvals page: `/finance/budget-approvals/`
- [ ] Can approve requests
- [ ] Admin interface: `/admin/`
- [ ] Can view transactions

---

**🎯 MAIN TAKEAWAY:**

**The budget dashboard you want is:**
```
http://127.0.0.1:8000/finance/budget-dashboard/coda/
```

**NOT `/dashboard/` (that's a different app!)**

---

Happy Testing! 🚀

