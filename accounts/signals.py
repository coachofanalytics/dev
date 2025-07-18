from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, CustomerUser


# @receiver(post_save, sender=User)
# def create_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)


# @receiver(post_save, sender=User)
# def save_profile(sender, instance, **kwargs):
#     instance.profile.save()

@receiver(post_save, sender=CustomerUser)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        # Create a blank profile, populate what we can
        Profile.objects.create(
            user=instance,
            email=instance.email,
            phone=instance.phone,
        )
    else:
        profile = instance.profile
        if not profile.email:
            profile.email = instance.email
        if not profile.phone:
            profile.phone = instance.phone
        profile.save()