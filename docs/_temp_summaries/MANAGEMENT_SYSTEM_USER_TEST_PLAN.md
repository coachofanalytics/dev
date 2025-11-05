# MANAGEMENT SYSTEM - USER TESTING PLAN
**Date:** November 3, 2025  
**Purpose:** Test existing system from user perspective BEFORE adding new features

---

## 🎯 OBJECTIVE

Understand what ALREADY EXISTS and WORKS before building anything new.

**Approach:** Manual user testing to see the actual flow.

---

## 🧪 TEST SCENARIO 1: Employee Task Flow

### User: gndahiro (PAID employee)
**Credentials:** Username: gndahiro / Password: MANAGER2030

### Steps to Test:

**1. Login**
```
URL: http://127.0.0.1:5000/accounts/login/
Login as: gndahiro
```

**2. View Tasks**
```
URL: /management/tasks/
Check: 
- How many tasks are shown?
- What are the points for each task?
- Can you see task details?
```

**3. View Task History**
```
URL: /management/userevidence/ (or similar)
Check:
- How many TaskHistory records?
- Can you see past months?
- Are points recorded correctly?
```

**4. View Payslip**
```
URL: /management/payroll/?username=gndahiro&pay_type=taskhistory
Check:
- Is salary calculated?
- Are bonuses shown?
- Are deductions shown?
- Is net pay displayed?
- Can you select different months?
```

**5. Try Task Reset**
```
URL: /management/reset_tasks/
OR: /management/reset_tasks/select/ (new UI)

Check:
- Does it show gndahiro?
- Is gndahiro auto-selected?
- Does preview work?
- Does reset work?
- Do tasks move to history?
```

---

## 🧪 TEST SCENARIO 2: Admin View

### User: Admin/Superuser

### Steps:

**1. Company Agenda**
```
URL: /management/companyagenda/
Check what admin dashboard shows
```

**2. All Employees Tasks**
```
URL: /management/tasks/
Filter to see all employees
```

**3. Payroll for All**
```
URL: /management/payroll/?pay_type=taskhistory
Check if you can see different employees
```

**4. Task Reset Interface**
```
URL: /management/reset_tasks/select/
Check:
- Does it show all employees?
- Are employee types shown?
- Does 33% compliance show?
- Can you select/deselect?
```

---

## 📊 WHAT TO OBSERVE

### From gndahiro perspective:

1. **Tasks:**
   - [ ] Can view current tasks?
   - [ ] Can add evidence to tasks?
   - [ ] Can see points accumulating?

2. **History:**
   - [ ] Can view past months?
   - [ ] Can see completed tasks?
   - [ ] History shows correct data?

3. **Payslip:**
   - [ ] Can view own payslip?
   - [ ] Salary calculated correctly?
   - [ ] Can select different months?
   - [ ] Shows bonuses and deductions?

4. **Compliance:**
   - [ ] Is 33% rule enforced?
   - [ ] Shows compliance status?
   - [ ] Payment held if non-compliant?

---

## 📝 DOCUMENT FINDINGS

After testing, note:

### What Works:
- List features that work well
- Note any good UX elements
- Document the actual flow

### What Doesn't Work:
- Any errors encountered
- Confusing UI elements
- Missing features user expects

### What's Unclear:
- Features that exist but not obvious
- Process that needs documentation
- Where users might get stuck

---

## 🎯 READY TO TEST?

**Start with:**
```bash
cd coda
python manage.py runserver 5000

# Then open browser:
http://127.0.0.1:5000/accounts/login/

# Login as gndahiro and explore!
```

**I'll wait for your findings before suggesting any new code.**

---

**Let's understand what exists first!** ✅

