from django.contrib import admin
from .models import TestTracker


@admin.register(TestTracker)
class TestTrackerAdmin(admin.ModelAdmin):

    list_display = (
        "test_name",
        "test_type",
        "status",
        "execution_time",
        "executed_at",
    )