""" Shareholders Management System Views

This module provides views for the Shareholders Management System.
Access is restricted to admin users only (same permission as Automation dashboard).
"""

from django.shortcuts import render, redirect
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
