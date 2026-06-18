from django.db import models
from django.conf import settings


class DocumentApplication(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    service_type = models.CharField(max_length=50)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    id_number = models.CharField(max_length=20)
    district = models.CharField(max_length=100)
    sub_county = models.CharField(max_length=100)
    reason = models.TextField()
    status = models.CharField(max_length=20, default="draft")
    fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class DocumentDraft(models.Model):
    application = models.OneToOneField(DocumentApplication, on_delete=models.CASCADE)
    completion_percentage = models.IntegerField(default=0)
    draft_data = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Draft for {self.application}"