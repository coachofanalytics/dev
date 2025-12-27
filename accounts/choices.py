from django.db import models

class CategoryChoices(models.IntegerChoices):
    ORDINARY_MEMBER = 1, 'Ordinary Member (Free)'
    ACTIVE_MEMBER = 2, 'Active Member'
    EXECUTIVE_MEMBER = 3, 'Executive Member'
    FBO_ORDINARY = 4, 'FBO & Ordinary (Free)'
    ACTIVE_ORGANIZATION = 5, 'Active Organization'
    ROYAL_ORGANIZATION = 6, 'Royal Organization'


class SubCategoryChoices(models.IntegerChoices):
    NO_SELECTION = 0, 'No selection'
    FULL_TIME = 1, 'Full Time'
    CONTRACTUAL = 2, 'Contractual'
    AGENT = 3, 'Agent'
    SHORT_TERM = 4, 'Short Term'
    LONG_TERM = 5, 'Long Term'
    CURRENT = 6, 'Current'
    PROSPECTIVE = 7, 'Prospective'
    OTHER = 8, 'Other'