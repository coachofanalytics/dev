from decimal import *
from django.utils.translation import gettext_lazy as _
from django.db import models


class DepartmentManager(models.Manager):
    def all(self):
        return self.get_queryset()

    def get_by_id(self, id):
        qs = self.get_queryset().filter(id=id)
        if qs.count() == 1:
            return qs.first()
        return None
