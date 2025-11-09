"""
Broker API integration service.

Phase 4 enhancement: synchronize managed trading accounts with supported broker APIs
without duplicating existing position logic.
"""

import logging
from dataclasses import dataclass
from decimal import Decimal, DecimalException
from typing import Any, Dict, Iterable, List, Optional

from django.core.exceptions import ValidationError
from django.utils import timezone

from .base_service import BaseInvestingService
from ..models import (
    BrokerConnection,
    ManagedTradingAccount,
    OptionsPosition,
    TradingActivity,
)

logger = logging.getLogger(__name__)


@dataclass
class BrokerSyncResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0

    def as_dict(self) -> Dict[str, int]:
        return {'created': self.created, 'updated': self.updated, 'skipped': self.skipped}


class BrokerAPIService(BaseInvestingService):
    """
    Service responsible for syncing managed trading accounts with broker APIs.

    This class intentionally avoids direct HTTP implementation details so that
    individual broker adapters can plug in via `_fetch_from_broker`.
    """

    SUPPORTED_BROKERS = {
        'td': 'TD Ameritrade',
        'ibkr': 'Interactive Brokers',
        'tasty': 'Tastytrade',
        'schwab': 'Schwab',
    }

    def sync_positions(
        self,
        account: ManagedTradingAccount,
        *,
        broker_payload: Optional[Iterable[Dict[str, Any]]] = None,
        performed_by=None,
    ) -> Dict[str, int]:
        """
        Synchronise open positions for a managed account from its broker connection.

        Args:
            account: ManagedTradingAccount to sync.
            broker_payload: Optional iterable payload (mostly for tests) to bypass API calls.
            performed_by: Optional user performing the sync, recorded in activity log.

        Returns:
            Dictionary summary with created/updated/skipped counts.
        """
        connection = self._get_connection(account)
        if not connection.has_credentials:
            raise ValidationError("Broker credentials are not configured for this account.")

        payload = broker_payload if broker_payload is not None else self._fetch_from_broker(connection)

        result = BrokerSyncResult()
        for raw_position in payload or []:
            mapped = self._map_position_payload(raw_position, account)
            if not mapped:
                result.skipped += 1
                continue

            filters = mapped.pop('lookup')
            defaults = mapped.pop('defaults')

            position, created = OptionsPosition.objects.update_or_create(
                managed_account=account,
                **filters,
                defaults=defaults,
            )
            if created:
                result.created += 1
            else:
                result.updated += 1

        connection.last_sync = timezone.now()
        connection.save(update_fields=['last_sync', 'updated_at'])

        self._log_sync_activity(account, result, performed_by)
        logger.info(
            "Broker sync completed for account %s (%s) - %s",
            account.account_number,
            connection.get_broker_display(),
            result.as_dict(),
        )

        return result.as_dict()

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _get_connection(self, account: ManagedTradingAccount) -> BrokerConnection:
        try:
            return account.broker_connection
        except BrokerConnection.DoesNotExist as exc:
            raise ValidationError("Managed account is not linked to a broker connection.") from exc

    def _fetch_from_broker(self, connection: BrokerConnection) -> List[Dict[str, Any]]:
        """
        Placeholder for concrete broker implementation.

        Subclasses or adapters should override this method to perform actual API calls.
        """
        raise NotImplementedError(
            f"Broker API fetching not implemented for broker '{connection.broker}'."
        )

    def _map_position_payload(
        self,
        payload: Dict[str, Any],
        account: ManagedTradingAccount,
    ) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Normalise broker payload into OptionPosition-compatible defaults.
        """
        try:
            symbol = payload['symbol'].upper()
            strategy = payload.get('strategy', 'other')
            expiration = payload.get('expiration_date')
        except KeyError:
            logger.warning("Broker payload missing required keys: %s", payload)
            return None

        premium = self._to_decimal(payload.get('premium_collected', 0))
        capital_required = self._to_decimal(payload.get('capital_required', 0))
        unrealized = self._to_decimal(payload.get('unrealized_pnl', 0))
        realized = self._to_decimal(payload.get('realized_pnl', 0))

        lookup = {
            'symbol': symbol,
            'strategy': strategy,
        }
        if expiration:
            lookup['expiration_date'] = expiration

        defaults = {
            'positions': payload.get('legs') or [],
            'capital_required': capital_required,
            'premium_collected': premium,
            'max_profit': payload.get('max_profit', premium),
            'max_loss': payload.get('max_loss', capital_required - premium),
            'current_value': payload.get('current_value', premium),
            'unrealized_pnl': unrealized,
            'realized_pnl': realized,
            'status': payload.get('status', 'open'),
            'notes': payload.get('notes', '') or f"Synced from {account.account_number} broker feed.",
        }

        # Optional fields
        if payload.get('entry_date'):
            defaults['entry_date'] = payload['entry_date']
        if payload.get('exit_date'):
            defaults['exit_date'] = payload['exit_date']
        if payload.get('position_delta') is not None:
            defaults['position_delta'] = self._to_decimal(payload['position_delta'])
        if payload.get('position_theta') is not None:
            defaults['position_theta'] = self._to_decimal(payload['position_theta'])

        return {'lookup': lookup, 'defaults': defaults}

    def _to_decimal(self, value: Any) -> Decimal:
        try:
            return Decimal(str(value))
        except (DecimalException, TypeError, ValueError):
            return Decimal('0')

    def _log_sync_activity(
        self,
        account: ManagedTradingAccount,
        result: BrokerSyncResult,
        performed_by,
    ):
        description = (
            f"Broker sync completed ({result.created} created, "
            f"{result.updated} updated, {result.skipped} skipped)"
        )
        TradingActivity.objects.create(
            managed_account=account,
            activity_type='broker_sync',
            description=description,
            performed_by=performed_by,
            data_snapshot=result.as_dict(),
        )

