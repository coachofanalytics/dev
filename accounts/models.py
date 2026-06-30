from django.utils import timezone
from datetime import timedelta
from django.db import models

from django.contrib.auth.models import AbstractUser, Group, Permission
from accounts.choices import CategoryChoices, SubCategoryChoices
from accounts.modelmanager import DepartmentManager
from django_countries.fields import CountryField
from django.utils.text import slugify


# class Region(models.Model):
#     name = models.CharField(max_length=100)

#     def __str__(self):
#         return self.name
    

# class Chapter(models.Model):
#     region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='subregions')
#     name = models.CharField(max_length=100)

#     def __str__(self):
#         return self.name


class CustomerUser(AbstractUser):
    groups = models.ManyToManyField(Group, related_name="custom_user_set")
    user_permissions = models.ManyToManyField(
        Permission, related_name="custom_user_set"
    )

    def get_category_display_name(self):
        return dict(CategoryChoices.choices).get(self.category, "Unknown")

    # added this column here
    def get_subcategory_display_name(self):
        return dict(SubCategoryChoices.choices).get(self.subcategory, "Unknown")

    class Score(models.IntegerChoices):
        Male = 1
        Female = 2

    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    date_joined = models.DateTimeField(default=timezone.now)
    email = models.CharField(max_length=255)
    category = models.IntegerField(choices=CategoryChoices.choices, default=999)
    # added this column here
    is_admin = models.BooleanField("Is admin", default=False)
    is_member = models.BooleanField("Is Member", default=False)
    # is_active = models.BooleanField('Is Active', default=True)
    email_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=50, unique=True, null=True, blank=True)
    country = CountryField(blank=True, null=True)
    state = models.CharField(blank=True, null=True, max_length=255)
    city = models.CharField(blank=True, null=True, max_length=255)
    # region_id = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='member_region', default=9)
    # chapter_id = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='member_chapter', default=23)


    class Meta:
        # ordering = ["-date_joined"]
        # ordering = ["username"]
        ordering = ["-id"]
        verbose_name_plural = "Users"

    @property
    def full_name(self):
        fullname = f"{self.first_name},{self.last_name}"
        return fullname

    @property
    def user_details(self):
        user_details = (
            f"Username: {self.username}\n"
            # f"Country: {self.country.name if self.country else 'N/A'}"
        )
        return user_details

    @property
    def is_recent(self):
        return self.date_joined >= timezone.now() - timedelta(days=365)

    # @property
    # def tenure(self):
    #     number_days = (timezone.now().date() - self.date_joined.date()).days
    #     months = number_days / 30
    #     return months
    
    @property
    def member_number(self):
        # #user_id = str(1000000 + self.id)
        # user_id = str(self.id)
        # member_number = f"DC48-000-000{user_id}"
        # print(user_id, member_number)
        # return member_number

        num = 10000000 + self.id
        num_str = str(num)
        user_id = num_str[1:]
        member_number = f"DC48-{user_id}"
        return member_number

class Membership(models.Model):
    PAYMENT_STATUS = [
        ("PAID", "Paid"),
        ("NOT_PAID", "Not Paid"),
    ]

    member = models.ForeignKey(
        CustomerUser, on_delete=models.CASCADE, related_name="memberships"
    )
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    currency = models.CharField(max_length=10, default="KES")
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default="NOT_PAID")
    paid_date = models.DateTimeField(
        null=True, blank=True
    )  # Tracks the date when payment is made

    def __str__(self):
        return f"{self.member.full_name} - {self.status}"

    @property
    def is_paid(self):
        return self.status == "PAID" and self.paid_date is not None


class Department(models.Model):
    """Department Table will provide a list of the different departments in CODA"""

    # Department
    # BASIC = "Basic"
    HR = "HR Department"
    IT = "IT Department"
    MKT = "Marketing Department"
    FIN = "Finance Department"
    SECURITY = "Security Department"
    MANAGEMENT = "Management Department"
    # Project = "Project"
    HEALTH = "Health Department"
    Other = "Other"
    DEPARTMENT_CHOICES = [
        # (BASIC, "BASIC Department"),
        (HR, "HR Department"),
        (IT, "IT Department"),
        (MKT, "Marketing Department"),
        (FIN, "Finance Department"),
        # (Project, "Project"),
        (SECURITY, "Security Department"),
        (MANAGEMENT, "Management Department"),
        (HEALTH, "Health Department"),
        (Other, "Other"),
    ]

    name = models.CharField(
        max_length=100,
        choices=DEPARTMENT_CHOICES,
        default=Other,
    )

    description = models.TextField(max_length=500, null=True, blank=True)
    slug = models.SlugField(
        verbose_name=("Department safe URL"), max_length=255, unique=True
    )
    # created_date = models.DateTimeField(_('entered on'),default=timezone.now, editable=True)
    is_featured = models.BooleanField("Is featured", default=True)
    is_active = models.BooleanField(default=True)

    objects = DepartmentManager()

    @classmethod
    def get_default_pk(cls):
        cat, created = cls.objects.get_or_create(
            name="Other", defaults=dict(description="this is not an cat")
        )
        return cat.pk

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"

    # def get_absolute_url(self):
    #     return reverse('management:department_list', args=[self.slug])
    def __str__(self):
        return self.name


class MeetingAttendace(models.Model):
    meeting_id = models.AutoField(primary_key=True)
    meeting_date = models.DateField(null=False, blank=False)
    member = models.ForeignKey(
        CustomerUser, on_delete=models.CASCADE, related_name="attendance"
    )
    is_attendee = models.BooleanField(default=False)

    def __str__(self):
        return f" Meeting of {self.meeting_date}"
    


class Region(models.Model):
    name = models.CharField(max_length = 100)

    def __str__(self):
        return self.name
    

class Chapter(models.Model):
    region = models.ForeignKey(Region, on_delete = models.CASCADE, related_name ='subregions', null=True, blank=True)
    name = models.CharField(max_length = 100)

    
    def __str__(self):
        return self.name
    

class Profile(models.Model):
    GovernanceCategoryChoices = [
        ('Global Executive Committee', 'Global Executive Committee'),
        ('Regional Administration', 'Regional Administration'),
        ('County Assembly Administration', 'County Assembly Administration')
    ]
    governance_category = models.CharField(max_length=255, choices=GovernanceCategoryChoices)
    member = models.OneToOneField(CustomerUser, on_delete=models.CASCADE, related_name='profile')
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='img/governance', default='img/governance/dc48k_logo.png')
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)
    ui_order = models.IntegerField(unique=False, default=0) # used organize leadership/photos on ui.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            # Generate a slug from title or fallback to name
            base = self.title or f"{self.member.first_name}-{self.member.last_name}" or f"user-{self.member.pk}"
            candidate = slugify(base)
            unique = candidate
            i = 2
            # Ensure the slug is unique
            while Profile.objects.filter(slug=unique).exclude(pk=self.pk).exists():
                unique = f"{candidate}-{i}"
                i += 1
            self.slug = unique

        super(Profile, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.member.first_name} {self.member.last_name}" 
class UserProfile(models.Model):            
    
    user = models.OneToOneField(        
        "accounts.CustomerUser", 
        related_name="applicant_profile", # <--- CHANGE THIS LINE
        on_delete=models.CASCADE     
    )       
    position = models.CharField(max_length=255, blank=True, null=True)   
    # ... (the rest of your model stays exactly the same)     
    description = models.TextField(blank=True, null=True)        
    company = models.CharField(max_length=254, null=True, blank=True)       
    linkedin = models.CharField(max_length=500, null=True, blank=True)      
    section = models.CharField(max_length=2, default="A", blank=True)       
            
    image = models.ImageField(      
        default="default.jpg", upload_to="Application_Profile_pics", blank=True     
    )       
    # image2 = models.ForeignKey(       
    #     Assets, related_name="profile_image", on_delete=models.CASCADE, default=1       
    # )     
            
    upload_a = models.FileField(upload_to="Application_Profile/uploads", null=True, blank=True)     
    upload_b = models.FileField(upload_to="Application_Profile/uploads", null=True, blank=True)     
    upload_c = models.FileField(upload_to="Application_Profile/uploads", null=True, blank=True)     
            
    is_active = models.BooleanField("Is featured", default=True)        
    laptop_status = models.BooleanField("Is lap_status", default=True)      
            
    national_id_no = models.CharField(max_length=254, null=True, blank=True)        
    id_file = models.ImageField(upload_to='id_files/', null=True, blank=True)       
            
    emergency_name = models.CharField(max_length=254, null=True, blank=True)        
    emergency_address = models.CharField(max_length=254, null=True, blank=True)     
    emergency_citizenship = models.CharField(max_length=254, null=True, blank=True)     
    emergency_national_id_no = models.CharField(max_length=254, null=True, blank=True)      
    emergency_phone = models.CharField(max_length=254, null=True, blank=True)       
    emergency_email = models.CharField(max_length=254, null=True, blank=True)       
            
    def __str__(self):      
        return f"{self.user.username} Applicant Profile"        
            
    @property       
    def img_url(self):      
        if self.image2:     
            return self.image2.image_url        
        else:       
            return "default_image_url.jpg"      
            
    @property       
    def img_category(self):     
        img_cat = self.image2.category        
        return img_cat