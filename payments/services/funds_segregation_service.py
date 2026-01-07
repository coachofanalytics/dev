"""
Funds Segregation Service for Bankruptcy Protection.

This service manages the segregation of customer funds from operational funds,
ensuring compliance with financial regulations and providing bankruptcy protection.
"""

from decimal import Decimal
from django.db import transaction as db_transaction
from django.db.models import Sum
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class FundsSegregationService:
    """
    Service for managing segregated customer funds and ensuring bankruptcy protection.
    """

    @staticmethod
    def record_customer_deposit(transaction_obj, user=None):
        """
        Record a customer deposit in the segregated funds ledger.
        Called when a customer deposits funds into their wallet.
        """
        from ..models import SegregatedFundsLedger, Wallet

        try:
            with db_transaction.atomic():
                # Get current customer funds balance
                current_balance = FundsSegregationService.get_customer_funds_balance()
                new_balance = current_balance + transaction_obj.amount

                # Create ledger entry
                entry = SegregatedFundsLedger.objects.create(
                    fund_type='customer',
                    entry_type='deposit',
                    amount=transaction_obj.amount,
                    balance_after=new_balance,
                    reference_transaction=transaction_obj,
                    user=transaction_obj.user,
                    description=f"Customer deposit via {transaction_obj.payment_gateway}",
                    metadata={
                        'transaction_id': transaction_obj.transaction_id,
                        'gateway': transaction_obj.payment_gateway,
                        'wallet_id': transaction_obj.wallet.id if transaction_obj.wallet else None,
                    }
                )
                logger.info(f"Recorded customer deposit: {entry.entry_id} - ${transaction_obj.amount}")
                return entry

        except Exception as e:
            logger.error(f"Failed to record customer deposit: {str(e)}")
            return None

    @staticmethod
    def record_customer_withdrawal(transaction_obj, user=None):
        """
        Record a customer withdrawal/payment from segregated funds.
        Called when customer uses wallet funds for payment.
        """
        from ..models import SegregatedFundsLedger

        try:
            with db_transaction.atomic():
                current_balance = FundsSegregationService.get_customer_funds_balance()
                new_balance = current_balance - transaction_obj.amount

                entry = SegregatedFundsLedger.objects.create(
                    fund_type='customer',
                    entry_type='withdrawal',
                    amount=-transaction_obj.amount,
                    balance_after=new_balance,
                    reference_transaction=transaction_obj,
                    user=transaction_obj.user,
                    description=f"Customer payment for {transaction_obj.transaction_type}",
                    metadata={
                        'transaction_id': transaction_obj.transaction_id,
                        'transaction_type': transaction_obj.transaction_type,
                    }
                )
                logger.info(f"Recorded customer withdrawal: {entry.entry_id} - ${transaction_obj.amount}")
                return entry

        except Exception as e:
            logger.error(f"Failed to record customer withdrawal: {str(e)}")
            return None

    @staticmethod
    def record_fee_collection(amount, description, user=None, transaction_obj=None):
        """
        Record platform fee collection (moves from customer to operational).
        """
        from ..models import SegregatedFundsLedger

        try:
            with db_transaction.atomic():
                # Deduct from customer funds
                customer_balance = FundsSegregationService.get_customer_funds_balance()
                new_customer_balance = customer_balance - amount

                SegregatedFundsLedger.objects.create(
                    fund_type='customer',
                    entry_type='fee_collection',
                    amount=-amount,
                    balance_after=new_customer_balance,
                    reference_transaction=transaction_obj,
                    user=user,
                    description=f"Fee collected: {description}",
                )

                # Add to operational funds
                operational_balance = FundsSegregationService.get_operational_funds_balance()
                new_operational_balance = operational_balance + amount

                entry = SegregatedFundsLedger.objects.create(
                    fund_type='operational',
                    entry_type='fee_collection',
                    amount=amount,
                    balance_after=new_operational_balance,
                    reference_transaction=transaction_obj,
                    user=user,
                    description=f"Fee received: {description}",
                )

                logger.info(f"Recorded fee collection: ${amount}")
                return entry

        except Exception as e:
            logger.error(f"Failed to record fee collection: {str(e)}")
            return None

    @staticmethod
    def record_refund(transaction_obj, user=None):
        """
        Record a refund to customer.
        """
        from ..models import SegregatedFundsLedger

        try:
            with db_transaction.atomic():
                current_balance = FundsSegregationService.get_customer_funds_balance()
                new_balance = current_balance + transaction_obj.amount

                entry = SegregatedFundsLedger.objects.create(
                    fund_type='customer',
                    entry_type='refund',
                    amount=transaction_obj.amount,
                    balance_after=new_balance,
                    reference_transaction=transaction_obj,
                    user=transaction_obj.user,
                    description=f"Refund processed for transaction {transaction_obj.transaction_id}",
                    metadata={
                        'original_transaction_id': transaction_obj.transaction_id,
                    }
                )
                logger.info(f"Recorded refund: {entry.entry_id} - ${transaction_obj.amount}")
                return entry

        except Exception as e:
            logger.error(f"Failed to record refund: {str(e)}")
            return None

    @staticmethod
    def get_customer_funds_balance():
        """
        Get the current total balance of segregated customer funds.
        """
        from ..models import SegregatedFundsLedger

        last_entry = SegregatedFundsLedger.objects.filter(
            fund_type='customer'
        ).order_by('-created_at').first()

        if last_entry:
            return last_entry.balance_after
        return Decimal('0.00')

    @staticmethod
    def get_operational_funds_balance():
        """
        Get the current total balance of operational funds.
        """
        from ..models import SegregatedFundsLedger

        last_entry = SegregatedFundsLedger.objects.filter(
            fund_type='operational'
        ).order_by('-created_at').first()

        if last_entry:
            return last_entry.balance_after
        return Decimal('0.00')

    @staticmethod
    def perform_daily_reconciliation(performed_by=None):
        """
        Perform daily reconciliation of customer funds.
        Compares total wallet balances with segregated funds ledger.
        """
        from ..models import Wallet, FundsReconciliation

        try:
            today = timezone.now().date()

            # Check if already reconciled today
            existing = FundsReconciliation.objects.filter(reconciliation_date=today).first()
            if existing:
                logger.info(f"Reconciliation already exists for {today}")
                return existing

            with db_transaction.atomic():
                # Sum all customer wallet balances
                total_wallets = Wallet.objects.aggregate(
                    total=Sum('balance')
                )['total'] or Decimal('0.00')

                # Get segregated funds balance
                total_ledger = FundsSegregationService.get_customer_funds_balance()

                # Create reconciliation record
                reconciliation = FundsReconciliation.objects.create(
                    reconciliation_date=today,
                    total_customer_wallets=total_wallets,
                    total_customer_funds_ledger=total_ledger,
                    performed_by=performed_by,
                )

                if reconciliation.status == 'discrepancy':
                    logger.warning(
                        f"Reconciliation discrepancy found: "
                        f"Wallets=${total_wallets}, Ledger=${total_ledger}, "
                        f"Diff=${reconciliation.discrepancy_amount}"
                    )
                else:
                    logger.info(f"Reconciliation successful for {today}: ${total_wallets}")

                return reconciliation

        except Exception as e:
            logger.error(f"Failed to perform reconciliation: {str(e)}")
            return None

    @staticmethod
    def get_funds_summary():
        """
        Get a summary of all segregated funds.
        """
        from ..models import Wallet, FundsReconciliation, CustomerFundsProtection

        total_wallets = Wallet.objects.aggregate(
            total=Sum('balance')
        )['total'] or Decimal('0.00')

        customer_funds = FundsSegregationService.get_customer_funds_balance()
        operational_funds = FundsSegregationService.get_operational_funds_balance()

        last_reconciliation = FundsReconciliation.objects.order_by('-reconciliation_date').first()
        protection_config = CustomerFundsProtection.get_current()

        return {
            'total_customer_wallets': total_wallets,
            'segregated_customer_funds': customer_funds,
            'operational_funds': operational_funds,
            'discrepancy': abs(total_wallets - customer_funds),
            'last_reconciliation': last_reconciliation,
            'protection_status': protection_config.compliance_status,
            'segregation_policy': protection_config.segregation_policy,
        }

    @staticmethod
    def get_ledger_entries(fund_type=None, limit=100):
        """
        Get recent ledger entries for audit purposes.
        """
        from ..models import SegregatedFundsLedger

        queryset = SegregatedFundsLedger.objects.all()
        if fund_type:
            queryset = queryset.filter(fund_type=fund_type)

        return queryset[:limit]

    @staticmethod
    def initialize_funds_from_wallets():
        """
        Initialize segregated funds ledger from existing wallet balances.
        Use this once during initial setup.
        """
        from ..models import Wallet, SegregatedFundsLedger

        # Check if already initialized
        if SegregatedFundsLedger.objects.exists():
            logger.warning("Funds ledger already has entries. Skipping initialization.")
            return False

        try:
            with db_transaction.atomic():
                total_wallets = Wallet.objects.aggregate(
                    total=Sum('balance')
                )['total'] or Decimal('0.00')

                if total_wallets > Decimal('0.00'):
                    SegregatedFundsLedger.objects.create(
                        fund_type='customer',
                        entry_type='reconciliation_adjustment',
                        amount=total_wallets,
                        balance_after=total_wallets,
                        description="Initial balance from existing customer wallets",
                        metadata={'initialization': True, 'date': timezone.now().isoformat()}
                    )
                    logger.info(f"Initialized customer funds ledger with ${total_wallets}")

                return True

        except Exception as e:
            logger.error(f"Failed to initialize funds ledger: {str(e)}")
            return False
