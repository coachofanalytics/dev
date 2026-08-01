from django.contrib import admin
from .models import TestTracker,Transaction


from django.contrib import admin

# from .models import Transaction


@admin.register(TestTracker)
class TestTrackerAdmin(admin.ModelAdmin):

    list_display = (
        "test_name",
        "test_type",
        "status",
        "execution_time",
        "executed_at",
    )


    from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sender",
        "department",
        "receiver",
        "phone",
        "type",
        "amount",
        "transaction_cost",
        "total_amount",
        "payment_method",
        "activity_date",
        "created_at",
    )

    list_filter = (
        "type",
        "payment_method",
        "activity_date",
        "created_at",
    )

    search_fields = (
        "receiver",
        "phone",
        "department",
        "description",
        "sender__username",
        "sender__email",
    )

    readonly_fields = (
        "total_amount",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-activity_date",
        "-created_at",
    )

    date_hierarchy = "activity_date"