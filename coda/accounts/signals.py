from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone

from accounts.choices import UserCategory as CategoryChoices
from accounts.utils import send_email_to_applicant
from .models import LoginHistory
from .models import CustomerUser, UserGroups
from django.db.models.signals import post_save
from django.utils.text import slugify


@receiver(user_logged_in)
def track_login(sender, user, request, **kwargs):
    LoginHistory.objects.create(user=user, login_time=timezone.now())


@receiver(user_logged_out)
def track_logout(sender, user, request, **kwargs):
    last_login_entry = (
        LoginHistory.objects.filter(user=user).order_by("-login_time").first()
    )
    if last_login_entry and last_login_entry.logout_time is None:
        last_login_entry.logout_time = timezone.now()
        last_login_entry.save()


# @receiver(post_save, sender=User)
# def create_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)


# @receiver(post_save, sender=User)
# def save_profile(sender, instance, **kwargs):
#     instance.profile.save()


@receiver(post_save, sender=CustomerUser)
def add_user_to_group(sender, instance, created, **kwargs):
    if created:  # Only add the user to a group when a new user is created
        # Get the category of the new user
        category = instance.category

        # Generate the base group name based on the category
        base_group_name = slugify(dict(CategoryChoices.choices)[category])

        # Find the latest group in the category
        last_group = (
            UserGroups.objects.filter(name__startswith=base_group_name)
            .order_by("-id")
            .first()
        )

        if last_group and last_group.users.count() < 30:
            # Add the user to the last group if it has less than 30 users
            last_group.users.add(instance)
            last_group.save()
            print(
                f"User {instance.username} added to existing group: {last_group.name}"
            )
        else:
            # Create a new group if the last group is full or does not exist
            group_count = (
                UserGroups.objects.filter(name__startswith=base_group_name).count() + 1
            )
            new_group_name = f"{base_group_name} Group {group_count}"

            # Create a new group and add the user
            new_group = UserGroups.objects.create(
                name=new_group_name, is_active=True, is_featured=True
            )
            new_group.users.add(instance)
            new_group.save()
            print(f"User {instance.username} added to new group: {new_group.name}")


@receiver(post_save, sender=CustomerUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when a new user is created"""
    if created:
        try:
            # Check if profile already exists
            if not hasattr(instance, 'profile'):
                from .models import UserProfile
                from main.models import Assets
                
                # Ensure default assets exist
                assets = Assets.objects.all()
                if not assets:
                    Assets.objects.create(
                        name="default",
                        category="default", 
                        description="default",
                        image_url="default",
                    )
                
                # Create user profile
                UserProfile.objects.create(user=instance)
                print(f"Profile created for user: {instance.username}")
        except Exception as e:
            print(f"Error creating profile for user {instance.username}: {e}")

@receiver(post_save, sender=CustomerUser)
def send_applicant_email_on_activation(sender, instance, **kwargs):
    print(f"Signal triggered for user: {instance.email}")
    print(f"User is_active: {instance.is_active}, category: {instance.category}")

    # Check if the user is a Job Applicant and if the account has been activated
    if instance.category == CategoryChoices.APPLICANT and instance.is_active:
        print(f"User {instance.email} is a Job Applicant and is active. Sending email.")
        send_email_to_applicant(instance)
    else:
        print(f"Conditions not met for sending email to {instance.email}")
