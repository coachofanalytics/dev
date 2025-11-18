# Navigation Guide: Main Dashboard to Phase 3 Analytics

## Main Dashboard (`/dashboard`)

The main unified dashboard is the entry point for all users. From here, users can navigate to various features based on their role.

### For Employees (Applicant Role)

From the main dashboard at `/dashboard`, employees will see these **Quick Action** buttons:

1. **Company Agenda** → `/management/companyagenda/`
   - View company-wide agenda items

2. **My Tasks** → `/management/userdashboard/`
   - View and manage personal tasks

3. **Enhanced Dashboard** → `/management/enhanced-dashboard/` ⭐ **NEW**
   - Enhanced task dashboard with tier tracking, monthly stats, and analytics navigation

4. **Advanced Analytics** → `/management/analytics/` ⭐ **NEW**
   - Main analytics hub with links to all Phase 3 features

5. **HR Services** → `/hr/`
   - Access HR services and policies

6. **Help Center** → `/help/`
   - Get help and support

---

## Navigation Flow

### Path 1: Main Dashboard → Enhanced Dashboard → Analytics

```
/dashboard
  ↓ (Click "Enhanced Dashboard")
/management/enhanced-dashboard/
  ↓ (Click any analytics button in "Phase 3: Advanced Analytics" section)
/management/analytics/...
```

**Enhanced Dashboard Features:**
- User tier status and progress
- Monthly statistics
- Recent tasks
- **Phase 3 Analytics Navigation Section** with 8 buttons:
  - 📈 Activity Forecast
  - 💰 Budget Forecast
  - 📊 Historical Trends
  - 👤 My Performance Trends
  - 📋 Real-time Compliance KPIs
  - 📜 Compliance History
  - 🔍 Detect Anomalies
  - 🎯 All Analytics Dashboard

### Path 2: Main Dashboard → Advanced Analytics (Direct)

```
/dashboard
  ↓ (Click "Advanced Analytics")
/management/analytics/
  ↓ (Main analytics hub with links to all features)
```

**Main Analytics Dashboard (`/management/analytics/`) Features:**
- Quick overview of all analytics
- Navigation buttons to:
  - Activity Forecast Dashboard
  - Trend Analysis Dashboard
  - Compliance Dashboard
  - Anomaly Detection Dashboard

---

## Phase 3 Analytics Dashboards

### 1. Activity Forecast Dashboard
**URL:** `/management/analytics/forecast/activity/`

**Features:**
- Forecast activity trends for next 3+ months
- Historical data comparison
- Confidence scoring
- Trend direction analysis

**Navigation:**
- From Enhanced Dashboard: Click "📈 Activity Forecast"
- From Analytics Hub: Click "📈 Activity Forecast"

### 2. Trend Analysis Dashboard
**URL:** `/management/analytics/trends/`

**Features:**
- Historical trend analysis (12+ months)
- Monthly trends breakdown
- Category and department trends
- Seasonal pattern detection
- Overall trend direction and strength

**Navigation:**
- From Enhanced Dashboard: Click "📊 Historical Trends" or "👤 My Performance Trends"
- From Analytics Hub: Click "📉 Trend Analysis"

### 3. Compliance Dashboard
**URL:** `/management/analytics/compliance/`

**Features:**
- Real-time compliance KPIs
- Overall compliance rate
- Employee compliance breakdown
- Department-level compliance
- Compliance history and trends
- Automated alerts

**Navigation:**
- From Enhanced Dashboard: Click "📋 Real-time Compliance KPIs" or "📜 Compliance History"
- From Analytics Hub: Click "✅ Compliance Monitoring"

### 4. Anomaly Detection Dashboard
**URL:** `/management/analytics/anomalies/`

**Features:**
- Automated anomaly detection
- Activity volume anomalies
- Performance anomalies
- Compliance anomalies
- Evidence coverage anomalies
- Severity classification (Critical, High, Medium, Low)

**Navigation:**
- From Enhanced Dashboard: Click "🔍 Detect Anomalies"
- From Analytics Hub: Click "⚠️ Anomaly Detection"

---

## Quick Reference: All Navigation Paths

### From Main Dashboard (`/dashboard`)
1. **Enhanced Dashboard** → `/management/enhanced-dashboard/`
2. **Advanced Analytics** → `/management/analytics/`

### From Enhanced Dashboard (`/management/enhanced-dashboard/`)
1. **Activity Forecast** → `/management/analytics/forecast/activity/`
2. **Budget Forecast** → `/management/api/forecast/budget/` (API endpoint)
3. **Historical Trends** → `/management/analytics/trends/`
4. **My Performance Trends** → `/management/analytics/trends/?employee_id={user_id}`
5. **Real-time Compliance KPIs** → `/management/analytics/compliance/`
6. **Compliance History** → `/management/analytics/compliance/?months_back=12`
7. **Detect Anomalies** → `/management/analytics/anomalies/`
8. **All Analytics Dashboard** → `/management/analytics/`

### From Analytics Hub (`/management/analytics/`)
1. **Activity Forecast** → `/management/analytics/forecast/activity/`
2. **Trend Analysis** → `/management/analytics/trends/`
3. **Compliance Monitoring** → `/management/analytics/compliance/`
4. **Anomaly Detection** → `/management/analytics/anomalies/`
5. **Back to Enhanced Dashboard** → `/management/enhanced-dashboard/`

---

## User Experience Flow

### Typical User Journey

1. **Login** → Redirected to `/dashboard`
2. **Main Dashboard** → See overview and quick actions
3. **Click "Enhanced Dashboard"** → See personal stats and analytics buttons
4. **Click Analytics Button** → Navigate to specific analytics feature
5. **View Analytics** → See data, charts, and insights
6. **Navigate Back** → Use "Back to Analytics" or "Back to Dashboard" buttons

### Alternative Journey

1. **Login** → Redirected to `/dashboard`
2. **Main Dashboard** → Click "Advanced Analytics"
3. **Analytics Hub** → See overview and choose specific analytics
4. **View Analytics** → Navigate to specific feature
5. **Navigate Back** → Return to hub or dashboard

---

## Button Locations Summary

### Main Dashboard (`/dashboard`)
- ✅ **Enhanced Dashboard** button (Quick Actions)
- ✅ **Advanced Analytics** button (Quick Actions)

### Enhanced Dashboard (`/management/enhanced-dashboard/`)
- ✅ **Phase 3: Advanced Analytics** section with 8 navigation buttons
- ✅ Organized by category (Forecasting, Trends, Compliance, Anomalies)

### Analytics Hub (`/management/analytics/`)
- ✅ Navigation buttons to all analytics features
- ✅ Quick overview cards
- ✅ Back navigation to Enhanced Dashboard

---

## Notes

- All analytics dashboards have consistent navigation:
  - "Back to Analytics" button to return to hub
  - "Back to Dashboard" button to return to main dashboard
- All buttons are color-coded by category for easy identification
- Responsive design works on mobile and desktop
- All analytics features require user authentication

---

**Last Updated:** November 6, 2025  
**Phase 3 Status:** ✅ Complete

