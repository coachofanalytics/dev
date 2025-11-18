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

        # Safely query projections - handle database schema issues gracefully
        try:
            # Check if budget relationship exists
            if hasattr(BudgetEstimateProjection, 'budget'):
                qs = BudgetEstimateProjection.objects.all()
                # Try to use select_related if the relationship exists
                try:
                    qs = qs.select_related("budget__company", "budget__department", "budget__category")
                except Exception:
                    # If select_related fails, just use all() without joins
                    pass
                
                if company_id:
                    try:
                        qs = qs.filter(budget__company_id=company_id)
                    except Exception:
                        # If budget relationship doesn't work, filter by company directly if field exists
                        if hasattr(BudgetEstimateProjection, 'company'):
                            qs = qs.filter(company_id=company_id)
                if department_id:
                    try:
                        qs = qs.filter(budget__department_id=department_id)
                    except Exception:
                        # If budget relationship doesn't work, filter by department directly if field exists
                        if hasattr(BudgetEstimateProjection, 'department'):
                            qs = qs.filter(department_id=department_id)
            else:
                # No budget relationship, query without it
                qs = BudgetEstimateProjection.objects.all()
                if company_id and hasattr(BudgetEstimateProjection, 'company'):
                    qs = qs.filter(company_id=company_id)
                if department_id and hasattr(BudgetEstimateProjection, 'department'):
                    qs = qs.filter(department_id=department_id)
        except Exception as e:
            # Fallback: just get all projections if query fails
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error querying projections with filters: {e}")
            qs = BudgetEstimateProjection.objects.all()

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


