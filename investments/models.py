from django.db import models
from decimal import Decimal
from django.utils import timezone


class investment_content(models.Model):
    title =models.CharField(max_length=50,null=False)
    slug= models.CharField(max_length=200,null=False)
    description=models.TextField(null=True)

    def __str__(self):
        return self.title
