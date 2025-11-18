# Dashboard Inventory and Analysis

**Date:** November 6, 2025  
**Purpose:** Comprehensive inventory of all dashboards across the CODA system with recommendations for consolidation and role-based access.

---

## Executive Summary

The CODA system currently has **60+ dashboard templates** and **multiple dashboard views** across different apps. This analysis identifies all dashboards, their intended audiences, and provides recommendations for consolidation.

---

## 1. MAIN/UNIFIED DASHBOARDS

### 1.1 Unified Dashboard (Primary Entry Point)
**URL:** `/dashboard/`  
**View:** `unified_dashboard.views.unified_dashboard`  
**Template:** `unified_dashboard/dashboard.html`  
**Status:** ✅ **ACTIVE - PRIMARY**

**Who Should See:**
- **All authenticated users** (role-based customization)
- Admin users → Administrator Dashboard
- Investor users → Investor Dashboard
- Applicant/Employee users → Employee Dashboard
- Student users → Student Dashboard
- Consultant users → Consultant Dashboard
- Explorer users → Explorer Dashboard

**Features:**
- Role-based quick actions
- Role-based sections/widgets
- "My Account Services" section
- Theme switching (Navy & Gold / Purple)

**Recommendation:** ✅ **KEEP AS PRIMARY** - This is the main entry point and should remain.

---

## 2. MANAGEMENT APP DASHBOARDS

### 2.1 Enhanced Task Dashboard
**URL:** `/management/enhanced-dashboard/`  
**View:** `management.views_enhanced_dashboard.enhanced_task_dashboard`  
**Template:** `management/enhanced_task_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **All staff/employees** (is_staff=True)
- Employees tracking their tasks and performance
- Users who need tier tracking and monthly stats

**Features:**
- User tier status and progress
- Monthly statistics
- Recent tasks
- Phase 3 Analytics navigation section
- Quick actions (refresh, export, etc.)

**Recommendation:** ✅ **KEEP** - Rename to "Task Dashboard" or "My Tasks Dashboard" (remove "Enhanced")

---

### 2.2 Analytics Dashboard (Phase 3)
**URL:** `/management/analytics/`  
**View:** `management.views.analytics_dashboard_views.analytics_dashboard`  
**Template:** `management/analytics/analytics_dashboard.html`  
**Status:** ✅ **ACTIVE - NEW**

**Who Should See:**
- **All staff/employees** (is_staff=True)
- Managers and admins for team analytics
- Users who need forecasting, trends, compliance monitoring

**Features:**
- Activity Forecast Dashboard
- Trend Analysis Dashboard
- Compliance Dashboard
- Anomaly Detection Dashboard

**Recommendation:** ✅ **KEEP** - This is Phase 3 feature, well-organized

---

### 2.3 Activity Forecast Dashboard
**URL:** `/management/analytics/forecast/activity/`  
**View:** `management.views.analytics_dashboard_views.activity_forecast_dashboard`  
**Template:** `management/analytics/activity_forecast_dashboard.html`  
**Status:** ✅ **ACTIVE - NEW**

**Who Should See:**
- **Managers and admins** (forecasting needs)
- Optional for regular employees

**Recommendation:** ✅ **KEEP** - Part of Phase 3 analytics suite

---

### 2.4 Trend Analysis Dashboard
**URL:** `/management/analytics/trends/`  
**View:** `management.views.analytics_dashboard_views.trend_analysis_dashboard`  
**Template:** `management/analytics/trend_analysis_dashboard.html`  
**Status:** ✅ **ACTIVE - NEW**

**Who Should See:**
- **All staff/employees** (for personal trends)
- **Managers and admins** (for team/department trends)

**Recommendation:** ✅ **KEEP** - Part of Phase 3 analytics suite

---

### 2.5 Compliance Dashboard
**URL:** `/management/analytics/compliance/`  
**View:** `management.views.analytics_dashboard_views.compliance_dashboard`  
**Template:** `management/analytics/compliance_dashboard.html`  
**Status:** ✅ **ACTIVE - NEW**

**Who Should See:**
- **Managers and admins** (compliance monitoring)
- HR staff
- Finance staff (for payroll approval)

**Recommendation:** ✅ **KEEP** - Part of Phase 3 analytics suite

---

### 2.6 Anomaly Detection Dashboard
**URL:** `/management/analytics/anomalies/`  
**View:** `management.views.analytics_dashboard_views.anomaly_detection_dashboard`  
**Template:** `management/analytics/anomaly_detection_dashboard.html`  
**Status:** ✅ **ACTIVE - NEW**

**Who Should See:**
- **Managers and admins** (anomaly monitoring)
- System administrators

**Recommendation:** ✅ **KEEP** - Part of Phase 3 analytics suite

---

### 2.7 Performance Insights Dashboard (Commented Out)
**URL:** `/management/insights/performance-dashboard/` (commented)  
**View:** `management.views.insights_views.PerformanceInsightsDashboard`  
**Template:** `management/insights/performance_dashboard.html`  
**Status:** ⚠️ **COMMENTED OUT**

**Who Should See:**
- Managers and admins

**Recommendation:** ⚠️ **REVIEW** - Similar to Trend Analysis Dashboard, consider consolidating

---

### 2.8 Meeting Link Review Dashboard
**URL:** `/management/meeting-links/review/`  
**View:** `management.views.meeting_review_views.meeting_link_review_dashboard`  
**Template:** `management/daf/meeting_link_review.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Managers and admins** (for reviewing AI-suggested meeting links)
- Users who need to approve/reject meeting-to-task links

**Recommendation:** ✅ **KEEP** - Specialized workflow dashboard

---

### 2.9 Task History Dashboard
**URL:** `/management/task-history/`  
**View:** `management.views_enhanced_dashboard.task_history_view`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **All staff/employees** (viewing their task history)

**Recommendation:** ✅ **KEEP** - Could be integrated into Enhanced Task Dashboard as a tab

---

### 2.10 Task Leaderboard
**URL:** `/management/leaderboard/`  
**View:** `management.views_enhanced_dashboard.task_leaderboard`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **All staff/employees** (gamification/competition)

**Recommendation:** ✅ **KEEP** - Could be integrated into Enhanced Task Dashboard as a tab

---

### 2.11 Tier Analytics Dashboard
**URL:** `/management/tier-analytics/`  
**View:** `management.views_enhanced_dashboard.tier_analytics`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **All staff/employees** (tier progression analytics)

**Recommendation:** ✅ **KEEP** - Could be integrated into Enhanced Task Dashboard as a tab

---

## 3. FINANCE APP DASHBOARDS

### 3.1 Unified Budget Dashboard (Primary)
**URL:** `/finance/budget-dashboard/<company_slug>/`  
**View:** `finance.views.budget.dashboard.unified_budget_dashboard`  
**Template:** `finance/budgets/unified_dashboard.html`  
**Status:** ✅ **ACTIVE - PRIMARY**

**Who Should See:**
- **Finance managers and admins**
- Department heads (for their department budgets)
- CFO/Finance leadership

**Features:**
- Overview tab
- Planning tab
- Analytics tab
- Approvals tab
- Consolidates multiple budget views

**Recommendation:** ✅ **KEEP AS PRIMARY** - This consolidates many budget dashboards

---

### 3.2 Finance Dashboard (Legacy)
**URL:** `/finance/finance-dashboard/<company_slug>/`  
**View:** `finance.views.core.views_finance_dashboard.finance_dashboard`  
**Template:** `finance/finance_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- Finance staff
- Admins

**Recommendation:** ⚠️ **CONSIDER DEPRECATING** - Check if functionality is in Unified Budget Dashboard

---

### 3.3 Enhanced Legacy Dashboard
**URL:** `/finance/legacy-dashboard/<company_slug>/`  
**View:** `finance.views.legacy.views_legacy_dashboard.enhanced_legacy_dashboard`  
**Template:** `finance/enhanced_legacy_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- Finance staff (legacy workflows)

**Recommendation:** ⚠️ **REVIEW** - "Enhanced Legacy" is confusing. Consider renaming or deprecating if Unified Budget Dashboard covers it

---

### 3.4 Smart Collateral Dashboard
**URL:** `/finance/admin/smart-collateral-dashboard/`  
**View:** `finance.views.smart_collateral_dashboard`  
**Template:** `finance/smart_collateral_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Finance admins** (collateral management)
- Loan officers

**Recommendation:** ✅ **KEEP** - Specialized functionality

---

### 3.5 Salary Dashboard
**URL:** `/finance/salary/dashboard/`  
**View:** `finance.views.budget.views_salary_dashboard.salary_dashboard`  
**Template:** `finance/salary/salary_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **HR and Finance staff** (salary management)
- Admins

**Recommendation:** ✅ **KEEP** - Specialized functionality

---

### 3.6 Loan Budget Dashboard
**URL:** `/finance/loan/<company_slug>/dashboard/`  
**View:** `finance.views.loan.budget_integration.loan_budget_dashboard`  
**Template:** `finance/loans/loan_budget_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Finance staff** (loan-budget integration)
- Loan officers

**Recommendation:** ✅ **KEEP** - Specialized functionality

---

### 3.7 Realtime Compliance Dashboard
**URL:** `/finance/realtime/compliance-dashboard/`  
**View:** `finance.views.realtime_compliance.realtime_compliance_dashboard`  
**Template:** `finance/realtime/realtime_compliance_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Finance and HR staff** (compliance monitoring)
- Admins

**Recommendation:** ⚠️ **CONSIDER CONSOLIDATING** - Similar to Management Compliance Dashboard. Could be unified.

---

### 3.8 Budget Approval Dashboard
**URL:** `/finance/budget/<company_slug>/approvals/`  
**View:** `finance.views.budget.approvals.budget_approval_dashboard`  
**Template:** `finance/budgets/approval_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Finance managers** (budget approval workflow)
- Approvers

**Recommendation:** ✅ **KEEP** - Part of Unified Budget Dashboard (Approvals tab)

---

### 3.9 Tier Management Dashboard
**URL:** `/finance/tier-management/<company_slug>/`  
**View:** `finance.views.budget.views_tier_management.tier_management_dashboard`  
**Template:** `finance/budgets/tier_management_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Finance managers** (tier configuration)
- Admins

**Recommendation:** ✅ **KEEP** - Specialized configuration dashboard

---

### 3.10 Payment Dashboard
**URL:** `/finance/my-payments/`  
**View:** `finance.views.payment.dashboard_views.payment_dashboard`  
**Template:** `finance/payments/payment_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **All users** (viewing their payment history)
- Employees checking salary/payment status

**Recommendation:** ✅ **KEEP** - User-facing payment dashboard

---

### 3.11 Admin Controls Dashboard
**URL:** `/finance/admin/controls-dashboard/`  
**View:** `finance.views.admin_controls.admin_controls_dashboard`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Finance admins** (system controls)

**Recommendation:** ✅ **KEEP** - Admin-only functionality

---

### 3.12 Automation Dashboard
**URL:** `/finance/automation/`  
**View:** `finance.views.automation.automation_dashboard`  
**Template:** `finance/automation_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Finance admins** (automation configuration)

**Recommendation:** ✅ **KEEP** - Specialized configuration dashboard

---

### 3.13 Budget Requests Dashboard
**URL:** `/finance/budget-requests/`  
**View:** `finance.views.forms.budget_requests_list`  
**Template:** `finance/budget_requests_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Finance staff** (managing budget requests)
- Request approvers

**Recommendation:** ✅ **KEEP** - Workflow dashboard

---

### 3.14 Audit Logs Dashboard
**URL:** `/finance/automation/audit-logs/`  
**View:** `finance.views.automation.audit_logs_dashboard`  
**Template:** `finance/audit_logs_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Finance admins** (audit trail)

**Recommendation:** ✅ **KEEP** - Audit functionality

---

### 3.15 Approval Policies Dashboard
**URL:** `/finance/automation/policies/`  
**View:** `finance.views.automation.approval_policies_dashboard`  
**Template:** `finance/approval_policies_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Finance admins** (policy configuration)

**Recommendation:** ✅ **KEEP** - Configuration dashboard

---

### 3.16 Disbursements Dashboard
**URL:** `/finance/disbursements/`  
**View:** `finance.views.disbursements.disbursements_dashboard`  
**Template:** `finance/disbursements_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Finance staff** (disbursement management)

**Recommendation:** ✅ **KEEP** - Specialized workflow

---

### 3.17 Unified Department Dashboard
**URL:** `/finance/department/<department_name>/`  
**View:** `finance.views.legacy.views_unified_department.unified_department_dashboard`  
**Template:** `finance/unified_department_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Department heads** (department-specific finance view)
- Finance staff

**Recommendation:** ✅ **KEEP** - Department-specific view

---

### 3.18 Analytics Dashboard (Finance)
**URL:** `/finance/analytics/` (redirects to Unified Budget Dashboard)  
**Status:** ⚠️ **REDIRECT**

**Recommendation:** ✅ **KEEP AS REDIRECT** - Good consolidation

---

## 4. INVESTING APP DASHBOARDS

### 4.1 Investment Dashboard (Main)
**URL:** `/investing/dashboard/`  
**View:** `investing.views.investment_dashboard`  
**Template:** `investing/investment_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Investors** (client portal)
- Investment staff

**Recommendation:** ✅ **KEEP** - Primary investment dashboard

---

### 4.2 Monitor Dashboard (Managed Trading)
**URL:** `/investing/managed/monitor/`  
**View:** `investing.views.managed_trading.monitoring.monitor_dashboard`  
**Template:** `investing/managed/monitor_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Investment staff** (position monitoring)
- Portfolio managers

**Recommendation:** ✅ **KEEP** - Real-time monitoring

---

### 4.3 Preset Analytics Dashboard
**URL:** `/investing/managed/staff/analytics/presets/`  
**View:** `investing.views.managed_trading.preset_analytics.preset_analytics_dashboard`  
**Template:** `investing/staff/preset_analytics_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Investment staff** (preset analytics)
- Portfolio managers

**Recommendation:** ✅ **KEEP** - Specialized analytics

---

### 4.4 Risk Management Dashboard
**URL:** `/investing/risk-management/`  
**Template:** `investing/risk_management_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Investment staff** (risk assessment)
- Portfolio managers

**Recommendation:** ✅ **KEEP** - Risk management functionality

---

### 4.5 Client Portal Dashboard
**URL:** `/investing/managed/portal/`  
**View:** `investing.views.managed_trading.client.client_portal`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Investors/clients** (their account view)

**Recommendation:** ✅ **KEEP** - Client-facing dashboard

---

## 5. AI SERVICES APP DASHBOARDS

### 5.1 Diaspora Dashboard
**URL:** `/ai_services/diaspora/`  
**View:** `ai_services.views.diaspora_dashboard`  
**Template:** `ai_services/diaspora_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Admins** (AI services overview)
- AI service users

**Recommendation:** ✅ **KEEP** - AI services hub

---

### 5.2 AI Configuration Dashboard
**URL:** `/ai_services/diaspora/ai-configuration/`  
**Template:** `ai_services/ai_configuration_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Admins** (AI configuration)

**Recommendation:** ✅ **KEEP** - Configuration dashboard

---

### 5.3 Advanced Analytics Dashboard
**URL:** `/ai_services/diaspora/advanced-analytics/`  
**Template:** `ai_services/advanced_analytics_dashboard.html`  
**Status:** ✅ **ACTIVE**

**Who Should See:**
- **Admins** (system analytics)

**Recommendation:** ✅ **KEEP** - System-level analytics

---

## 6. PORTFOLIO APP DASHBOARDS

### 6.1 Presentation Dashboards (Multiple)
**Templates:**
- `portfolio/legacy-ai-diaspora/presentation_dashboard.html`
- `portfolio/legacy-ai-diaspora/investor_presentation_dashboard.html`
- `portfolio/legacy-ai-diaspora/hybrid_presentation_dashboard.html`
- `portfolio/legacy-ai-diaspora/banking_presentation_dashboard.html`
- `portfolio/legacy-ai-diaspora/analytics_dashboard.html`
- `portfolio/legacy-ai-diaspora/ai_configuration_dashboard.html`
- `portfolio/legacy-ai-diaspora/advanced_analytics_dashboard.html`

**Status:** ⚠️ **LEGACY - IN PORTFOLIO APP**

**Who Should See:**
- Presentation audiences
- Investors
- Banking clients

**Recommendation:** ⚠️ **REVIEW** - These appear to be legacy/duplicate of AI Services dashboards. Consider consolidating or removing if unused.

---

## 7. TESTING/DEVELOPMENT DASHBOARDS

### 7.1 Button Testing Dashboard
**URL:** `/management/button-testing/`  
**Template:** `management/button_testing_dashboard.html`  
**Status:** ⚠️ **TESTING**

**Recommendation:** ⚠️ **REMOVE OR RESTRICT** - Should only be accessible in development

---

### 7.2 AI Test Dashboard
**URL:** `/management/ai-test-dashboard/` (commented)  
**Template:** `management/ai_test_dashboard.html`  
**Status:** ⚠️ **COMMENTED OUT**

**Recommendation:** ⚠️ **REMOVE** - Testing dashboard, should not be in production

---

## SUMMARY STATISTICS

### By App:
- **Unified Dashboard:** 1 main dashboard (role-based)
- **Management:** 11 dashboards (including Phase 3 analytics)
- **Finance:** 18+ dashboards
- **Investing:** 5 dashboards
- **AI Services:** 3+ dashboards
- **Portfolio:** 7+ legacy dashboards
- **Testing:** 2 testing dashboards

### Total: **47+ Active Dashboards**

---

## RECOMMENDATIONS

### High Priority Consolidations:

1. **Management App:**
   - ✅ Keep Enhanced Task Dashboard (rename to "Task Dashboard")
   - ✅ Keep Analytics Dashboard suite (Phase 3)
   - ⚠️ Consider integrating Task History, Leaderboard, Tier Analytics as tabs in Task Dashboard

2. **Finance App:**
   - ✅ Keep Unified Budget Dashboard as primary
   - ⚠️ Review "Enhanced Legacy Dashboard" - rename or deprecate
   - ⚠️ Consider consolidating Realtime Compliance Dashboard with Management Compliance Dashboard

3. **Portfolio App:**
   - ⚠️ Review legacy dashboards - remove if unused or consolidate with AI Services

4. **Testing Dashboards:**
   - ⚠️ Remove or restrict access to testing dashboards

### Naming Convention Recommendations:

1. **Remove "Enhanced" prefix** - Too many "enhanced" dashboards
2. **Use clear, descriptive names:**
   - "Task Dashboard" instead of "Enhanced Task Dashboard"
   - "Budget Dashboard" instead of "Unified Budget Dashboard" (it's already the primary)
   - "Legacy Dashboard" instead of "Enhanced Legacy Dashboard"

3. **Group by functionality:**
   - Task Management → Task Dashboard
   - Budget Management → Budget Dashboard
   - Analytics → Analytics Dashboard
   - Compliance → Compliance Dashboard

### Role-Based Access Recommendations:

1. **Create a dashboard access matrix** showing:
   - Which dashboards each role can access
   - Primary dashboard for each role
   - Secondary/specialized dashboards

2. **Implement dashboard permissions** to prevent unauthorized access

---

## NEXT STEPS

1. ✅ **Complete this inventory** (DONE)
2. ⏳ **Create role-based access matrix**
3. ⏳ **Implement dashboard permissions**
4. ⏳ **Rename dashboards** (remove "Enhanced" where appropriate)
5. ⏳ **Consolidate duplicate functionality**
6. ⏳ **Remove testing dashboards** from production
7. ⏳ **Update navigation** to reflect consolidated structure

---

**Last Updated:** November 6, 2025  
**Status:** ✅ Inventory Complete - Ready for Review

