from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone

from .models import BudgetEstimateProjection, Company, Department


@login_required
def projections_list(request):
    """List saved projections and allow submit action."""
    company_id = request.GET.get("company_id")
    department_id = request.GET.get("department_id")

    qs = BudgetEstimateProjection.objects.select_related("company", "department", "template").all()
    if company_id:
        qs = qs.filter(company_id=company_id)
    if department_id:
        qs = qs.filter(department_id=department_id)

    if request.method == "POST":
        proj_id = request.POST.get("projection_id")
        action = request.POST.get("action")
        projection = get_object_or_404(BudgetEstimateProjection, id=proj_id)

        if action == "submit" and projection.status == "draft":
            projection.status = "submitted"
            projection.submitted_at = timezone.now()
            projection.save(update_fields=["status", "submitted_at"])
            messages.success(request, f"Projection {projection.id} submitted for approval.")
        else:
            messages.warning(request, "No action performed.")
        return redirect(reverse("finance:projections-list") + (f"?company_id={company_id}" if company_id else ""))

    context = {
        "projections": qs.order_by("-created_at")[:200],
        "companies": Company.objects.all()[:100],
        "departments": Department.objects.all()[:100],
        "selected_company_id": company_id,
        "selected_department_id": department_id,
    }
    return render(request, "finance/projections_list.html", context)


