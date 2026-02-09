"""
Ledger Checksum Service - Deterministic checksum generation.

Migrated to investing app - models imported from shareholders app.
"""

import hashlib
import json
from decimal import Decimal
import logging

# Models imported from original shareholders app (preserves DB ownership)
from investing.models_shareholders import Deal, LedgerEntry

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


class LedgerChecksumService:
    """Service for generating deterministic ledger checksums."""
    
    def __init__(self, deal: Deal):
        self.deal = deal
    
    def get_canonical_data(self) -> str:
        entries = LedgerEntry.objects.filter(
            deal=self.deal,
            status__in=['APPROVED', 'SUBMITTED']
        ).order_by('date', 'tx_id')
        
        if not entries.exists():
            return ''
        
        data_list = []
        for entry in entries:
            data_list.append({
                'tx_id': entry.tx_id,
                'tier': entry.tier,
                'value_usd': str(entry.value_usd),
                'date': entry.date.isoformat(),
                'status': entry.status,
            })
        
        return json.dumps(data_list, cls=DecimalEncoder, sort_keys=True)
    
    def calculate_checksum(self) -> str:
        canonical_data = self.get_canonical_data()
        if not canonical_data:
            return '0x0000...0000'
        hash_bytes = hashlib.sha256(canonical_data.encode('utf-8')).hexdigest()
        return f'0x{hash_bytes[:8]}...{hash_bytes[-4:]}'
    
    def get_full_checksum(self) -> str:
        canonical_data = self.get_canonical_data()
        if not canonical_data:
            return '0' * 64
        return hashlib.sha256(canonical_data.encode('utf-8')).hexdigest()
