from django.db import models

class Scholarship(models.Model):
    LEVEL_CHOICES = [
        ('Undergraduate', 'Undergraduate'),
        ('Masters', 'Masters'),
        ('PhD', 'PhD'),
        ('Vocational', 'Vocational'),
    ]
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Closing Soon', 'Closing Soon'),
        ('Closed', 'Closed'),
    ]
    title = models.CharField(max_length=255)
    provider = models.CharField(max_length=255)
    level = models.CharField(max_length=50, choices=LEVEL_CHOICES)
    field = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    deadline = models.DateField()
    amount = models.CharField(max_length=100)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Open')

    def __str__(self):
        return self.title


class Course(models.Model):
    ENROLLMENT_CHOICES = [
        ('Open', 'Open'),
        ('Closing Soon', 'Closing Soon'),
        ('Closed', 'Closed'),
    ]
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    format = models.CharField(max_length=100)
    enrollment = models.CharField(max_length=50, choices=ENROLLMENT_CHOICES)
    start_date = models.DateField()

    def __str__(self):
        return self.title
