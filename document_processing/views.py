from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import DocumentApplication

@login_required
def document_application_list(request):
    applications = DocumentApplication.objects.filter(
        user=request.user
    ).order_by('-submitted_at')

    paginator = Paginator(applications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'document_processing/DocumentApplication.html',
        {'page_obj': page_obj}
    )