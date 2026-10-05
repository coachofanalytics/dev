from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    class Meta:
        abstract = True


class Services(models.Model):
    serial = models.PositiveIntegerField(null=True, blank=True)
    title = models.CharField(
        default="training",
        max_length=254,
    )
    slug = models.SlugField(
        default="slug",
        max_length=255,
    )
    description = models.TextField(null=True, blank=True)
    sub_titles = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Services"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f"/services/{self.slug}/"


class Assets(TimeStampedModel):
    name = models.CharField(
        max_length=200,
        null=True,
        blank=True,
    )
    category = models.CharField(
        default="background",
        max_length=200,
        null=True,
        blank=True,
    )
    image_string = models.TextField(
        null=True,
        blank=True,
    )
    description = models.TextField(
        null=True,
        blank=True,
        default="background",
    )
    service_image = models.ImageField(
        null=True,
        blank=True,
        upload_to="images/",
        default="background",
    )
    image_url = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        default="background",
    )

    class Meta:
        verbose_name_plural = "Assets"

    @property
    def split_name(self):
        if self.name and "_" in self.name:
            parts = self.name.split("_", 1)
            return parts[0], parts[1]

        return "", ""

    def __str__(self):
        return self.name or "Unnamed Asset"


class Readme(TimeStampedModel):
    title = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    slug = models.SlugField(
        default="slug",
        max_length=255,
    )
    description = models.TextField(blank=True, null=True)
    installation = models.TextField(blank=True, null=True)
    usage = models.TextField(blank=True, null=True)
    configuration = models.TextField(blank=True, null=True)
    deployment = models.TextField(blank=True, null=True)
    contributing = models.TextField(blank=True, null=True)
    license = models.TextField(blank=True, null=True)
    credits = models.TextField(blank=True, null=True)
    contact = models.TextField(blank=True, null=True)
    additional_sections = models.TextField(blank=True, null=True)
    links = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Readme"

    def __str__(self):
        return self.title or "Readme Entry"


def readme_pre_save_receiver(sender, instance, **kwargs):
    if not instance.slug and instance.title:
        instance.slug = slugify(instance.title)


pre_save.connect(
    readme_pre_save_receiver,
    sender=Readme,
)


class MembershipRegistration(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
    )
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return (
            f"{self.first_name} "
            f"{self.last_name} "
            f"({self.email})"
        )


class ServiceCategory(models.Model):
    service = models.IntegerField(
        null=True,
        blank=True,
    )
    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )
    description = models.TextField(
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Service Category"
        verbose_name_plural = "Service Categories"

    def __str__(self):
        return self.name or "Service Category"

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)


class WCAGStandardWebsite(models.Model):
    company = models.CharField(
        max_length=500,
        null=True,
        blank=True,
    )
    app_name = models.CharField(
        max_length=500,
        null=True,
        blank=True,
    )
    page_name = models.TextField(
        null=True,
        blank=True,
    )
    website_url = models.FileField(
        upload_to="uploads/",
        null=True,
        blank=True,
    )
    updated_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    test_field = models.CharField(
        max_length=10,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.page_name or "Unnamed Page"


class Location(models.Model):
    zipcode = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    class Meta:
        unique_together = (
            "zipcode",
            "city",
            "state",
            "country",
        )
        ordering = [
            "country",
            "state",
            "city",
        ]

    def __str__(self):
        return (
            f"{self.city}, "
            f"{self.state}, "
            f"{self.country} "
            f"({self.zipcode})"
        )


class Pricing(models.Model):
    serial = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.IntegerField(
        help_text=(
            "Category reference "
            "(for example, Business or Individual)"
        )
    )
    subcategory = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    price = models.FloatField()
    discounted_price = models.FloatField(
        null=True,
        blank=True,
    )
    duration = models.PositiveIntegerField(
        help_text="Duration value"
    )
    contract_length = models.IntegerField(
        null=True,
        blank=True,
        help_text="Contract period",
    )
    is_direct = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    redirect_url_path = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["serial"]

    def __str__(self):
        return self.name


class Plan(models.Model):
    task = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    duration = models.IntegerField(
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True,
    )
    what = models.TextField(null=True, blank=True)
    why = models.TextField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    doc = models.FileField(
        upload_to="plans/docs/",
        null=True,
        blank=True,
    )
    pptlink = models.CharField(
        max_length=500,
        null=True,
        blank=True,
    )
    videolink = models.CharField(
        max_length=500,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    is_answered = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return self.task or f"Plan {self.pk}"


class ClientAvailability(models.Model):
    client = models.IntegerField()
    day = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()
    time_standards = models.CharField(max_length=20)
    topic = models.CharField(max_length=255)

    def __str__(self):
        return (
            f"Client {self.client} - "
            f"{self.day} "
            f"({self.start_time} to {self.end_time})"
        )


class Search(models.Model):
    topic = models.CharField(max_length=255)
    question = models.TextField()
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    uploaded = models.BooleanField(default=False)

    def __str__(self):
        return self.topic


class Company(models.Model):
    name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
    slug = models.SlugField(
        null=True,
        blank=True,
    )
    sector = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
    mission = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    website = models.URLField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name or "Company"


class MyModel(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="main_mymodels",
    )

    def __str__(self):
        return str(self.user)