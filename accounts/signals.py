# from django.contrib.auth.models import User
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
def update_or_create_profile_from_customer_user(sender, instance, **kwargs):
    user = instance.members  


    profile, created = Profile.objects.get_or_create(user=user)

  
    if instance.title:
        profile.title = instance.title

    # if instance.region:
    #     profile.region = instance.region

    # if instance.chapter:
    #     profile.chapter = instance.chapter

    # if instance.image:
    #     profile.image = instance.image

  
    # if user.phone:
    #     profile.phone = user.phone

    # if user.email:
    #     profile.email = user.email

    profile.save()
