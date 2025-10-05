import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from professional_services.models import ClientAssessment
from accounts.models import CustomerUser
from django.contrib.auth.models import AbstractUser
from mail.custom_email import send_email
from accounts.utils import send_verification_email
from core.utils import generate_password    


# @receiver(post_save, sender=ClientAssessment)
# def create_customer_user(sender, instance, created, **kwargs):
   
#     if created and not CustomerUser.objects.filter(email=instance.email).exists():
#         random_password = generate_password(8)
#         user = CustomerUser.objects.create(
#             username = instance.email,
#             gender = None,
#             first_name=instance.first_name,
#             last_name=instance.last_name,
#             email=instance.email,
#             category=2,
#             sub_category=0
#         )

#         # set password
#         user.set_password(random_password)
#         user.is_client = True
               
#         token = str(uuid.uuid4())
#         user.verification_token = token
#         user.is_active = True  # Keep the account inactive until verified
#         print('going to create the user')
#         user.save()
#         send_verification_email(user, password=random_password)

