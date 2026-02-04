""" Shareholders Management System Views

This module provides views for the Shareholders Management System.
Access is restricted to admin users only (same permission as Automation dashboard).

Phase 1: Database-backed views with real queries.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from core.permissions import is_admin, require_admin
from .models import Deal, DealConfig, DealWeights, Member, LedgerEntry, LedgerEvidence
from .services import get_dashboard_metrics

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
    
    Access Control:
        - Requires login
        - Requires admin privileges (is_staff or is_superuser)
        - Same permission logic as Automation dashboard
    
    Phase 1: Real database queries with client-side filtering preserved.
    """
    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found. Please create a deal first.")
            return redirect('shareholders:shareholders_dashboard')
        
        # Query ledger entries for this deal
        ledger_entries_qs = LedgerEntry.objects.filter(
            deal=deal
        ).select_related('contributor').order_by('-date', '-created_at')
        
        # Convert to list of dicts for template (maintains existing template structure)
        ledger_entries = []
        for entry in ledger_entries_qs:
            ledger_entries.append({
                'id': entry.tx_id,
                'contributor_name': entry.contributor.legal_name,
                'tier': entry.get_tier_display(),
                'asset_class': entry.asset_class,
                'internal_units': f"{entry.internal_units_value:,.0f} {entry.internal_units_label or ''}" if entry.internal_units_label else f"{entry.internal_units_value:,.0f}",
                'value_usd': float(entry.value_usd),
                'status': entry.get_status_display(),
                'date': entry.date.strftime('%Y-%m-%d'),
                'notes': entry.notes or '',
                'has_proof': entry.has_proof,
            })
        
        # Summary statistics
        summary_stats = {
            'total_volume_usd': float(ledger_entries_qs.aggregate(total=Sum('value_usd'))['total'] or 0),
            'approved_count': ledger_entries_qs.filter(status='APPROVED').count(),
            'in_dispute_count': ledger_entries_qs.filter(status='IN_DISPUTE').count(),
            'latest_checksum': '0x8f2d...e1',  # Placeholder for Phase 6
        }
        
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
            'ledger_entries': ledger_entries,
            'summary_stats': summary_stats,
            'tier_legend': tier_legend,
            'status_types': status_types,
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
    
    Phase 1: Real database queries; equity % placeholder (Phase 4).
    """
    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found. Please create a deal first.")
            return redirect('shareholders:shareholders_dashboard')
        
        # Query active members
        members_qs = Member.objects.filter(
            deal=deal,
            is_archived=False
        ).order_by('legal_name')
        
        # Build member data with aggregated contributions
        members = []
        for member in members_qs:
            # Aggregate contributions by tier
            cash_invested = LedgerEntry.objects.filter(
                contributor=member,
                tier='CASH',
                status__in=['APPROVED', 'SUBMITTED']
            ).aggregate(total=Sum('value_usd'))['total'] or Decimal('0.00')
            
            in_kind_value = LedgerEntry.objects.filter(
                contributor=member,
                tier='IN_KIND',
                status__in=['APPROVED', 'SUBMITTED']
            ).aggregate(total=Sum('value_usd'))['total'] or Decimal('0.00')
            
            time_hours = LedgerEntry.objects.filter(
                contributor=member,
                tier='TIME',
                status__in=['APPROVED', 'SUBMITTED']
            ).aggregate(total=Sum('internal_units_value'))['total'] or Decimal('0.00')
            
            work_points = LedgerEntry.objects.filter(
                contributor=member,
                tier='WORK',
                status__in=['APPROVED', 'SUBMITTED']
            ).aggregate(total=Sum('internal_units_value'))['total'] or Decimal('0.00')
            
            members.append({
                'id': member.id,
                'name': member.legal_name,
                'role': member.role_title or '',
                'type': member.get_member_type_display(),
                'verified': member.verified,
                'equity_percentage': '—',  # Phase 4: equity calculation
                'cash_invested': float(cash_invested),
                'in_kind_value': float(in_kind_value),
                'time_hours': float(time_hours),
                'work_points': float(work_points),
                'email': member.email,
                'phone': member.phone or '',
                'joined_date': member.joined_date.strftime('%Y-%m-%d'),
                'bio': member.bio or '',
            })
        
        context = {
            'title': 'Members & Equity',
            'page_title': 'Members & Equity - Shareholders Management',
            'user': request.user,
            'members': members,
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
    
    Phase 1: Real POST handling to create Member records.
    """
    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found. Please create a deal first.")
            return redirect('shareholders:members_overview')
        
        if request.method == 'POST':
            # Extract form data
            legal_name = request.POST.get('legal_name', '').strip()
            member_type = request.POST.get('member_type', 'PERSON')
            role = request.POST.get('role', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            
            # Validation
            if not legal_name or not email:
                messages.error(request, "Legal name and email are required.")
                return render(request, 'shareholders/member_register.html', {
                    'title': 'Register Member',
                    'page_title': 'Register New Member - Shareholders Management',
                    'user': request.user,
                    'role_catalog': get_role_catalog(),
                })
            
            # Create member
            member = Member.objects.create(
                deal=deal,
                legal_name=legal_name,
                member_type=member_type,
                role_title=role,
                email=email,
                phone=phone,
                verified=False,  # Default unverified; admin can verify later
                is_active=True
            )
            
            messages.success(request, f"Member {member.legal_name} registered successfully!")
            return redirect('shareholders:members_overview')
        
        # GET request - show form
        context = {
            'title': 'Register Member',
            'page_title': 'Register New Member - Shareholders Management',
            'user': request.user,
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
    
    Phase 1: Real queries with aggregated contribution data.
    """
    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found.")
            return redirect('shareholders:members_overview')
        
        # Get member
        member = get_object_or_404(Member, id=member_id, deal=deal)
        
        # Aggregate contributions by tier
        cash_invested = LedgerEntry.objects.filter(
            contributor=member,
            tier='CASH',
            status__in=['APPROVED', 'SUBMITTED']
        ).aggregate(total=Sum('value_usd'))['total'] or Decimal('0.00')
        
        in_kind_value = LedgerEntry.objects.filter(
            contributor=member,
            tier='IN_KIND',
            status__in=['APPROVED', 'SUBMITTED']
        ).aggregate(total=Sum('value_usd'))['total'] or Decimal('0.00')
        
        time_hours = LedgerEntry.objects.filter(
            contributor=member,
            tier='TIME',
            status__in=['APPROVED', 'SUBMITTED']
        ).aggregate(total=Sum('internal_units_value'))['total'] or Decimal('0.00')
        
        work_points = LedgerEntry.objects.filter(
            contributor=member,
            tier='WORK',
            status__in=['APPROVED', 'SUBMITTED']
        ).aggregate(total=Sum('internal_units_value'))['total'] or Decimal('0.00')
        
        # Get contribution history
        contribution_history_qs = LedgerEntry.objects.filter(
            contributor=member
        ).order_by('-date', '-created_at')[:10]  # Latest 10
        
        contribution_history = []
        for entry in contribution_history_qs:
            contribution_history.append({
                'id': entry.tx_id,
                'tier': entry.get_tier_display(),
                'asset_class': entry.asset_class,
                'internal_units': f"{entry.internal_units_value:,.0f} {entry.internal_units_label or ''}",
                'status': entry.get_status_display(),
                'date': entry.date.strftime('%Y-%m-%d'),
            })
        
        # Build member dict for template
        member_data = {
            'id': member.id,
            'name': member.legal_name,
            'role': member.role_title or '',
            'type': member.get_member_type_display(),
            'verified': member.verified,
            'equity_percentage': '—',  # Phase 4
            'cash_invested': float(cash_invested),
            'in_kind_value': float(in_kind_value),
            'time_hours': float(time_hours),
            'work_points': float(work_points),
            'email': member.email,
            'phone': member.phone or '',
            'joined_date': member.joined_date.strftime('%Y-%m-%d'),
            'bio': member.bio or '',
        }
        
        context = {
            'title': f"{member.legal_name} - Member Profile",
            'page_title': f"{member.legal_name} - Shareholders Management",
            'user': request.user,
            'member': member_data,
            'contribution_history': contribution_history,
        }
        
        return render(request, 'shareholders/member_detail.html', context)
        
    except Member.DoesNotExist:
        messages.error(request, f"Member with ID {member_id} not found.")
        return redirect('shareholders:members_overview')
    except Exception as e:
        logger.error(f"Error in member detail: {str(e)}")
        messages.error(request, f"Error loading member profile: {str(e)}")
        return redirect('shareholders:members_overview')


@login_required
@require_admin
def member_edit(request, member_id):
    """
    Edit Member Profile - Form for updating member information.
    
    Phase 1: Real POST handling to update Member records.
    """
    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found.")
            return redirect('shareholders:members_overview')
        
        # Get member
        member = get_object_or_404(Member, id=member_id, deal=deal)
        
        if request.method == 'POST':
            # Update editable fields
            member.legal_name = request.POST.get('legal_name', member.legal_name).strip()
            member.role_title = request.POST.get('role', member.role_title).strip()
            member.email = request.POST.get('email', member.email).strip()
            member.phone = request.POST.get('phone', member.phone).strip()
            member.bio = request.POST.get('bio', member.bio or '').strip()
            member.verified = request.POST.get('verified') == 'on'
            
            member.save()
            
            messages.success(request, f"Member {member.legal_name} updated successfully!")
            return redirect('shareholders:member_detail', member_id=member.id)
        
        # GET request - show form
        member_data = {
            'id': member.id,
            'name': member.legal_name,
            'role': member.role_title or '',
            'type': member.get_member_type_display(),
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
    
    Phase 1: Real POST handling to create LedgerEntry records.
    """
    try:
        deal = get_active_deal()
        if not deal:
            messages.warning(request, "No active deal found. Please create a deal first.")
            return redirect('shareholders:members_overview')
        
        # Get member_id from query param (optional)
        member_id = request.GET.get('member_id')
        selected_member = None
        
        if member_id:
            try:
                selected_member_obj = Member.objects.get(id=int(member_id), deal=deal)
                selected_member = {
                    'id': selected_member_obj.id,
                    'name': selected_member_obj.legal_name
                }
            except (ValueError, TypeError, Member.DoesNotExist):
                pass
        
        if request.method == 'POST':
            # Extract form data
            contributor_id = request.POST.get('member_id')
            tier = request.POST.get('tier', 'CASH')
            asset_class = request.POST.get('asset_class', '').strip()
            date_str = request.POST.get('date')
            internal_units = request.POST.get('internal_units', '').strip()
            value_usd = request.POST.get('value_usd', '0').strip()
            exchange_rate = request.POST.get('exchange_rate', '1.0').strip()
            notes = request.POST.get('notes', '').strip()
            
            # Validation
            if not contributor_id or not asset_class or not date_str or not value_usd:
                messages.error(request, "Missing required fields.")
                return render(request, 'shareholders/contribution_log.html', {
                    'title': 'Log New Contribution',
                    'page_title': 'Log New Contribution - Shareholders Management',
                    'user': request.user,
                    'selected_member': selected_member,
                })
            
            try:
                contributor = Member.objects.get(id=contributor_id, deal=deal)
                
                # Parse values
                value_usd_decimal = Decimal(value_usd.replace(',', ''))
                exchange_rate_decimal = Decimal(exchange_rate.split()[0]) if ' ' in exchange_rate else Decimal(exchange_rate)
                
                # Parse internal units
                internal_units_parts = internal_units.split()
                if len(internal_units_parts) >= 2:
                    internal_units_value = Decimal(internal_units_parts[0].replace(',', ''))
                    internal_units_label = ' '.join(internal_units_parts[1:])
                else:
                    internal_units_value = Decimal(internal_units.replace(',', '')) if internal_units else value_usd_decimal
                    internal_units_label = 'USD' if tier == 'CASH' else ''
                
                # Create ledger entry
                entry = LedgerEntry.objects.create(
                    deal=deal,
                    contributor=contributor,
                    tier=tier,
                    asset_class=asset_class,
                    internal_units_value=internal_units_value,
                    internal_units_label=internal_units_label,
                    value_usd=value_usd_decimal,
                    currency='USD',
                    exchange_rate=exchange_rate_decimal,
                    status='SUBMITTED',  # Default status
                    date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                    notes=notes
                )
                
                messages.success(request, f"Contribution {entry.tx_id} logged successfully!")
                return redirect('shareholders:ledgers_view')
                
            except Member.DoesNotExist:
                messages.error(request, "Selected member not found.")
            except (ValueError, Decimal.InvalidOperation) as e:
                messages.error(request, f"Invalid numeric value: {str(e)}")
            except Exception as e:
                logger.error(f"Error creating ledger entry: {str(e)}")
                messages.error(request, f"Error: {str(e)}")
        
        # GET request - show form
        # Get all active members for the dropdown
        all_members = Member.objects.filter(deal=deal, is_archived=False).order_by('legal_name')
        
        context = {
            'title': 'Log New Contribution',
            'page_title': 'Log New Contribution - Shareholders Management',
            'user': request.user,
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
