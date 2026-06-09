# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from main.models import Governance, Profile

# @receiver(post_save, sender=Governance)
# def update_or_create_profile_from_governance(sender, instance, **kwargs):
#     user = instance.members  


#     profile, created = Profile.objects.get_or_create(user=user)

  
#     if instance.title:
#         profile.title = instance.title

#     if instance.region:
#         profile.region = instance.region

#     if instance.chapter:
#         profile.chapter = instance.chapter

#     if instance.image:
#         profile.image = instance.image

  
#     # if user.phone:
#     #     profile.phone = user.phone

#     # if user.email:
#     #     profile.email = user.email

#     profile.save()
