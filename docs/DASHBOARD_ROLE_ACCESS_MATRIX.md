# Dashboard Role-Based Access Matrix

**Date:** November 6, 2025  
**Purpose:** Define which dashboards each user role should access

---

## Role Definitions

- **Admin:** Superuser, full system access
- **Staff:** Employee with staff privileges (is_staff=True)
- **Employee/Applicant:** Regular employee (category=1)
- **Investor:** Investor user (category=4)
- **Student:** Student user (category=2)
- **Consultant:** Consultant user (category=3)
- **Explorer:** Visitor/researcher (category=5)

---

## PRIMARY DASHBOARDS (Entry Points)

| Role | Primary Dashboard | URL | Purpose |
|------|------------------|-----|---------|
| **All Users** | Unified Dashboard | `/dashboard/` | Main entry point, role-based customization |
| **Admin** | Unified Dashboard (Admin View) | `/dashboard/` | System overview, all features |
| **Staff/Employee** | Unified Dashboard (Employee View) | `/dashboard/` | Employee services, tasks |
| **Investor** | Unified Dashboard (Investor View) | `/dashboard/` | Investment portfolio |
| **Student** | Unified Dashboard (Student View) | `/dashboard/` | Training, learning |
| **Consultant** | Unified Dashboard (Consultant View) | `/dashboard/` | Interview management |

---

## MANAGEMENT APP DASHBOARDS

| Dashboard | Admin | Staff | Employee | Investor | Student | Consultant |
|-----------|-------|------|----------|----------|---------|------------|
| **Task Dashboard** (Enhanced) | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Analytics Dashboard** | ✅ | ✅ | ✅* | ❌ | ❌ | ❌ |
| - Activity Forecast | ✅ | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| - Trend Analysis | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| - Compliance | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| - Anomaly Detection | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Meeting Link Review** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Task History** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Task Leaderboard** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Tier Analytics** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |

**Legend:**
- ✅ = Full Access
- ✅* = Limited Access (own data only)
- ⚠️ = Optional/On Request
- ❌ = No Access

---

## FINANCE APP DASHBOARDS

| Dashboard | Admin | Staff | Employee | Investor | Student | Consultant |
|-----------|-------|------|----------|----------|---------|------------|
| **Budget Dashboard** (Unified) | ✅ | ✅* | ❌ | ❌ | ❌ | ❌ |
| **Finance Dashboard** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Smart Collateral** | ✅ | ✅* | ❌ | ❌ | ❌ | ❌ |
| **Salary Dashboard** | ✅ | ✅* | ❌ | ❌ | ❌ | ❌ |
| **Loan Budget Dashboard** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Realtime Compliance** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Budget Approval** | ✅ | ✅* | ❌ | ❌ | ❌ | ❌ |
| **Tier Management** | ✅ | ✅* | ❌ | ❌ | ❌ | ❌ |
| **Payment Dashboard** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Admin Controls** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Automation Dashboard** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Budget Requests** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Audit Logs** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Approval Policies** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Disbursements** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Department Dashboard** | ✅ | ✅* | ❌ | ❌ | ❌ | ❌ |

**Notes:**
- ✅* = Department-specific or role-limited access
- Payment Dashboard = All users can view their own payments

---

## INVESTING APP DASHBOARDS

| Dashboard | Admin | Staff | Employee | Investor | Student | Consultant |
|-----------|-------|------|----------|----------|---------|------------|
| **Investment Dashboard** | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Monitor Dashboard** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Preset Analytics** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Risk Management** | ✅ | ✅ | ❌ | ✅* | ❌ | ❌ |
| **Client Portal** | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |

**Notes:**
- ✅* = Investors can view their own risk assessments

---

## AI SERVICES APP DASHBOARDS

| Dashboard | Admin | Staff | Employee | Investor | Student | Consultant |
|-----------|-------|------|----------|----------|---------|------------|
| **Diaspora Dashboard** | ✅ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| **AI Configuration** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Advanced Analytics** | ✅ | ⚠️ | ❌ | ❌ | ❌ | ❌ |

**Notes:**
- ⚠️ = Staff may have limited access based on permissions

---

## RECOMMENDED ACCESS RULES

### 1. Default Access (No Special Permissions)
- **All Users:** Unified Dashboard, Payment Dashboard (own data)
- **Staff/Employees:** Task Dashboard, Task History, Task Leaderboard, Tier Analytics
- **Investors:** Investment Dashboard, Client Portal

### 2. Manager-Level Access (Department/Team Managers)
- Budget Dashboard (department view)
- Compliance Dashboards
- Team Analytics
- Department Dashboard

### 3. Admin-Only Access
- Admin Controls Dashboard
- Automation Dashboard
- Audit Logs Dashboard
- Approval Policies Dashboard
- AI Configuration Dashboard
- System-level analytics

### 4. Finance-Specific Access
- Finance staff: All Finance dashboards
- Department heads: Budget Dashboard (department view)
- Regular employees: Budget Requests (create/view own)

### 5. Investment-Specific Access
- Investment staff: All Investing dashboards
- Investors: Investment Dashboard, Client Portal, Risk Management (own)

---

## IMPLEMENTATION RECOMMENDATIONS

### 1. Create Permission Decorators
```python
@require_finance_staff
@require_manager
@require_admin
@require_investor
```

### 2. Add Permission Checks to Views
- Check user role
- Check department membership
- Check specific permissions

### 3. Update Navigation
- Show only accessible dashboards in navigation
- Hide unauthorized dashboards
- Provide clear error messages for unauthorized access

### 4. Dashboard Grouping
- Group dashboards by app/functionality
- Show primary dashboard prominently
- Show secondary dashboards in submenus

---

**Last Updated:** November 6, 2025  
**Status:** ✅ Ready for Implementation

