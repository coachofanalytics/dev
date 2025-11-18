# Finance Integration Guide

**Phase 2: Budget Integration**  
**Date:** November 6, 2025

---

## Overview

This guide explains how Finance app consumes Management Budget Integration APIs for budget estimation and validation.

---

## Integration Architecture

### Two Integration Methods

1. **Direct Service Calls** (Same Django Project)
   - Uses Django's RequestFactory to call Management views directly
   - No HTTP overhead
   - Faster and more efficient
   - Default method

2. **HTTP API Calls** (Separate Services)
   - Uses HTTP requests to call Management APIs
   - Works when services are deployed separately
   - Requires `requests` library
   - Fallback method

---

## Finance Services

### ManagementIntegrationService

**Location:** `coda/finance/services/management_integration_service.py`

**Purpose:** Provides clean interface for Finance to consume Management APIs

**Methods:**
- `get_activity_totals()` - Get validated activity totals
- `get_evidence_validation()` - Get evidence validation data
- `get_validated_budget_data()` - Get combined activity + evidence data

**Usage Example:**
```python
from finance.services.management_integration_service import ManagementIntegrationService

# Initialize service
management_api = ManagementIntegrationService()

# Get activity totals (uses direct call by default)
result = management_api.get_activity_totals(
    month=10,
    year=2025,
    department_id=1,
    include_evidence=True,
    include_validation=True
)

if result['success']:
    activity_data = result['data']
    totals = activity_data['totals']
    print(f"Total earnings: {totals['total_earnings']}")
```

### IntegratedBudgetService (Updated)

**Location:** `coda/finance/services/integrated_budget_service.py`

**Changes:**
- Now supports `use_api=True` parameter
- When enabled, uses Management APIs instead of direct DB queries
- Falls back to direct queries if API fails

**Usage Example:**
```python
from finance.services.integrated_budget_service import IntegratedBudgetService

# Use API-based approach
budget_service = IntegratedBudgetService(use_api=True)
summary = budget_service.get_monthly_budget_summary(
    target_month=10,
    target_year=2025,
    department=department
)
```

---

## Finance Views Integration

### Unified Budget Dashboard (Enhanced)

**Endpoint:** `/finance/budget-dashboard/<company_slug>/?tab=overview`

**Purpose:** Existing unified budget dashboard now includes Management activity data

**Integration:**
- Management activity data is automatically fetched and included in the Overview tab
- No new views or templates created - reuses existing infrastructure
- Activity data available in `overview_data.management_activity_data`
- Evidence validation available in `overview_data.management_evidence_data`

**Query Parameters:**
- `tab`: Active tab (default: `overview`)
- `department_id`: Optional department filter

**Example:**
```
/finance/budget-dashboard/coda/?tab=overview&department_id=1
```

**Note:** The integration follows the reusability principle - no duplicate views or templates were created. Management data is seamlessly integrated into existing Finance budget views.

---

## Integration Flow

### Step 1: Finance Service Calls Management API

```python
# In Finance service
management_api = ManagementIntegrationService()
activity_result = management_api.get_activity_totals(
    month=10,
    year=2025,
    department_id=1
)
```

### Step 2: Management API Returns Validated Data

```json
{
  "data": {
    "period": "10/2025",
    "totals": {
      "total_earnings": 5000.0,
      "completion_rate": 0.75,
      ...
    },
    "validation_status": {
      "is_validated": true,
      "compliance_rate": 80.0,
      ...
    }
  }
}
```

### Step 3: Finance Uses Data for Budget Estimation

```python
# Finance uses activity totals for budget calculations
total_earnings = activity_result['data']['totals']['total_earnings']
is_validated = activity_result['data']['validation_status']['is_validated']

if is_validated:
    # Include in budget estimation
    budget_amount += total_earnings
```

---

## Benefits

1. **Separation of Concerns:** Finance doesn't need to know Management's internal structure
2. **API Contract:** Stable interface between apps
3. **Validation:** Management validates data before Finance consumes it
4. **Evidence Tracking:** Finance can verify evidence completeness
5. **Flexibility:** Supports both direct calls and HTTP APIs

---

## Testing

### Test Direct Service Calls

```python
from finance.services.management_integration_service import ManagementIntegrationService

service = ManagementIntegrationService()
result = service.get_activity_totals(
    month=10,
    year=2025,
    use_direct_call=True
)

assert result['success'] == True
assert 'data' in result
```

### Test HTTP API Calls

```python
service = ManagementIntegrationService()
result = service.get_activity_totals(
    month=10,
    year=2025,
    use_direct_call=False  # Use HTTP API
)

assert result['success'] == True
assert result['source'] == 'http_api'
```

---

## Error Handling

The integration service handles errors gracefully:

1. **Direct Call Fails:** Falls back to HTTP API
2. **HTTP API Fails:** Returns error response with details
3. **Both Fail:** Returns error response, Finance can use fallback logic

**Error Response Format:**
```json
{
  "success": false,
  "data": {},
  "meta": {},
  "errors": ["Error message here"]
}
```

---

## Configuration

### Enable API-Based Approach

In Finance views/services, set `use_api=True`:

```python
budget_service = IntegratedBudgetService(use_api=True)
```

### Use HTTP API Instead of Direct Calls

```python
management_api = ManagementIntegrationService()
result = management_api.get_activity_totals(
    use_direct_call=False  # Use HTTP API
)
```

---

## Next Steps

1. **Test Integration:** Verify Finance can consume Management APIs
2. **Update Budget Views:** Use integrated data in budget dashboards
3. **Add Validation:** Use evidence validation in budget approval workflow
4. **Monitor Performance:** Track API call performance and optimize

---

**Status:** ✅ **COMPLETE**  
**Ready for:** Testing and deployment

