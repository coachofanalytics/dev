from django.db import models
from main.models import Assets,TimeStampedModel
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from random import randint
# # Create your models here.
from django.contrib.auth import get_user_model
from django_countries.fields import CountryField
# from finance.utils import get_exchange_rate
User = get_user_model() 

class Ads(models.Model):
    my_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    company = models.CharField(max_length=100, null=True, blank=True)
    ad_title = models.CharField(max_length=100, null=True, blank=True)
    bulletin = models.CharField(max_length=100, null=True, blank=True)
    short_name = models.CharField(max_length=50, null=True, blank=True)
    company_site = models.CharField(max_length=255, null=True, blank=True)
    meeting_link = models.CharField(max_length=500, null=True, blank=True)
    video_link = models.CharField(max_length=500, null=True, blank=True)
    signature = models.CharField(max_length=255, null=True, blank=True)
    description= models.TextField(null=True, blank=True)
    message= models.TextField(null=True, blank=True)
    image_name = models.ForeignKey(
        Assets, related_name="message_image", on_delete=models.CASCADE,default=1
    )
    link = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    #in future we required field that help us to define which platform this ads coming

    class Meta:
        verbose_name_plural = "Ads"
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['company']),
            models.Index(fields=['my_user']),
            # Composite indexes for common query patterns
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['created_at', 'is_active']),
        ]

    def __str__(self):
        return str(self.ad_title)

    def clean(self):
        """Validate Ads model data"""
        from django.core.exceptions import ValidationError
        
        # Validate company site format if provided
        if self.company_site and not self.company_site.startswith(('http://', 'https://')):
            raise ValidationError("Company site must start with http:// or https://")
        
        # Validate meeting link format if provided
        if self.meeting_link and not self.meeting_link.startswith(('http://', 'https://')):
            raise ValidationError("Meeting link must start with http:// or https://")
        
        # Validate video link format if provided
        if self.video_link and not self.video_link.startswith(('http://', 'https://')):
            raise ValidationError("Video link must start with http:// or https://")
        
        # Validate general link format if provided
        if self.link and not self.link.startswith(('http://', 'https://')):
            raise ValidationError("Link must start with http:// or https://")
        
        # Validate required fields for active ads
        if self.is_active:
            if not self.ad_title:
                raise ValidationError("Ad title is required for active ads")
            if not self.company:
                raise ValidationError("Company name is required for active ads")

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.clean()
        super().save(*args, **kwargs)

class Whatsapp_Groups(models.Model):
    # types
    CATEGORY_CHOICES = [
        ("Finance", "Finance"),
        ("IT", "IT"),
        ("Internal", "Internal"),
        ("Political", "Political"),
        ("Business", "Business"),
        ("other", "other"),
    ]
    TYPE_CHOICES = [
        ("investments", "investments"),
        ("data_analysis", "data_analysis"),
        ("coda", "coda"),
        ("Job_Support", "Job_Support"),
        ("interview", "interview"),
        ("mentorship", "mentorship"),
        ("automation", "automation"),
        ("other", "other"),
    ]
    id = models.AutoField(primary_key=True)
    country = CountryField(blank_label='(select country)', null=True, blank=True)
    group_id = models.CharField(max_length=100, null=True, blank=True)
    slug = models.SlugField(max_length=100, null=True, blank=True,unique=True)
    group_name = models.CharField(max_length=100, null=True, blank=True)
    participants = models.CharField(max_length=50, null=True, blank=True)
    category = models.CharField(
        max_length=25,
        choices=CATEGORY_CHOICES,
        default="other",
    )
    type = models.CharField(
        max_length=25,
        choices=TYPE_CHOICES,
        default="other",
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "WhatsApp Groups"
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['category']),
            models.Index(fields=['type']),
            models.Index(fields=['country']),
            models.Index(fields=['slug']),
            # Composite indexes for common query patterns
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['type', 'is_active']),
            models.Index(fields=['country', 'is_active']),
        ]

    def __str__(self):
        return self.group_name

    def clean(self):
        """Validate Whatsapp_Groups model data"""
        from django.core.exceptions import ValidationError
        
        # Validate group name is required for active groups
        if self.is_active and not self.group_name:
            raise ValidationError("Group name is required for active groups")
        
        # Validate group_id is required for active groups
        if self.is_active and not self.group_id:
            raise ValidationError("Group ID is required for active groups")
        
        # Validate participants count if provided
        if self.participants:
            try:
                participant_count = int(self.participants)
                if participant_count < 0:
                    raise ValidationError("Participant count cannot be negative")
                if participant_count > 1000000:  # WhatsApp group limit
                    raise ValidationError("Participant count exceeds reasonable limit")
            except ValueError:
                raise ValidationError("Participants must be a valid number")
        
        # Validate slug uniqueness (handled by model field, but additional check)
        if self.slug:
            existing = Whatsapp_Groups.objects.filter(slug=self.slug).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError("Slug must be unique")

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.clean()
        super().save(*args, **kwargs)

# @receiver(pre_save, sender=Whatsapp_Groups)
# def populate_slug(sender, instance, **kwargs):
#     # If the slug is not already set and group_id is present, set the slug based on group_id
#     if not instance.slug and instance.group_id:
#         instance.slug = slugify(instance.group_id)+ str(random(20))

# @receiver(pre_save, sender=Whatsapp_Groups)
# def populate_slug(sender, instance, **kwargs):
#     if not instance.slug and instance.group_id:
#         # Generate a random number between 0 and 99999
#         random_number = randint(0, 99999)
#         # Append the random number to the slugified group_id
#         instance.slug = slugify(instance.group_id) + str(random_number)



@receiver(pre_save, sender=Whatsapp_Groups)
def populate_slug(sender, instance, **kwargs):
    if instance.pk is None and not instance.slug and instance.group_id:
        base_slug = slugify(instance.group_id)
        if not base_slug:  # Handle case where slugify returns empty string
            base_slug = f"group-{instance.pk or 'new'}"
        
        slug = base_slug
        attempts = 0
        max_attempts = 10
        
        # Check if the slug is unique and modify it until it is unique
        while Whatsapp_Groups.objects.filter(slug=slug).exists() and attempts < max_attempts:
            random_number = randint(1000, 9999999)  # More reasonable range
            slug = f'{base_slug}-{random_number}'
            attempts += 1
        
        # If we still have conflicts, add timestamp
        if attempts >= max_attempts:
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            slug = f'{base_slug}-{timestamp}'
        
        instance.slug = slug