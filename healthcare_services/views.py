from django.views.generic import ListView
from .models import DoctorSpecialty


class DoctorSpecialtyListView(ListView):
    model = DoctorSpecialty
    template_name = "healthcare_services/doctor_specialty_list.html"
    context_object_name = "specialties"
    ordering = ["name"]
    paginate_by = 20

    