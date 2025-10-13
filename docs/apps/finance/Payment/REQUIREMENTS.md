# Payment System - Requirements

## Business Goals

Enable users to make payments through multiple convenient methods with automated confirmation.

## Functional Requirements

### REQ-001: Payment Method Selection
Users choose from:
- M-Pesa (mobile money)
- Stripe (credit/debit card)
- Bank Transfer (manual)

### REQ-002: M-Pesa Integration
- STK Push (automated prompt)
- Phone number validation
- Amount confirmation
- Payment callback handling

### REQ-003: Stripe Integration
- Card tokenization (secure)
- Payment intent creation
- 3D Secure support
- Receipt generation

### REQ-004: Bank Transfer
- Display account details
- Payment reference generation
- Manual confirmation process

### REQ-005: Payment Tracking
- Transaction status monitoring
- Confirmation emails
- Payment history

## Business Rules

- All payments require confirmation before processing
- M-Pesa: Minimum KES 10, Maximum KES 150,000
- Stripe: Minimum KES 100 (fees apply)
- Bank Transfer: Any amount, manual verification

## Current Status

**All requirements on hold** - Payment system disabled pending:
1. Decision: Deploy `_deprecated` module OR refactor
2. Testing in UAT environment
3. Payment gateway credentials verification

---

**Last Updated:** October 13, 2025  
**Status:** On Hold

