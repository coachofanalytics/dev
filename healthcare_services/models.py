from django.db import models
from django.conf import settings


class DoctorSpecialty(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name
        
# Create your models here.
