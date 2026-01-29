""" Shareholders Management System Views

This module provides views for the Shareholders Management System.
Access is restricted to admin users only (same permission as Automation dashboard).
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import logging
from datetime import datetime, timedelta

from core.permissions import is_admin, require_admin

logger = logging.getLogger(__name__)


@login_required
@require_admin
def shareholders_dashboard(request):
    """
    Main shareholders dashboard view.
    
    Access Control:
        - Requires login
        - Requires admin privileges (is_staff or is_superuser)
        - Same permission logic as Automation dashboard
    
    If unauthorized user tries to access directly via URL, they are redirected
    to the unified dashboard with an error message.
    """
    try:
        context = {
            'title': 'Shareholders Management Dashboard',
            'page_title': 'Shareholders Management System',
            'user': request.user,
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
    Ledger Snapshots view - Displays contribution ledger entries.
    
    Access Control:
        - Requires login
        - Requires admin privileges (is_staff or is_superuser)
        - Same permission logic as Automation dashboard
    
    This is a frontend-only view using dummy data structured to match
    future backend models. When models are created, simply replace the
    dummy data with querysets without changing the template structure.
    
    Data Structure (Backend-Ready):
        - ledger_entries: List of dicts mimicking future LedgerEntry model
        - summary_stats: Dict mimicking future aggregated queries
        - tier_legend: Reference data for contribution tiers
        - status_types: Reference data for entry statuses
    """
    try:
        # DUMMY DATA - Structured to match future backend models
        # When backend is implemented, replace with:
        # ledger_entries = LedgerEntry.objects.filter(...).order_by('-date')
        
        ledger_entries = [
            {
                'id': 'TX-9012',
                'contributor_name': 'Alice Mwangi',
                'tier': 'Cash',
                'asset_class': 'Capital Injection',
                'internal_units': '15,000',
                'value_usd': 15000,
                'status': 'Approved',
                'date': '2025-12-10',
                'notes': 'Initial Seed Round',
                'has_proof': True,
            },
            {
                'id': 'TX-9013',
                'contributor_name': 'Bob Chen',
                'tier': 'Work',
                'asset_class': 'Dev Architecture',
                'internal_units': '450 pts',
                'value_usd': 4500,
                'status': 'In Dispute',
                'date': '2025-12-11',
                'notes': 'Disputed hours count',
                'has_proof': True,
            },
            {
                'id': 'TX-9014',
                'contributor_name': 'David Kim',
                'tier': 'Time',
                'asset_class': 'Project Mgt',
                'internal_units': '120 hrs',
                'value_usd': 1200,
                'status': 'Approved',
                'date': '2025-12-12',
                'notes': 'Weekly syncs Q4',
                'has_proof': False,
            },
            {
                'id': 'TX-9015',
                'contributor_name': 'Global Ventures',
                'tier': 'Cash',
                'asset_class': 'Series A Entry',
                'internal_units': '50,000',
                'value_usd': 50000,
                'status': 'Approved',
                'date': '2025-12-14',
                'notes': 'Equity buy-in',
                'has_proof': True,
            },
            {
                'id': 'TX-9016',
                'contributor_name': 'Alice Mwangi',
                'tier': 'In-Kind',
                'asset_class': 'Hardware',
                'internal_units': '2 Units',
                'value_usd': 2000,
                'status': 'Pending',
                'date': '2025-12-15',
                'notes': 'MacBook Pro M3 Max',
                'has_proof': True,
            },
            {
                'id': 'TX-9017',
                'contributor_name': 'Bob Chen',
                'tier': 'In-Kind',
                'asset_class': 'Office Lease',
                'internal_units': '3 Months',
                'value_usd': 3000,
                'status': 'Approved',
                'date': '2025-12-16',
                'notes': 'Hub co-working space',
                'has_proof': True,
            },
            {
                'id': 'TX-9018',
                'contributor_name': 'David Kim',
                'tier': 'Work',
                'asset_class': 'QA Testing',
                'internal_units': '80 pts',
                'value_usd': 800,
                'status': 'Pending',
                'date': '2025-12-18',
                'notes': 'V1.2 Stability tests',
                'has_proof': False,
            },
        ]
        
        # Summary statistics (future: aggregated from db)
        summary_stats = {
            'total_volume_usd': 76500,  # Future: LedgerEntry.objects.aggregate(Sum('value_usd'))
            'approved_count': 142,      # Future: LedgerEntry.objects.filter(status='Approved').count()
            'in_dispute_count': 3,      # Future: LedgerEntry.objects.filter(status='In Dispute').count()
            'latest_checksum': '0x8f2d...e1',  # Future: Snapshot.objects.latest().checksum
        }
        
        # Tier legend (future: from model choices)
        tier_legend = [
            {'name': 'Cash', 'color': 'emerald', 'description': 'Cash Contribution'},
            {'name': 'In-Kind', 'color': 'blue', 'description': 'In-Kind Asset'},
            {'name': 'Time', 'color': 'indigo', 'description': 'Time Logged'},
            {'name': 'Work', 'color': 'amber', 'description': 'Work Unit'},
        ]
        
        # Status types (future: from model choices)
        status_types = ['Approved', 'Pending', 'In Dispute']
        
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
    Members & Equity Overview - Main members listing page.
    
    Access Control:
        - Requires login
        - Requires admin privileges (is_staff or is_superuser)
    
    This is a frontend-only view with dummy data structured for future backend.
    When models are created, replace dummy data with querysets.
    
    Data Structure (Backend-Ready):
        - members: List of dicts mimicking future Member/Shareholder model
        - summary_stats: Dict with aggregated member statistics
    """
    try:
        # DUMMY DATA - Structured to match future backend models
        # When backend is implemented, replace with:
        # members = Member.objects.filter(is_active=True).order_by('-equity_percentage')
        
        members = [
            {
                'id': 1,
                'name': 'Alice Mwangi',
                'role': 'Founder',
                'type': 'Person',
                'verified': True,
                'equity_percentage': 35.5,
                'cash_invested': 15000,
                'in_kind_value': 2000,
                'time_hours': 450,
                'work_points': 120,
                'email': 'alice@phoenix.io',
                'phone': '+254 712 345 678',
                'joined_date': '2025-01-10',
                'bio': 'Serial entrepreneur focused on African fintech growth.',
            },
            {
                'id': 2,
                'name': 'Bob Chen',
                'role': 'Lead Dev',
                'type': 'Person',
                'verified': True,
                'equity_percentage': 28.2,
                'cash_invested': 2000,
                'in_kind_value': 5000,
                'time_hours': 800,
                'work_points': 450,
                'email': 'bob@dev.net',
                'phone': '+254 722 000 111',
                'joined_date': '2025-02-15',
                'bio': 'Full stack architect with experience in blockchain and high-scale systems.',
            },
            {
                'id': 3,
                'name': 'Global Ventures',
                'role': 'Investor',
                'type': 'Entity',
                'verified': True,
                'equity_percentage': 30.3,
                'cash_invested': 50000,
                'in_kind_value': 0,
                'time_hours': 50,
                'work_points': 0,
                'email': 'ops@globalv.com',
                'phone': '+1 555 0199',
                'joined_date': '2025-03-01',
                'bio': 'Venture capital firm specializing in emerging markets.',
            },
            {
                'id': 4,
                'name': 'David Kim',
                'role': 'PM',
                'type': 'Person',
                'verified': False,
                'equity_percentage': 6.0,
                'cash_invested': 0,
                'in_kind_value': 1500,
                'time_hours': 600,
                'work_points': 300,
                'email': 'dkim@pm.org',
                'phone': '+254 733 999 888',
                'joined_date': '2025-05-12',
                'bio': 'Agile project manager with a focus on lean development methodologies.',
            },
        ]
        
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
    
    Access Control:
        - Requires login
        - Requires admin privileges
    
    This is a frontend-only view. When backend is implemented,
    add POST handling to create Member instances.
    """
    try:
        # Role catalog (future: from model choices)
        role_catalog = [
            'Founder',
            'Lead Developer',
            'Investor',
            'Project Manager',
            'Marketing Lead',
            'Finance Officer',
            'External Partner',
        ]
        
        context = {
            'title': 'Register Member',
            'page_title': 'Register New Member - Shareholders Management',
            'user': request.user,
            'role_catalog': role_catalog,
        }
        
        return render(request, 'shareholders/member_register.html', context)
        
    except Exception as e:
        logger.error(f"Error in member register: {str(e)}")
        messages.error(request, f"Error loading registration form: {str(e)}")
        return redirect('shareholders:members_overview')


@login_required
@require_admin
def member_detail(request, member_id):
    """
    Member Profile Detail View - Shows comprehensive member information.
    
    Access Control:
        - Requires login
        - Requires admin privileges
    
    Args:
        member_id: ID of the member to display
    
    This is a frontend-only view. When backend is implemented:
    member = get_object_or_404(Member, id=member_id)
    """
    try:
        # DUMMY DATA - Find member by ID
        # Future: member = get_object_or_404(Member, id=member_id)
        
        all_members = [
            {
                'id': 1,
                'name': 'Alice Mwangi',
                'role': 'Founder',
                'type': 'Person',
                'verified': True,
                'equity_percentage': 35.5,
                'cash_invested': 15000,
                'in_kind_value': 2000,
                'time_hours': 450,
                'work_points': 120,
                'email': 'alice@phoenix.io',
                'phone': '+254 712 345 678',
                'joined_date': '2025-01-10',
                'bio': 'Serial entrepreneur focused on African fintech growth.',
            },
            {
                'id': 2,
                'name': 'Bob Chen',
                'role': 'Lead Dev',
                'type': 'Person',
                'verified': True,
                'equity_percentage': 28.2,
                'cash_invested': 2000,
                'in_kind_value': 5000,
                'time_hours': 800,
                'work_points': 450,
                'email': 'bob@dev.net',
                'phone': '+254 722 000 111',
                'joined_date': '2025-02-15',
                'bio': 'Full stack architect with experience in blockchain and high-scale systems.',
            },
            {
                'id': 3,
                'name': 'Global Ventures',
                'role': 'Investor',
                'type': 'Entity',
                'verified': True,
                'equity_percentage': 30.3,
                'cash_invested': 50000,
                'in_kind_value': 0,
                'time_hours': 50,
                'work_points': 0,
                'email': 'ops@globalv.com',
                'phone': '+1 555 0199',
                'joined_date': '2025-03-01',
                'bio': 'Venture capital firm specializing in emerging markets.',
            },
            {
                'id': 4,
                'name': 'David Kim',
                'role': 'PM',
                'type': 'Person',
                'verified': False,
                'equity_percentage': 6.0,
                'cash_invested': 0,
                'in_kind_value': 1500,
                'time_hours': 600,
                'work_points': 300,
                'email': 'dkim@pm.org',
                'phone': '+254 733 999 888',
                'joined_date': '2025-05-12',
                'bio': 'Agile project manager with a focus on lean development methodologies.',
            },
        ]
        
        member = next((m for m in all_members if m['id'] == member_id), None)
        
        if not member:
            messages.error(request, f"Member with ID {member_id} not found.")
            return redirect('shareholders:members_overview')
        
        # Mock contribution history for this member
        contribution_history = [
            {
                'id': 'TX-9012',
                'tier': 'Cash',
                'asset_class': 'Capital Injection',
                'internal_units': '15,000',
                'status': 'Approved',
                'date': '2025-12-10',
            }
        ] if member['id'] == 1 else []
        
        context = {
            'title': f"{member['name']} - Member Profile",
            'page_title': f"{member['name']} - Shareholders Management",
            'user': request.user,
            'member': member,
            'contribution_history': contribution_history,
        }
        
        return render(request, 'shareholders/member_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error in member detail: {str(e)}")
        messages.error(request, f"Error loading member profile: {str(e)}")
        return redirect('shareholders:members_overview')


@login_required
@require_admin
def member_edit(request, member_id):
    """
    Edit Member Profile - Form for updating member information.
    
    Access Control:
        - Requires login
        - Requires admin privileges
    
    Args:
        member_id: ID of the member to edit
    
    This is a frontend-only view. When backend is implemented,
    add POST handling to update Member instances.
    """
    try:
        # DUMMY DATA - Same as member_detail
        all_members = [
            {
                'id': 1,
                'name': 'Alice Mwangi',
                'role': 'Founder',
                'type': 'Person',
                'verified': True,
                'equity_percentage': 35.5,
                'cash_invested': 15000,
                'in_kind_value': 2000,
                'time_hours': 450,
                'work_points': 120,
                'email': 'alice@phoenix.io',
                'phone': '+254 712 345 678',
                'joined_date': '2025-01-10',
                'bio': 'Serial entrepreneur focused on African fintech growth.',
            },
            {
                'id': 2,
                'name': 'Bob Chen',
                'role': 'Lead Dev',
                'type': 'Person',
                'verified': True,
                'equity_percentage': 28.2,
                'cash_invested': 2000,
                'in_kind_value': 5000,
                'time_hours': 800,
                'work_points': 450,
                'email': 'bob@dev.net',
                'phone': '+254 722 000 111',
                'joined_date': '2025-02-15',
                'bio': 'Full stack architect with experience in blockchain and high-scale systems.',
            },
            {
                'id': 3,
                'name': 'Global Ventures',
                'role': 'Investor',
                'type': 'Entity',
                'verified': True,
                'equity_percentage': 30.3,
                'cash_invested': 50000,
                'in_kind_value': 0,
                'time_hours': 50,
                'work_points': 0,
                'email': 'ops@globalv.com',
                'phone': '+1 555 0199',
                'joined_date': '2025-03-01',
                'bio': 'Venture capital firm specializing in emerging markets.',
            },
            {
                'id': 4,
                'name': 'David Kim',
                'role': 'PM',
                'type': 'Person',
                'verified': False,
                'equity_percentage': 6.0,
                'cash_invested': 0,
                'in_kind_value': 1500,
                'time_hours': 600,
                'work_points': 300,
                'email': 'dkim@pm.org',
                'phone': '+254 733 999 888',
                'joined_date': '2025-05-12',
                'bio': 'Agile project manager with a focus on lean development methodologies.',
            },
        ]
        
        member = next((m for m in all_members if m['id'] == member_id), None)
        
        if not member:
            messages.error(request, f"Member with ID {member_id} not found.")
            return redirect('shareholders:members_overview')
        
        # Role catalog
        role_catalog = [
            'Founder',
            'Lead Developer',
            'Investor',
            'Project Manager',
            'Marketing Lead',
            'Finance Officer',
            'External Partner',
        ]
        
        context = {
            'title': f"Edit {member['name']}",
            'page_title': f"Edit Member - Shareholders Management",
            'user': request.user,
            'member': member,
            'role_catalog': role_catalog,
        }
        
        return render(request, 'shareholders/member_edit.html', context)
        
    except Exception as e:
        logger.error(f"Error in member edit: {str(e)}")
        messages.error(request, f"Error loading edit form: {str(e)}")
        return redirect('shareholders:members_overview')


@login_required
@require_admin
def contribution_log(request):
    """
    Log New Contribution - Form for recording member contributions.
    
    Access Control:
        - Requires login
        - Requires admin privileges
    
    This is a frontend-only view. When backend is implemented,
    add POST handling to create LedgerEntry instances.
    """
    try:
        # Get member_id from query param (optional)
        member_id = request.GET.get('member_id')
        selected_member = None
        
        if member_id:
            try:
                member_id = int(member_id)
                # Future: selected_member = get_object_or_404(Member, id=member_id)
                all_members = [
                    {'id': 1, 'name': 'Alice Mwangi'},
                    {'id': 2, 'name': 'Bob Chen'},
                    {'id': 3, 'name': 'Global Ventures'},
                    {'id': 4, 'name': 'David Kim'},
                ]
                selected_member = next((m for m in all_members if m['id'] == member_id), None)
            except (ValueError, TypeError):
                pass
        
        context = {
            'title': 'Log New Contribution',
            'page_title': 'Log New Contribution - Shareholders Management',
            'user': request.user,
            'selected_member': selected_member,
        }
        
        return render(request, 'shareholders/contribution_log.html', context)
        
    except Exception as e:
        logger.error(f"Error in contribution log: {str(e)}")
        messages.error(request, f"Error loading contribution form: {str(e)}")
        return redirect('shareholders:members_overview')
