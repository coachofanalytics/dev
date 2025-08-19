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
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Create a Profile when a CustomerUser is created.
    Also update the phone and email if the Profile exists.
    """
    if created:
        # If the user is newly created, create a new profile
        profile, created = Profile.objects.get_or_create(member=instance)
        if created:
            print(f"Profile created for {instance.username}")
        else:
            print(f"Profile already exists for {instance.username}")

        # Initialize Profile fields with the User's data
        profile.email = instance.email
        profile.phone = instance.phone
        profile.save()
        
    else:
        # If the user exists, update the profile if needed
        try:
            profile = instance.profile
            profile.email = instance.email
            profile.phone = instance.phone
            profile.save()
        except Profile.DoesNotExist:
            # Handle case where profile doesn't exist (it should, by now)
            print(f"Profile does not exist for {instance.username}. Creating one.")
            Profile.objects.create(
                member=instance,
                email=instance.email,
                phone=instance.phone
            )