"""
Phase 6: Client Onboarding Views
Risk assessment, application, and contract signing
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from ...models import (
    InvestorRiskProfile,
    ManagedTradingApplication,
    ManagedTradingContract,
    ManagedTradingAccount
)
from ...forms_onboarding import (
    RiskToleranceQuestionnaireForm,
    ManagedTradingApplicationForm,
    ContractReviewForm,
    ContractSignatureForm
)
from ...services.application_approval_service import ApplicationReviewService


# Helper function to check if user is staff
def is_staff(user):
    return user.is_staff


@login_required
def risk_assessment_view(request):
    """Step 1: Risk tolerance questionnaire"""
    # Check if user already has a current risk profile
    try:
        existing_profile = InvestorRiskProfile.objects.get(
            user=request.user,
            is_current=True
        )
        if not existing_profile.is_expired:
            messages.info(request, "You already have a current risk assessment. You can proceed to application.")
            return redirect('investing:managed_trading_apply')
    except InvestorRiskProfile.DoesNotExist:
        existing_profile = None
    
    if request.method == 'POST':
        form = RiskToleranceQuestionnaireForm(request.POST)
        if form.is_valid():
            # Calculate results
            risk_score = form.calculate_risk_score()
            risk_category = form.get_risk_category()
            recommended_tiers = form.get_recommended_tiers()
            
            # Save risk profile
            # Mark old profiles as not current
            InvestorRiskProfile.objects.filter(user=request.user).update(is_current=False)
            
            risk_profile = InvestorRiskProfile.objects.create(
                user=request.user,
                questionnaire_data=form.cleaned_data,
                risk_score=risk_score,
                risk_category=risk_category,
                is_current=True
            )
            
            messages.success(
                request,
                f"Risk assessment complete! You scored {risk_score}/100 ({risk_category}). "
                f"Recommended tiers: {', '.join(recommended_tiers)}"
            )
            
            return redirect('investing:managed_trading_apply')
    else:
        form = RiskToleranceQuestionnaireForm()
    
    context = {
        'form': form,
        'existing_profile': existing_profile,
    }
    return render(request, 'investing/onboarding/risk_assessment.html', context)


@login_required
def managed_trading_apply_view(request):
    """Step 2: Managed trading application"""
    # Check if user has risk profile
    try:
        risk_profile = InvestorRiskProfile.objects.get(
            user=request.user,
            is_current=True
        )
    except InvestorRiskProfile.DoesNotExist:
        messages.error(request, "Please complete the risk assessment first.")
        return redirect('investing:risk_assessment')
    
    # Check for existing pending application
    existing_application = ManagedTradingApplication.objects.filter(
        user=request.user,
        status='pending'
    ).first()
    
    if existing_application:
        messages.info(request, "You already have a pending application.")
        return redirect('investing:application_detail', application_id=existing_application.id)
    
    if request.method == 'POST':
        form = ManagedTradingApplicationForm(
            request.POST,
            user=request.user,
            risk_profile=risk_profile
        )
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.risk_profile = risk_profile
            application.save()
            
            messages.success(request, "Application submitted successfully! Please review and sign contracts.")
            return redirect('investing:contract_review', application_id=application.id)
    else:
        form = ManagedTradingApplicationForm(
            user=request.user,
            risk_profile=risk_profile
        )
    
    # Get tier configurations from database
    from investing.models import FeeTierConfiguration
    tier_configs = FeeTierConfiguration.objects.filter(is_active=True).order_by('display_order', 'minimum_capital')
    
    context = {
        'form': form,
        'risk_profile': risk_profile,
        'tier_configs': tier_configs,  # Pass database configs to template
        'preview_tiers': ManagedTradingAccount.PREVIEW_ONLY_TIERS,
    }
    return render(request, 'investing/onboarding/application.html', context)


@login_required
def application_detail_view(request, application_id):
    """View application details"""
    application = get_object_or_404(
        ManagedTradingApplication,
        id=application_id,
        user=request.user
    )
    
    context = {
        'application': application,
        'contracts': application.contracts.all(),
    }
    return render(request, 'investing/onboarding/application_detail.html', context)


@login_required
def contract_review_view(request, application_id):
    """Step 3: Review and sign contracts"""
    application = get_object_or_404(
        ManagedTradingApplication,
        id=application_id,
        user=request.user
    )
    
    # Generate contracts if not already generated
    if not application.contracts_generated:
        generate_contracts(application)
        application.contracts_generated = True
        application.save()
    
    contracts = application.contracts.all().order_by('contract_type')
    
    context = {
        'application': application,
        'contracts': contracts,
        'all_signed': application.all_contracts_signed,
    }
    return render(request, 'investing/onboarding/contract_review.html', context)


@login_required
@require_http_methods(["POST"])
def sign_contract_view(request, contract_id):
    """Sign a single contract (AJAX)"""
    contract = get_object_or_404(ManagedTradingContract, id=contract_id)
    
    # Verify user owns this contract
    if contract.application and contract.application.user != request.user:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
    
    form = ContractSignatureForm(request.POST)
    if form.is_valid():
        signature_data = form.cleaned_data['signature_data']
        ip_address = request.META.get('REMOTE_ADDR')
        
        contract.sign(signature_data, ip_address)
        
        # Check if all contracts are signed
        application = contract.application
        all_signed = not application.contracts.filter(is_signed=False).exists()
        
        if all_signed:
            # Check for auto-approval
            approval_service = ApplicationReviewService()
            can_auto_approve, reason = approval_service.check_auto_approval(application)
            
            if can_auto_approve:
                # Auto-approve immediately
                result = approval_service.approve_application(
                    application,
                    approved_by=None,
                    auto_approved=True
                )
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Contract signed! Your application has been automatically approved!',
                    'all_signed': True,
                    'auto_approved': True,
                    'account_number': result['account'].account_number if result['status'] == 'success' else None,
                    'redirect_url': '/investing/managed/portal/'
                })
        
        return JsonResponse({
            'status': 'success',
            'message': 'Contract signed successfully',
            'all_signed': all_signed,
            'auto_approved': False
        })
    else:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid signature data'
        }, status=400)


# ============================================================================
# STAFF VIEWS - Application Review
# ============================================================================

@user_passes_test(is_staff)
def pending_applications_view(request):
    """Staff view: Pending applications queue"""
    approval_service = ApplicationReviewService()
    pending = approval_service.get_pending_applications()
    
    # Get summary for each application
    applications_data = []
    for app in pending:
        summary = approval_service.get_application_summary(app)
        applications_data.append(summary)
    
    context = {
        'applications': applications_data,
        'total_pending': len(applications_data),
    }
    return render(request, 'investing/onboarding/staff/pending_applications.html', context)


@user_passes_test(is_staff)
def review_application_view(request, application_id):
    """Staff view: Review single application"""
    application = get_object_or_404(ManagedTradingApplication, id=application_id)
    approval_service = ApplicationReviewService()
    summary = approval_service.get_application_summary(application)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            result = approval_service.approve_application(
                application,
                approved_by=request.user,
                auto_approved=False
            )
            
            if result['status'] == 'success':
                messages.success(
                    request,
                    f"Application approved! Account {result['account'].account_number} created."
                )
                return redirect('investing:pending_applications')
            else:
                messages.error(request, result['message'])
        
        elif action == 'reject':
            reason = request.POST.get('rejection_reason')
            if reason:
                result = approval_service.reject_application(
                    application,
                    rejected_by=request.user,
                    reason=reason
                )
                messages.success(request, "Application rejected")
                return redirect('investing:pending_applications')
            else:
                messages.error(request, "Please provide a rejection reason")
    
    context = {
        'application': application,
        'summary': summary,
        'contracts': application.contracts.all(),
    }
    return render(request, 'investing/onboarding/staff/review_application.html', context)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_contracts(application):
    """Generate all 4 required contracts for an application"""
    contracts_to_generate = [
        {
            'type': 'ima',
            'title': 'Investment Management Agreement',
            'template': 'contracts/ima_template.html'
        },
        {
            'type': 'risk_disclosure',
            'title': 'Options Trading Risk Disclosure',
            'template': 'contracts/risk_disclosure_template.html'
        },
        {
            'type': 'fee_agreement',
            'title': 'Fee Schedule Agreement',
            'template': 'contracts/fee_agreement_template.html'
        },
        {
            'type': 'terms',
            'title': 'Terms of Service',
            'template': 'contracts/terms_template.html'
        },
    ]
    
    for contract_data in contracts_to_generate:
        # Check if contract already exists
        existing = application.contracts.filter(contract_type=contract_data['type']).first()
        if not existing:
            # Generate contract text (placeholder for now)
            contract_text = generate_contract_text(
                contract_data['type'],
                application
            )
            
            ManagedTradingContract.objects.create(
                application=application,
                contract_type=contract_data['type'],
                title=contract_data['title'],
                contract_text=contract_text
            )


def generate_contract_text(contract_type, application):
    """
    Generate contract text based on type and application details
    This is a placeholder - in production, use templates or PDF generation
    """
    base_template = f"""
<h1>{get_contract_title(contract_type)}</h1>

<p><strong>Date:</strong> {timezone.now().strftime('%B %d, %Y')}</p>

<p><strong>Client:</strong> {application.user.get_full_name()}</p>
<p><strong>Account Type:</strong> {application.get_fee_tier_display()}</p>
<p><strong>Initial Capital:</strong> ${application.initial_capital:,.2f}</p>

{get_contract_body(contract_type, application)}

<p><strong>By signing below, you acknowledge that you have read, understood, and agree to all terms and conditions.</strong></p>
    """
    return base_template


def get_contract_title(contract_type):
    """Get contract title by type"""
    titles = {
        'ima': 'Investment Management Agreement',
        'risk_disclosure': 'Options Trading Risk Disclosure',
        'fee_agreement': 'Fee Schedule Agreement',
        'terms': 'Terms of Service'
    }
    return titles.get(contract_type, 'Contract')


def get_contract_body(contract_type, application):
    """Get contract body by type"""
    if contract_type == 'ima':
        return f"""
<h2>1. Services</h2>
<p>CODA agrees to provide managed options trading services for your account.</p>

<h2>2. Fee Structure</h2>
<p>You have selected the <strong>{application.get_fee_tier_display()}</strong> tier.</p>

<h2>3. Investment Authority</h2>
<p>You grant CODA discretionary trading authority over your account.</p>

<h2>4. Risk Acknowledgment</h2>
<p>You acknowledge that options trading involves substantial risk.</p>
        """
    elif contract_type == 'risk_disclosure':
        return """
<h2>Options Trading Risks</h2>
<p>Options trading involves substantial risk and is not suitable for all investors.</p>
<p>You may lose your entire investment.</p>
<p>Past performance does not guarantee future results.</p>
        """
    elif contract_type == 'fee_agreement':
        tier_fees = {
            'balanced': '$249/mo management + 12% performance (6% hurdle)',
            'elite': '$399/mo management + 18% performance (5% hurdle, coming soon)',
            'consultative': '$420/mo legacy sleeve + 10% performance bonus',
            'custom': 'Custom fee schedule (see signed rider)',
            'starter': '10% profit share (legacy)',
            'professional': '15% profit share (legacy)',
            'premium': '20% profit share + priority support (legacy)',
            'co_invest': '30% profit share + CODA co-investment (legacy)',
        }
        fee_structure = tier_fees.get(application.fee_tier, '10% profit share')
        
        return f"""
<h2>Fee Structure</h2>
<p><strong>Tier:</strong> {application.get_fee_tier_display()}</p>
<p><strong>Fees:</strong> {fee_structure}</p>
<p>Fees are calculated monthly on realized profits only.</p>
        """
    elif contract_type == 'terms':
        return """
<h2>Terms of Service</h2>
<p>1. Account Management: CODA will manage your account professionally.</p>
<p>2. Reporting: You will receive monthly performance reports.</p>
<p>3. Termination: Either party may terminate with 30 days notice.</p>
<p>4. Confidentiality: All account information is confidential.</p>
        """
    else:
        return "<p>Standard contract terms apply.</p>"

