from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from document_processing.models import Application


@login_required
def document_application_list(request):
    """
    List all document applications.
    """

    applications = Application.objects.all().order_by('-submitted_at')

    # Search functionality
    search = request.GET.get('search')

    if search:
        applications = applications.filter(
            first_name__icontains=search
        ) | applications.filter(
            last_name__icontains=search
        ) | applications.filter(
            id_number__icontains=search
        ) | applications.filter(
            service_type__icontains=search
        )

    # Pagination
    paginator = Paginator(applications, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search': search,
        'total_applications': applications.count(),
    }

    return render(
        request,
        'document_processing/document_application_list.html',
        context
    )
