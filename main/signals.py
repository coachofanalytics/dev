from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ExpertInquiry

@receiver(post_save, sender=ExpertInquiry)
def inquiry_saved_handler(sender, instance, created, **kwargs):
    """Handle post-save signals for ExpertInquiry"""
    if created:
        print(f"🔔 New inquiry created: {instance.full_name}")
        # You could add Slack/Discord notifications here