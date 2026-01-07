"""
Tests for payments models.
"""

import pytest
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils import timezone

from payments.models import (
    Wallet,
    SubscriptionPlan,
    UserSubscription,
    Invoice,
    Transaction,
    PaymentGatewayConfig,
)


@pytest.mark.django_db
class TestWalletModel:
    """Tests for Wallet model."""

    def test_wallet_auto_created_for_user(self, create_user):
        """Test that wallet is automatically created when user is created."""
        user = create_user()

        assert hasattr(user, 'wallet')
        assert user.wallet.user == user
        assert user.wallet.balance == Decimal("0.00")
        assert user.wallet.currency == "USD"
        assert user.wallet.is_active is True

    def test_wallet_string_representation(self, create_user):
        """Test Wallet __str__ method."""
        user = create_user(username="john_doe")
        user.wallet.balance = Decimal("100.50")
        user.wallet.save()

        assert str(user.wallet) == "john_doe's Wallet - $100.50"

    def test_wallet_credit_operation(self, create_user):
        """Test crediting money to wallet."""
        user = create_user()
        wallet = user.wallet

        result = wallet.credit(Decimal("50.00"))
        assert result is True
        assert wallet.balance == Decimal("50.00")

        result = wallet.credit(Decimal("25.50"))
        assert result is True
        assert wallet.balance == Decimal("75.50")

    def test_wallet_credit_with_negative_amount_fails(self, create_user):
        """Test crediting negative amount returns False."""
        user = create_user()
        wallet = user.wallet
        wallet.balance = Decimal("100.00")
        wallet.save()

        result = wallet.credit(Decimal("-50.00"))
        assert result is False
        wallet.refresh_from_db()
        assert wallet.balance == Decimal("100.00")

    def test_wallet_debit_operation(self, create_user):
        """Test debiting money from wallet."""
        user = create_user()
        wallet = user.wallet
        wallet.balance = Decimal("100.00")
        wallet.save()

        result = wallet.debit(Decimal("30.00"))
        assert result is True
        assert wallet.balance == Decimal("70.00")

    def test_wallet_debit_insufficient_balance(self, create_user):
        """Test debiting more than balance returns False."""
        user = create_user()
        wallet = user.wallet
        wallet.balance = Decimal("50.00")
        wallet.save()

        result = wallet.debit(Decimal("100.00"))
        assert result is False
        wallet.refresh_from_db()
        assert wallet.balance == Decimal("50.00")

    def test_wallet_has_sufficient_balance(self, create_user):
        """Test has_sufficient_balance method."""
        user = create_user()
        wallet = user.wallet
        wallet.balance = Decimal("100.00")
        wallet.save()

        assert wallet.has_sufficient_balance(Decimal("50.00")) is True
        assert wallet.has_sufficient_balance(Decimal("100.00")) is True
        assert wallet.has_sufficient_balance(Decimal("150.00")) is False

    def test_wallet_one_to_one_with_user(self, create_user):
        """Test that Wallet has one-to-one relationship with User."""
        user = create_user()

        # Wallet should already exist from signal
        assert hasattr(user, 'wallet')

        # Try to create another wallet for same user should raise error
        with pytest.raises(IntegrityError):
            Wallet.objects.create(user=user)


@pytest.mark.django_db
class TestSubscriptionPlanModel:
    """Tests for SubscriptionPlan model."""

    def test_create_subscription_plan(self):
        """Test creating a subscription plan."""
        plan = SubscriptionPlan.objects.create(
            name="Premium",
            slug="premium",
            description="Premium subscription",
            price=Decimal("29.99"),
            duration_days=30,
            features=["Feature 1", "Feature 2"],
        )

        assert plan.name == "Premium"
        assert plan.slug == "premium"
        assert plan.price == Decimal("29.99")
        assert plan.duration_days == 30
        assert plan.features == ["Feature 1", "Feature 2"]
        assert plan.is_active is True
        assert plan.is_featured is False

    def test_subscription_plan_string_representation(self):
        """Test SubscriptionPlan __str__ method."""
        plan = SubscriptionPlan.objects.create(
            name="Basic",
            slug="basic",
            description="Basic plan",
            price=Decimal("9.99"),
            duration_days=30,
        )

        assert str(plan) == "Basic - $9.99/30 days"

    def test_subscription_plan_unique_slug(self):
        """Test that subscription plan slug must be unique."""
        SubscriptionPlan.objects.create(
            name="Plan 1",
            slug="unique-slug",
            description="Test",
            price=Decimal("10.00"),
        )

        with pytest.raises(IntegrityError):
            SubscriptionPlan.objects.create(
                name="Plan 2",
                slug="unique-slug",
                description="Test",
                price=Decimal("20.00"),
            )

    def test_subscription_plan_ordering_by_price(self):
        """Test that plans are ordered by price."""
        plan1 = SubscriptionPlan.objects.create(
            name="Premium", slug="premium", description="Test", price=Decimal("99.99")
        )
        plan2 = SubscriptionPlan.objects.create(
            name="Basic", slug="basic", description="Test", price=Decimal("9.99")
        )
        plan3 = SubscriptionPlan.objects.create(
            name="Standard", slug="standard", description="Test", price=Decimal("29.99")
        )

        plans = list(SubscriptionPlan.objects.all())
        assert plans[0] == plan2  # Basic $9.99
        assert plans[1] == plan3  # Standard $29.99
        assert plans[2] == plan1  # Premium $99.99


@pytest.mark.django_db
class TestUserSubscriptionModel:
    """Tests for UserSubscription model."""

    def test_create_user_subscription(self, create_user):
        """Test creating a user subscription."""
        user = create_user()
        plan = SubscriptionPlan.objects.create(
            name="Premium",
            slug="premium",
            description="Test",
            price=Decimal("29.99"),
        )

        subscription = UserSubscription.objects.create(user=user, plan=plan)

        assert subscription.user == user
        assert subscription.plan == plan
        assert subscription.status == "pending"
        assert subscription.auto_renew is True
        assert subscription.payment_method == "wallet"

    def test_subscription_activate(self, create_user):
        """Test activating a subscription."""
        user = create_user()
        plan = SubscriptionPlan.objects.create(
            name="Premium",
            slug="premium",
            description="Test",
            price=Decimal("29.99"),
            duration_days=30,
        )

        subscription = UserSubscription.objects.create(user=user, plan=plan)
        subscription.activate()

        assert subscription.status == "active"
        assert subscription.start_date is not None
        assert subscription.end_date is not None
        assert (subscription.end_date - subscription.start_date).days == 30

    def test_subscription_cancel(self, create_user):
        """Test canceling a subscription."""
        user = create_user()
        plan = SubscriptionPlan.objects.create(
            name="Premium", slug="premium", description="Test", price=Decimal("29.99")
        )

        subscription = UserSubscription.objects.create(user=user, plan=plan)
        subscription.activate()
        subscription.cancel()

        assert subscription.status == "cancelled"
        assert subscription.auto_renew is False

    def test_subscription_is_valid(self, create_user):
        """Test subscription validity check."""
        user = create_user()
        plan = SubscriptionPlan.objects.create(
            name="Premium",
            slug="premium",
            description="Test",
            price=Decimal("29.99"),
            duration_days=30,
        )

        subscription = UserSubscription.objects.create(user=user, plan=plan)

        # Pending subscription is not valid
        assert subscription.is_valid() is False

        # Active subscription is valid
        subscription.activate()
        assert subscription.is_valid() is True

        # Expired subscription is not valid
        subscription.end_date = timezone.now() - timedelta(days=1)
        subscription.save()
        assert subscription.is_valid() is False

    def test_subscription_days_remaining(self, create_user):
        """Test days_remaining calculation."""
        user = create_user()
        plan = SubscriptionPlan.objects.create(
            name="Premium",
            slug="premium",
            description="Test",
            price=Decimal("29.99"),
            duration_days=30,
        )

        subscription = UserSubscription.objects.create(user=user, plan=plan)
        subscription.activate()

        # Should have approximately 30 days remaining
        days = subscription.days_remaining()
        assert 29 <= days <= 30

    def test_subscription_needs_renewal_notification(self, create_user):
        """Test needs_renewal_notification property."""
        user = create_user()
        plan = SubscriptionPlan.objects.create(
            name="Premium",
            slug="premium",
            description="Test",
            price=Decimal("29.99"),
            duration_days=30,
        )

        subscription = UserSubscription.objects.create(user=user, plan=plan)
        subscription.status = "active"
        subscription.start_date = timezone.now()

        # 6 days remaining - should need notification
        subscription.end_date = timezone.now() + timedelta(days=6)
        subscription.save()
        assert subscription.needs_renewal_notification is True

        # 10 days remaining - should not need notification
        subscription.end_date = timezone.now() + timedelta(days=10)
        subscription.save()
        assert subscription.needs_renewal_notification is False

        # Already expired - should not need notification
        subscription.end_date = timezone.now() - timedelta(days=1)
        subscription.save()
        assert subscription.needs_renewal_notification is False

    def test_subscription_string_representation(self, create_user):
        """Test UserSubscription __str__ method."""
        user = create_user(username="john")
        plan = SubscriptionPlan.objects.create(
            name="Premium", slug="premium", description="Test", price=Decimal("29.99")
        )

        subscription = UserSubscription.objects.create(user=user, plan=plan)

        assert str(subscription) == "john - Premium (pending)"


@pytest.mark.django_db
class TestInvoiceModel:
    """Tests for Invoice model."""

    def test_create_invoice(self, create_user):
        """Test creating an invoice."""
        user = create_user()
        invoice = Invoice.objects.create(
            user=user,
            amount=Decimal("99.99"),
            due_date=timezone.now() + timedelta(days=7),
            description="Subscription payment",
        )

        assert invoice.user == user
        assert invoice.amount == Decimal("99.99")
        assert invoice.currency == "USD"
        assert invoice.status == "pending"
        assert invoice.invoice_number is not None
        assert invoice.invoice_number.startswith("INV-")

    def test_invoice_auto_generate_invoice_number(self, create_user):
        """Test that invoice number is automatically generated."""
        user = create_user()
        invoice1 = Invoice.objects.create(
            user=user,
            amount=Decimal("10.00"),
            due_date=timezone.now() + timedelta(days=7),
            description="Test 1",
        )
        invoice2 = Invoice.objects.create(
            user=user,
            amount=Decimal("20.00"),
            due_date=timezone.now() + timedelta(days=7),
            description="Test 2",
        )

        assert invoice1.invoice_number is not None
        assert invoice2.invoice_number is not None
        assert invoice1.invoice_number != invoice2.invoice_number
        assert invoice1.invoice_number.startswith("INV-")
        assert invoice2.invoice_number.startswith("INV-")

    def test_invoice_mark_as_paid(self, create_user):
        """Test marking invoice as paid."""
        user = create_user()
        invoice = Invoice.objects.create(
            user=user,
            amount=Decimal("50.00"),
            due_date=timezone.now() + timedelta(days=7),
            description="Test",
        )

        invoice.mark_as_paid()

        assert invoice.status == "paid"
        assert invoice.paid_date is not None

    def test_invoice_is_overdue(self, create_user):
        """Test is_overdue check."""
        user = create_user()

        # Invoice due in future - not overdue
        invoice1 = Invoice.objects.create(
            user=user,
            amount=Decimal("50.00"),
            due_date=timezone.now() + timedelta(days=7),
            description="Test",
        )
        assert invoice1.is_overdue() is False

        # Invoice due in past - overdue
        invoice2 = Invoice.objects.create(
            user=user,
            amount=Decimal("50.00"),
            due_date=timezone.now() - timedelta(days=1),
            description="Test",
        )
        assert invoice2.is_overdue() is True

        # Paid invoice - not overdue
        invoice3 = Invoice.objects.create(
            user=user,
            amount=Decimal("50.00"),
            due_date=timezone.now() - timedelta(days=1),
            description="Test",
        )
        invoice3.mark_as_paid()
        assert invoice3.is_overdue() is False

    def test_invoice_string_representation(self, create_user):
        """Test Invoice __str__ method."""
        user = create_user(username="john")
        invoice = Invoice.objects.create(
            user=user,
            amount=Decimal("99.99"),
            due_date=timezone.now() + timedelta(days=7),
            description="Test",
        )

        result = str(invoice)
        assert "john" in result
        assert "$99.99" in result
        assert "INV-" in result


@pytest.mark.django_db
class TestTransactionModel:
    """Tests for Transaction model."""

    def test_create_transaction(self, create_user):
        """Test creating a transaction."""
        user = create_user()
        wallet = user.wallet  # Use auto-created wallet

        transaction = Transaction.objects.create(
            user=user,
            wallet=wallet,
            transaction_type="deposit",
            amount=Decimal("100.00"),
            payment_gateway="stripe",
        )

        assert transaction.user == user
        assert transaction.wallet == wallet
        assert transaction.transaction_type == "deposit"
        assert transaction.amount == Decimal("100.00")
        assert transaction.payment_gateway == "stripe"
        assert transaction.status == "pending"
        assert transaction.currency == "USD"
        assert transaction.retry_count == 0

    def test_transaction_auto_generate_transaction_id(self, create_user):
        """Test that transaction ID is automatically generated."""
        user = create_user()

        txn1 = Transaction.objects.create(
            user=user,
            transaction_type="deposit",
            amount=Decimal("10.00"),
            payment_gateway="stripe",
        )
        txn2 = Transaction.objects.create(
            user=user,
            transaction_type="deposit",
            amount=Decimal("20.00"),
            payment_gateway="stripe",
        )

        assert txn1.transaction_id is not None
        assert txn2.transaction_id is not None
        assert txn1.transaction_id != txn2.transaction_id
        assert txn1.transaction_id.startswith("TXN-")
        assert txn2.transaction_id.startswith("TXN-")

    def test_transaction_mark_as_completed(self, create_user):
        """Test marking transaction as completed."""
        user = create_user()

        transaction = Transaction.objects.create(
            user=user,
            transaction_type="deposit",
            amount=Decimal("50.00"),
            payment_gateway="stripe",
        )

        transaction.mark_as_completed()

        assert transaction.status == "completed"

    def test_transaction_mark_as_failed(self, create_user):
        """Test marking transaction as failed."""
        user = create_user()

        transaction = Transaction.objects.create(
            user=user,
            transaction_type="deposit",
            amount=Decimal("50.00"),
            payment_gateway="stripe",
        )

        transaction.mark_as_failed("Payment declined")

        assert transaction.status == "failed"
        assert transaction.metadata.get("failure_reason") == "Payment declined"

    def test_transaction_metadata_storage(self, create_user):
        """Test storing metadata in transaction."""
        user = create_user()

        transaction = Transaction.objects.create(
            user=user,
            transaction_type="deposit",
            amount=Decimal("50.00"),
            payment_gateway="stripe",
            metadata={"stripe_charge_id": "ch_123", "fees": "2.50"},
        )

        assert transaction.metadata["stripe_charge_id"] == "ch_123"
        assert transaction.metadata["fees"] == "2.50"

    def test_transaction_string_representation(self, create_user):
        """Test Transaction __str__ method."""
        user = create_user(username="john")

        transaction = Transaction.objects.create(
            user=user,
            transaction_type="deposit",
            amount=Decimal("100.50"),
            payment_gateway="stripe",
        )

        result = str(transaction)
        assert "john" in result
        assert "$100.50" in result
        assert "TXN-" in result


@pytest.mark.django_db
class TestPaymentGatewayConfigModel:
    """Tests for PaymentGatewayConfig model."""

    def test_create_gateway_config(self, create_user):
        """Test creating a payment gateway configuration."""
        admin_user = create_user(username="admin")

        config = PaymentGatewayConfig.objects.create(
            gateway_name="stripe",
            is_active=True,
            is_test_mode=True,
            config_data={
                "api_key": "sk_test_123",
                "publishable_key": "pk_test_123",
            },
            last_updated_by=admin_user,
        )

        assert config.gateway_name == "stripe"
        assert config.is_active is True
        assert config.is_test_mode is True
        assert config.config_data["api_key"] == "sk_test_123"
        assert config.last_updated_by == admin_user

    def test_gateway_config_unique_gateway_name(self, create_user):
        """Test that gateway_name must be unique."""
        admin_user = create_user()

        PaymentGatewayConfig.objects.create(
            gateway_name="stripe",
            config_data={},
            last_updated_by=admin_user,
        )

        with pytest.raises(IntegrityError):
            PaymentGatewayConfig.objects.create(
                gateway_name="stripe",
                config_data={},
                last_updated_by=admin_user,
            )

    def test_gateway_config_string_representation(self, create_user):
        """Test PaymentGatewayConfig __str__ method."""
        admin_user = create_user()

        config = PaymentGatewayConfig.objects.create(
            gateway_name="stripe",
            is_active=True,
            is_test_mode=True,
            config_data={},
            last_updated_by=admin_user,
        )

        result = str(config)
        assert "Stripe" in result
        assert "TEST" in result
        assert "Active" in result

    def test_gateway_config_live_mode(self, create_user):
        """Test gateway configuration in live mode."""
        admin_user = create_user()

        config = PaymentGatewayConfig.objects.create(
            gateway_name="stripe",
            is_active=True,
            is_test_mode=False,
            config_data={},
            last_updated_by=admin_user,
        )

        result = str(config)
        assert "LIVE" in result
