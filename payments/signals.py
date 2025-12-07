from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Wallet


@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    """
    Automatically create a wallet when a new user is created.
    Wrapped in try-except to handle initial deployment when tables don't exist.
    """
    if created:
        try:
            Wallet.objects.create(user=instance)
        except Exception:
            # Table might not exist during initial deployment/migrations
            pass


@receiver(post_save, sender=User)
def save_user_wallet(sender, instance, **kwargs):
    """
    Save wallet when user is saved.
    Wrapped in try-except to handle initial deployment when tables don't exist.
    """
    try:
        if hasattr(instance, 'wallet'):
            instance.wallet.save()
    except Exception:
        # Table might not exist during initial deployment/migrations
        pass
