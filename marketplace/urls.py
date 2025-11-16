from django.urls import path
from . import views

app_name = "marketplace"

urlpatterns = [
    # Browse views
    path("businesses/", views.browse_businesses, name="browse_businesses"),
    path("opportunities/", views.browse_opportunities, name="browse_opportunities"),
    path("jobs/", views.browse_jobs, name="browse_jobs"),

    # Business actions - must come before detail views to avoid slug matching
    path("business/update/", views.update_business_profile, name="update_business_profile"),
    path("opportunity/post/", views.post_investment_opportunity, name="post_investment_opportunity"),
    path("job/post/", views.post_job_opportunity, name="post_job_opportunity"),
    path("investors/", views.find_investors, name="find_investors"),

    # Detail views - slug patterns come after specific paths
    path("business/<int:business_id>/", views.business_detail, name="business_detail"),
    path("opportunity/<slug:slug>/", views.opportunity_detail, name="opportunity_detail"),
    path("job/<slug:slug>/", views.job_detail, name="job_detail"),

    # Saved items
    path("saved/", views.my_saved_items, name="my_saved_items"),
]
