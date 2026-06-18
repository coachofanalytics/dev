from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from.forms import Document_ApplicationForm

from .models import Document_Application
import uuid


@login_required
def document_application_list(request):
    applications = Document_Application.objects.filter(
        user=request.user
    ).order_by("-id")

    paginator = Paginator(applications, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "document_processing/document_application_list.html",
        {
            "page_obj": page_obj,
            "total_applications": applications.count(),
        }
    )
 

@login_required
def Document_Application_create(request):
    if request.method == "POST":
        form = Document_ApplicationForm(request.POST)

        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.application_number = "APP-" + str(uuid.uuid4())[:8].upper()
            application.status = "draft"
            application.save()

            return redirect("document_application_list")

    else:
        form = Document_ApplicationForm()

    context = {
        "form": form
    }

    return render(
        request,
        "document_processing/document_application_form.html",
        context
    )