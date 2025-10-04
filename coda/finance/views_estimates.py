from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone

from .models import (
    BudgetEstimationTemplate,
    BudgetEstimateProjection,
)
from .services.budget_estimation_service import BudgetEstimationService


@login_required
def estimate_wizard(request):
    """User-facing estimate wizard: pick horizon/template, preview, save/submit."""
    companies = Company.objects.all()[:200]
    departments = Department.objects.all()[:200]
    templates = BudgetEstimationTemplate.objects.filter(is_active=True).order_by("name")

    context = {
        "companies": companies,
        "departments": departments,
        "templates": templates,
        "result": None,
        "selected": {},
    }

    if request.method == "POST":
        company_id = request.POST.get("company_id")
        department_id = request.POST.get("department_id")
        template_id = request.POST.get("template_id")
        horizon = request.POST.get("horizon", "monthly")
        method = request.POST.get("method", "average")
        action = request.POST.get("action", "estimate")

        if not company_id:
            messages.error(request, "Please select a company.")
            return render(request, "finance/estimates_wizard.html", context)

        company = Company.objects.filter(id=company_id).first()
        department = Department.objects.filter(id=department_id).first() if department_id else None
        template = BudgetEstimationTemplate.objects.filter(id=template_id).first() if template_id else None

        context["selected"] = {
            "company_id": company_id,
            "department_id": department_id or "",
            "template_id": template_id or "",
            "horizon": horizon,
            "method": method,
        }

        # Handle individual category submission
        if action == "submit_category":
            category = request.POST.get("category")
            amount = request.POST.get("amount")
            if category and amount:
                # Create a single-category projection
                proj = BudgetEstimateProjection.objects.create(
                    company=company,
                    department=department,
                    template=template,
                    horizon=horizon,
                    method=method,
                    estimates={category: float(amount)},
                    total_estimate=float(amount),
                    created_by=getattr(request.user, "customeruser", None) or None,
                    status="submitted",
                    submitted_at=timezone.now()
                )
                messages.success(request, f"Category '{category}' (${amount}) submitted for approval as Projection #{proj.id}.")
                return redirect(reverse("finance:projections-list"))
            else:
                messages.error(request, "Category and amount are required for individual submission.")
                return render(request, "finance/estimates_wizard.html", context)

        # Handle preview estimate
        svc = BudgetEstimationService()
        try:
            if horizon == "monthly":
                result = svc.estimate_next_month_budget(company=company, department=department, method=method)
            else:
                annual = svc.estimate_annual_budget(company=company, department=department, method="ytd_average")
                factor = 2 if horizon == "two_year" else 5
                result = {
                    "estimates": annual.get("estimates", {}),
                    "total_estimate": (annual.get("total_estimate") or 0) * factor,
                    "method": f"ytd_average_x{factor}",
                }
        except Exception as e:
            messages.error(request, f"Estimation failed: {e}")
            return render(request, "finance/estimates_wizard.html", context)

        # Save as projection
        if action in ("save", "submit"):
            # Convert Decimal objects to float for JSON serialization
            estimates = {}
            for key, value in result.get("estimates", {}).items():
                if hasattr(value, 'quantize'):  # Decimal object
                    estimates[key] = float(value)
                else:
                    estimates[key] = float(value) if value is not None else 0.0
            
            proj = BudgetEstimateProjection.objects.create(
                company=company,
                department=department,
                template=template,
                horizon=horizon,
                method=result.get("method", method),
                estimates=estimates,
                total_estimate=float(result.get("total_estimate") or 0),
                created_by=getattr(request.user, "customeruser", None) or None,
            )
            if action == "submit":
                proj.status = "submitted"
                proj.submitted_at = timezone.now()
                proj.save(update_fields=["status", "submitted_at"])
                messages.success(request, f"Projection #{proj.id} submitted for approval.")
            else:
                messages.success(request, f"Projection #{proj.id} saved.")
            return redirect(reverse("finance:projections-list"))

        # Show preview
        context["result"] = result
        return render(request, "finance/estimates_wizard.html", context)

    return render(request, "finance/estimates_wizard.html", context)


