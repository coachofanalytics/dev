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

- Min loan amount: KES 5,000
- Max loan amount: KES 500,000 (varies by product)
- Interest rates: 8-18% p.a.
- Terms: 3-36 months
- Collateral required for amounts >100K

---

**Last Updated:** October 13, 2025

