from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from finance_app.models import PaymentInformation
# from finance_app.forms import PaymentInformationForm


# =========================
# LIST VIEW
# =========================
def payment_list(request):
    payments = PaymentInformation.objects.all().order_by("-created_at")
    return render(request, "finance_app/paymentinformation_list.html", {"payments": payments})
