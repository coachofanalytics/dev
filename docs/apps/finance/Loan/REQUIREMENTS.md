# Loan System - Requirements

## Business Goals

Provide accessible loan products to CODA members with automated eligibility checking and transparent terms.

## Functional Requirements

### REQ-001: Loan Product Catalog ✅
Products with:
- Name, description
- Interest rate
- Term (months)
- Min/max amounts
- Product type (Fixed, Variable, KCC)

### REQ-002: Loan Application ✅
Users can apply with:
- Requested amount
- Purpose
- Employment details
- Collateral (if applicable)

### REQ-003: Eligibility Checking ✅
Auto-check based on:
- Employment status
- Income level
- Existing loans
- Credit history (if available)

### REQ-004: KCC Integration ✅
Special loan products for KCC members:
- Lower interest rates
- Longer terms
- Higher limits

### REQ-005: Loan Analytics 📋
Admin dashboard showing:
- Applications by status
- Approval rates
- Default rates
- Revenue projections

## Business Rules

### Eligibility Criteria

#### 1. Staff Members (Category 2)
- **Who:** CODA employees (`user.category == 2` AND `user.is_staff == True`)
- **Eligibility:** ✅ ALWAYS ELIGIBLE (automatic)
- **Loan Limits:** $100 - $5,000
- **Products:** Staff Emergency Loan, Staff Development Loan
- **Requirements:** None (staff get automatic eligibility)

#### 2. KCC Members
- **Who:** Users with active Karen Country Club membership
- **Eligibility:** ✅ ELIGIBLE if membership active
- **Loan Limits:** $500 - $10,000
- **Products:** KCC Quick Cash (Tier 1, 2, 3)
- **Requirements:**
  - `profile.is_karen_country_club_member == True`
  - `kcc_membership_expiry >= today`

#### 3. External Users (Non-Staff, Non-KCC)
- **Who:** All other active users (Categories 1, 3, 4, 5)
- **Eligibility:** ✅ ELIGIBLE (very permissive)
- **Loan Limits:** $200 - $2,000
- **Products:** Personal, Emergency, Business Startup, Education loans
- **Requirements:** Active account

#### 4. Inactive Users
- **Eligibility:** ❌ NOT ELIGIBLE
- **Reason:** Account is inactive

### Loan Limits by User Type

| User Type | Min Amount | Max Amount | Interest Rate | Term |
|-----------|-----------|------------|---------------|------|
| Staff | $100 | $5,000 | 8-12% | 3-24 months |
| KCC Member | $500 | $10,000 | 10-15% | 6-36 months |
| External | $200 | $2,000 | 15-18% | 3-12 months |

### General Rules
- Collateral required for amounts >$5,000
- Guarantor required for amounts >$2,000
- Maximum 2 active loans per user
- Good standing required (no defaults)

**Source:** LOAN_ELIGIBILITY_ANALYSIS.md

---

## Guarantor & Collateral Requirements

### Staff Members (Category 2)
**Guarantor Requirements:**
- Must be current/active staff member (`is_staff=True`)
- Employment duration: **3+ months minimum**
- Active status required (`is_active=True`)
- Must be category 2 (staff)
- Superusers excluded from guarantor list

**Validation Flow:**
```
1. Is guarantor provided? → YES
2. Is guarantor category 2 (staff)? → YES
3. Is guarantor active staff? → YES
4. Has guarantor been employed 3+ months? → YES
5. ✅ VALID
```

### KCC Members
**Guarantor Requirements:**
- Must be KCC member with active membership
- Membership status: `is_karen_country_club_member=True`
- Membership not expired: `kcc_membership_expiry >= today`
- Non-staff categories (1, 3, 4, 5)

**Credit Score Tiers:**
- **Tier 1 (Basic):** Credit score 300-499
- **Tier 2 (Standard):** Credit score 500-699
- **Tier 3 (Premium):** Credit score 700+

**Validation Flow:**
```
1. Is guarantor provided? → YES
2. Is borrower KCC member with active membership? → YES
3. Is guarantor KCC member? → YES
4. Is guarantor's KCC membership active? → YES
5. ✅ VALID
```

### External Users (Non-Staff, Non-KCC)
**Requirements:**
- **Guarantor:** Always required (manual entry)
- **Collateral:** Always required (minimum 10 characters description)

**Validation Flow:**
```
1. Is guarantor provided? → YES
2. Is collateral provided (10+ chars)? → YES
3. ✅ VALID
```

**Source:** GUARANTOR_COLLATERAL_REQUIREMENTS.md

---

## Future: Smart Collateral System (Phase 5)

### Vision
Advanced collateral management using IoT, blockchain, and AI for maximum security.

**Components:**
1. **IoT Device Network**
   - GPS trackers (real-time location, geofencing)
   - Smart cameras (AI analysis, motion detection)
   - Environmental sensors (temperature, humidity, damage detection)
   - Smart locks (biometric, remote control)

2. **Blockchain Integration**
   - Smart contracts (Ethereum/Polygon)
   - Immutable collateral liens
   - Automated repossession triggers
   - Payment enforcement

3. **AI-Powered Risk Engine**
   - Behavior analysis (payment patterns)
   - Market prediction (price trends, volatility)
   - Collateral valuation (real-time value, condition)
   - Early warning system

**Status:** Future feature (Phase 5)  
**Source:** SMART_COLLATERAL_SYSTEM_DESIGN.md

---

**Last Updated:** October 13, 2025

