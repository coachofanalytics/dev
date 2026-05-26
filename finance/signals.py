from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Opportunity, NewsLetterSubscriber

@receiver(pre_save, sender=Opportunity)
def store_original_status(sender, instance, **kwargs):
    """
    Store the status from the database before the save happens
    so we can compare it in the post_save signal.
    """
    if instance.pk:
        try:
            old_instance = Opportunity.objects.get(pk=instance.pk)
            instance._previous_status = old_instance.status
        except Opportunity.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None

@receiver(post_save, sender=Opportunity)
def notify_user_on_status_change(sender, instance, created, **kwargs):
    """
    Automation: Triggers professional email alerts when an admin
    changes the status of an investment opportunity.
    """
    # Skip if it's a brand new submission (handled by the View success message)
    if created:
        return

    # Only trigger if the status has actually changed
    previous_status = getattr(instance, '_previous_status', None)

    if previous_status != instance.status:

        if instance.status == 'APPROVED':
            subject = f"APPROVED: {instance.title}"
            message = (
                f"Hello,\n\n"
                f"Good news! Your investment opportunity '{instance.title}' has been verified "
                f"by our team and is now live on the Diaspora Investment Directory.\n\n"
                f"View it here: {getattr(settings, 'SITE_URL', 'http://localhost:8000')}/finance/directory/\n\n"
                f"Thank you for contributing to the community!"
            )

        elif instance.status == 'REJECTED':
            subject = f"Update on your submission: {instance.title}"
            message = (
                f"Hello,\n\n"
                f"Thank you for submitting '{instance.title}' to the Diaspora Investment Directory.\n\n"
                f"After review, we are unable to publish this listing at this time. Please ensure "
                f"your submission follows our community guidelines regarding verified contacts "
                f"and clear descriptions.\n\n"
                f"You are welcome to submit a revised version in the future."
            )
        else:
            return # No email for other status changes

        # Send the mail
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.contact], # Assuming contact field holds the submitter's email
            fail_silently=True,
        )

@receiver(post_save, sender=NewsLetterSubscriber)
def send_welcome_email(sender, instance, created, **kwargs):
    if created:  # Only send on the FIRST save
        send_mail(
            'Welcome to the DC48 Investment Network!',
            f'Hi {instance.email},\n\nThank you for subscribing to our directory alerts. We will notify you as soon as new vetted opportunities are posted.',
            'noreply@dc48.com',
            [instance.email],
            fail_silently=False,
        )
