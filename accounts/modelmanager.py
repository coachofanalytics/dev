from django.db.models import Q
from decimal import *
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from datetime import datetime
from django.contrib.auth import get_user_model
from django.utils import timezone


class DepartmentManager(models.Manager):
    def all(self):
        return self.get_queryset()

    def get_by_id(self, id):
        qs = self.get_queryset().filter(id=id)
        if qs.count() == 1:
            return qs.first()
        return None
