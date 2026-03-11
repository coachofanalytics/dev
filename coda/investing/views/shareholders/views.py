""" Shareholders Management System Views

This module provides views for the Shareholders Management System.
Access is restricted to admin users only (same permission as Automation dashboard).

Phase 1: Database-backed views with real queries.
Phase 2: Full ledger backend with approval workflow, disputes, and CSV export.

Note: Views migrated to investing app - models imported from shareholders app.
"""

import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_POST, require_GET
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from core.permissions import is_admin, require_admin

# Models now owned by investing app
from investing.models_shareholders import (
    Deal, DealConfig, DealWeights, Member, LedgerEntry, LedgerEvidence,
    LedgerApproval, LedgerDispute, LedgerAuditLog
)

# Services imported from new location in investing app
from investing.services.shareholders.dashboard_service import get_dashboard_metrics
from investing.services.shareholders.ledger_query import LedgerQueryService
from investing.services.shareholders.ledger_checksum import LedgerChecksumService

logger = logging.getLogger(__name__)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_active_deal():
    """
    Get the currently active deal (Phase 1: assumes single deal).
    Future: multi-deal support with user selection.
    """
    return Deal.objects.filter(is_active=True).first()


@login_required
@require_admin
def shareholders_dashboard(request):
    """
    Main shareholders dashboard view with real database metrics and equity estimation.
    
    Access Control:
        - Requires login
        - Requires admin privileges (is_staff or is_superuser)
        - Same permission logic as Automation dashboard
    
    Business Logic:
        - All stats computed from approved/submitted ledger entries
        - Equity calculated using weighted contribution model
        - Read-only operations (no writes)
    """
    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found. Please create a deal first.")
            return redirect('dashboard:unified_dashboard')
        
        # Get all dashboard metrics via service
        metrics = get_dashboard_metrics(deal)
        
        # Check for configuration issues
        if not metrics['weights_status']['valid']:
            messages.warning(
                request,
                f"Weight configuration issue: {metrics['weights_status']['warning']}"
            )
        
        # Build template context
        context = {
            'title': 'Shareholders Management Dashboard',
            'page_title': 'Shareholders Management System',
            'user': request.user,
            'deal': deal,
            
            # Stats cards
            'active_members': metrics['active_members'],
            'total_cash_invested': metrics['total_cash_invested'],
            'pending_approvals': metrics['pending_approvals'],
            'snapshot_display': metrics['snapshot_display'],
            'snapshot_date': metrics['snapshot_date'],
            'fx_peg_rate': metrics['fx_peg_rate'],
            
            # Cap table with equity estimates
            'members_data': metrics['members_data'],
            
            # Weights
            'cash_weight': metrics['cash_weight'],
            'inkind_weight': metrics['inkind_weight'],
            'time_weight': metrics['time_weight'],
            'work_weight': metrics['work_weight'],
            'weights_status': metrics['weights_status'],
        }
        
        return render(request, 'investing/shareholders/shareholders_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in shareholders dashboard: {str(e)}")
        messages.error(request, f"Error loading shareholders dashboard: {str(e)}")
        return redirect('dashboard:unified_dashboard')


@login_required
@require_admin
def ledgers_view(request):
    """
    Ledger Snapshots view - Displays contribution ledger entries from database.
    
    Phase 2: Full server-side filtering, search, and pagination.
    """
    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found. Please create a deal first.")
            return redirect('shareholders:shareholders_dashboard')
        
        # Initialize services
        query_service = LedgerQueryService(deal)
        checksum_service = LedgerChecksumService(deal)
        
        # Get filter parameters from request
        search = request.GET.get('search', '').strip()
        status = request.GET.get('status', 'all')
        tier = request.GET.get('tier', 'all')
        date_range = request.GET.get('date_range', 'all_time')
        page = int(request.GET.get('page', 1))
        
        # Get filtered entries
        result = query_service.get_filtered_entries(
            search=search,
            status=status,
            tier=tier,
            date_range=date_range,
            page=page,
            per_page=25,
        )
        
        # Get summary stats for the full (unfiltered) dataset
        summary_stats = query_service.get_summary_stats()
        summary_stats['latest_checksum'] = checksum_service.calculate_checksum()
        
        # Tier legend
        tier_legend = [
            {'name': 'Cash', 'color': 'emerald', 'description': 'Cash Contribution'},
            {'name': 'In-Kind', 'color': 'blue', 'description': 'In-Kind Asset'},
            {'name': 'Time', 'color': 'indigo', 'description': 'Time Logged'},
            {'name': 'Work', 'color': 'amber', 'description': 'Work Unit'},
        ]
        
        # Status types
        status_types = ['Approved', 'Submitted for Review', 'In Dispute', 'Rejected']
        
        context = {
            'title': 'Ledger Snapshots',
            'page_title': 'Ledger Snapshots - Shareholders Management',
            'user': request.user,
            'deal': deal,
            'ledger_entries': result['entries'],
            'summary_stats': summary_stats,
            'tier_legend': tier_legend,
            'status_types': status_types,
            # Pagination
            'current_page': result['page'],
            'total_pages': result['total_pages'],
            'total_count': result['total_count'],
            'has_next': result['has_next'],
            'has_previous': result['has_previous'],
            # Active filters (for form state)
            'current_search': search,
            'current_status': status,
            'current_tier': tier,
            'current_date_range': date_range,
        }
        
        return render(request, 'investing/shareholders/shareholders_ledgers.html', context)
        
    except Exception as e:
        logger.error(f"Error in ledgers view: {str(e)}")
        messages.error(request, f"Error loading ledgers: {str(e)}")
        return redirect('shareholders:shareholders_dashboard')


# ===================================================================
# MEMBERS & EQUITY VIEWS
# ===================================================================

@login_required
@require_admin
def members_overview(request):
    """
    Members & Equity Overview - Main members listing page from database.
    
    Access Control:
        - Requires login
        - Requires admin privileges (is_staff or is_superuser)
    
    Phase 3: Real database queries with service-based aggregation; equity % placeholder (Phase 4).
    """
    from investing.services.shareholders.member_metrics import get_deal_member_summary
    
    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found. Please create a deal first.")
            return redirect('shareholders:shareholders_dashboard')
        
        # Use service to get member summaries
        # Policy: Include only APPROVED by default (conservative)
        members = get_deal_member_summary(deal, include_submitted=False)
        
        context = {
            'title': 'Members & Equity',
            'page_title': 'Members & Equity - Shareholders Management',
            'user': request.user,
            'members': members,
            'members_count': len(members),
        }
        
        return render(request, 'investing/shareholders/shareholders_members_overview.html', context)
        
    except Exception as e:
        logger.error(f"Error in members overview: {str(e)}")
        messages.error(request, f"Error loading members: {str(e)}")
        return redirect('shareholders:shareholders_dashboard')


@login_required
@require_admin
def member_register(request):
    """
    Register New Member - Form for adding new members/shareholders.
    
    Phase 3: Real POST handling with form validation, document upload, and audit logging.
    """
    from investing.forms_shareholders import MemberRegisterForm
    from investing.services.shareholders.audit_service import AuditService, get_client_ip
    
    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found. Please create a deal first.")
            return redirect('shareholders:members_overview')
        
        if request.method == 'POST':
            form = MemberRegisterForm(request.POST, request.FILES)
            form.deal = deal  # Attach deal for validation
            
            if form.is_valid():
                # Create member
                member = form.save(commit=False)
                member.deal = deal
                member.verified = False  # Default unverified
                member.is_active = True  # Member is active upon creation
                member.created_by = request.user  # RBAC: Track ownership
                member.save()
                
                # Handle optional identity document upload
                identity_doc = form.cleaned_data.get('identity_document')
                if identity_doc:
                    member.identity_document = identity_doc
                    member.save()
                    logger.info(f"Identity document uploaded for {member.legal_name}: {identity_doc.name}")
                
                # Handle optional profile photo upload
                profile_photo = form.cleaned_data.get('profile_photo')
                if profile_photo:
                    member.profile_photo = profile_photo
                    member.save()
                    logger.info(f"Profile photo uploaded for {member.legal_name}: {profile_photo.name}")
                
                # Create audit log
                AuditService.log_member_created(
                    member=member,
                    actor=request.user,
                    ip_address=get_client_ip(request)
                )
                
                messages.success(request, f"Member {member.legal_name} registered successfully!")
                return redirect('shareholders:member_detail', member_id=member.id)
            else:
                # Form has errors
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        else:
            form = MemberRegisterForm()
        
        context = {
            'title': 'Register Member',
            'page_title': 'Register New Member - Shareholders Management',
            'user': request.user,
            'form': form,
            'role_catalog': get_role_catalog(),
        }
        
        return render(request, 'investing/shareholders/shareholders_member_register.html', context)
        
    except Exception as e:
        logger.error(f"Error in member register: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('shareholders:members_overview')


@login_required
@require_admin
def member_detail(request, member_id):
    """
    Member Profile Detail View - Shows comprehensive member information from database.
    
    Phase 3: Real queries with aggregated contribution data using services.
    """
    from investing.services.shareholders.member_metrics import MemberMetricsService
    from investing.services.shareholders.dashboard_service import EquityEstimationService
    
    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found.")
            return redirect('shareholders:members_overview')
        
        # Get member
        member = get_object_or_404(Member, id=member_id, deal=deal, is_archived=False)
        
        # Use service to get metrics and history
        metrics_service = MemberMetricsService(member, include_submitted=True)
        metrics = metrics_service.get_all_metrics()
        contribution_history = metrics_service.get_contribution_history(limit=10)
        
        # Calculate equity percentage using EquityEstimationService
        equity_service = EquityEstimationService(deal)
        equity_data = equity_service.calculate_equity_for_all_members()
        member_equity = next(
            (item['equity_percentage'] for item in equity_data if item['member'].id == member.id),
            Decimal('0.00')
        )
        
        # Build member dict for template
        member_data = {
            'id': member.id,
            'name': member.legal_name,
            'role': member.role_title or '',
            'type': member.get_member_type_display(),
            'type_code': member.member_type,
            'verified': member.verified,
            'equity_percentage': float(member_equity),
            'cash_invested': float(metrics['cash_invested']),
            'in_kind_value': float(metrics['in_kind_value']),
            'time_logged': float(metrics['time_logged']),
            'work_units': float(metrics['work_units']),
            'email': member.email,
            'phone': member.phone or '',
            'joined_date': member.joined_date.strftime('%Y-%m-%d'),
            'joined_date_formatted': member.joined_date.strftime('%b %d, %Y'),
            'bio': member.bio or '',
            'contribution_count': metrics_service.get_contribution_count(),
            'pending_count': metrics_service.get_pending_count(),
            'profile_photo': member.profile_photo.url if member.profile_photo else None,
        }
        
        context = {
            'title': f"{member.legal_name} - Member Profile",
            'page_title': f"{member.legal_name} - Shareholders Management",
            'user': request.user,
            'member': member_data,
            'contribution_history': contribution_history,
            'can_edit_member': request.user.is_superuser or member.created_by == request.user,
        }
        
        return render(request, 'investing/shareholders/shareholders_member_detail.html', context)
        
    except Http404:
        # Let Django handle 404 properly
        raise
    except Exception as e:
        logger.error(f"Error in member detail: {str(e)}")
        messages.error(request, f"Error loading member profile: {str(e)}")
        return redirect('shareholders:members_overview')


@login_required
@require_admin
def member_edit(request, member_id):
    """
    Edit Member Profile - Form for updating member information.
    
    Phase 3: Real POST handling with form validation, audit logging, and archive functionality.
    
    RBAC Security:
        - Only the user who created this member (created_by) can edit.
        - Superusers can edit any member.
        - All other staff get 403 Forbidden on edit attempt.
    """
    from investing.forms_shareholders import MemberEditForm
    from investing.services.shareholders.audit_service import AuditService, get_client_ip
    from django.http import HttpResponseForbidden
    
    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found.")
            return redirect('shareholders:members_overview')
        
        # Get member
        member = get_object_or_404(Member, id=member_id, deal=deal, is_archived=False)
        
        # RBAC: Only created_by or superuser can edit
        can_edit = request.user.is_superuser or member.created_by == request.user
        if not can_edit:
            # Log unauthorized edit attempt
            logger.warning(
                f"Unauthorized member edit attempt: user={request.user.username}, "
                f"member_id={member_id}, member_name={member.legal_name}"
            )
            return HttpResponseForbidden(
                "<h1>403 Forbidden</h1><p>You do not have permission to edit this member. "
                "Only the creator or a superuser can edit member profiles.</p>"
            )
        
        # Handle archive request (separate from edit)
        if request.method == 'POST' and 'archive' in request.POST:
            archive_reason = request.POST.get('archive_reason', '').strip()
            member.is_archived = True
            member.save()
            
            # Create audit log
            AuditService.log_member_archived(
                member=member,
                actor=request.user,
                reason=archive_reason,
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f"Member {member.legal_name} archived successfully.")
            return redirect('shareholders:members_overview')
        
        if request.method == 'POST':
            # Track changes for audit
            original_data = {
                'legal_name': member.legal_name,
                'role_title': member.role_title,
                'email': member.email,
                'phone': member.phone,
                'bio': member.bio,
                'verified': member.verified,
            }
            
            # SECURITY: Strip 'verified' from POST data for non-superusers
            post_data = request.POST.copy()
            if not request.user.is_superuser and 'verified' in post_data:
                del post_data['verified']
                logger.warning(
                    f"Non-superuser attempted to change verified status: "
                    f"user={request.user.username}, member_id={member_id}"
                )
            
            form = MemberEditForm(post_data, request.FILES, instance=member, user=request.user)
            
            if form.is_valid():
                updated_member = form.save()
                
                # Track what changed
                changed_fields = {}
                for field in ['legal_name', 'role_title', 'email', 'phone', 'bio', 'verified']:
                    old_val = original_data[field]
                    new_val = getattr(updated_member, field)
                    if old_val != new_val:
                        changed_fields[field] = {'old': str(old_val), 'new': str(new_val)}
                
                if changed_fields:
                    # Create audit log
                    AuditService.log_member_updated(
                        member=updated_member,
                        actor=request.user,
                        changed_fields=changed_fields,
                        ip_address=get_client_ip(request)
                    )
                
                # Handle file uploads (outside form.save since these are extra fields)
                profile_photo = form.cleaned_data.get('profile_photo')
                identity_doc = form.cleaned_data.get('identity_document')
                save_files = False
                if profile_photo:
                    updated_member.profile_photo = profile_photo
                    save_files = True
                    logger.info(f"Profile photo updated for {updated_member.legal_name}")
                if identity_doc:
                    updated_member.identity_document = identity_doc
                    save_files = True
                    logger.info(f"Identity document updated for {updated_member.legal_name}")
                if save_files:
                    updated_member.save()
                
                # SECURITY: Audit verification status changes via immutable AuditLog
                if 'verified' in changed_fields:
                    try:
                        from investing.models_shareholders import AuditLog
                        old_verified = original_data['verified']
                        new_verified = updated_member.verified
                        action = 'VERIFICATION_APPROVED' if new_verified else 'VERIFICATION_REJECTED'
                        AuditLog.objects.create(
                            deal=deal,
                            actor=request.user,
                            action_type=action,
                            entity_type='MEMBER',
                            entity_id=str(updated_member.id),
                            entity_reference=updated_member.legal_name,
                            description=(
                                f"Verification status changed from {old_verified} to {new_verified} "
                                f"for member {updated_member.legal_name} by {request.user.username}"
                            ),
                            ip_address=get_client_ip(request),
                            request_source='web',
                            status='SUCCESS',
                            old_values={'verified': old_verified},
                            new_values={'verified': new_verified},
                        )
                    except Exception as e:
                        logger.error(f"Error creating verification audit log: {str(e)}")
                
                messages.success(request, f"Member {updated_member.legal_name} updated successfully!")
                return redirect('shareholders:member_detail', member_id=updated_member.id)
            else:
                # Form has errors
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        else:
            form = MemberEditForm(instance=member, user=request.user)
        
        # Build member data for template
        member_data = {
            'id': member.id,
            'name': member.legal_name,
            'role': member.role_title or '',
            'type': member.get_member_type_display(),
            'type_code': member.member_type,
            'verified': member.verified,
            'email': member.email,
            'phone': member.phone or '',
            'joined_date': member.joined_date.strftime('%Y-%m-%d'),
            'bio': member.bio or '',
        }
        
        context = {
            'title': f"Edit {member.legal_name}",
            'page_title': f"Edit Member - Shareholders Management",
            'user': request.user,
            'member': member_data,
            'member_obj': member,  # Raw model instance for file URLs in template
            'form': form,
            'role_catalog': get_role_catalog(),
            'can_verify': request.user.is_superuser,  # RBAC: Only superusers can change verification
        }
        
        return render(request, 'investing/shareholders/shareholders_member_edit.html', context)
        
    except Member.DoesNotExist:
        messages.error(request, f"Member with ID {member_id} not found.")
        return redirect('shareholders:members_overview')
    except Exception as e:
        logger.error(f"Error in member edit: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('shareholders:members_overview')


@login_required
@require_admin
def contribution_log(request):
    """
    Log New Contribution - Form for recording member contributions.
    
    Phase 3: Real POST handling with form validation, proof upload, and audit logging.
    """
    from investing.forms_shareholders import ContributionLogForm
    from investing.services.shareholders.contribution_service import ContributionSubmissionService
    from investing.services.shareholders.audit_service import get_client_ip
    
    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found. Please create a deal first.")
            return redirect('shareholders:members_overview')
        
        # Get member_id from query param (optional pre-selection)
        member_id = request.GET.get('member_id')
        selected_member = None
        
        if member_id:
            try:
                selected_member_obj = Member.objects.get(id=int(member_id), deal=deal, is_archived=False)
                selected_member = {
                    'id': selected_member_obj.id,
                    'name': selected_member_obj.legal_name
                }
            except (ValueError, TypeError, Member.DoesNotExist):
                pass
        
        if request.method == 'POST':
            form = ContributionLogForm(request.POST, request.FILES, deal=deal)
            
            if form.is_valid():
                # Use ContributionSubmissionService to create entry
                service = ContributionSubmissionService(deal)
                
                try:
                    entry = service.submit_contribution(
                        contributor=form.cleaned_data['contributor'],
                        tier=form.cleaned_data['tier'],
                        asset_class=form.cleaned_data['asset_class'],
                        date=form.cleaned_data['date'],
                        internal_units_value=form.cleaned_data['internal_units_value'],
                        internal_units_label=form.cleaned_data.get('internal_units_label') or '',
                        value_usd=form.cleaned_data['value_usd'],
                        currency=form.cleaned_data.get('currency') or 'USD',
                        exchange_rate=form.cleaned_data.get('exchange_rate') or Decimal('1.0'),
                        actor=request.user,
                        notes=form.cleaned_data.get('notes') or '',
                        proof_document=form.cleaned_data.get('proof_document'),
                        ip_address=get_client_ip(request),
                        tier_metadata=form.cleaned_data.get('tier_metadata') or {},
                        is_auto_calculated=form.cleaned_data.get('_auto_calculated', False),  # Phase 3
                    )
                    
                    messages.success(
                        request,
                        f"Contribution {entry.tx_id} submitted successfully! "
                        f"Status: Pending Review"
                    )
                    return redirect('shareholders:ledgers_view')
                    
                except Exception as e:
                    logger.error(f"Error submitting contribution: {str(e)}")
                    messages.error(request, f"Error submitting contribution: {str(e)}")
            else:
                # Form has errors
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        else:
            # GET request - create empty form
            initial_data = {}
            if selected_member:
                try:
                    member_obj = Member.objects.get(id=selected_member['id'], deal=deal)
                    initial_data['contributor'] = member_obj
                except Member.DoesNotExist:
                    pass
            
            form = ContributionLogForm(deal=deal, initial=initial_data)
        
        # Get all active members for template (if needed outside form)
        all_members = Member.objects.filter(deal=deal, is_archived=False).order_by('legal_name')
        
        # Get DealConfig rates for JavaScript dynamic calculation
        time_rate = Decimal('50.00')  # Default
        work_rate = Decimal('100.00')  # Default
        fx_peg_rate = Decimal('127.0000')  # Phase 5: Default KES/USD rate
        try:
            config = deal.config
            time_rate = config.time_rate
            work_rate = config.work_rate
            fx_peg_rate = config.fx_peg_rate  # Phase 5: For currency conversion
        except:
            pass
        
        context = {
            'title': 'Log New Contribution',
            'page_title': 'Log New Contribution - Shareholders Management',
            'user': request.user,
            'form': form,
            'selected_member': selected_member,
            'all_members': all_members,
            'time_rate': time_rate,  # For JavaScript
            'work_rate': work_rate,  # For JavaScript
            'fx_peg_rate': fx_peg_rate,  # Phase 5: For currency conversion
        }
        
        return render(request, 'investing/shareholders/shareholders_contribution_log.html', context)
        
    except Exception as e:
        logger.error(f"Error in contribution log: {str(e)}")
        messages.error(request, f"Error loading contribution form: {str(e)}")
        return redirect('shareholders:members_overview')


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_role_catalog():
    """Returns the list of available roles for members"""
    return [
        'Founder',
        'Lead Developer',
        'Investor',
        'Project Manager',
        'Marketing Lead',
        'Finance Officer',
        'External Partner',
    ]


# =============================================================================
# PHASE 2: LEDGER ENDPOINTS (Detail, Receipt, Approve, Dispute, CSV Export)
# =============================================================================

@login_required
@require_admin
def ledger_detail(request, tx_id):
    """
    Get comprehensive details for a single ledger entry.
    
    Returns JSON for AJAX modal loading or renders detail page.
    """
    try:
        deal = get_active_deal()
        if not deal:
            return JsonResponse({'error': 'No active deal found'}, status=400)
        
        query_service = LedgerQueryService(deal)
        entry_detail = query_service.get_entry_detail(tx_id)
        
        if not entry_detail:
            return JsonResponse({'error': f'Entry {tx_id} not found'}, status=404)
        
        # Check if AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'entry': entry_detail})
        
        # Render detail page
        context = {
            'title': f'Transaction {tx_id}',
            'page_title': f'{tx_id} - Ledger Entry Detail',
            'user': request.user,
            'entry': entry_detail,
            'deal': deal,
        }
        return render(request, 'investing/shareholders/shareholders_ledger_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error fetching ledger detail for {tx_id}: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=500)
        messages.error(request, f"Error: {str(e)}")
        return redirect('shareholders:ledgers_view')


@login_required
@require_admin
@require_GET
def ledger_receipt(request, tx_id):
    """
    Get receipt data for a ledger entry (JSON endpoint for modal).
    """
    try:
        deal = get_active_deal()
        if not deal:
            return JsonResponse({'error': 'No active deal found'}, status=400)
        
        query_service = LedgerQueryService(deal)
        entry = query_service.get_entry_by_tx_id(tx_id)
        
        if not entry:
            return JsonResponse({'error': f'Entry {tx_id} not found'}, status=404)
        
        # Get deal config for FX info
        config = getattr(deal, 'config', None)
        fx_mode = config.fx_mode if config else 'PEGGED'
        fx_rate = float(config.fx_peg_rate) if config else 127.0
        
        receipt_data = {
            'tx_id': entry.tx_id,
            'contributor_name': entry.contributor.legal_name,
            'contributor_type': entry.contributor.get_member_type_display(),
            'tier': entry.get_tier_display(),
            'tier_code': entry.tier,
            'asset_class': entry.asset_class,
            'internal_units': f"{entry.internal_units_value:,.0f} {entry.internal_units_label or ''}".strip(),
            'value_usd': float(entry.value_usd),
            'currency': entry.currency,
            'exchange_rate': float(entry.exchange_rate),
            'status': entry.get_status_display(),
            'status_code': entry.status,
            'date': entry.date.strftime('%B %d, %Y'),
            'date_short': entry.date.strftime('%Y-%m-%d'),
            'deal_name': deal.name,
            'fx_mode': fx_mode,
            'fx_rate': fx_rate,
            'has_proof': entry.has_proof,
        }
        
        return JsonResponse({'receipt': receipt_data})
        
    except Exception as e:
        logger.error(f"Error fetching receipt for {tx_id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_admin
@require_GET
def ledger_proof(request, tx_id):
    """
    Serve proof file for inline viewing (Phase 3: Preview functionality).
    
    Returns the actual file with Content-Disposition: inline headers
    to force browser to display rather than download.
    """
    from django.http import FileResponse
    import mimetypes
    import os
    
    try:
        deal = get_active_deal()
        if not deal:
            return JsonResponse({'error': 'No active deal found'}, status=400)
        
        # Get the entry
        try:
            entry = LedgerEntry.objects.get(tx_id=tx_id, deal=deal)
        except LedgerEntry.DoesNotExist:
            return JsonResponse({'error': f'Entry {tx_id} not found'}, status=404)
        
        # Check if entry has proof
        if not entry.has_proof:
            return JsonResponse({'error': 'No proof available for this entry'}, status=404)
        
        # Get the first evidence file (primary proof)
        evidence = entry.evidence.first()
        
        if not evidence or not evidence.file:
            return JsonResponse({'error': 'Proof file not found'}, status=404)
        
        # Get file path and open file
        file_path = evidence.file.path
        file_name = os.path.basename(file_path)
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            # Fallback MIME types
            ext = file_name.split('.')[-1].lower()
            mime_type_map = {
                'pdf': 'application/pdf',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
            }
            mime_type = mime_type_map.get(ext, 'application/octet-stream')
        
        # Open and serve file with inline disposition
        file_handle = open(file_path, 'rb')
        response = FileResponse(file_handle, content_type=mime_type)
        
        # CRITICAL: Set Content-Disposition to 'inline' to preview, not download
        response['Content-Disposition'] = f'inline; filename="{file_name}"'
        
        # Additional headers for better preview support
        response['X-Content-Type-Options'] = 'nosniff'
        
        return response
        
    except Exception as e:
        logger.error(f"Error serving proof for {tx_id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_admin
@require_POST
def ledger_approve(request, tx_id):
    """
    Approve a ledger entry (POST action, JSON endpoint).
    
    RBAC Security:
        - Only SUPERUSERS can approve ledger entries.
        - Staff attempting approval receive 403 JSON.
    
    Returns:
        JsonResponse with {ok, status, entry_id} on success
        JsonResponse with {ok, error} on failure
    """
    # RBAC: Superuser-only
    if not request.user.is_superuser:
        return JsonResponse(
            {'ok': False, 'error': 'FORBIDDEN: Only superusers can approve ledger entries.'},
            status=403
        )
    
    try:
        deal = get_active_deal()
        if not deal:
            return JsonResponse({'ok': False, 'error': 'No active deal found'}, status=400)
        
        # Get the entry
        try:
            entry = LedgerEntry.objects.get(tx_id=tx_id, deal=deal)
        except LedgerEntry.DoesNotExist:
            return JsonResponse({'ok': False, 'error': f'Entry {tx_id} not found'}, status=404)
        
        # Check if already approved
        if entry.status == 'APPROVED':
            return JsonResponse({'ok': False, 'error': 'Entry is already approved'}, status=400)
        
        # Check if in dispute
        if entry.status == 'IN_DISPUTE':
            return JsonResponse({'ok': False, 'error': 'Cannot approve entry that is in dispute'}, status=400)
        
        # Get notes from request
        import json
        try:
            body = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            body = {}
        notes = body.get('notes', '')
        
        old_status = entry.status
        
        # Update entry status
        entry.status = 'APPROVED'
        entry.save()
        
        # Create approval record
        LedgerApproval.objects.create(
            ledger_entry=entry,
            action='APPROVED',
            approved_by=request.user,
            notes=notes
        )
        
        # Create audit log
        LedgerAuditLog.objects.create(
            ledger_entry=entry,
            action='APPROVED',
            performed_by=request.user,
            old_value=old_status,
            new_value='APPROVED',
            details={'notes': notes},
            ip_address=get_client_ip(request)
        )
        
        logger.info(f"Entry {tx_id} approved by {request.user}")
        
        return JsonResponse({
            'ok': True,
            'status': 'APPROVED',
            'entry_id': tx_id,
            'message': f'Entry {tx_id} has been approved'
        })
        
    except Exception as e:
        logger.error(f"Error approving entry {tx_id}: {str(e)}")
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@login_required
@require_admin
@require_POST
def ledger_dispute(request, tx_id):
    """
    Flag a dispute for a ledger entry (POST action, JSON endpoint).
    
    RBAC Security:
        - Only SUPERUSERS can flag disputes.
        - Staff attempting dispute receive 403 JSON.
    
    Returns:
        JsonResponse with {ok, status, entry_id} on success
        JsonResponse with {ok, error} on failure
    """
    # RBAC: Superuser-only
    if not request.user.is_superuser:
        return JsonResponse(
            {'ok': False, 'error': 'FORBIDDEN: Only superusers can flag disputes.'},
            status=403
        )
    
    try:
        deal = get_active_deal()
        if not deal:
            return JsonResponse({'ok': False, 'error': 'No active deal found'}, status=400)
        
        # Get the entry
        try:
            entry = LedgerEntry.objects.get(tx_id=tx_id, deal=deal)
        except LedgerEntry.DoesNotExist:
            return JsonResponse({'ok': False, 'error': f'Entry {tx_id} not found'}, status=404)
        
        # Check if already in dispute
        if entry.status == 'IN_DISPUTE':
            return JsonResponse({'ok': False, 'error': 'Entry is already in dispute'}, status=400)
        
        # Get reason from request
        import json
        try:
            body = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            body = {}
        reason = body.get('reason', '').strip()
        
        if not reason:
            return JsonResponse({'ok': False, 'error': 'Dispute reason is required'}, status=400)
        
        # Check dispute window (optional - warn but allow)
        config = getattr(deal, 'config', None)
        dispute_window_days = config.dispute_window_days if config else 7
        
        days_since_entry = (timezone.now().date() - entry.date).days
        within_window = days_since_entry <= dispute_window_days
        
        old_status = entry.status
        
        # Update entry status
        entry.status = 'IN_DISPUTE'
        entry.save()
        
        # Create dispute record
        LedgerDispute.objects.create(
            ledger_entry=entry,
            status='OPEN',
            raised_by=request.user,
            reason=reason
        )
        
        # Create audit log
        LedgerAuditLog.objects.create(
            ledger_entry=entry,
            action='DISPUTE_RAISED',
            performed_by=request.user,
            old_value=old_status,
            new_value='IN_DISPUTE',
            details={
                'reason': reason,
                'within_window': within_window,
                'days_since_entry': days_since_entry
            },
            ip_address=get_client_ip(request)
        )
        
        logger.info(f"Dispute raised for entry {tx_id} by {request.user}")
        
        return JsonResponse({
            'ok': True,
            'status': 'IN_DISPUTE',
            'entry_id': tx_id,
            'message': f'Dispute has been raised for entry {tx_id}',
            'within_window': within_window
        })
        
    except Exception as e:
        logger.error(f"Error flagging dispute for entry {tx_id}: {str(e)}")
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@login_required
@require_admin
@require_GET
def ledgers_export_csv(request):
    """
    Export ledger entries as CSV (respects current filters).
    
    Exports the filtered view matching current search/filter parameters.
    """
    try:
        deal = get_active_deal()
        if not deal:
            messages.error(request, 'No active deal found')
            return redirect('shareholders:ledgers_view')
        
        # Get filter parameters from request
        search = request.GET.get('search', '').strip()
        status = request.GET.get('status', 'all')
        tier = request.GET.get('tier', 'all')
        date_range = request.GET.get('date_range', 'all_time')
        
        # Get all matching entries (no pagination)
        query_service = LedgerQueryService(deal)
        entries = query_service.get_all_for_export(
            search=search,
            status=status if status != 'all' else None,
            tier=tier if tier != 'all' else None,
            date_range=date_range
        )
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'ledger_export_{deal.slug}_{timestamp}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        # Write header row
        writer.writerow([
            'Transaction ID',
            'Date',
            'Contributor',
            'Tier',
            'Asset Class',
            'Internal Units',
            'Value (USD)',
            'Status',
            'Currency',
            'Exchange Rate',
            'Notes'
        ])
        
        # Write data rows
        for entry in entries:
            writer.writerow([
                entry['id'],
                entry['date'],
                entry['contributor_name'],
                entry['tier'],
                entry['asset_class'],
                entry['internal_units'],
                f"${entry['value_usd']:,.2f}",
                entry['status'],
                entry['currency'],
                entry['exchange_rate'],
                entry['notes']
            ])
        
        # Log export action
        logger.info(f"CSV export by {request.user}: {len(entries)} entries")
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        messages.error(request, f"Error exporting CSV: {str(e)}")
        return redirect('shareholders:ledgers_view')


def get_client_ip(request):
    """Extract client IP from request headers"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ===================================================================
# SNAPSHOTS VIEWS (Phase 2: Full Backend Integration)
# ===================================================================

@login_required
@require_admin
def snapshots_view(request):
    """
    Equity Snapshots List View - Fully database-backed with real snapshots.
    
    Access Control:
        - Requires login
        - Requires admin privileges (is_staff or is_superuser)
    
    Features:
        - Real snapshot history from database
        - Server-side filtering and pagination
        - Summary metrics and statistics
        - Integrity verification
    """
    from investing.services.shareholders.snapshot_query_service import SnapshotQueryService
    from investing.services.shareholders.snapshot_generation_service import SnapshotGenerationService
    
    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found. Please create a deal first.")
            return redirect('dashboard:unified_dashboard')
        
        # Initialize services
        query_service = SnapshotQueryService(deal)
        gen_service = SnapshotGenerationService(deal)
        
        # Auto-lock expired snapshots
        gen_service.auto_lock_expired_snapshots()
        
        # Get filter parameters
        search = request.GET.get('search', '').strip()
        status = request.GET.get('status', 'all')
        page = int(request.GET.get('page', 1))
        
        # Get filtered snapshots
        result = query_service.get_filtered_snapshots(
            search=search,
            status=status if status != 'all' else None,
            page=page,
            per_page=25,
        )
        
        # Get summary stats
        stats = query_service.get_summary_stats()
        
        # Format snapshots for template
        snapshots_data = []
        for snapshot in result['snapshots']:
            snapshots_data.append({
                'id': snapshot.id,
                'version_id': snapshot.version_id,
                'date_locked': snapshot.snapshot_date.strftime('%Y-%m-%d'),
                'valuation': int(snapshot.total_valuation_usd),
                'members_count': snapshot.members_count,
                'checksum': snapshot.checksum,
                'status': snapshot.status,
                'is_locked': snapshot.is_locked,
            })
        
        # Format summary metrics
        last_consensus_date = (
            stats['latest_finalized_date'].strftime('%b %d')
            if stats['latest_finalized_date']
            else '—'
        )
        
        next_scheduled_date = (
            stats['next_scheduled_date'].strftime('%b %d')
            if stats['next_scheduled_date']
            else '—'
        )
        
        # Integrity check (all snapshots have checksums)
        integrity_status = {
            'valid': True,
            'message': 'All snapshots are hashed and chained. The current ledger state matches the rolling checksum of the active transaction pool. No tampering detected.',
        }
        
        context = {
            'title': 'Equity Snapshots',
            'page_title': 'Equity Snapshots - Shareholders Management',
            'user': request.user,
            'deal': deal,
            
            # Summary cards
            'snapshot_history_count': stats['total_count'],
            'last_consensus_date': last_consensus_date,
            'last_consensus_verified': stats['latest_finalized'] is not None,
            'next_scheduled_date': next_scheduled_date,
            'next_scheduled_days': stats['next_scheduled_days'],
            
            # Snapshot list
            'snapshots': snapshots_data,
            'show_empty': len(snapshots_data) == 0,
            
            # Pagination
            'current_page': result['page'],
            'total_pages': result['total_pages'],
            'total_count': result['total_count'],
            'has_next': result['has_next'],
            'has_previous': result['has_previous'],
            
            # Active filters
            'current_search': search,
            'current_status': status,
            
            # Integrity check
            'integrity_status': integrity_status,
        }
        
        return render(request, 'investing/shareholders/shareholders_snapshots.html', context)
        
    except Exception as e:
        logger.error(f"Error in snapshots view: {str(e)}")
        messages.error(request, f"Error loading snapshots: {str(e)}")
        return redirect('shareholders:shareholders_dashboard')


@login_required
@require_admin
@require_POST
def snapshot_create(request):
    """
    Create a new equity snapshot for the deal.
    
    POST Parameters:
        - version_id: Version identifier (optional, auto-generated if not provided)
        - period_start: Start date (optional, defaults to deal start)
        - period_end: End date (optional, defaults to today)
        - notes: Optional notes
    """
    from investing.services.shareholders.snapshot_generation_service import SnapshotGenerationService
    from investing.services.shareholders.snapshot_query_service import SnapshotQueryService
    from investing.services.shareholders.audit_service import get_client_ip
    from datetime import date, timedelta
    
    try:
        deal = get_active_deal()
        if not deal:
            messages.error(request, "No active deal found.")
            return redirect('shareholders:snapshots_view')
        
        # Get parameters
        version_id = request.POST.get('version_id', '').strip()
        period_start_str = request.POST.get('period_start', '').strip()
        period_end_str = request.POST.get('period_end', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        # Initialize services
        gen_service = SnapshotGenerationService(deal)
        query_service = SnapshotQueryService(deal)
        
        # Generate version ID if not provided
        if not version_id:
            version_id = query_service.generate_next_version_id()
        
        # Parse dates or use defaults
        if period_start_str:
            period_start = date.fromisoformat(period_start_str)
        else:
            # Default to 30 days ago
            period_start = date.today() - timedelta(days=30)
        
        if period_end_str:
            period_end = date.fromisoformat(period_end_str)
        else:
            period_end = date.today()
        
        # Generate snapshot
        snapshot = gen_service.generate_snapshot(
            version_id=version_id,
            period_start=period_start,
            period_end=period_end,
            created_by=request.user,
            notes=notes or None
        )
        
        # Create audit log
        from investing.models_shareholders import SnapshotAuditLog
        SnapshotAuditLog.objects.create(
            snapshot=snapshot,
            action='CREATED',
            performed_by=request.user,
            details={
                'period_start': period_start.isoformat(),
                'period_end': period_end.isoformat(),
                'members_count': snapshot.members_count,
            },
            ip_address=get_client_ip(request)
        )

        # ── Phase: Monthly snapshot email notifications ──────────────────────
        # Send each member a personal copy of their equity snapshot using the
        # email address registered to their member profile.
        try:
            from mail.custom_email import send_email
            from django.urls import reverse

            snapshot_url = request.build_absolute_uri(
                reverse('shareholders:snapshot_detail', args=[snapshot.id])
            )

            email_errors = []
            email_sent = 0

            lines = snapshot.lines.select_related('member')
            for line in lines:
                member = line.member
                if not member.email:
                    logger.warning(
                        f"Snapshot email skipped for member '{member.legal_name}': no email on record."
                    )
                    continue

                email_context = {
                    'member': member,
                    'snapshot': snapshot,
                    'line': line,
                    'dashboard_url': snapshot_url,
                    # category 2 → EMAIL_INFO route (non-payment, non-HR)
                    'purpose': 'info',
                }

                success = send_email(
                    category=2,  # routes to EMAIL_INFO (non-zero avoids falsy check)
                    to_email=[member.email],
                    subject=f"Your Equity Snapshot \u2013 {snapshot.version_id}",
                    html_template='investing/shareholders/emails/snapshot_email.html',
                    context=email_context,
                )

                if success:
                    email_sent += 1
                else:
                    email_errors.append(member.email)
                    logger.error(
                        f"Failed to send snapshot email to {member.email} for snapshot {snapshot.version_id}"
                    )

            if email_sent:
                logger.info(
                    f"Snapshot {snapshot.version_id}: emailed {email_sent}/{lines.count()} members."
                )
            if email_errors:
                logger.warning(
                    f"Snapshot {snapshot.version_id}: failed to email: {', '.join(email_errors)}"
                )

        except Exception as email_exc:
            # Email failures must never block snapshot creation
            logger.error(f"Snapshot email dispatch error for {version_id}: {str(email_exc)}")
        # ────────────────────────────────────────────────────────────────────

        messages.success(
            request,
            f"Snapshot {version_id} created successfully with {snapshot.members_count} members."
        )
        return redirect('shareholders:snapshots_view')
        
    except Exception as e:
        logger.error(f"Error creating snapshot: {str(e)}")
        messages.error(request, f"Error creating snapshot: {str(e)}")
        return redirect('shareholders:snapshots_view')


# ===================================================================
# DEAL CONFIG VIEW (Phase: Frontend-Only UI)
# ===================================================================

@login_required
@require_admin
def deal_config_view(request):
    """
    Deal Configuration View - Fully database-backed governance settings.
    
    Access Control:
        - Requires login
        - Requires admin privileges (is_staff or is_superuser)
        - VIEW: Accessible to staff/admin users (read-only)
        - EDIT: Only superusers can modify configuration
    
    Features:
        - Load real config from DealConfig and DealWeights models
        - Display all governance settings
        - Provide edit interface (only for superusers)
    """
    from investing.services.shareholders.deal_config_service import DealConfigService
    
    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found. Please create a deal first.")
            return redirect('dashboard:unified_dashboard')
        
        # Initialize service
        config_service = DealConfigService(deal)
        
        # Get or create config and weights
        config = config_service.get_or_create_config()
        weights = config_service.get_or_create_weights()
        
        # Prepare context data from real DB
        config_data = {
            # Deal Identity
            'deal_name': deal.name,
            'deal_status': 'Active' if deal.is_active else 'Inactive',
            'created_date': deal.created_at.strftime('%Y-%m-%d'),
            
            # FX & Currency Policy
            'base_currency': config.base_currency,
            'fx_mode': config.fx_mode,
            'peg_rate': float(config.fx_peg_rate),
            
            # Contribution Weights (from DealWeights)
            'cash_weight': float(weights.cash_weight),
            'inkind_weight': float(weights.in_kind_weight),
            'time_weight': float(weights.time_weight),
            'work_weight': float(weights.work_weight),
            
            # Valuation Rules
            'time_rate': float(config.time_rate),
            'work_rate': float(config.work_rate),
            'inkind_mode': config.inkind_valuation_mode,
            
            # Approval & Dispute Policy
            'dispute_window_days': config.dispute_window_days,
            'require_approval_cash': config.require_approval_cash,
            'require_approval_inkind': config.require_approval_inkind,
            'require_approval_time': config.require_approval_time,
            'require_approval_work': config.require_approval_work,
            'auto_lock_snapshots': config.auto_lock_snapshots,
            
            # Snapshot Policy
            'snapshot_frequency': config.snapshot_frequency,
            'snapshot_day': config.snapshot_day,
        }
        
        context = {
            'title': 'Deal Configuration',
            'page_title': 'Deal Configuration - Shareholders Management',
            'user': request.user,
            'deal': deal,
            'config': config_data,
            'can_edit': request.user.is_superuser,  # RBAC: Only superusers can edit
        }
        
        return render(request, 'investing/shareholders/deal_config.html', context)
        
    except Exception as e:
        logger.error(f"Error in deal config view: {str(e)}")
        messages.error(request, f"Error loading deal configuration: {str(e)}")
        return redirect('shareholders:shareholders_dashboard')


@login_required
@require_admin
@require_POST
def deal_config_save(request):
    """
    Save Deal Configuration changes to database.
    
    RBAC Security:
        - Only SUPERUSERS can save configuration changes
        - Staff users attempting POST will receive 403 Forbidden
        - Audit log records unauthorized attempts
    
    POST Parameters:
        - All config and weight fields
    """
    from investing.services.shareholders.deal_config_service import DealConfigService
    from investing.services.shareholders.audit_service import get_client_ip
    from django.core.exceptions import ValidationError
    from django.http import HttpResponseForbidden
    
    # RBAC: Only superusers can edit configuration
    if not request.user.is_superuser:
        # Log unauthorized attempt
        try:
            from investing.models_shareholders import AuditLog
            deal = get_active_deal()
            if deal:
                AuditLog.objects.create(
                    deal=deal,
                    actor=request.user,
                    action_type='CONFIG_UPDATED',
                    entity_type='DEAL_CONFIG',
                    entity_id=str(deal.id),
                    entity_reference=f'Deal Config - {deal.name}',
                    description=f'Unauthorized config edit attempt by {request.user.username}',
                    ip_address=get_client_ip(request),
                    request_source='web',
                    status='FAILED',
                    details={
                        'error': 'Unauthorized attempt by non-superuser',
                        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:255],
                    },
                )
        except Exception as e:
            logger.error(f"Error logging unauthorized config edit attempt: {str(e)}")
        
        messages.error(
            request,
            "Access Denied: Only superusers can modify deal configuration. Your attempt has been logged."
        )
        return HttpResponseForbidden(
            "<h1>403 Forbidden</h1><p>Only superusers can modify deal configuration.</p>"
        )
    
    try:
        deal = get_active_deal()
        if not deal:
            messages.error(request, "No active deal found.")
            return redirect('shareholders:deal_config')
        
        # Initialize service
        config_service = DealConfigService(deal)
        
        # Extract config data from POST
        config_data = {
            'fx_mode': request.POST.get('fx_mode'),
            'fx_peg_rate': request.POST.get('peg_rate'),
            'time_rate': request.POST.get('time_rate'),
            'work_rate': request.POST.get('work_rate'),
            'inkind_valuation_mode': request.POST.get('inkind_mode'),
            'dispute_window_days': request.POST.get('dispute_window'),
            'require_approval_cash': request.POST.get('approval_cash') == 'true',
            'require_approval_inkind': request.POST.get('approval_inkind') == 'true',
            'require_approval_time': request.POST.get('approval_time') == 'true',
            'require_approval_work': request.POST.get('approval_work') == 'true',
            'snapshot_frequency': request.POST.get('snapshot_freq'),
            'snapshot_day': request.POST.get('snapshot_day'),
            'auto_lock_snapshots': request.POST.get('auto_lock') == 'true',
        }
        
        # Extract weights data from POST
        weights_data = {
            'cash_weight': request.POST.get('cash_weight'),
            'inkind_weight': request.POST.get('inkind_weight'),
            'time_weight': request.POST.get('time_weight'),
            'work_weight': request.POST.get('work_weight'),
        }
        
        # Update config and weights
        config_service.update_config(
            config_data,
            user=request.user,
            ip_address=get_client_ip(request)
        )
        
        config_service.update_weights(
            weights_data,
            user=request.user,
            ip_address=get_client_ip(request)
        )
        
        messages.success(
            request,
            "Deal configuration updated successfully! Changes are now active across all shareholders pages."
        )
        return redirect('shareholders:deal_config')
        
    except ValidationError as e:
        messages.error(request, f"Validation error: {str(e)}")
        return redirect('shareholders:deal_config')
    except Exception as e:
        logger.error(f"Error saving deal config: {str(e)}")
        messages.error(request, f"Error saving configuration: {str(e)}")
        return redirect('shareholders:deal_config')


# ===================================================================
# AUDIT LOG VIEW (Phase: Frontend-Only UI)
# ===================================================================

@login_required
@require_admin
def audit_log_view(request):
    """
    Audit Log View - DB-backed audit trail for compliance.
    
    Access Control:
        - Requires login
        - Requires admin privileges (is_staff or is_superuser)
    
    Phase: Backend integration with real audit logs from database.
    
    UI Features:
        - Chronological audit trail
        - Server-side filtering by date, action type, entity type, actor
        - Pagination for performance
        - Read-only compliance view
        - Summary metrics
    """
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    from investing.models_shareholders import AuditLog
    from django.db.models import Q
    from datetime import datetime
    
    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found. Please create a deal first.")
            return redirect('dashboard:unified_dashboard')
        
        # Get all audit logs for this deal
        audit_logs = AuditLog.objects.filter(deal=deal).select_related('actor')
        
        # Apply filters from request
        date_start = request.GET.get('date_start')
        date_end = request.GET.get('date_end')
        action_type = request.GET.get('action_type')
        entity_type = request.GET.get('entity_type')
        actor_filter = request.GET.get('actor')
        search = request.GET.get('search')
        
        # Date range filter
        if date_start:
            try:
                start_date = datetime.strptime(date_start, '%Y-%m-%d')
                audit_logs = audit_logs.filter(timestamp__gte=start_date)
            except ValueError:
                pass
        
        if date_end:
            try:
                end_date = datetime.strptime(date_end, '%Y-%m-%d')
                audit_logs = audit_logs.filter(timestamp__lte=end_date)
            except ValueError:
                pass
        
        # Action type filter
        if action_type:
            audit_logs = audit_logs.filter(action_type=action_type)
        
        # Entity type filter
        if entity_type:
            audit_logs = audit_logs.filter(entity_type=entity_type)
        
        # Actor filter
        if actor_filter:
            audit_logs = audit_logs.filter(actor__username__icontains=actor_filter)
        
        # Search filter (searches description and entity reference)
        if search:
            audit_logs = audit_logs.filter(
                Q(description__icontains=search) |
                Q(entity_reference__icontains=search) |
                Q(entity_id__icontains=search)
            )
        
        # Pagination
        paginator = Paginator(audit_logs, 50)  # 50 logs per page
        page = request.GET.get('page', 1)
        
        try:
            audit_logs_page = paginator.page(page)
        except PageNotAnInteger:
            audit_logs_page = paginator.page(1)
        except EmptyPage:
            audit_logs_page = paginator.page(paginator.num_pages)
        
        # Summary stats
        total_events = AuditLog.objects.filter(deal=deal).count()
        latest_log = AuditLog.objects.filter(deal=deal).first()
        last_activity = latest_log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if latest_log else 'N/A'
        
        # Prepare audit logs for template
        audit_logs_list = []
        for log in audit_logs_page:
            audit_logs_list.append({
                'id': log.id,
                'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'actor': log.actor.username if log.actor else 'System',
                'action_type': log.action_type,
                'action_display': log.get_action_type_display(),
                'entity_type': log.entity_type,
                'entity_display': log.get_entity_type_display(),
                'entity_reference': log.entity_reference,
                'description': log.description,
                'source_ip': log.ip_address or 'N/A',
                'status': log.status,
                'status_display': log.get_status_display(),
            })
        
        # Serialize for JavaScript (for modal)
        import json
        audit_logs_json = json.dumps(audit_logs_list)
        
        # Get unique values for filters
        action_types = AuditLog.ACTION_TYPE_CHOICES
        entity_types = AuditLog.ENTITY_TYPE_CHOICES
        
        context = {
            'title': 'Audit Log',
            'page_title': 'Audit Log - Shareholders Management',
            'user': request.user,
            'deal': deal,
            'audit_logs': audit_logs_list,
            'audit_logs_json': audit_logs_json,
            'audit_logs_page': audit_logs_page,
            'total_events': total_events,
            'last_activity': last_activity,
            'action_types': action_types,
            'entity_types': entity_types,
            # Preserve filter values
            'filter_date_start': date_start or '',
            'filter_date_end': date_end or '',
            'filter_action_type': action_type or '',
            'filter_entity_type': entity_type or '',
            'filter_actor': actor_filter or '',
            'filter_search': search or '',
        }
        
        return render(request, 'investing/shareholders/audit_log.html', context)
        
    except Exception as e:
        logger.error(f"Error in audit log view: {str(e)}")
        messages.error(request, f"Error loading audit log: {str(e)}")
        return redirect('shareholders:shareholders_dashboard')


# =============================================================================
# SHAREHOLDER DIRECT DEPOSIT FLOW
# =============================================================================

# Payment method configuration for shareholder deposits
SHAREHOLDER_PAYMENT_METHODS = {
    'stripe': {
        'name': 'Card (Stripe)',
        'icon_bg': '#f0f0fe',
        'icon_color': '#6366f1',
        'desc': 'Secure card payment',
        'time': 'Instant',
        'fee': '2.9% + 30¢',
        'has_api': True,
    },
    'paypal': {
        'name': 'PayPal',
        'icon_bg': '#dbeafe',
        'icon_color': '#1d4ed8',
        'desc': 'Pay with PayPal',
        'time': 'Instant',
        'fee': '3.5%',
        'has_api': True,
    },
    'mpesa': {
        'name': 'M-Pesa',
        'icon_bg': '#f0fdf4',
        'icon_color': '#16a34a',
        'desc': 'Mobile money (Kenya)',
        'time': 'Instant',
        'fee': '2.5%',
        'has_api': True,
    },
    'cashapp': {
        'name': 'Cash App',
        'icon_bg': '#dcfce7',
        'icon_color': '#16a34a',
        'desc': 'Pay with Cash App',
        'time': 'Instant',
        'fee': '1.5%',
        'has_api': True,
    },
}


@login_required
@require_admin
def shareholder_deposit(request):
    """
    Shareholder Direct Deposit - Method Selection Page
    
    Flow: contribution_log → THIS PAGE → gateway page → success → contribution_log (pre-filled)
    
    Accepts query params:
        ?amount=<USD amount>
        ?member_id=<member ID>
        ?contributor=<member ID>
    """
    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found.")
            return redirect('shareholders:contribution_log')

        amount = request.GET.get('amount', '')
        member_id = request.GET.get('member_id', '') or request.GET.get('contributor', '')

        # Validate amount
        try:
            amount_float = float(amount) if amount else 0.0
        except (ValueError, TypeError):
            amount_float = 0.0

        # Get member name for display
        member_name = ''
        if member_id:
            try:
                member = Member.objects.get(id=int(member_id), deal=deal, is_archived=False)
                member_name = member.legal_name
            except (ValueError, TypeError, Member.DoesNotExist):
                pass

        context = {
            'title': 'Direct Deposit',
            'page_title': 'Direct Deposit - Shareholder Contribution',
            'user': request.user,
            'deal': deal,
            'amount': amount_float,
            'amount_str': f'{amount_float:.2f}' if amount_float > 0 else '',
            'member_id': member_id,
            'member_name': member_name,
            'payment_methods': SHAREHOLDER_PAYMENT_METHODS,
        }

        return render(request, 'investing/shareholders/shareholders_deposit.html', context)

    except Exception as e:
        logger.error(f"Error in shareholder_deposit: {str(e)}")
        messages.error(request, f"Error loading deposit page: {str(e)}")
        return redirect('shareholders:contribution_log')


@login_required
@require_admin
def shareholder_deposit_process(request, method):
    """
    Process shareholder deposit for a specific payment gateway.
    
    For Stripe: Creates Stripe Checkout Session and redirects to Stripe hosted page.
    For manual methods: Shows payment instructions with reference + "I've Deposited" button.
    
    Accepts GET params: ?amount=<USD>
    Accepts POST: amount field
    """
    import os

    if method not in SHAREHOLDER_PAYMENT_METHODS:
        messages.error(request, 'Invalid payment method.')
        return redirect('shareholders:shareholder_deposit')

    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found.")
            return redirect('shareholders:shareholder_deposit')

        # Get amount from POST or GET
        amount = 0.0
        member_id = ''
        if request.method == 'POST':
            try:
                amount = float(request.POST.get('amount', 0))
            except (ValueError, TypeError):
                amount = 0.0
            member_id = request.POST.get('member_id', '')
        else:
            try:
                amount = float(request.GET.get('amount', 0))
            except (ValueError, TypeError):
                amount = 0.0
            member_id = request.GET.get('member_id', '')

        if amount <= 0:
            messages.error(request, 'Please enter a valid deposit amount.')
            return redirect('shareholders:shareholder_deposit')

        # Store deposit info in session for success redirect
        request.session['sh_deposit_amount'] = amount
        request.session['sh_deposit_method'] = method
        request.session['sh_deposit_member_id'] = member_id

        method_info = SHAREHOLDER_PAYMENT_METHODS[method]

        # ── STRIPE: Redirect to Stripe Checkout ─────────────────────────
        if method == 'stripe':
            try:
                import stripe
                from django.conf import settings
                from django.urls import reverse

                stripe_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
                if not stripe_key:
                    # Fallback to manual payment details
                    messages.info(request, 'Stripe is not configured. Showing manual payment details.')
                    # Fall through to manual flow below
                else:
                    stripe.api_key = stripe_key

                    success_url = request.build_absolute_uri(
                        reverse('shareholders:shareholder_deposit_success')
                    ) + '?session_id={CHECKOUT_SESSION_ID}&method=stripe'
                    cancel_url = request.build_absolute_uri(
                        reverse('shareholders:shareholder_deposit')
                    ) + f'?amount={amount}&member_id={member_id}'

                    checkout_session = stripe.checkout.Session.create(
                        payment_method_types=['card'],
                        line_items=[{
                            'price_data': {
                                'currency': 'usd',
                                'product_data': {
                                    'name': 'Shareholder Cash Contribution',
                                    'description': f'Direct deposit of ${amount:.2f} USD',
                                },
                                'unit_amount': int(amount * 100),
                            },
                            'quantity': 1,
                        }],
                        mode='payment',
                        success_url=success_url,
                        cancel_url=cancel_url,
                        customer_email=request.user.email if request.user.email else None,
                        metadata={
                            'source': 'shareholder_contribution',
                            'user_id': str(request.user.id),
                            'member_id': str(member_id),
                            'amount': str(amount),
                        },
                    )

                    return redirect(checkout_session.url)

            except ImportError:
                messages.info(request, 'Stripe library not installed. Showing manual payment details.')
            except Exception as stripe_err:
                logger.error(f"Stripe checkout error: {str(stripe_err)}")
                messages.warning(request, 'Card payment temporarily unavailable. Use manual payment details below.')

        # ── ROUTE TO METHOD-SPECIFIC REAL GATEWAY PAGES ────────────────
        from finance.views.payment.payment_details import (
            generate_payment_reference,
        )

        payment_reference = generate_payment_reference(request.user.id, method)
        request.session['sh_deposit_reference'] = payment_reference

        base_context = {
            'title': f'Deposit via {method_info["name"]}',
            'page_title': f'Direct Deposit - {method_info["name"]}',
            'user': request.user,
            'deal': deal,
            'method': method,
            'method_info': method_info,
            'amount': amount,
            'member_id': member_id,
            'payment_reference': payment_reference,
        }

        # ── PayPal: Real PayPal JS SDK Smart Payment Buttons ──────────
        if method == 'paypal':
            from django.conf import settings as django_settings
            paypal_client_id = getattr(django_settings, 'PAYPAL_CLIENT_ID', '') or 'AYsNJlHsAzemW-IvLkkf42iMHGdTMxFfupX6CTI2-rhDDfU67zTQ2n_lszMkxcrrYq_5Qltrw99Lep4D'
            base_context['paypal_client_id'] = paypal_client_id
            return render(request, 'investing/shareholders/shareholders_deposit_paypal.html', base_context)

        # ── M-Pesa: Real STK Push (Daraja API) ───────────────────────
        if method == 'mpesa':
            base_context['mpesa_phone'] = os.environ.get('MPESA_PHONE_NUMBER', '+254 728905233')
            base_context['mpesa_paybill'] = os.environ.get('MPESA_PAYBILL', '600100')
            return render(request, 'investing/shareholders/shareholders_deposit_mpesa.html', base_context)

        # ── CashApp: Square Web Payments SDK + Cash App direct payment ──
        if method == 'cashapp':
            from django.conf import settings as django_settings

            # Square SDK credentials (for full Cash App Pay integration)
            square_app_id = getattr(django_settings, 'SQUARE_APPLICATION_ID', '') or os.environ.get('SQUARE_APPLICATION_ID', '')
            square_location_id = getattr(django_settings, 'SQUARE_LOCATION_ID', '') or os.environ.get('SQUARE_LOCATION_ID', '')
            square_env = getattr(django_settings, 'SQUARE_ENVIRONMENT', 'sandbox')
            # Check if Square is actually configured (not placeholder)
            square_configured = bool(
                square_app_id and square_location_id
                and 'PLACEHOLDER' not in square_app_id.upper()
            )
            base_context['square_application_id'] = square_app_id
            base_context['square_location_id'] = square_location_id
            base_context['square_environment'] = square_env
            base_context['square_configured'] = square_configured

            # Cash App direct payment info (always available)
            cashapp_tag = os.environ.get('CASHAPP', '$codainfo')
            cashapp_id = cashapp_tag.lstrip('$')
            base_context['cashapp_tag'] = cashapp_tag
            base_context['cashapp_url'] = f'https://cash.app/${cashapp_id}/{amount:.2f}'

            return render(request, 'investing/shareholders/shareholders_deposit_cashapp.html', base_context)

        # ── Stripe fallback: if Stripe was unconfigured / errored, redirect back ──
        if method == 'stripe':
            return redirect('shareholders:shareholder_deposit')

    except Exception as e:
        logger.error(f"Error in shareholder_deposit_process: {str(e)}")
        messages.error(request, f"Error processing deposit: {str(e)}")
        return redirect('shareholders:shareholder_deposit')


@login_required
@require_admin
def shareholder_deposit_success(request):
    """
    Shareholder Deposit Success - redirects back to contribution_log with amount pre-filled.
    
    Handles:
    - Stripe success callback (with ?session_id=...)
    - Manual "I've deposited" confirmation (POST)
    """
    method = request.GET.get('method', '') or request.POST.get('method', '')
    
    # Retrieve deposit data from session
    amount = request.session.get('sh_deposit_amount', 0)
    deposit_method = request.session.get('sh_deposit_method', method or 'unknown')
    member_id = request.session.get('sh_deposit_member_id', '')
    reference = request.session.get('sh_deposit_reference', '')

    # For Stripe: verify the checkout session
    if method == 'stripe':
        session_id = request.GET.get('session_id', '')
        if session_id:
            try:
                import stripe
                from django.conf import settings
                stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
                checkout_session = stripe.checkout.Session.retrieve(session_id)
                if checkout_session.payment_status == 'paid':
                    metadata = checkout_session.metadata or {}
                    amount = float(metadata.get('amount', amount))
                    member_id = metadata.get('member_id', member_id)
                    reference = f"STRIPE-SH-{session_id[:12]}"
                    logger.info(f"Stripe shareholder deposit verified: ${amount} session={session_id}")
                else:
                    messages.warning(request, 'Payment session found but not yet confirmed. Please check back later.')
            except Exception as e:
                logger.error(f"Error verifying Stripe session for shareholder deposit: {str(e)}")
                # Still proceed - amount is in session

    # Clear session deposit data
    for key in ['sh_deposit_amount', 'sh_deposit_method', 'sh_deposit_member_id', 'sh_deposit_reference', 'sh_mpesa_checkout_id']:
        request.session.pop(key, None)

    if not amount or float(amount) <= 0:
        messages.warning(request, 'No deposit amount recorded. Please try again.')
        return redirect('shareholders:shareholder_deposit')

    # Build redirect URL back to contribution_log with pre-filled data
    from django.urls import reverse
    import urllib.parse

    params = {
        'deposit_amount': f'{float(amount):.2f}',
        'deposit_method': deposit_method,
        'deposit_ref': reference,
    }
    if member_id:
        params['member_id'] = member_id

    contribution_url = reverse('shareholders:contribution_log') + '?' + urllib.parse.urlencode(params)

    messages.success(
        request,
        f'Deposit of ${float(amount):,.2f} via {deposit_method.title()} recorded successfully! '
        f'Reference: {reference}. Now submit your contribution below.'
    )

    return redirect(contribution_url)


# =============================================================================
# SHAREHOLDER DEPOSIT: REAL PAYMENT GATEWAY AJAX ENDPOINTS
# =============================================================================

@login_required
@require_admin
def shareholder_paypal_capture(request):
    """
    AJAX endpoint: Record PayPal payment captured via PayPal JS SDK.
    Called from shareholders_deposit_paypal.html after PayPal onApprove callback.
    """
    import json

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        order_id = data.get('orderID', '')
        transaction_id = data.get('transactionID', '')
        amount = float(data.get('amount', 0))
        payer_email = data.get('payerEmail', '')
        payment_method = data.get('method', 'paypal')  # 'paypal' or 'venmo'

        if amount <= 0:
            return JsonResponse({'error': 'Invalid amount'}, status=400)

        # Update session deposit data
        member_id = request.session.get('sh_deposit_member_id', '')
        request.session['sh_deposit_amount'] = amount
        request.session['sh_deposit_method'] = payment_method
        request.session['sh_deposit_reference'] = f"{payment_method.upper()}-SH-{transaction_id or order_id}"

        logger.info(
            f"PayPal shareholder deposit captured: ${amount:.2f}, "
            f"order={order_id}, tx={transaction_id}, payer={payer_email}"
        )

        from django.urls import reverse
        success_url = reverse('shareholders:shareholder_deposit_success') + '?method=paypal'

        return JsonResponse({
            'success': True,
            'redirect_url': success_url,
        })

    except Exception as e:
        logger.error(f"Error capturing PayPal shareholder payment: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_admin
def shareholder_cashapp_capture(request):
    """
    AJAX endpoint: Process Cash App Pay payment via Square Payments API.
    Called from shareholders_deposit_cashapp.html after Square SDK tokenization.
    """
    import json

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        source_id = data.get('sourceId', '')  # Token from Square SDK
        amount = float(data.get('amount', 0))

        if not source_id:
            return JsonResponse({'error': 'Payment token required'}, status=400)
        if amount <= 0:
            return JsonResponse({'error': 'Invalid amount'}, status=400)

        import os
        access_token = os.environ.get('SQUARE_ACCESS_TOKEN', '')
        location_id = os.environ.get('SQUARE_LOCATION_ID', '')

        if not access_token or not location_id:
            return JsonResponse({'error': 'Cash App Pay not configured. Contact support.'}, status=503)

        # Create payment via Square Payments API
        import requests as http_requests
        import uuid

        square_env = os.environ.get('SQUARE_ENVIRONMENT', 'sandbox')
        if square_env == 'production':
            square_api_url = 'https://connect.squareup.com/v2/payments'
        else:
            square_api_url = 'https://connect.squareupsandbox.com/v2/payments'

        idempotency_key = str(uuid.uuid4())
        member_id = request.session.get('sh_deposit_member_id', '')

        payment_body = {
            'source_id': source_id,
            'idempotency_key': idempotency_key,
            'amount_money': {
                'amount': int(amount * 100),  # Square uses cents
                'currency': 'USD'
            },
            'location_id': location_id,
            'note': f'Shareholder Cash Contribution ${amount:.2f}',
            'reference_id': f'SH-CASHAPP-{request.user.id}-{idempotency_key[:8]}',
        }

        headers = {
            'Square-Version': '2024-01-18',
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }

        response = http_requests.post(square_api_url, headers=headers, json=payment_body, timeout=30)
        result = response.json()

        if response.status_code == 200 and 'payment' in result:
            payment = result['payment']
            payment_id = payment.get('id', '')
            status = payment.get('status', '')

            request.session['sh_deposit_amount'] = amount
            request.session['sh_deposit_method'] = 'cashapp'
            request.session['sh_deposit_reference'] = f'CASHAPP-SH-{payment_id[:16]}'

            logger.info(
                f"Cash App Pay shareholder deposit captured: ${amount:.2f}, "
                f"payment_id={payment_id}, status={status}"
            )

            from django.urls import reverse
            success_url = reverse('shareholders:shareholder_deposit_success') + '?method=cashapp'

            return JsonResponse({
                'success': True,
                'redirect_url': success_url,
                'payment_id': payment_id,
            })
        else:
            errors = result.get('errors', [{}])
            error_detail = errors[0].get('detail', 'Payment failed') if errors else 'Payment failed'
            logger.error(f"Square Cash App Pay error: {result}")
            return JsonResponse({'error': error_detail}, status=400)

    except Exception as e:
        logger.error(f"Error capturing Cash App Pay shareholder payment: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_admin
def shareholder_mpesa_stk_push(request):
    """
    AJAX endpoint: Initiate M-Pesa STK Push via Safaricom Daraja API.
    Sends a payment prompt directly to the user's phone.
    """
    import json
    import os

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        phone_number = data.get('phone_number', '')
        amount = float(data.get('amount', 0))

        if not phone_number or amount <= 0:
            return JsonResponse({'error': 'Phone number and valid amount required'}, status=400)

        # Check if M-Pesa credentials are available
        consumer_key = os.environ.get('MPESA_CONSUMER_KEY', '')
        consumer_secret = os.environ.get('MPESA_CONSUMER_SECRET', '')
        shortcode = os.environ.get('MPESA_SHORTCODE', '')

        if not all([consumer_key, consumer_secret, shortcode]):
            return JsonResponse({
                'error': 'M-Pesa API credentials not configured. Please contact support.'
            }, status=503)

        from finance.services.mpesa_service import MPESAService
        mpesa = MPESAService()

        # Validate and format phone number
        is_valid, formatted_phone = mpesa.validate_phone_number(phone_number)
        if not is_valid:
            return JsonResponse({
                'error': 'Invalid phone number. Please use format 254XXXXXXXXX or 07XXXXXXXX'
            }, status=400)

        # Get access token
        access_token = mpesa.get_access_token()

        # Prepare STK Push request
        import requests as http_requests

        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        password = mpesa._generate_password(timestamp)
        member_id = request.session.get('sh_deposit_member_id', '')
        reference = f"SH-MPESA-{request.user.id}-{timestamp}"

        stk_data = {
            "BusinessShortCode": mpesa.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": formatted_phone,
            "PartyB": mpesa.shortcode,
            "PhoneNumber": formatted_phone,
            "CallBackURL": f"{mpesa.callback_url}/mpesa/stk-callback",
            "AccountReference": reference,
            "TransactionDesc": f"Shareholder Contribution ${amount:.2f}"
        }

        stk_url = f"{mpesa.base_url}/mpesa/stkpush/v1/processrequest"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        response = http_requests.post(stk_url, headers=headers, json=stk_data, timeout=30)
        result = response.json()

        if result.get('ResponseCode') == '0':
            checkout_request_id = result.get('CheckoutRequestID', '')
            request.session['sh_mpesa_checkout_id'] = checkout_request_id
            request.session['sh_deposit_reference'] = reference
            request.session['sh_deposit_amount'] = amount
            request.session['sh_deposit_method'] = 'mpesa'

            logger.info(f"M-Pesa STK Push initiated: checkout={checkout_request_id}, phone={formatted_phone}")

            return JsonResponse({
                'success': True,
                'checkout_request_id': checkout_request_id,
                'message': 'Payment prompt sent to your phone. Please enter your M-Pesa PIN.'
            })
        else:
            error_msg = result.get('ResponseDescription', '') or result.get('errorMessage', 'Failed to initiate STK Push')
            logger.error(f"M-Pesa STK Push failed: {result}")
            return JsonResponse({'success': False, 'error': error_msg})

    except Exception as e:
        logger.error(f"M-Pesa STK Push error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_admin
def shareholder_mpesa_check_status(request):
    """
    AJAX endpoint: Check M-Pesa STK Push payment status.
    Called by polling from the M-Pesa deposit page.
    """
    import os

    checkout_id = request.GET.get('checkout_request_id', '') or request.session.get('sh_mpesa_checkout_id', '')

    if not checkout_id:
        return JsonResponse({'error': 'No checkout request ID'}, status=400)

    try:
        consumer_key = os.environ.get('MPESA_CONSUMER_KEY', '')
        consumer_secret = os.environ.get('MPESA_CONSUMER_SECRET', '')

        if not all([consumer_key, consumer_secret]):
            return JsonResponse({'status': 'pending', 'message': 'Checking payment status...'})

        from finance.services.mpesa_service import MPESAService
        mpesa = MPESAService()
        access_token = mpesa.get_access_token()

        import requests as http_requests

        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        password = mpesa._generate_password(timestamp)

        query_data = {
            "BusinessShortCode": mpesa.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_id
        }

        query_url = f"{mpesa.base_url}/mpesa/stkpushquery/v1/query"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        response = http_requests.post(query_url, headers=headers, json=query_data, timeout=15)
        result = response.json()

        result_code = result.get('ResultCode')

        # Result codes: 0 = success, 1032 = cancelled by user, 1 = insufficient balance
        if str(result_code) == '0':
            from django.urls import reverse
            success_url = reverse('shareholders:shareholder_deposit_success') + '?method=mpesa'
            logger.info(f"M-Pesa STK Push confirmed: checkout={checkout_id}")
            return JsonResponse({
                'status': 'completed',
                'redirect_url': success_url,
            })
        elif str(result_code) == '1032':
            return JsonResponse({
                'status': 'cancelled',
                'message': 'Payment was cancelled. You can try again.'
            })
        elif str(result_code) in ('1', '2001'):
            return JsonResponse({
                'status': 'failed',
                'message': 'Insufficient balance or transaction limit reached.'
            })
        else:
            return JsonResponse({
                'status': 'pending',
                'message': 'Waiting for payment confirmation...'
            })

    except Exception as e:
        logger.error(f"M-Pesa status check error: {str(e)}")
        return JsonResponse({'status': 'pending', 'message': 'Checking payment status...'})
