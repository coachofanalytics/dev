# Onboarding & Compliance Testing Strategy

## **Document Purpose**

Comprehensive testing strategy for the Managed Options Trading client onboarding, compliance, and batch approval workflow.

**Created:** October 27, 2025  
**Testing Philosophy:** Get it right before deployment - test every step  

---

## **🎯 TESTING APPROACH**

### **Three-Layer Testing**

1. **Unit Tests** - Individual components (models, forms, services)
2. **Integration Tests** - Workflows (onboarding flow, approval flow)
3. **End-to-End Tests** - Complete user journeys (new client → first trade)

### **Testing Priority**

- **P1 (Critical):** Must work for launch
- **P2 (Important):** Should work for good UX
- **P3 (Nice to Have):** Can be added post-launch

---

## **📋 TEST PLAN BY PHASE**

### **PHASE 1: ONBOARDING FOUNDATION**

#### **Test Suite 1.1: Risk Tolerance Questionnaire**

**Component:** `forms_risk_assessment.py::RiskToleranceQuestionnaireForm`

**Unit Tests:**
```python
@pytest.mark.django_db
def test_risk_questionnaire_all_questions():
    """Test all 10 questions are present"""
    form = RiskToleranceQuestionnaireForm()
    assert len(form.fields) == 10
    for i in range(1, 11):
        assert f'question_{i}' in form.fields

@pytest.mark.django_db
def test_risk_score_calculation_conservative():
    """Test conservative score (0-30 points)"""
    data = {f'question_{i}': 1 for i in range(1, 11)}  # All conservative answers
    form = RiskToleranceQuestionnaireForm(data)
    assert form.is_valid()
    assert form.calculate_risk_score() <= 30
    assert form.get_risk_category() == 'conservative'

@pytest.mark.django_db
def test_risk_score_calculation_moderate():
    """Test moderate score (31-60 points)"""
    data = {f'question_{i}': 2 for i in range(1, 11)}  # All moderate answers
    form = RiskToleranceQuestionnaireForm(data)
    assert form.is_valid()
    assert 31 <= form.calculate_risk_score() <= 60
    assert form.get_risk_category() == 'moderate'

@pytest.mark.django_db
def test_risk_score_calculation_aggressive():
    """Test aggressive score (61-100 points)"""
    data = {f'question_{i}': 3 for i in range(1, 11)}  # All aggressive answers
    form = RiskToleranceQuestionnaireForm(data)
    assert form.is_valid()
    assert form.calculate_risk_score() >= 61
    assert form.get_risk_category() == 'aggressive'

@pytest.mark.django_db
def test_fee_tier_recommendation_conservative():
    """Test tier recommendation for conservative profile"""
    data = {f'question_{i}': 1 for i in range(1, 11)}
    form = RiskToleranceQuestionnaireForm(data)
    recommendations = form.get_recommended_tiers()
    assert 'consultative' in recommendations
    assert 'professional' in recommendations
    assert 'co_invest' not in recommendations

@pytest.mark.django_db
def test_fee_tier_recommendation_aggressive():
    """Test tier recommendation for aggressive profile"""
    data = {f'question_{i}': 3 for i in range(1, 11)}
    form = RiskToleranceQuestionnaireForm(data)
    recommendations = form.get_recommended_tiers()
    assert 'premium' in recommendations
    assert 'co_invest' in recommendations
```

**Integration Tests:**
```python
@pytest.mark.django_db
def test_risk_assessment_flow(client, test_user):
    """Test complete risk assessment flow"""
    client.force_login(test_user)
    
    # Step 1: Navigate to risk assessment
    response = client.get('/investing/managed/risk-assessment/')
    assert response.status_code == 200
    assert 'Risk Tolerance Questionnaire' in response.content.decode()
    
    # Step 2: Submit questionnaire
    data = {f'question_{i}': 2 for i in range(1, 11)}  # Moderate profile
    response = client.post('/investing/managed/risk-assessment/', data)
    assert response.status_code == 302  # Redirect to application
    
    # Step 3: Verify risk profile saved
    test_user.refresh_from_db()
    assert hasattr(test_user, 'risk_profile')
    assert test_user.risk_profile.risk_score == 50  # 10 questions * 5 points each
    assert test_user.risk_profile.risk_category == 'moderate'
```

**Manual Testing Checklist:**
- [ ] Load risk assessment page
- [ ] All 10 questions display correctly
- [ ] Radio buttons work
- [ ] Cannot submit without answering all questions
- [ ] Score calculation displays correctly
- [ ] Recommended tiers show based on score
- [ ] Redirect to application works
- [ ] Back button preserves answers

---

#### **Test Suite 1.2: Managed Trading Application**

**Component:** `forms.py::ManagedTradingApplicationForm`

**Unit Tests:**
```python
@pytest.mark.django_db
def test_application_form_valid_data(test_user):
    """Test application form with valid data"""
    data = {
        'user': test_user.id,
        'initial_capital': 30000,
        'fee_tier': 'professional',
        'preferred_manager': None,
        'funding_method': 'wire',
    }
    form = ManagedTradingApplicationForm(data)
    assert form.is_valid()

@pytest.mark.django_db
def test_application_minimum_capital_validation():
    """Test minimum capital requirement ($5,000)"""
    data = {
        'initial_capital': 4999,  # Below minimum
        'fee_tier': 'professional',
    }
    form = ManagedTradingApplicationForm(data)
    assert not form.is_valid()
    assert 'initial_capital' in form.errors

@pytest.mark.django_db
def test_application_tier_capital_match():
    """Test capital matches tier requirements"""
    # Starter tier requires $5k-$15k
    data = {
        'initial_capital': 4000,  # Too low for starter
        'fee_tier': 'starter',
    }
    form = ManagedTradingApplicationForm(data)
    assert not form.is_valid()
    
    # Premium requires $15k+
    data = {
        'initial_capital': 10000,  # Too low for premium
        'fee_tier': 'premium',
    }
    form = ManagedTradingApplicationForm(data)
    assert not form.is_valid()

@pytest.mark.django_db
def test_application_risk_tier_mismatch_warning():
    """Test warning for risk/tier mismatch"""
    # Conservative user selecting aggressive tier
    data = {
        'risk_profile_score': 20,  # Conservative
        'fee_tier': 'premium',  # Aggressive tier
        'initial_capital': 20000,
    }
    form = ManagedTradingApplicationForm(data)
    warnings = form.get_warnings()
    assert 'risk_mismatch' in warnings
```

**Integration Tests:**
```python
@pytest.mark.django_db
def test_complete_application_submission(client, test_user_with_risk_profile):
    """Test complete application submission"""
    client.force_login(test_user_with_risk_profile)
    
    # Navigate to application
    response = client.get('/investing/managed/apply/')
    assert response.status_code == 200
    
    # Verify risk profile pre-filled
    content = response.content.decode()
    assert 'moderate' in content.lower()
    
    # Submit application
    data = {
        'initial_capital': 30000,
        'fee_tier': 'professional',
        'funding_method': 'wire',
    }
    response = client.post('/investing/managed/apply/', data)
    assert response.status_code == 302
    
    # Verify application created
    from investing.models import ManagedTradingApplication
    app = ManagedTradingApplication.objects.get(user=test_user_with_risk_profile)
    assert app.status == 'pending'
    assert app.initial_capital == 30000
```

**Manual Testing Checklist:**
- [ ] Application form loads with risk profile data
- [ ] Fee tier options filtered by risk profile
- [ ] Capital amount validation works
- [ ] Tier/capital mismatch shows error
- [ ] Risk/tier mismatch shows warning
- [ ] Form submits successfully
- [ ] Redirect to contract review works
- [ ] Application appears in staff queue

---

#### **Test Suite 1.3: Contract System**

**Component:** `models.py::ManagedTradingContract` + existing `BaseContract`

**Unit Tests:**
```python
@pytest.mark.django_db
def test_contract_generation_ima(managed_account):
    """Test IMA contract generation"""
    contract = ManagedTradingContract.objects.create(
        managed_account=managed_account,
        contract_type='ima',
        title='Investment Management Agreement',
    )
    assert contract.contract_type == 'ima'
    assert contract.status == 'pending'

@pytest.mark.django_db
def test_contract_signature_capture(managed_account):
    """Test signature data storage"""
    contract = ManagedTradingContract.objects.create(
        managed_account=managed_account,
        contract_type='ima',
    )
    
    # Sign contract
    signature_data = 'data:image/png;base64,iVBORw0KG...'
    contract.signature_data = signature_data
    contract.signed_date = timezone.now()
    contract.status = 'signed'
    contract.save()
    
    contract.refresh_from_db()
    assert contract.is_signed
    assert contract.signature_data == signature_data

@pytest.mark.django_db
def test_all_contracts_signed(managed_account):
    """Test checking if all required contracts signed"""
    # Create 4 required contracts
    for contract_type in ['ima', 'risk_disclosure', 'fee_agreement', 'terms']:
        ManagedTradingContract.objects.create(
            managed_account=managed_account,
            contract_type=contract_type,
            status='signed',
        )
    
    assert managed_account.all_contracts_signed() == True
```

**Integration Tests:**
```python
@pytest.mark.django_db
def test_contract_signing_flow(client, test_user_with_application):
    """Test complete contract signing flow"""
    client.force_login(test_user_with_application)
    
    # Step 1: Navigate to contract review
    response = client.get('/investing/managed/contracts/review/')
    assert response.status_code == 200
    
    # Verify 4 contracts generated
    content = response.content.decode()
    assert 'Investment Management Agreement' in content
    assert 'Options Trading Risk Disclosure' in content
    assert 'Fee Schedule Agreement' in content
    assert 'Terms of Service' in content
    
    # Step 2: Sign first contract (IMA)
    signature_data = {'signature': 'data:image/png;base64,...'}
    response = client.post('/investing/managed/contracts/sign/ima/', signature_data)
    assert response.status_code == 200
    assert response.json()['status'] == 'signed'
    
    # Step 3: Sign remaining contracts
    for contract_type in ['risk_disclosure', 'fee_agreement', 'terms']:
        response = client.post(f'/investing/managed/contracts/sign/{contract_type}/', signature_data)
        assert response.status_code == 200
    
    # Step 4: Verify all contracts signed
    response = client.get('/investing/managed/contracts/status/')
    data = response.json()
    assert data['all_signed'] == True
    assert data['next_url'] == '/investing/managed/application/complete/'
```

**Manual Testing Checklist:**
- [ ] Contract review page loads
- [ ] All 4 contracts display
- [ ] Can scroll through each contract
- [ ] Signature canvas works (mouse/touch)
- [ ] Cannot submit without signature
- [ ] Clear signature button works
- [ ] Signed contracts show checkmark
- [ ] Cannot edit signed contracts
- [ ] PDF download works
- [ ] All signed → redirect to completion page

---

### **PHASE 2: STAFF APPROVAL**

#### **Test Suite 2.1: Application Review Queue**

**Component:** `views/managed_trading/applications.py`

**Unit Tests:**
```python
@pytest.mark.django_db
def test_pending_applications_queryset(staff_user):
    """Test pending applications query"""
    # Create test applications
    approved_app = create_application(status='approved')
    pending_app1 = create_application(status='pending')
    pending_app2 = create_application(status='pending')
    
    from investing.services import ApplicationReviewService
    service = ApplicationReviewService()
    pending = service.get_pending_applications()
    
    assert pending.count() == 2
    assert pending_app1 in pending
    assert pending_app2 in pending
    assert approved_app not in pending

@pytest.mark.django_db
def test_application_approval(staff_user, pending_application):
    """Test approving an application"""
    service = ApplicationReviewService()
    result = service.approve_application(
        application=pending_application,
        approved_by=staff_user,
    )
    
    assert result['status'] == 'success'
    assert result['account'] is not None
    
    pending_application.refresh_from_db()
    assert pending_application.status == 'approved'
    
    # Verify account created
    account = result['account']
    assert account.client == pending_application.user
    assert account.status == 'active'

@pytest.mark.django_db
def test_application_rejection(staff_user, pending_application):
    """Test rejecting an application"""
    service = ApplicationReviewService()
    result = service.reject_application(
        application=pending_application,
        rejected_by=staff_user,
        reason='Insufficient risk tolerance for selected tier'
    )
    
    assert result['status'] == 'success'
    pending_application.refresh_from_db()
    assert pending_application.status == 'rejected'
    assert 'risk tolerance' in pending_application.rejection_reason
```

**Integration Tests:**
```python
@pytest.mark.django_db
def test_staff_approval_workflow(client, staff_user, pending_application):
    """Test staff approving application and creating account"""
    client.force_login(staff_user)
    
    # Step 1: View pending applications
    response = client.get('/investing/managed/applications/')
    assert response.status_code == 200
    content = response.content.decode()
    assert pending_application.user.get_full_name() in content
    
    # Step 2: Review application details
    response = client.get(f'/investing/managed/applications/{pending_application.id}/')
    assert response.status_code == 200
    assert 'Risk Profile' in response.content.decode()
    assert 'All Contracts Signed' in response.content.decode()
    
    # Step 3: Approve application
    data = {
        'action': 'approve',
        'account_manager': staff_user.id,
    }
    response = client.post(f'/investing/managed/applications/{pending_application.id}/review/', data)
    assert response.status_code == 302
    
    # Step 4: Verify account created
    from investing.models import ManagedTradingAccount
    account = ManagedTradingAccount.objects.get(client=pending_application.user)
    assert account.status == 'active'
    assert account.account_manager == staff_user
    
    # Step 5: Verify email sent
    from django.core import mail
    assert len(mail.outbox) == 1
    assert 'Account Ready' in mail.outbox[0].subject
```

**Manual Testing Checklist:**
- [ ] Staff can access applications queue
- [ ] Pending applications show correctly
- [ ] Click application to view details
- [ ] Risk profile displays
- [ ] Signed contracts visible
- [ ] Approve button creates account
- [ ] Account number generated (CODA-OPT-XXX)
- [ ] Rejection form works
- [ ] Email sent to client
- [ ] Application removed from queue

---

#### **Test Suite 2.2: Auto-Approval Rules**

**Component:** `services/application_approval_service.py`

**Unit Tests:**
```python
@pytest.mark.django_db
def test_auto_approval_qualified_applicant():
    """Test auto-approval for qualified applicant"""
    application = create_application(
        risk_score=50,  # Moderate
        fee_tier='professional',  # Matches moderate
        initial_capital=30000,  # Above minimum
        all_contracts_signed=True,
    )
    
    service = ApplicationReviewService()
    result = service.check_auto_approval(application)
    
    assert result['auto_approve'] == True
    assert result['reason'] == 'Meets all criteria'

@pytest.mark.django_db
def test_auto_approval_risk_tier_mismatch():
    """Test manual review required for risk/tier mismatch"""
    application = create_application(
        risk_score=20,  # Conservative
        fee_tier='premium',  # Aggressive tier - mismatch!
        initial_capital=30000,
        all_contracts_signed=True,
    )
    
    service = ApplicationReviewService()
    result = service.check_auto_approval(application)
    
    assert result['auto_approve'] == False
    assert 'risk mismatch' in result['reason'].lower()

@pytest.mark.django_db
def test_auto_approval_missing_contracts():
    """Test manual review if contracts not signed"""
    application = create_application(
        risk_score=50,
        fee_tier='professional',
        initial_capital=30000,
        all_contracts_signed=False,  # Not signed!
    )
    
    service = ApplicationReviewService()
    result = service.check_auto_approval(application)
    
    assert result['auto_approve'] == False
    assert 'contracts' in result['reason'].lower()
```

**Manual Testing Checklist:**
- [ ] Qualified application auto-approved within 5 minutes
- [ ] Email sent immediately
- [ ] Account created with correct details
- [ ] Mismatched application goes to manual review
- [ ] Missing contracts trigger manual review
- [ ] Capital below tier minimum triggers review
- [ ] Staff notified of manual reviews

---

### **PHASE 3: BATCH APPROVAL**

#### **Test Suite 3.1: Position Batch Model**

**Component:** `models.py::PositionBatch`

**Unit Tests:**
```python
@pytest.mark.django_db
def test_batch_creation(managed_account):
    """Test creating a position batch"""
    batch = PositionBatch.objects.create(
        managed_account=managed_account,
        batch_number='BATCH-2025-W47',
        approval_deadline=timezone.now() + timedelta(hours=24),
        status='pending',
    )
    assert batch.is_pending
    assert not batch.is_expired

@pytest.mark.django_db
def test_batch_capital_calculation(managed_account):
    """Test total capital calculation"""
    batch = PositionBatch.objects.create(managed_account=managed_account)
    
    # Add 3 positions
    pos1 = create_position(batch=batch, capital_required=3000)
    pos2 = create_position(batch=batch, capital_required=2500)
    pos3 = create_position(batch=batch, capital_required=3000)
    
    assert batch.total_capital_required == 8500
    assert batch.total_positions == 3

@pytest.mark.django_db
def test_batch_timeout_check():
    """Test batch timeout detection"""
    # Create expired batch
    batch = PositionBatch.objects.create(
        managed_account=managed_account,
        approval_deadline=timezone.now() - timedelta(hours=1),  # 1 hour ago
        status='pending',
    )
    
    assert batch.is_expired
    
    # Run timeout check
    service = BatchApprovalService()
    service.process_expired_batches()
    
    batch.refresh_from_db()
    assert batch.status == 'expired'
```

**Integration Tests:**
```python
@pytest.mark.django_db
def test_weekly_batch_generation(staff_user, managed_account):
    """Test generating weekly position batch"""
    # Create 3 pending positions throughout the week
    pos1 = create_position(managed_account=managed_account, status='pending')
    pos2 = create_position(managed_account=managed_account, status='pending')
    pos3 = create_position(managed_account=managed_account, status='pending')
    
    # Generate batch (Friday)
    service = BatchApprovalService()
    batch = service.create_weekly_batch(managed_account)
    
    assert batch.total_positions == 3
    assert batch.status == 'pending'
    assert batch.approval_deadline > timezone.now()
    
    # Verify positions linked to batch
    pos1.refresh_from_db()
    assert pos1.batch == batch
```

**Manual Testing Checklist:**
- [ ] Staff can create batch manually
- [ ] Batch includes all pending positions
- [ ] Total capital calculated correctly
- [ ] Deadline set to 24 hours from now
- [ ] Batch number generated (BATCH-YYYY-Wxx)
- [ ] Client notified via email/SMS

---

#### **Test Suite 3.2: Client Batch Approval**

**Component:** `views/managed_trading/batches.py` + `templates/managed/batch_approval.html`

**Integration Tests:**
```python
@pytest.mark.django_db
def test_client_batch_approval_flow(client, test_user, pending_batch):
    """Test client approving entire batch"""
    client.force_login(test_user)
    
    # Step 1: Navigate to batch approval
    response = client.get(f'/investing/managed/portal/approvals/batch/{pending_batch.id}/')
    assert response.status_code == 200
    content = response.content.decode()
    assert '3 positions' in content.lower()
    assert '$8,500' in content  # Total capital
    
    # Step 2: Approve all
    data = {
        'action': 'approve_all',
        'signature': 'data:image/png;base64,...',
    }
    response = client.post(f'/investing/managed/portal/approvals/batch/{pending_batch.id}/submit/', data)
    assert response.status_code == 302
    
    # Step 3: Verify batch approved
    pending_batch.refresh_from_db()
    assert pending_batch.status == 'approved'
    assert pending_batch.approval_signature is not None
    
    # Step 4: Verify positions executed
    for position in pending_batch.positions.all():
        assert position.status == 'open'
        assert position.approved_at is not None

@pytest.mark.django_db
def test_client_batch_partial_approval(client, test_user, pending_batch):
    """Test client approving some positions, rejecting others"""
    client.force_login(test_user)
    
    # Approve 2 out of 3 positions
    data = {
        'action': 'review_individually',
        'position_1': 'approve',
        'position_2': 'approve',
        'position_3': 'reject',
        'rejection_reason_3': 'Too risky for current market',
        'signature': 'data:image/png;base64,...',
    }
    response = client.post(f'/investing/managed/portal/approvals/batch/{pending_batch.id}/submit/', data)
    assert response.status_code == 302
    
    # Verify results
    positions = pending_batch.positions.all()
    assert positions[0].status == 'open'
    assert positions[1].status == 'open'
    assert positions[2].status == 'rejected'

@pytest.mark.django_db
def test_batch_timeout_24_hours(client, expired_batch):
    """Test batch auto-rejection after 24 hours"""
    client.force_login(expired_batch.managed_account.client)
    
    # Try to approve expired batch
    response = client.get(f'/investing/managed/portal/approvals/batch/{expired_batch.id}/')
    assert response.status_code == 200
    content = response.content.decode()
    assert 'expired' in content.lower()
    assert 'cannot approve' in content.lower()
    
    # Verify positions rejected
    for position in expired_batch.positions.all():
        assert position.status == 'rejected'
        assert 'timeout' in position.rejection_reason.lower()
```

**Manual Testing Checklist:**
- [ ] Client receives email notification
- [ ] Email contains batch summary
- [ ] Click link to approval page
- [ ] All positions displayed with details
- [ ] Click "View Details" for each position
- [ ] Total capital displayed
- [ ] Max profit/loss shown
- [ ] Approve All button works
- [ ] Signature capture appears
- [ ] Sign and submit
- [ ] Confirmation page displays
- [ ] Email confirmation sent
- [ ] Positions appear in portfolio
- [ ] Individual approval works
- [ ] Reject All works
- [ ] Timeout (24hr) triggers auto-reject
- [ ] Reminder email sent at 12 hours

---

### **PHASE 4: INTEGRATION & AUTOMATION**

#### **Test Suite 4.1: GoToMeeting Integration**

**Component:** `services/gotomeeting_service.py`

**Unit Tests:**
```python
@pytest.mark.django_db
def test_create_gotomeeting_link():
    """Test creating GoToMeeting session link"""
    service = GoToMeetingService()
    result = service.create_meeting(
        title='Options Review Session',
        start_time=timezone.now() + timedelta(days=1),
        duration_minutes=60,
    )
    
    assert result['meeting_url'] is not None
    assert 'gotomeeting.com' in result['meeting_url']
    assert result['meeting_id'] is not None

@pytest.mark.django_db
def test_session_with_gotomeeting(managed_account):
    """Test creating session with GoToMeeting link"""
    from investing.models import TradingSession
    
    session = TradingSession.objects.create(
        managed_account=managed_account,
        session_type='position_review',
        scheduled_date=timezone.now() + timedelta(days=1),
    )
    
    # Generate meeting link
    service = GoToMeetingService()
    meeting = service.create_meeting_for_session(session)
    
    session.refresh_from_db()
    assert session.meeting_url is not None
    assert session.meeting_id is not None
```

**Manual Testing Checklist:**
- [ ] Staff can schedule session
- [ ] GoToMeeting link generated
- [ ] Calendar invite sent to client
- [ ] Client receives email with link
- [ ] Click link opens GoToMeeting
- [ ] Session recorded (if enabled)
- [ ] Recording stored in system
- [ ] Session notes created
- [ ] Positions approved in session skip batch

---

#### **Test Suite 4.2: Notifications**

**Component:** Email/SMS notification system

**Unit Tests:**
```python
@pytest.mark.django_db
def test_batch_approval_email(pending_batch):
    """Test batch approval notification email"""
    service = NotificationService()
    service.send_batch_approval_notification(pending_batch)
    
    from django.core import mail
    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert pending_batch.managed_account.client.email in email.to
    assert 'batch approval' in email.subject.lower()
    assert pending_batch.batch_number in email.body

@pytest.mark.django_db
def test_batch_reminder_12_hours():
    """Test reminder sent 12 hours before deadline"""
    batch = create_batch(
        approval_deadline=timezone.now() + timedelta(hours=12)
    )
    
    # Run reminder task
    service = NotificationService()
    service.send_batch_reminders()
    
    from django.core import mail
    assert len(mail.outbox) == 1
    assert 'reminder' in mail.outbox[0].subject.lower()

@pytest.mark.django_db
def test_timeout_notification():
    """Test notification sent when batch times out"""
    batch = create_batch(
        status='expired',
        approval_deadline=timezone.now() - timedelta(hours=1)
    )
    
    service = NotificationService()
    service.send_timeout_notification(batch)
    
    from django.core import mail
    assert len(mail.outbox) == 1
    assert 'expired' in mail.outbox[0].subject.lower()
```

**Manual Testing Checklist:**
- [ ] Application submitted → email sent
- [ ] Application approved → email sent
- [ ] Batch created → email sent
- [ ] Batch reminder at 12 hours
- [ ] Batch timeout → email sent
- [ ] Position executed → email sent
- [ ] SMS notifications work (if configured)

---

## **🔄 END-TO-END TESTING**

### **Complete User Journey Tests**

#### **Journey 1: New Conservative Client**
```
Test: Conservative investor → Consultative tier → Session approval
Steps:
1. Register as new user → Select "Investor" category
2. Complete risk assessment → Score 25 (Conservative)
3. Apply for managed trading → Select Consultative tier
4. Review and sign 4 contracts
5. Wait for staff approval (auto-approved)
6. Receive welcome email with account number
7. Schedule first session via calendar
8. Attend GoToMeeting session
9. Manager proposes AAPL trade in session
10. Client approves verbally → Manager enters position
11. Position marked "Session Approved" → No batch needed
12. Position executes immediately
13. Client sees position in portal

Expected: ✅ All steps complete, position live
```

#### **Journey 2: Moderate Client with Batch Approval**
```
Test: Moderate investor → Professional tier → Batch approval
Steps:
1-6. Same as Journey 1 (through account approval)
7. Manager identifies 3 trades Mon-Fri
8. Friday: Batch created with 3 positions
9. Client receives email notification
10. Client clicks link to batch approval page
11. Reviews all 3 positions
12. Clicks "Approve All"
13. Signs approval
14. Receives confirmation email
15. All 3 positions execute
16. Portfolio updated

Expected: ✅ All positions approved and executed
```

#### **Journey 3: Batch Timeout Scenario**
```
Test: Client doesn't respond → 24-hour timeout
Steps:
1-8. Same as Journey 2 (through batch creation)
9. Client receives email but doesn't respond
10. 12 hours later: Reminder email sent
11. Still no response
12. 24 hours after batch creation: Timeout triggered
13. Batch status → "Expired"
14. All positions → "Rejected"
15. Client receives timeout notification
16. Capital remains available for next week

Expected: ✅ Positions rejected, no execution
```

---

## **📊 TESTING METRICS**

### **Success Criteria**

| Component | Target Coverage | Current | Status |
|-----------|----------------|---------|--------|
| Models | 90% | TBD | 🔄 Pending |
| Forms | 85% | TBD | 🔄 Pending |
| Views | 80% | TBD | 🔄 Pending |
| Services | 90% | TBD | 🔄 Pending |
| Templates | Manual 100% | TBD | 🔄 Pending |
| End-to-End | 100% | TBD | 🔄 Pending |

### **Pre-Deployment Checklist**

**Critical (Must Pass):**
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] 3 complete end-to-end journeys tested manually
- [ ] Batch timeout tested and verified
- [ ] Email notifications work
- [ ] Contract signatures save correctly
- [ ] Auto-approval rules work
- [ ] Manual approval workflow works
- [ ] Client approval interface works
- [ ] 24-hour timeout enforced

**Important (Should Pass):**
- [ ] GoToMeeting integration works
- [ ] SMS notifications work (if configured)
- [ ] Session pre-approval works
- [ ] Reminder emails send at 12 hours
- [ ] PDF generation works
- [ ] All admin interfaces functional

**Nice to Have:**
- [ ] Performance test (100 concurrent users)
- [ ] Load test (1000 applications)
- [ ] Mobile responsive testing
- [ ] Cross-browser testing

---

## **🚀 TESTING SCHEDULE**

### **Week 1: Development + Unit Tests**
- Mon-Tue: Build Phase 1 + Unit tests
- Wed-Thu: Build Phase 2 + Unit tests
- Fri: Build Phase 3 + Unit tests

### **Week 2: Integration + E2E**
- Mon: Integration tests for onboarding
- Tue: Integration tests for approval
- Wed: Integration tests for batch
- Thu: End-to-end testing (3 journeys)
- Fri: Bug fixes + retest

### **Week 3: UAT + Deployment**
- Mon-Wed: User acceptance testing (real users)
- Thu: Final fixes
- Fri: Deploy to production

---

## **✅ SUMMARY**

**Total Test Cases:** ~80 automated + ~40 manual checks  
**Estimated Testing Time:** 40 hours  
**Critical Path:** Batch approval + timeout  
**Highest Risk:** Auto-approval rules  

**Philosophy:** Test everything before deploying - Get it right the first time! 🎯

