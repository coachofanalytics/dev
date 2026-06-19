from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import DoctorSpecialty
from .forms import DoctorSpecialtyForm


@login_required
def doctor_specialty_list(request):
    specialties = DoctorSpecialty.objects.all().order_by("name")

    return render(
        request,
        "healthcare_services/doctor_specialty_list.html",
        {"specialties": specialties}
    )

    @login_required
def doctor_specialty_create(request):
    if request.method == "POST":
        form = DoctorSpecialtyForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("doctor_specialty_list")
    else:
        form = DoctorSpecialtyForm()

    return render(
        request,
        "healthcare_services/doctor_specialty_form.html",
        {"form": form}
    )


# Create your views here.
