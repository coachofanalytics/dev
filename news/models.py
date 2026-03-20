from django.db import models
from django.utils.text import slugify
from .ai_services import generate_article_summary
# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class NewsArticle(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    author = models.CharField(max_length=100)
    featured_image =models.ImageField(upload_to='news_images/')
    content = models.TextField()

    status = models.CharField(max_length=10,choices=STATUS_CHOICES, default='DRAFT')
    ai_summary = models.TextField(blank=True,null=False, help_text="AI_generated summary for index page")
    is_breaking = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.PositiveBigIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        if self.content and not self.ai_summary:
            self.ai_summary = generate_article_summary(self.content)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.title