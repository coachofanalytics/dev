from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse, Http404, JsonResponse
from django.urls import reverse
from django.db.models import Q
from django.conf import settings

from document_processing.models import (
    Application,
    Payment,
    GeneratedDocument,
    DataAccessLog,
    SERVICE_FEES,
    SUBCOUNTY_MAP,
)
from document_processing.forms import (
    ApplicationStep1Form,
    ApplicationSummaryForm,
    PaymentMethodForm,
)
from mail.custom_email import send_email


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _owner_or_404(request, queryset, user_field="user", **kwargs):
    """Return an object owned by the current user or raise 404 (AC12)."""
    return get_object_or_404(queryset, **{user_field: request.user}, **kwargs)


def _notify(user, subject, template, context):
    """Send a notification respecting the user's preferences (best effort)."""
    try:
        recipients = []
        if getattr(user, "email", None):
            recipients.append(user.email)
        if recipients:
            send_email(
                category=1,
                to_email=recipients,
                subject=subject,
                html_template=template,
                context=context,
            )
    except Exception as e:  # pragma: no cover - notifications are best effort
        import logging
        logging.getLogger(__name__).warning("Notification failed: %s", e)


# ---------------------------------------------------------------------------
# Applications dashboard
# ---------------------------------------------------------------------------

@login_required
def document_application_list(request):
    """My Applications dashboard (AC3)."""
    applications = Application.objects.filter(user=request.user).order_by(
        "-submitted_at", "-updated_at"
    )

    stats = [
        {"label": "Total Applications", "value": applications.count(), "color": "#2f63f4"},
        {
            "label": "Pending Action",
            "value": applications.filter(
                status__in=["submitted", "payment_pending"]
            ).count(),
            "color": "#f59e0b",
        },
        {
            "label": "Approved",
            "value": applications.filter(status="approved").count(),
            "color": "#0A926D",
        },
    ]

    search = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "").strip()
    field = request.GET.get("field", "all")

    if search:
        if field == "application_no":
            applications = applications.filter(application_number__icontains=search)
        elif field == "service":
            applications = applications.filter(service__icontains=search)
        elif field == "applicant":
            applications = applications.filter(
                Q(first_name__icontains=search) | Q(last_name__icontains=search)
            )
        else:
            applications = applications.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(id_number__icontains=search)
                | Q(application_number__icontains=search)
                | Q(service__icontains=search)
            )

    if status_filter:
        applications = applications.filter(status=status_filter)

    paginator = Paginator(applications, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "search": search,
        "status_filter": status_filter,
        "field": field,
        "stats": stats,
        "status_choices": Application.STATUS_CHOICES,
        "active_sidebar": "applications",
    }
    return render(request, "document_processing/document_application_list.html", context)


@login_required
def application_detail(request, pk):
    """View a single application (AC12 authorization)."""
    application = _owner_or_404(request, Application.objects, pk=pk)
    DataAccessLog.log_access(
        user=request.user,
        institution="Document Processing Portal",
        data_accessed=f"Application {application.application_number}",
        purpose="User viewed application details",
        access_type="view",
    )
    context = {"application": application, "active_sidebar": "applications"}
    return render(request, "document_processing/application_detail.html", context)


# ---------------------------------------------------------------------------
# Drafts
# ---------------------------------------------------------------------------

@login_required
def drafts_list(request):
    """Saved drafts (AC4)."""
    drafts = Application.objects.filter(
        user=request.user, status="draft"
    ).order_by("-updated_at")
    paginator = Paginator(drafts, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    context = {"page_obj": page_obj, "active_sidebar": "drafts"}
    return render(request, "document_processing/drafts_list.html", context)


@login_required
def delete_draft(request, pk):
    """Delete a draft with confirmation (AC4)."""
    draft = _owner_or_404(request, Application.objects, pk=pk)
    if request.method == "POST":
        draft.delete()
        messages.success(request, "Draft deleted successfully.")
        return redirect("document_processing:drafts")
    context = {"draft": draft, "active_sidebar": "drafts"}
    return render(request, "document_processing/delete_draft.html", context)


# ---------------------------------------------------------------------------
# New application workflow (3 steps)
# ---------------------------------------------------------------------------

@login_required
def application_create(request):
    """Step 1: Application form (AC5, AC6)."""
    if request.method == "POST":
        form = ApplicationStep1Form(request.POST)
        action = request.POST.get("action", "next")

        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.status = "draft"
            application.current_step = 1
            application.completion_percentage = 40
            application.fee = SERVICE_FEES.get(application.service, 0)
            application.save()

            if action == "save_draft":
                messages.success(request, "Draft saved. You can resume it later.")
                return redirect("document_processing:drafts")
            return redirect(
                "document_processing:application_summary", pk=application.pk
            )
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ApplicationStep1Form()

    context = {
        "form": form,
        "step": 1,
        "active_sidebar": "applications",
        "subcounty_map": SUBCOUNTY_MAP,
    }
    return render(request, "document_processing/application_form.html", context)


@login_required
def application_edit(request, pk):
    """Re-open Step 1 for an existing draft/application (Edit action)."""
    application = _owner_or_404(request, Application.objects, pk=pk)
    if request.method == "POST":
        form = ApplicationStep1Form(request.POST, instance=application)
        action = request.POST.get("action", "next")
        if form.is_valid():
            application = form.save(commit=False)
            application.fee = SERVICE_FEES.get(application.service, 0)
            application.save()
            if action == "save_draft":
                messages.success(request, "Draft saved.")
                return redirect("document_processing:drafts")
            return redirect(
                "document_processing:application_summary", pk=application.pk
            )
        messages.error(request, "Please correct the errors below.")
    else:
        form = ApplicationStep1Form(instance=application)

    context = {
        "form": form,
        "application": application,
        "step": 1,
        "active_sidebar": "applications",
        "subcounty_map": SUBCOUNTY_MAP,
    }
    return render(request, "document_processing/application_form.html", context)


@login_required
def application_summary(request, pk):
    """Step 2: Summary & confirmation (AC7)."""
    application = _owner_or_404(request, Application.objects, pk=pk)
    if request.method == "POST":
        form = ApplicationSummaryForm(request.POST)
        action = request.POST.get("action", "next")
        if form.is_valid():
            application.notify_by_phone = form.cleaned_data["notify_by_phone"]
            application.phone = form.cleaned_data.get("phone", "")
            application.notify_by_email = form.cleaned_data["notify_by_email"]
            application.email = form.cleaned_data.get("email", "")
            application.certified = form.cleaned_data["certified"]
            application.current_step = 2
            application.completion_percentage = 80
            if action == "cancel":
                application.save()
                return redirect("document_processing:applications")
            application.save()
            return redirect(
                "document_processing:application_payment", pk=application.pk
            )
        messages.error(request, "Please correct the errors below.")
    else:
        initial = {
            "notify_by_phone": application.notify_by_phone,
            "phone": application.phone,
            "notify_by_email": application.notify_by_email,
            "email": application.email,
            "certified": application.certified,
        }
        form = ApplicationSummaryForm(initial=initial)

    context = {
        "form": form,
        "application": application,
        "step": 2,
        "active_sidebar": "applications",
    }
    return render(request, "document_processing/application_summary.html", context)


@login_required
def application_payment(request, pk):
    """Step 3: Payment page (AC8)."""
    application = _owner_or_404(request, Application.objects, pk=pk)
    payment = application.payment
    context = {
        "application": application,
        "payment": payment,
        "step": 3,
        "active_sidebar": "applications",
    }
    return render(request, "document_processing/application_payment.html", context)


@login_required
def process_payment(request, pk):
    """Handle payment method modal submission (AC8, AC9)."""
    application = _owner_or_404(request, Application.objects, pk=pk)

    # Prevent duplicate payment confirmations (AC9).
    existing = application.payments.filter(status="paid").first()
    if existing:
        messages.info(request, "This application has already been paid.")
        return redirect("document_processing:application_payment", pk=application.pk)

    if request.method == "POST":
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            method = form.cleaned_data["method"]
            payer_phone = form.cleaned_data.get("payer_phone", "")
            transaction_id = form.cleaned_data.get("transaction_id", "")

            bill_id = f"BILL-{application.application_number}-{timezone.now().strftime('%H%M%S')}"
            payment = Payment.objects.create(
                application=application,
                method=method,
                amount=application.service_fee,
                bill_id=bill_id,
                payer_phone=payer_phone,
                transaction_id=transaction_id or None,
                status="paid",
                paid_at=timezone.now(),
            )
            application.status = "paid"
            application.current_step = 3
            application.completion_percentage = 100
            application.submitted_at = application.submitted_at or timezone.now()
            application.save()

            DataAccessLog.log_access(
                user=request.user,
                institution="Payment Provider",
                data_accessed=f"Payment for {application.application_number}",
                purpose=f"Payment confirmed via {payment.get_method_display()}",
                access_type="view",
            )
            _notify(
                request.user,
                "Payment received - DC48K Document Processing",
                "email/payment_received.html",
                {"application": application, "payment": payment},
            )
            messages.success(
                request,
                "Payment confirmed. Your request is now processing.",
            )
            return redirect("document_processing:application_payment", pk=application.pk)
        messages.error(request, "Please complete the payment details.")
    else:
        form = PaymentMethodForm()

    context = {
        "application": application,
        "form": form,
        "step": 3,
        "active_sidebar": "applications",
    }
    return render(request, "document_processing/application_payment.html", context)


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

@login_required
def documents_list(request):
    """My Documents (AC10)."""
    docs = GeneratedDocument.objects.filter(
        application__user=request.user
    ).order_by("-issued_at")
    paginator = Paginator(docs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))
    context = {"page_obj": page_obj, "active_sidebar": "documents"}
    return render(request, "document_processing/documents_list.html", context)


@login_required
def view_document(request, pk):
    """Secure online viewer (AC10, AC12)."""
    doc = _owner_or_404(request, GeneratedDocument.objects, user_field="application__user", pk=pk)
    DataAccessLog.log_access(
        user=request.user,
        institution="Document Processing Portal",
        data_accessed=f"Document {doc.title}",
        purpose="User viewed document online",
        access_type="view",
    )
    context = {"document": doc, "active_sidebar": "documents"}
    return render(request, "document_processing/view_document.html", context)


@login_required
def download_document(request, pk):
    """Secure, time-limited download (AC10, AC12)."""
    doc = _owner_or_404(request, GeneratedDocument.objects, user_field="application__user", pk=pk)
    if not doc.is_token_valid:
        doc.save()  # regenerate token + expiry
    DataAccessLog.log_access(
        user=request.user,
        institution="Document Processing Portal",
        data_accessed=f"Document {doc.title}",
        purpose="User downloaded document",
        access_type="download",
    )
    if not doc.file:
        raise Http404("Document file not found.")
    response = HttpResponse(doc.file, content_type="application/octet-stream")
    response["Content-Disposition"] = f'attachment; filename="{doc.title}.pdf"'
    return response


# ---------------------------------------------------------------------------
# Data access history (audit log)
# ---------------------------------------------------------------------------

@login_required
def access_history(request):
    """Read-only audit log (AC11)."""
    logs = DataAccessLog.objects.filter(user=request.user).order_by("-created_at")

    institution = request.GET.get("institution", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    if institution:
        logs = logs.filter(institution__icontains=institution)
    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)
    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)

    paginator = Paginator(logs, 15)
    page_obj = paginator.get_page(request.GET.get("page"))
    context = {
        "page_obj": page_obj,
        "institution": institution,
        "date_from": date_from,
        "date_to": date_to,
        "active_sidebar": "access_history",
    }
    return render(request, "document_processing/access_history.html", context)


# ---------------------------------------------------------------------------
# AJAX helpers (dependent dropdowns)
# ---------------------------------------------------------------------------

@login_required
def subcounties_json(request):
    """Return sub-counties for a given district (AC6 dependent dropdown)."""
    district = request.GET.get("district", "")
    options = SUBCOUNTY_MAP.get(district, [])
    return JsonResponse({"subcounties": options})
