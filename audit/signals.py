"""
Audit signals for automatic event capture.

These signals automatically log events throughout the system without
requiring explicit calls to the audit service.
"""

from typing import Any, Optional
from django.db.models.signals import post_save, pre_delete, post_delete
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver, Signal
from django.contrib.auth.models import User
from django.db.models import Model

from audit.services.audit_service import AuditService

# Custom signals for events not covered by Django's built-in signals
password_changed = Signal()
profile_updated = Signal()
payment_completed = Signal()
subscription_changed = Signal()


@receiver(user_logged_in)
def log_user_login(sender: Any, request: Any, user: User, **kwargs: Any) -> None:
    """
    Log successful user login.

    Args:
        sender: The sender class
        request: HttpRequest object
        user: User who logged in
        **kwargs: Additional arguments
    """
    AuditService.log_login_attempt(
        username=user.username,
        status="success",
        request=request,
        user=user,
        risk_score=0,  # Default risk score for successful login
    )


@receiver(user_logged_out)
def log_user_logout(sender: Any, request: Any, user: User, **kwargs: Any) -> None:
    """
    Log user logout.

    Args:
        sender: The sender class
        request: HttpRequest object
        user: User who logged out
        **kwargs: Additional arguments
    """
    if user and user.is_authenticated:
        AuditService.log_event(
            event_type="logout",
            description=f"User {user.username} logged out",
            user=user,
            request=request,
            severity="info",
        )


@receiver(user_login_failed)
def log_failed_login(sender: Any, credentials: dict, request: Any = None, **kwargs: Any) -> None:
    """
    Log failed login attempt.

    Args:
        sender: The sender class
        credentials: Login credentials attempted
        request: HttpRequest object (if available)
        **kwargs: Additional arguments
    """
    username = credentials.get("username", "unknown")

    if request:
        AuditService.log_login_attempt(
            username=username,
            status="failed",
            request=request,
            failure_reason="invalid_credentials",
            risk_score=30,  # Moderate risk for failed login
        )
    else:
        # If no request object, create minimal audit log
        AuditService.log_event(
            event_type="login_failed",
            description=f"Failed login attempt for user: {username}",
            username=username,
            severity="warning",
            metadata={"credentials": {"username": username}},
        )


@receiver(password_changed)
def log_password_change(sender: Any, user: User, request: Any = None, **kwargs: Any) -> None:
    """
    Log password change event.

    Args:
        sender: The sender class
        user: User whose password changed
        request: HttpRequest object (if available)
        **kwargs: Additional arguments
    """
    AuditService.log_event(
        event_type="password_changed",
        description=f"Password changed for user {user.username}",
        user=user,
        request=request,
        severity="info",
        metadata={"changed_by": "user"},
    )


@receiver(post_save, sender=User)
def log_user_changes(sender: Any, instance: User, created: bool, **kwargs: Any) -> None:
    """
    Log user creation and updates.

    Args:
        sender: The sender class (User model)
        instance: User instance
        created: Whether this is a new user
        **kwargs: Additional arguments
    """
    if created:
        AuditService.log_event(
            event_type="user_created",
            description=f"New user created: {instance.username}",
            user=instance,
            severity="info",
            related_object=instance,
            metadata={
                "email": instance.email,
                "is_staff": instance.is_staff,
                "is_superuser": instance.is_superuser,
            },
        )
    else:
        # Only log updates if user is already authenticated (skip during migration)
        if instance.pk:
            AuditService.log_event(
                event_type="user_updated",
                description=f"User updated: {instance.username}",
                user=instance,
                severity="info",
                related_object=instance,
                metadata={
                    "is_active": instance.is_active,
                    "is_staff": instance.is_staff,
                },
            )


@receiver(pre_delete, sender=User)
def log_user_deletion(sender: Any, instance: User, **kwargs: Any) -> None:
    """
    Log user deletion (before deletion to preserve data).

    Args:
        sender: The sender class (User model)
        instance: User instance being deleted
        **kwargs: Additional arguments
    """
    AuditService.log_event(
        event_type="user_deleted",
        description=f"User deleted: {instance.username}",
        username=instance.username,
        severity="warning",
        metadata={
            "user_id": instance.pk,
            "email": instance.email,
            "date_joined": instance.date_joined.isoformat(),
        },
    )


@receiver(profile_updated)
def log_profile_update(
    sender: Any, user: User, request: Any = None, old_values: Optional[dict] = None,
    new_values: Optional[dict] = None, **kwargs: Any
) -> None:
    """
    Log profile updates.

    Args:
        sender: The sender class
        user: User whose profile was updated
        request: HttpRequest object (if available)
        old_values: Previous profile values
        new_values: New profile values
        **kwargs: Additional arguments
    """
    AuditService.log_user_action(
        action="profile_updated",
        description=f"Profile updated for {user.username}",
        user=user,
        request=request,
        old_values=old_values,
        new_values=new_values,
    )


@receiver(payment_completed)
def log_payment(
    sender: Any,
    user: User,
    transaction: Optional[Model] = None,
    amount: Optional[float] = None,
    currency: str = "USD",
    payment_method: Optional[str] = None,
    **kwargs: Any
) -> None:
    """
    Log completed payment.

    Args:
        sender: The sender class
        user: User who made payment
        transaction: Transaction model instance
        amount: Payment amount
        currency: Currency code
        payment_method: Payment method used
        **kwargs: Additional arguments
    """
    description = f"Payment completed: {amount} {currency}"
    if payment_method:
        description += f" via {payment_method}"

    AuditService.log_payment_event(
        event_type="payment_completed",
        description=description,
        user=user,
        transaction=transaction,
        amount=amount,
        currency=currency,
        payment_method=payment_method,
    )


@receiver(subscription_changed)
def log_subscription_change(
    sender: Any,
    user: User,
    action: str,
    subscription: Optional[Model] = None,
    plan_name: Optional[str] = None,
    **kwargs: Any
) -> None:
    """
    Log subscription changes.

    Args:
        sender: The sender class
        user: User whose subscription changed
        action: Action type (created, renewed, cancelled, expired)
        subscription: Subscription model instance
        plan_name: Name of subscription plan
        **kwargs: Additional arguments
    """
    event_type_map = {
        "created": "subscription_created",
        "renewed": "subscription_renewed",
        "cancelled": "subscription_cancelled",
        "expired": "subscription_expired",
    }

    event_type = event_type_map.get(action, "subscription_created")
    description = f"Subscription {action}"
    if plan_name:
        description += f": {plan_name}"

    AuditService.log_event(
        event_type=event_type,
        description=description,
        user=user,
        severity="info",
        related_object=subscription,
        metadata={
            "action": action,
            "plan_name": plan_name,
        },
    )


# Import payments models to set up signals (avoid circular imports)
try:
    from payments.models import Transaction, UserSubscription

    @receiver(post_save, sender=Transaction)
    def log_transaction_created(sender: Any, instance: Transaction, created: bool, **kwargs: Any) -> None:
        """
        Log transaction creation and status changes.

        Args:
            sender: Transaction model
            instance: Transaction instance
            created: Whether this is a new transaction
            **kwargs: Additional arguments
        """
        if created:
            AuditService.log_payment_event(
                event_type="payment_initiated",
                description=f"Payment initiated: {instance.transaction_id}",
                user=instance.user,
                transaction=instance,
                amount=float(instance.amount),
                currency=instance.currency,
                payment_method=instance.payment_gateway,
                metadata={
                    "transaction_type": instance.transaction_type,
                    "status": instance.status,
                },
            )
        elif instance.status == "completed":
            payment_completed.send(
                sender=sender,
                user=instance.user,
                transaction=instance,
                amount=float(instance.amount),
                currency=instance.currency,
                payment_method=instance.payment_gateway,
            )
        elif instance.status == "failed":
            AuditService.log_payment_event(
                event_type="payment_failed",
                description=f"Payment failed: {instance.transaction_id}",
                user=instance.user,
                transaction=instance,
                amount=float(instance.amount),
                currency=instance.currency,
                payment_method=instance.payment_gateway,
                metadata=instance.metadata,
            )

    @receiver(post_save, sender=UserSubscription)
    def log_subscription_created(sender: Any, instance: UserSubscription, created: bool, **kwargs: Any) -> None:
        """
        Log subscription creation and status changes.

        Args:
            sender: UserSubscription model
            instance: UserSubscription instance
            created: Whether this is a new subscription
            **kwargs: Additional arguments
        """
        if created:
            subscription_changed.send(
                sender=sender,
                user=instance.user,
                action="created",
                subscription=instance,
                plan_name=instance.plan.name,
            )
        else:
            # Log status changes
            if instance.status == "cancelled":
                subscription_changed.send(
                    sender=sender,
                    user=instance.user,
                    action="cancelled",
                    subscription=instance,
                    plan_name=instance.plan.name,
                )
            elif instance.status == "expired":
                subscription_changed.send(
                    sender=sender,
                    user=instance.user,
                    action="expired",
                    subscription=instance,
                    plan_name=instance.plan.name,
                )

except ImportError:
    # Payments app not installed or models not available
    pass


# Import marketplace models
try:
    from marketplace.models import BusinessProfile, InvestmentOpportunity, JobApplication

    @receiver(post_save, sender=BusinessProfile)
    def log_business_profile_changes(sender: Any, instance: BusinessProfile, created: bool, **kwargs: Any) -> None:
        """Log business profile creation and updates."""
        if created:
            AuditService.log_event(
                event_type="profile_updated",
                description=f"Business profile created: {instance.company_name}",
                user=instance.user,
                severity="info",
                related_object=instance,
            )

    @receiver(post_save, sender=InvestmentOpportunity)
    def log_investment_opportunity(sender: Any, instance: InvestmentOpportunity, created: bool, **kwargs: Any) -> None:
        """Log investment opportunity creation."""
        if created:
            AuditService.log_event(
                event_type="admin_action",
                description=f"Investment opportunity posted: {instance.title}",
                user=instance.business,
                severity="info",
                related_object=instance,
                metadata={
                    "amount_seeking": str(instance.amount_seeking),
                    "industry": instance.industry,
                },
            )

    @receiver(post_save, sender=JobApplication)
    def log_job_application(sender: Any, instance: JobApplication, created: bool, **kwargs: Any) -> None:
        """Log job application submission."""
        if created:
            AuditService.log_event(
                event_type="admin_action",
                description=f"Job application submitted: {instance.job.title}",
                user=instance.applicant,
                severity="info",
                related_object=instance,
                metadata={
                    "job_title": instance.job.title,
                    "status": instance.status,
                },
            )

except ImportError:
    # Marketplace app not installed
    pass
