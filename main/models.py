from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import CustomerUser, Region, Chapter
from django.utils.text import slugify



#from tableauhyperapi import DatabaseName

User = get_user_model()
# Create your models here.

class Page(models.Model):
    page_name = models.CharField(max_length=200)

    def __str__(self):
        return self.page_name

class Description(models.Model):
    page = models.ForeignKey(Page, related_name='descriptions', on_delete=models.CASCADE)
    name = models.CharField(max_length=100,null=False, blank=False) 
    content = models.TextField(null=False, blank=False)

    def __str__(self):
        return f"{self.name} for {self.page.page_name}"


class Content(models.Model):
    SECTION_CHOICES = [
        ('Our Story', 'Our Story'),
        ('Newsletter', 'Newsletter'),
        ('Blog', 'Blog'),
    ]

    section = models.CharField(max_length=50, choices=SECTION_CHOICES)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.section} - {self.title if self.title else 'Content'}"
    
    
class Assets(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(default='background',max_length=200,null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image_url = models.CharField(max_length=1000, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Assets"

    @property
    def split_name(self):
        image_1=self.name.split("_")[0]
        image_2=self.name.split("_")[1]
        image_name=image_1,image_2

        return image_name

    def __str__(self):
        return self.name
    

class Feedback(models.Model):
    user= models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    # category = models.ForeignKey(UserCategory,null=True,blank=True,on_delete=models.CASCADE)
    topic = models.CharField(max_length=254)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title
    
class Service(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.title

class SubService(models.Model):
    service = models.ForeignKey(Service, related_name='subservices', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return f"{self.title} - {self.service}"
    

class News(models.Model):
    CATEGORY_CHOICES = [
    ("political", "Political"),
    ("business", "Business"),
    ("education", "Education"),
    ("health", "Health"),
    ("culture", "Culture"),
    ("technology", "Technology"),
    ("events", "Events"),
    ]
    title = models.CharField(max_length=200, default="")
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="news", default="")
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="news", default="")
    content = models.TextField(default="")
    source = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="")
    link = models.URLField(null=True,blank=True)
    published_date = models.DateField()
    is_event = models.BooleanField(default=False)
    image = models.ImageField(upload_to='news_images/', blank=True, null=True)  # Add this line for image field
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    update_date = models.DateTimeField(auto_now=True, null=True)


    def __str__(self):
        return self.title    
    
class Team(models.Model):
    ROLE_CHOICES = [
        ('Governor', 'Governor'),
        ('Deputy Governor', 'Deputy Governor'),
        ('Regional Coordinator', 'Regional Coordinator'),
        ('Team Member', 'Team Member'),
    ]

    LEADERSHIP_CHOICES = [
        ('Local', 'Local'),
        ('Global', 'Global'),
    ]
    name = models.CharField(max_length=255)
    leadership = models.CharField(max_length=50, choices=LEADERSHIP_CHOICES, default='Local')  # or another default value
    facebook_link = models.URLField(blank=True, null=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    region = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='people/')
    bio = models.TextField()

    def __str__(self):
        return self.name


class Gallery(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='gallery/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    event_date = models.DateField()

    def __str__(self):
        return self.title



class ContactUs(models.Model):
    name = models.CharField(max_length=100, help_text="Full name of the user.")
    email = models.EmailField(help_text="Email address for correspondence.")
    phone_number = models.CharField(
        max_length=15, blank=True, null=True, 
        help_text="Phone number of the user (optional)."
    )
    message = models.TextField(help_text="Message or inquiry from the user.")
    submitted_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the message was submitted.")
    is_resolved = models.BooleanField(default=False, help_text="Flag to mark whether the query has been addressed.")

    def __str__(self):
        return f"Message from {self.name} ({self.email})"
    



class Faq(models.Model):
    CategoryChoices = [
        ('general', 'General'),
        ('technical', 'Technical'),
        ('billing', 'Billing'),
        ('account', 'Account'),
        ('other', 'Other'),
    ]
    question = models.CharField(max_length=255) #add questions 
    answer = models.TextField() #add answers
    category = models.CharField(max_length=255, choices=CategoryChoices, default=999)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question
    


class GetHelp(models.Model):
    title = models.CharField(max_length=255,null=False,blank=False)    
    content = models.TextField(null=False,blank=False)
    link = models.URLField(null=True,blank=False,max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(null=False,blank=False,auto_now_add=True)
    updated_at = models.DateTimeField(null=False,blank=False,auto_now=True)

    def __str__(self):
        return self.title 

    


class Governance(models.Model):
    GovernanceCategoryChoices = [
        ('Global Executive Committee', 'Global Executive Committee'),
        ('Regional Administration', 'Regional Administration'),
        ('County Assembly Administration', 'County Assembly Administration')
    ]
    governance_category = models.CharField(max_length=255, choices=GovernanceCategoryChoices)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    members = models.ForeignKey(CustomerUser, on_delete=models.CASCADE, related_name='governance')
    # user_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='governance')
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='regions', default="")
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='chapter', default="")
    image = models.ImageField(upload_to='img/governance', default='img/governance/dc48k_logo.png')
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ui_order = models.IntegerField(unique=False, default=0) # used organize leadership/photos on ui.

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.governance_category)
            slug = base_slug
            num = 1
            while Governance.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{num}"
                num += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.governance_category}, {self.title}, {self.members}"
    

class DonationOrganization(models.Model):
    name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    linked_profile = models.OneToOneField(User, on_delete=models.CASCADE)
    def __str__(self):
        return self.name

class History(models.Model):
    year = models.IntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to="history_images/", blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-year', 'order']

    def __str__(self):
        return f"{self.year}: {self.title}"


class ConsularAssistancePage(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Consular Assistance Page"
        verbose_name_plural = "Consular Assistance Pages"

    def __str__(self):
        return self.title


class LegalService(models.Model):
    """
    Model to store legal & immigration guidance services.
    Used on the Legal and Immigration Guidance dedicated page.
    """
    CATEGORY_CHOICES = [
        ('visa', 'Visa and Residency Services'),
        ('citizenship', 'Citizenship and Naturalization'),
        ('legal_referral', 'Legal Representation & Referrals'),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    image_url = models.URLField(blank=True, null=True)
    features = models.JSONField(default=list)
    cta_button_text = models.CharField(max_length=100, default='Learn More')
    cta_button_url = models.URLField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Legal Service'
        verbose_name_plural = 'Legal Services'

    def __str__(self):
        return self.title
