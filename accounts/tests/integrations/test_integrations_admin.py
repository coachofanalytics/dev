from django.contrib import admin

from .models import Transaction


# @admin.register(Transaction)
# class TransactionintegrationAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "sender",
#         "department",
#         "receiver",
#         "phone",
#         "type",
#         "amount",
#         "transaction_cost",
#         "total_amount",
#         "payment_method",
#         "activity_date",
#         "created_at",
#     )

#     list_filter = (
#         "type",
#         "payment_method",
#         "activity_date",
#         "created_at",
#     )

#     search_fields = (
#         "receiver",
#         "phone",
#         "department",
#         "description",
#         "sender__username",
#         "sender__email",
#     )

#     readonly_fields = (
#         "total_amount",
#         "created_at",
#         "updated_at",
#     )

#     ordering = (
#         "-activity_date",
#         "-created_at",
#     )

#     date_hierarchy = "activity_date"

#     fieldsets = (
#         (
#             "Transaction Details",
#             {
#                 "fields": (
#                     "sender",
#                     "department",
#                     "receiver",
#                     "phone",
#                     "type",
#                     "activity_date",
#                 )
#             },
#         ),
#         (
#             "Financial Information",
#             {
#                 "fields": (
#                     "qty",
#                     "amount",
#                     "transaction_cost",
#                     "total_amount",
#                     "payment_method",
#                 )
#             },
#         ),
#         (
#             "Additional Information",
#             {
#                 "fields": (
#                     "receipt_link",
#                     "description",
#                 )
#             },
#         ),
#         (
#             "System Information",
#             {
#                 "fields": (
#                     "created_at",
#                     "updated_at",
#                 ),
#                 "classes": ("collapse",),
#             },
#         ),
#     )

#     @admin.display(description="Total Amount")
#     def total_amount(self, obj):
#         return obj.total_amount