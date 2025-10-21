from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone

from finance.models import BudgetEstimateProjection
from accounts.models import Department
from main.models import Company


@login_required
def projections_list(request):
    """List saved projections and allow submit action."""
    try:
        company_id = request.GET.get("company_id")
        department_id = request.GET.get("department_id")

        qs = BudgetEstimateProjection.objects.select_related("budget__company", "budget__department", "budget__category").all()
        if company_id:
            qs = qs.filter(budget__company_id=company_id)
        if department_id:
            qs = qs.filter(budget__department_id=department_id)

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

        companies = Company.objects.all()[:100]
        
        departments = Department.objects.all()[:100]

        context = {
            "projections": qs.order_by("-created_at")[:200],
            "companies": companies,
            "departments": departments,
            "selected_company_id": company_id,
            "selected_department_id": department_id,
        }
        return render(request, "finance/projections_list.html", context)
    
    except Exception as e:
        from django.http import HttpResponse
        return HttpResponse(f"Error in projections_list: {str(e)}", status=500)


