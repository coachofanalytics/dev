"""
URL configuration for audit app.
"""

from django.urls import path
from audit import views

app_name = "audit"

urlpatterns = [
    # Audit log views
    path("logs/", views.AuditLogListView.as_view(), name="audit_log_list"),
    path("logs/<uuid:pk>/", views.AuditLogDetailView.as_view(), name="audit_log_detail"),
    path("logs/export/", views.AuditLogExportView.as_view(), name="audit_log_export"),
    path("logs/stats/", views.AuditLogStatsView.as_view(), name="audit_log_stats"),
    # Login history
    path(
        "login-history/",
        views.LoginHistoryListView.as_view(),
        name="login_history_list",
    ),
]
