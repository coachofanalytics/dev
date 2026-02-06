""" Shareholders Management System Views

This module provides views for the Shareholders Management System.
Access is restricted to admin users only (same permission as Automation dashboard).

Phase 1: Database-backed views with real queries.
Phase 2: Full ledger backend with approval workflow, disputes, and CSV export.
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
from .models import (
    Deal, DealConfig, DealWeights, Member, LedgerEntry, LedgerEvidence,
    LedgerApproval, LedgerDispute, LedgerAuditLog
)
from .dashboard_service import get_dashboard_metrics
from .services.ledger_query import LedgerQueryService
from .services.ledger_checksum import LedgerChecksumService

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
        
        return render(request, 'shareholders/dashboard.html', context)
        
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
        
        return render(request, 'shareholders/ledgers.html', context)
        
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
    from .services.member_metrics import get_deal_member_summary
    
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
        
        return render(request, 'shareholders/members_overview.html', context)
        
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
    from .forms import MemberRegisterForm
    from .services.audit_service import AuditService, get_client_ip
    
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
                member.save()
                
                # Handle optional identity document upload
                identity_doc = form.cleaned_data.get('identity_document')
                if identity_doc:
                    member.identity_document = identity_doc
                    member.save()
                    logger.info(f"Identity document uploaded for {member.legal_name}: {identity_doc.name}")
                
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
        
        return render(request, 'shareholders/member_register.html', context)
        
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
    from .services.member_metrics import MemberMetricsService
    
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
        
        # Build member dict for template
        member_data = {
            'id': member.id,
            'name': member.legal_name,
            'role': member.role_title or '',
            'type': member.get_member_type_display(),
            'type_code': member.member_type,
            'verified': member.verified,
            'equity_percentage': '—',  # Phase 4
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
        }
        
        context = {
            'title': f"{member.legal_name} - Member Profile",
            'page_title': f"{member.legal_name} - Shareholders Management",
            'user': request.user,
            'member': member_data,
            'contribution_history': contribution_history,
        }
        
        return render(request, 'shareholders/member_detail.html', context)
        
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
    """
    from .forms import MemberEditForm
    from .services.audit_service import AuditService, get_client_ip
    
    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found.")
            return redirect('shareholders:members_overview')
        
        # Get member
        member = get_object_or_404(Member, id=member_id, deal=deal, is_archived=False)
        
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
            
            form = MemberEditForm(request.POST, instance=member, user=request.user)
            
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
            'form': form,
            'role_catalog': get_role_catalog(),
        }
        
        return render(request, 'shareholders/member_edit.html', context)
        
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
    from .forms import ContributionLogForm
    from .services.contribution_service import ContributionSubmissionService
    from .services.audit_service import get_client_ip
    
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
                        ip_address=get_client_ip(request)
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
        
        context = {
            'title': 'Log New Contribution',
            'page_title': 'Log New Contribution - Shareholders Management',
            'user': request.user,
            'form': form,
            'selected_member': selected_member,
            'all_members': all_members,
        }
        
        return render(request, 'shareholders/contribution_log.html', context)
        
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
        return render(request, 'shareholders/ledger_detail.html', context)
        
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
@require_POST
def ledger_approve(request, tx_id):
    """
    Approve a ledger entry (POST action).
    
    Creates LedgerApproval record, updates entry status, and logs audit event.
    """
    try:
        deal = get_active_deal()
        if not deal:
            return JsonResponse({'error': 'No active deal found'}, status=400)
        
        # Get the entry
        try:
            entry = LedgerEntry.objects.get(tx_id=tx_id, deal=deal)
        except LedgerEntry.DoesNotExist:
            return JsonResponse({'error': f'Entry {tx_id} not found'}, status=404)
        
        # Check if already approved
        if entry.status == 'APPROVED':
            return JsonResponse({'error': 'Entry is already approved'}, status=400)
        
        # Check if in dispute
        if entry.status == 'IN_DISPUTE':
            return JsonResponse({'error': 'Cannot approve entry that is in dispute'}, status=400)
        
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
            'success': True,
            'message': f'Entry {tx_id} has been approved',
            'new_status': 'Approved'
        })
        
    except Exception as e:
        logger.error(f"Error approving entry {tx_id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_admin
@require_POST
def ledger_dispute(request, tx_id):
    """
    Flag a dispute for a ledger entry (POST action).
    
    Creates LedgerDispute record, updates entry status, and logs audit event.
    Checks dispute window from DealConfig.
    """
    try:
        deal = get_active_deal()
        if not deal:
            return JsonResponse({'error': 'No active deal found'}, status=400)
        
        # Get the entry
        try:
            entry = LedgerEntry.objects.get(tx_id=tx_id, deal=deal)
        except LedgerEntry.DoesNotExist:
            return JsonResponse({'error': f'Entry {tx_id} not found'}, status=404)
        
        # Check if already in dispute
        if entry.status == 'IN_DISPUTE':
            return JsonResponse({'error': 'Entry is already in dispute'}, status=400)
        
        # Get reason from request
        import json
        try:
            body = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            body = {}
        reason = body.get('reason', '').strip()
        
        if not reason:
            return JsonResponse({'error': 'Dispute reason is required'}, status=400)
        
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
            'success': True,
            'message': f'Dispute has been raised for entry {tx_id}',
            'new_status': 'In Dispute',
            'within_window': within_window
        })
        
    except Exception as e:
        logger.error(f"Error flagging dispute for entry {tx_id}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


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
