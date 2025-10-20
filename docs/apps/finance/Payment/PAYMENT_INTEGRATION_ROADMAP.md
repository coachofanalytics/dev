# Payment System Integration Roadmap

**Goal:** Integrate modern unified payment interface with legacy system  
**Timeline:** 6 weeks  
**Date Created:** October 16, 2025

---

## 🎯 INTEGRATION ARCHITECTURE

### Current State:
```
┌─────────────────────────────────────────────┐
│         LEGACY SYSTEM (Working)             │
├─────────────────────────────────────────────┤
│  URL: /finance/pay/                         │
│  Template: payments/pay.html                │
│  View: views.py::pay()                      │
│                                             │
│  Payment Methods:                           │
│  ✓ PayPal (inline SDK)                     │
│  ✓ M-Pesa (STK Push + OTP)                 │
│  ✓ Cashapp (email instructions)            │
│  ✓ Zelle (email instructions)              │
│  ✓ Venmo (email instructions)              │
│                                             │
│  Data: Payment_Information,                 │
│        Payment_History models               │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│      UNIFIED SYSTEM (Template Only)         │
├─────────────────────────────────────────────┤
│  URL: /finance/unified/methods/ (404)       │
│  Template: method_selection.html ✓          │
│  View: MISSING (was in _deprecated)         │
│                                             │
│  Status: NOT DEPLOYED                       │
│                                             │
│  Advanced Models Available:                 │
│  • PaymentMethod                            │
│  • PaymentTransaction                       │
│  • PaymentGateway                           │
└─────────────────────────────────────────────┘
```

### Target State:
```
┌──────────────────────────────────────────────────────────────┐
│              UNIFIED PAYMENT SYSTEM                          │
├──────────────────────────────────────────────────────────────┤
│  URL: /finance/unified/methods/                              │
│  Architecture: views/payment/ module                         │
│                                                              │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────────┐     │
│  │  Method    │  │   M-Pesa     │  │    Stripe       │     │
│  │ Selection  │→ │  Processor   │  │   Processor     │     │
│  │   View     │  │              │  │                 │     │
│  └────────────┘  └──────────────┘  └─────────────────┘     │
│        ↓                                                     │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────────┐     │
│  │   Bank     │  │  Callbacks   │  │   Success/      │     │
│  │ Processor  │  │   Handler    │  │   Failure       │     │
│  └────────────┘  └──────────────┘  └─────────────────┘     │
│                                                              │
│  Data Layer:                                                 │
│  • PaymentTransaction (immutable audit trail)                │
│  • PaymentMethod (configurable methods)                      │
│  • PaymentGateway (integration configs)                      │
│                                                              │
│  Services:                                                   │
│  • MPESAService (existing)                                   │
│  • StripeService (new)                                       │
│  • PaymentProcessingService (new)                            │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│         LEGACY SYSTEM (Maintained for Fallback)              │
├──────────────────────────────────────────────────────────────┤
│  URL: /finance/pay/ → REDIRECTS to /finance/unified/methods/│
│  Kept as emergency fallback                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## 📅 DETAILED IMPLEMENTATION TIMELINE

### **Week 1: Foundation & Planning** (Oct 16-22, 2025)

#### Day 1: Architecture Design ✓ COMPLETE
- [x] Study existing systems (COMPLETE - see PAYMENT_SYSTEM_ANALYSIS.md)
- [x] Review documentation
- [x] Identify integration points
- [x] Create roadmap

#### Day 2-3: Module Structure
- [ ] Create `coda/finance/views/payment/` directory
- [ ] Create `__init__.py` with view exports
- [ ] Create `method_selection.py` (main entry point)
- [ ] Create `base.py` (shared payment logic)

#### Day 4-5: Data Models Setup
- [ ] Review PaymentMethod model
- [ ] Create admin interface for PaymentMethod
- [ ] Create initial PaymentMethod records:
  - M-Pesa (mobile_money, active=True)
  - Stripe (card, active=True)
  - Bank Transfer (bank_transfer, active=True)
- [ ] Test PaymentTransaction creation
- [ ] Document model relationships

---

### **Week 2: M-Pesa Integration** (Oct 23-29, 2025)

#### Day 1: M-Pesa View
- [ ] Create `mpesa_processor.py`
- [ ] Implement `initiate_mpesa_payment(request)` view
- [ ] Phone number validation
- [ ] Amount validation
- [ ] Session management

#### Day 2: OTP Flow
- [ ] Create `otp_handler.py`
- [ ] Implement OTP generation
- [ ] Email OTP delivery
- [ ] OTP verification view
- [ ] Rate limiting (prevent spam)

#### Day 3: STK Push Integration
- [ ] Integrate existing `MPESAService`
- [ ] Implement `process_mpesa_stk(request)` view
- [ ] Error handling (timeout, insufficient funds)
- [ ] User feedback messages
- [ ] Loading states

#### Day 4: Callback Handler
- [ ] Create `callbacks.py`
- [ ] Implement `mpesa_callback(request)` view
- [ ] Parse Safaricom callback data
- [ ] Update PaymentTransaction status
- [ ] Send confirmation email/SMS
- [ ] Webhook signature verification

#### Day 5: Testing
- [ ] M-Pesa sandbox setup
- [ ] Test full flow (local)
- [ ] Test error scenarios
- [ ] Test callback handling
- [ ] Load testing (concurrent payments)

---

### **Week 3: Stripe & Bank Transfer** (Oct 30 - Nov 5, 2025)

#### Day 1-2: Stripe Integration
- [ ] Create `stripe_processor.py`
- [ ] Stripe account setup (test mode)
- [ ] Implement Payment Intent creation
- [ ] Stripe Elements form integration
- [ ] Client-side JavaScript for card input

#### Day 2 (continued): Stripe Processing
- [ ] Implement `process_stripe_payment(request)` view
- [ ] 3D Secure (SCA) support
- [ ] Error handling (card declined, etc.)
- [ ] Create `stripe_webhook(request)` view
- [ ] Webhook signature verification

#### Day 3: Stripe Testing
- [ ] Test mode setup
- [ ] Test cards (4242 4242 4242 4242)
- [ ] Test 3D Secure flow
- [ ] Test webhook callbacks
- [ ] Test error scenarios

#### Day 4: Bank Transfer
- [ ] Create `bank_processor.py`
- [ ] Implement `show_bank_details(request)` view
- [ ] Display account details
- [ ] Generate payment reference
- [ ] Upload proof of payment

#### Day 5: Bank Transfer Admin
- [ ] Admin verification workflow
- [ ] Proof of payment review
- [ ] Manual approval/rejection
- [ ] Notification system
- [ ] Testing

---

### **Week 4: URL Integration & UI Polish** (Nov 6-12, 2025)

#### Day 1: URL Configuration
- [ ] Update `finance/urls.py`
- [ ] Remove conditional payment_views import
- [ ] Add new payment URLs:
  ```python
  path('unified/methods/', method_selection_view)
  path('unified/mpesa/', mpesa_view)
  path('unified/stripe/', stripe_view)
  path('unified/bank/', bank_view)
  path('unified/callbacks/mpesa/', mpesa_callback)
  path('unified/callbacks/stripe/', stripe_webhook)
  path('unified/success/<transaction_id>/', success_view)
  path('unified/failed/<transaction_id>/', failed_view)
  ```

#### Day 2: Template Refinement
- [ ] Update `method_selection.html` styling
- [ ] Add payment method icons
- [ ] Responsive design testing
- [ ] Browser compatibility
- [ ] Accessibility (ARIA labels)

#### Day 3: Success/Failure Pages
- [ ] Create `success.html` template
- [ ] Create `failed.html` template
- [ ] Display transaction details
- [ ] Download receipt option
- [ ] Contact support link

#### Day 4: Dashboard Integration
- [ ] Update main dashboard "Make Payment" link
- [ ] Add payment history widget
- [ ] Recent transactions display
- [ ] Payment status indicators

#### Day 5: User Flow Testing
- [ ] Complete user journey testing
- [ ] Mobile responsiveness
- [ ] Cross-browser testing
- [ ] Accessibility audit
- [ ] Performance testing

---

### **Week 5: Testing & QA** (Nov 13-19, 2025)

#### Day 1-2: Local Testing
- [ ] All payment methods (M-Pesa, Stripe, Bank)
- [ ] Success scenarios
- [ ] Error scenarios
- [ ] Edge cases (network issues, timeouts)
- [ ] Security testing (CSRF, XSS)

#### Day 3: UAT Deployment
- [ ] Deploy to UAT environment
- [ ] Configure environment variables:
  ```bash
  MPESA_CONSUMER_KEY=xxx
  MPESA_CONSUMER_SECRET=xxx
  MPESA_SHORTCODE=xxx
  MPESA_PASSKEY=xxx
  STRIPE_PUBLIC_KEY=pk_test_xxx
  STRIPE_SECRET_KEY=sk_test_xxx
  ```
- [ ] Test callback URLs work
- [ ] Monitor logs

#### Day 4: UAT Testing
- [ ] Stakeholder testing
- [ ] User acceptance testing
- [ ] Collect feedback
- [ ] Bug fixes
- [ ] Performance monitoring

#### Day 5: Regression Testing
- [ ] Ensure legacy system still works
- [ ] Test all existing payment flows
- [ ] Run regression test suite
- [ ] Check no breaking changes
- [ ] Documentation review

---

### **Week 6: Migration & Launch** (Nov 20-26, 2025)

#### Day 1: Pre-Launch Preparation
- [ ] Final code review
- [ ] Security audit
- [ ] Performance optimization
- [ ] Database backups
- [ ] Rollback plan ready

#### Day 2: Soft Launch
- [ ] Deploy to production (off-hours)
- [ ] Add feature flag for gradual rollout
- [ ] Monitor error rates
- [ ] Test production payments (small amounts)
- [ ] Check callback URLs

#### Day 3: Gradual Rollout
- [ ] Enable for 10% of users
- [ ] Monitor metrics (success rate, errors)
- [ ] Enable for 50% of users
- [ ] Collect user feedback
- [ ] Bug fixes if needed

#### Day 4: Full Launch
- [ ] Redirect `/finance/pay/` to `/finance/unified/methods/`
- [ ] Update all dashboard links
- [ ] Announcement to users
- [ ] Monitor for 24 hours
- [ ] Keep legacy as fallback

#### Day 5: Post-Launch
- [ ] Monitor payment success rates
- [ ] Review error logs
- [ ] User feedback collection
- [ ] Documentation updates
- [ ] Celebrate! 🎉

---

## 🏗️ TECHNICAL ARCHITECTURE

### Directory Structure:
```
coda/finance/
├── views/
│   ├── payment/
│   │   ├── __init__.py              # Export all views
│   │   ├── base.py                  # Shared payment logic
│   │   ├── method_selection.py      # Main entry point
│   │   ├── mpesa_processor.py       # M-Pesa STK Push
│   │   ├── stripe_processor.py      # Stripe integration
│   │   ├── bank_processor.py        # Bank transfers
│   │   ├── callbacks.py             # Payment callbacks
│   │   └── success_failure.py       # Result pages
│
├── services/
│   ├── mpesa_service.py             # Existing M-Pesa API
│   ├── stripe_service.py            # NEW: Stripe API
│   └── payment_processing.py        # NEW: Unified processing
│
├── templates/finance/payments/
│   ├── unified/
│   │   ├── method_selection.html    # Existing (modern UI)
│   │   ├── mpesa_form.html          # M-Pesa phone input
│   │   ├── mpesa_otp.html           # OTP verification
│   │   ├── stripe_form.html         # Stripe card input
│   │   ├── bank_details.html        # Bank transfer info
│   │   ├── success.html             # Payment success
│   │   └── failed.html              # Payment failed
│
├── models/
│   ├── payment.py                   # PaymentMethod, PaymentTransaction, PaymentGateway
│   └── core.py                      # Payment_Information (legacy, keep for compat)
│
└── urls.py                          # Update with new routes
```

### Service Layer Architecture:
```python
# views/payment/base.py
class BasePaymentView:
    """Base class for all payment views"""
    
    def get_user_payment_context(self, user):
        """Get payment info (loan, service, history)"""
        # Reuse logic from legacy pay() view
        pass
    
    def create_payment_transaction(self, user, method, amount):
        """Create PaymentTransaction record"""
        pass
    
    def send_payment_confirmation(self, transaction):
        """Send email/SMS confirmation"""
        pass

# views/payment/method_selection.py
def unified_method_selection(request):
    """Main payment method selection"""
    
    # Get active payment methods from DB
    methods = PaymentMethod.objects.filter(is_active=True)
    
    # Get user payment context
    payment_info = get_user_payment_context(request.user)
    
    # Render with context
    return render(request, 'unified/method_selection.html', {
        'methods': methods,
        'payment_info': payment_info
    })

# services/payment_processing.py
class PaymentProcessingService(BaseFinanceService):
    """Unified payment processing logic"""
    
    def process_payment(self, user, method, amount, **kwargs):
        """Process payment based on method"""
        
        # Create transaction record
        transaction = PaymentTransaction.objects.create(
            user=user,
            payment_method=method,
            amount=amount,
            status='initiated',
            transaction_id=self.generate_transaction_id()
        )
        
        # Route to appropriate gateway
        if method.method_type == 'mobile_money':
            result = self.mpesa_service.initiate_stk_push(...)
        elif method.method_type == 'card':
            result = self.stripe_service.create_payment_intent(...)
        elif method.method_type == 'bank_transfer':
            result = self.bank_service.generate_reference(...)
        
        # Update transaction
        transaction.external_transaction_id = result['id']
        transaction.status = 'processing'
        transaction.save()
        
        return transaction
```

---

## 📊 SUCCESS METRICS

### Technical Metrics:
- **Uptime:** 99.9% availability
- **Response Time:** < 2 seconds for method selection
- **STK Push Time:** < 5 seconds for M-Pesa prompt
- **Callback Processing:** < 1 second
- **Error Rate:** < 1% of transactions

### Business Metrics:
- **Payment Success Rate:** > 95%
- **User Satisfaction:** Survey after payment
- **Method Adoption:** Track M-Pesa vs Stripe vs Bank
- **Revenue:** Track total payments processed
- **Conversion Rate:** Payment initiated → completed

### User Experience Metrics:
- **Time to Complete:** Track from selection to success
- **Drop-off Rate:** Where users abandon
- **Return Rate:** Do users complete payment after failure?
- **Support Tickets:** Payment-related issues

---

## 🔧 CONFIGURATION CHECKLIST

### Before UAT Deployment:
- [ ] M-Pesa sandbox credentials configured
- [ ] Stripe test mode keys configured
- [ ] Callback URLs whitelisted (M-Pesa dashboard)
- [ ] Webhook URLs configured (Stripe dashboard)
- [ ] Email service configured (confirmations)
- [ ] SMS service configured (optional)
- [ ] PaymentMethod records created
- [ ] PaymentGateway records created
- [ ] Admin permissions configured

### Before Production Deployment:
- [ ] M-Pesa production credentials
- [ ] Stripe production keys
- [ ] Callback URLs updated to production
- [ ] Webhook URLs updated to production
- [ ] SSL certificate valid
- [ ] Database backup completed
- [ ] Monitoring alerts configured
- [ ] Rollback plan tested
- [ ] Support team trained

---

## 🚨 RISK MITIGATION

### Risk 1: Payment Callback Failures
**Mitigation:**
- Implement retry mechanism
- Queue-based callback processing
- Manual reconciliation tool
- Alert on missed callbacks

### Risk 2: Gateway Downtime
**Mitigation:**
- Graceful degradation (disable method temporarily)
- Display downtime message
- Alternative payment methods available
- Monitor gateway status

### Risk 3: Duplicate Payments
**Mitigation:**
- Idempotency keys
- Transaction ID uniqueness
- User-facing confirmation before processing
- Duplicate detection in callback

### Risk 4: Security Vulnerabilities
**Mitigation:**
- CSRF protection (already in place)
- Webhook signature verification
- Rate limiting on payment endpoints
- PCI DSS compliance (for Stripe)
- Regular security audits

### Risk 5: Legacy System Breakage
**Mitigation:**
- Keep legacy system functional
- Feature flag for rollback
- Gradual rollout (10% → 50% → 100%)
- Comprehensive regression testing

---

## 📞 SUPPORT PLAN

### User Support:
- **FAQ:** Common payment issues and solutions
- **Help Page:** Step-by-step payment guide
- **Email Support:** info@codanalytics.net
- **Phone Support:** Available during business hours

### Technical Support:
- **Monitoring:** Real-time payment error alerts
- **Logging:** Detailed payment logs (PII redacted)
- **Dashboard:** Admin payment monitoring
- **Reconciliation:** Daily payment reconciliation report

### Escalation Path:
1. **Level 1:** User support (FAQ, basic troubleshooting)
2. **Level 2:** Technical support (investigate logs)
3. **Level 3:** Developer on-call (code fixes)
4. **Level 4:** Gateway support (M-Pesa, Stripe)

---

## ✅ GO-LIVE CHECKLIST

### Pre-Launch (Day Before):
- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] UAT sign-off received
- [ ] Database backup completed
- [ ] Rollback plan documented
- [ ] Support team briefed
- [ ] Monitoring alerts configured
- [ ] On-call engineer assigned

### Launch Day:
- [ ] Deploy during off-peak hours
- [ ] Monitor deployment logs
- [ ] Test smoke scenarios
- [ ] Verify callbacks working
- [ ] Check error rates
- [ ] Monitor user feedback
- [ ] Be ready to rollback

### Post-Launch (First Week):
- [ ] Daily monitoring
- [ ] Daily reconciliation
- [ ] User feedback review
- [ ] Bug fixes (if needed)
- [ ] Performance optimization
- [ ] Support ticket review
- [ ] Retrospective meeting

---

## 📚 DOCUMENTATION UPDATES

### Required Updates:
1. **Payment README:** Update status to "Active"
2. **Payment IMPLEMENTATION:** Add new architecture section
3. **Payment TESTING:** Add UAT results
4. **User Guide:** Create payment user guide
5. **Admin Guide:** Payment admin operations
6. **API Docs:** Payment API endpoints
7. **MASTER_REFERENCE:** Update payment section

---

## 🎯 SUCCESS CRITERIA

### Phase 1 Success:
- [x] Analysis complete
- [ ] Architecture defined
- [ ] Module structure created
- [ ] Data models configured

### Phase 2 Success:
- [ ] M-Pesa integration working
- [ ] Stripe integration working
- [ ] Bank transfer working
- [ ] All tests passing

### Phase 3 Success:
- [ ] Deployed to UAT
- [ ] User acceptance received
- [ ] Performance acceptable
- [ ] No critical bugs

### Final Success:
- [ ] Deployed to production
- [ ] Payment success rate > 95%
- [ ] User satisfaction > 90%
- [ ] No rollback needed
- [ ] Legacy system deprecated

---

**Last Updated:** October 16, 2025  
**Status:** Week 1 - Analysis Complete  
**Next Step:** Create module structure (Week 1, Day 2)


