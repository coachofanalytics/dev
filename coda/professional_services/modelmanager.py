
from django.db.models import Q
from decimal import *
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from datetime import datetime
from django.contrib.auth import get_user_model
from django.utils import timezone

# User=settings.AUTH_USER_MODEL
User = get_user_model()

# ==================================INTERVIEWS====================================
class InterviewQuerySet(models.query.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def featured(self):
        return self.filter(featured=True, is_active=True)

    def search(self, query):
        lookups = (
            Q(category__icontains=query)
            | Q(question_type__icontains=query)
            | Q(last_name__icontains=query)
            | Q(first_name__icontains=query)
            | Q(upload_date__icontains=query)
            | Q(username__username__icontains=query)
        )
        return self.filter(lookups).distinct()

class InterviewManager(models.Manager):
    def get_queryset(self):
        # return super(TaskManager, self).get_queryset().filter(is_active=True)
        return InterviewQuerySet(self.model, using=self._db)

    def all(self):
        return self.get_queryset()

    """ def featured(self):
        return self.get_queryset().featured() """

    def get_by_slug(self, slug):
        qs = self.get_queryset().filter(slug=slug)
        if qs.count() == 1:
            return qs.first()
        return None

    def get_by_question(self, question_type):
        qs = self.get_queryset().filter(question_type=question_type)
        if qs.count() == 1:
            return qs.first()
        return None

    def search(self, query):
        return self.get_queryset().active().search(query)

class RoleQuerySet(models.query.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def featured(self):
        return self.filter(featured=True, is_active=True)

    def search(self, query):
            lookups = (
                Q(category__icontains=query)| Q(question_type__icontains=query)
            )
            return self.filter(lookups).distinct()

class RoleManager(models.Manager):
    def get_queryset(self):
        # return super(TaskManager, self).get_queryset().filter(is_active=True)
        return RoleQuerySet(self.model, using=self._db)

    def all(self):
        return self.get_queryset()

    def get_by_slug(self, slug):
        qs = self.get_queryset().filter(slug=slug)
        if qs.count() == 1:
            return qs.first()
        return None

    def get_by_question(self, question_type):
        qs = self.get_queryset().filter(question_type=question_type)
        if qs.count() == 1:
            return qs.first()
        return None

    def search(self, query):
        return self.get_queryset().active().search(query)


class CategoryManager(models.Manager):
    def get_queryset(self):
        return super(CategoryManager, self).get_queryset().filter(is_active=True)
        # return RoleQuerySet(self.model, using=self._db)

    def all(self):
        return self.get_queryset()

    def get_by_slug(self, slug):
        qs = self.get_queryset().filter(slug=slug)
        if qs.count() == 1:
            return qs.first()
        return None

    def get_by_category(self, title):
        qs = self.get_queryset().filter(title=title)
        if qs.count() == 1:
            return qs.first()
        return None

    def search(self, query):
        return self.get_queryset().active().search(query)


class SubCategoryManager(models.Manager):
    def get_queryset(self):
        return super(SubCategoryManager, self).get_queryset().filter(is_active=True)
        # return RoleQuerySet(self.model, using=self._db)

    def all(self):
        return self.get_queryset()

    def get_by_slug(self, slug):
        qs = self.get_queryset().filter(slug=slug)
        if qs.count() == 1:
            return qs.first()
        return None

    def get_by_subcategory(self, title):
        qs = self.get_queryset().filter(title=title)
        if qs.count() == 1:
            return qs.first()
        return None

    def search(self, query):
        return self.get_queryset().active().search(query)

class ActivityManager(models.Manager):
    def get_queryset(self):
        return super(ActivityManager, self).get_queryset().filter()
        # return RoleQuerySet(self.model, using=self._db)

    def all(self):
        return self.get_queryset()

    def get_by_slug(self, slug):
        qs = self.get_queryset().filter(slug=slug)
        if qs.count() == 1:
            return qs.first()
        return None

    def get_by_activity(self, name):
        qs = self.get_queryset().filter(name=name)
        if qs.count() == 1:
            return qs.first()
        return None

    def search(self, query):
        return self.get_queryset().active().search(query)
