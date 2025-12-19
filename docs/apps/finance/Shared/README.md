# Shared Finance Documentation

This directory contains documentation for features and functionality that span multiple finance subsystems.

## Contents

### [THEME_SWITCHER.md](THEME_SWITCHER.md)
Theme customization feature for dashboards (Navy/Gold, Purple themes). Implemented using CSS variables and localStorage persistence.

**Applies To:**
- Unified Dashboard (`/dashboard/`)
- Budget Approval Dashboard (inherits styling)
- Future: All finance dashboards

### [DepartmentDashboard/](DepartmentDashboard/)
Enhanced department dashboard with modern card-based UI design (October 14, 2025).

**Contains:**
- DEPARTMENT_DASHBOARD_ENHANCEMENT.md - Full feature documentation
- DEPARTMENT_DASHBOARD_QUICK_START.md - 5-minute implementation guide
- DEPARTMENT_DASHBOARD_TOPIC_CARDS_UPDATE.md - Topic cards feature details
- DEPARTMENT_DASHBOARD_VISUAL_COMPARISON.md - Before/after comparison

**Features:** Card-based layout, edit buttons, animated stats, search interface, 3D hover effects

**Applies To:**
- Department Dashboards (`/finance/department/[company]/`)
- Template: `unified_department_dashboard_enhanced.html`

### API_REFERENCE.md (Planned)
Comprehensive API documentation for all finance endpoints:
- Cascading dropdown APIs
- AI prediction APIs
- Budget approval APIs
- Transaction analytics APIs

### DATA_ANALYSIS_FRAMEWORK.md (Planned)
Common data analysis approaches used across finance features:
- Spending pattern analysis
- Tier classification methodology
- Anomaly detection algorithms
- Forecasting techniques

---

**Last Updated:** October 13, 2025

