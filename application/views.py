
# ============================================================
# CODA APPLICATION - VIEWS
# ============================================================

from django.contrib.auth import get_user_model
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from django.views.decorators.http import require_http_methods

from .models import (
    UserProfile,
    JobDetails,
    JobOpening,
    JobApplication,
    Reporting,
    MyModel,
)

from .forms import JobApplicationForm


# ============================================================
# USER MODEL
# ============================================================

User = get_user_model()


# ============================================================
# APPLICATION HOME
# ============================================================

def home(request):
    """
    Display the application homepage.
    """

    return render(
        request,
        "application/home.html",
        {
            "title": "Application Home",
        },
    )


# ============================================================
# CAREERS PAGE
# ============================================================

def career(request):
    """
    Display the CODA careers page.
    """

    return render(
        request,
        "application/applications/career.html",
        {
            "title": "Careers",
        },
    )


# ============================================================
# JOB LISTINGS
# ============================================================

def job_list(request):
    """
    Display all active CODA job vacancies.
    """

    jobs = JobOpening.objects.filter(
        is_active=True
    ).order_by("-posted_on")

    context = {
        "title": "Available Job Listings",
        "jobs": jobs,
    }

    return render(
        request,
        "application/job_list.html",
        context,
    )


# ============================================================
# JOB DETAILS
# ============================================================

def job_detail(request, pk):
    """
    Display the details of one active vacancy.
    """

    job = get_object_or_404(
        JobOpening,
        pk=pk,
        is_active=True,
    )

    context = {
        "title": job.title,
        "job": job,
    }

    return render(
        request,
        "application/job_detail.html",
        context,
    )


# ============================================================
# JOB APPLICATION FORM
# ============================================================

@require_http_methods(["GET", "POST"])
def job_apply(request, pk):
    """
    Display and process an application for a vacancy.
    """

    job = get_object_or_404(
        JobOpening,
        pk=pk,
        is_active=True,
    )

    if request.method == "POST":

        form = JobApplicationForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            application = form.save(commit=False)

            # Associate the application with the selected job.
            application.job = job

            # Set the initial status.
            application.status = "submitted"

            # Save the application and uploaded CV.
            application.save()

            return render(
                request,
                "application/application_success.html",
                {
                    "title": "Application Submitted",
                    "job": job,
                },
            )

    else:

        form = JobApplicationForm()

    context = {
        "title": f"Apply for {job.title}",
        "job": job,
        "form": form,
    }

    return render(
        request,
        "application/job_apply.html",
        context,
    )


# ============================================================
# GENERAL APPLY PAGE
# ============================================================

def apply(request):
    """
    Existing general application route.

    Redirect visitors to CODA registration.
    """

    return redirect("accounts:join")
