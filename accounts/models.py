
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime,timedelta
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.models import AbstractUser, Group, Permission
from accounts.choices import CategoryChoices, SubCategoryChoices
from accounts.modelmanager import DepartmentManager




# class CustomerUser(AbstractUser):
#     accepted_terms = models.BooleanField(default=False)
    
#     groups = models.ManyToManyField(Group, related_name='custom_user_set')
#     user_permissions = models.ManyToManyField(Permission, related_name='custom_user_set')
#     def get_category_display_name(self):
#         return dict(CategoryChoices.choices).get(self.category, 'Unknown')    

#     # added this column here
#     def get_subcategory_display_name(self):
#         return dict(SubCategoryChoices.choices).get(self.subcategory, 'Unknown')    

#     class Score(models.IntegerChoices):
#         Male = 1
#         Female = 2
#     id = models.AutoField(primary_key=True)
#     first_name = models.CharField(max_length=255)
#     last_name = models.CharField(max_length=255)
#     date_joined = models.DateTimeField(default=timezone.now)
#     email = models.CharField(max_length=255)
#     category = models.IntegerField(choices=CategoryChoices.choices, default=999)
#     # added this column here
#     is_admin = models.BooleanField("Is admin", default=False)
#     is_member = models.BooleanField("Is Member", default=False)
#     email_verified = models.BooleanField(default=False)
#     verification_token = models.UUIDField( unique=True, null=True, blank=True)
#     class Meta:
#         # ordering = ["-date_joined"]
#         ordering = ["username"]
#         verbose_name_plural = "Users"

#     @property
#     def full_name(self):
#         fullname = f'{self.first_name},{self.last_name}'
#         return fullname
    
#     @property
#     def user_details(self):
#         user_details = (
#             f"Username: {self.username}\n"
           
#             # f"Country: {self.country.name if self.country else 'N/A'}"
#         )
#         return user_details
    
#     @property
#     def is_recent(self):
#         return self.date_joined >= timezone.now() - timedelta(days=365)
    
#     @property
#     def tenure(self):
#         number_days=(timezone.now().date() - self.date_joined.date()).days
#         months=number_days/30
#         return months

# class Membership(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     status = models.CharField(max_length=20)
#     plan = models.CharField(max_length=50, blank=True, null=True)

#     def __str__(self):
#         status_display = self.status.capitalize() if self.status else "Unknown"
#         return f"{self.user} - {status_display}"

# class Department(models.Model):
#     """Department Table will provide a list of the different departments in CODA"""

#     # Department
#     # BASIC = "Basic"
#     HR = "HR Department"
#     IT = "IT Department"
#     MKT = "Marketing Department"
#     FIN = "Finance Department"
#     SECURITY = "Security Department"
#     MANAGEMENT = "Management Department"
#     # Project = "Project"
#     HEALTH = "Health Department"
#     Other = "Other"
#     DEPARTMENT_CHOICES = [
#         # (BASIC, "BASIC Department"),
#         (HR, "HR Department"),
#         (IT, "IT Department"),
#         (MKT, "Marketing Department"),
#         (FIN, "Finance Department"),
#         # (Project, "Project"),
#         (SECURITY, "Security Department"),
#         (MANAGEMENT, "Management Department"),
#         (HEALTH, "Health Department"),
#         (Other, "Other"),
#     ]

#     name = models.CharField(
#         max_length=100,
#         choices=DEPARTMENT_CHOICES,
#         default=Other,
#     )

#     description = models.TextField(max_length=500, null=True, blank=True)
#     slug = models.SlugField(
#         verbose_name=("Department safe URL"), max_length=255, unique=True
#     )
#     # created_date = models.DateTimeField(_('entered on'),default=timezone.now, editable=True)
#     is_featured = models.BooleanField("Is featured", default=True)
#     is_active = models.BooleanField(default=True)

#     objects=DepartmentManager()

#     @classmethod
#     def get_default_pk(cls):
#         cat, created = cls.objects.get_or_create(
#             name="Other", defaults=dict(description="this is not an cat")
#         )
#         return cat.pk

#     class Meta:
#         verbose_name = ("Department")
#         verbose_name_plural = ("Departments") 

#     # def get_absolute_url(self):
#     #     return reverse('management:department_list', args=[self.slug])
#     def __str__(self):
#         return self.name  
# # account model
# class Account(models.Model): # make sure this exists
#     name = models.CharField(max_length=255)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.name




# # ACCOUNT _TEAM MEMBERS model

# class AccountTeamMember(models.Model):
#     # choose user role
#     USER_ROLES = [
#         ('ADMIN', 'Admin'),
#         ('MEMBER', 'Member'),
#         ('VIEWER', 'Viewer'),
#     ]

#     account = models.ForeignKey('Account', on_delete=models.CASCADE, related_name="team_members")
#     user = models.ForeignKey(CustomerUser, on_delete=models.CASCADE, related_name='team_memberships')
#     role = models.CharField(max_length=10, choices=USER_ROLES)
#     status = models.BooleanField(default=True)  # Active or Inactive
#     joined_date = models.DateTimeField(auto_now_add=True)
#     added_by = models.ForeignKey(CustomerUser, on_delete=models.SET_NULL, null=True, related_name='added_team_members')
#     notes = models.TextField(null=True, blank=True)
#     class Meta:
#         unique_together = ('account', 'user')  # Ensure a user can't be added multiple times to the same account
#         verbose_name = "Account Team Member"
#         verbose_name_plural = "Account Team Members"
#     def __str__(self):
#         return f"{self.user.username} - {self.get_role_display()} in {self.account.name}"

# # 👇 ADD THIS LINE BEFORE THE MODEL
# User = get_user_model()

from django.conf import settings

class UserGroups(models.Model):
    is_active = models.BooleanField(null=True, blank=True)
    is_featured = models.BooleanField(null=True, blank=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="user_groups")

    def __str__(self):
        return f"UserGroup {self.id}"