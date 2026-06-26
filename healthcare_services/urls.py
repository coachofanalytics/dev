from django.urls import path
from .views import DoctorSpecialtyListView

app_name = "healthcare_services"

urlpatterns = [
    path(
        "doctor-specialties/",
        DoctorSpecialtyListView.as_view(),
        name="doctor_specialty_list"
    ),
]