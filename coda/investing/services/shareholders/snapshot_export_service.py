"""
Snapshot Export Service

Generates CSV exports for snapshot data.
"""

import csv
from io import StringIO
from typing import List
from django.http import HttpResponse
import logging

from investing.models import EquitySnapshot, EquitySnapshotLine

logger = logging.getLogger(__name__)


class SnapshotExportService:
    """
    Service for exporting snapshots to CSV format.
    """
    
    @staticmethod
    def export_snapshot_list_csv(snapshots: List[EquitySnapshot]) -> HttpResponse:
        """
        Export a list of snapshots to CSV.
        
        Args:
            snapshots: List of EquitySnapshot instances
            
        Returns:
            HttpResponse with CSV content
        """
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Version ID',
            'Snapshot Date',
            'Period Start',
            'Period End',
            'Status',
            'Is Locked',
            'Members Count',
            'Total Cash (USD)',
            'Total In-Kind (USD)',
            'Total Time (USD)',
            'Total Work (USD)',
            'Total Valuation (USD)',
            'Checksum',
            'Created By',
            'Created At',
            'Locked By',
            'Locked At',
        ])
        
        # Write rows
        for snapshot in snapshots:
            writer.writerow([
                snapshot.version_id,
                snapshot.snapshot_date.strftime('%Y-%m-%d'),
                snapshot.period_start.strftime('%Y-%m-%d'),
                snapshot.period_end.strftime('%Y-%m-%d'),
                snapshot.get_status_display(),
                'Yes' if snapshot.is_locked else 'No',
                snapshot.members_count,
                f"{snapshot.total_cash_usd:.2f}",
                f"{snapshot.total_inkind_usd:.2f}",
                f"{snapshot.total_time_usd:.2f}",
                f"{snapshot.total_work_usd:.2f}",
                f"{snapshot.total_valuation_usd:.2f}",
                snapshot.checksum,
                snapshot.created_by.username if snapshot.created_by else '',
                snapshot.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                snapshot.locked_by.username if snapshot.locked_by else '',
                snapshot.locked_at.strftime('%Y-%m-%d %H:%M:%S') if snapshot.locked_at else '',
            ])
        
        # Create response
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="snapshots_export.csv"'
        
        logger.info(f"Exported {len(snapshots)} snapshots to CSV")
        
        return response
    
    @staticmethod
    def export_snapshot_detail_csv(snapshot: EquitySnapshot) -> HttpResponse:
        """
        Export detailed snapshot with member breakdown to CSV.
        
        Args:
            snapshot: EquitySnapshot instance
            
        Returns:
            HttpResponse with CSV content
        """
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Write snapshot header
        writer.writerow(['SNAPSHOT SUMMARY'])
        writer.writerow(['Version ID', snapshot.version_id])
        writer.writerow(['Snapshot Date', snapshot.snapshot_date.strftime('%Y-%m-%d')])
        writer.writerow(['Period', f"{snapshot.period_start.strftime('%Y-%m-%d')} to {snapshot.period_end.strftime('%Y-%m-%d')}"])
        writer.writerow(['Status', snapshot.get_status_display()])
        writer.writerow(['Is Locked', 'Yes' if snapshot.is_locked else 'No'])
        writer.writerow(['Checksum', snapshot.checksum])
        writer.writerow([])
        
        # Write totals
        writer.writerow(['TOTALS'])
        writer.writerow(['Total Cash (USD)', f"${snapshot.total_cash_usd:.2f}"])
        writer.writerow(['Total In-Kind (USD)', f"${snapshot.total_inkind_usd:.2f}"])
        writer.writerow(['Total Time (USD)', f"${snapshot.total_time_usd:.2f}"])
        writer.writerow(['Total Work (USD)', f"${snapshot.total_work_usd:.2f}"])
        writer.writerow(['Total Valuation (USD)', f"${snapshot.total_valuation_usd:.2f}"])
        writer.writerow([])
        
        # Write member breakdown header
        writer.writerow(['MEMBER BREAKDOWN'])
        writer.writerow([
            'Member Name',
            'Member Type',
            'Role',
            'Cash (USD)',
            'In-Kind (USD)',
            'Time (USD)',
            'Work (USD)',
            'Weighted Total (USD)',
            'Equity %',
        ])
        
        # Write member rows
        lines = snapshot.lines.all().order_by('-equity_percentage', 'member_name')
        for line in lines:
            writer.writerow([
                line.member_name,
                line.member_type,
                line.member_role or '',
                f"{line.cash_usd:.2f}",
                f"{line.inkind_usd:.2f}",
                f"{line.time_usd:.2f}",
                f"{line.work_usd:.2f}",
                f"{line.weighted_total_usd:.2f}",
                f"{line.equity_percentage:.2f}%",
            ])
        
        # Create response
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        filename = f"snapshot_{snapshot.version_id}_{snapshot.snapshot_date.strftime('%Y%m%d')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        logger.info(f"Exported snapshot {snapshot.version_id} detail to CSV")
        
        return response
