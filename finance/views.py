# dev/finance/views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import OverBoughtSold, Payment_History  # adjust if model name differs

def finance_dashboard(request):
    return render(request, "finance/finance_base.html")

def OverBoughtSold_list(request):
    records = OverBoughtSold.objects.order_by("-created_at", "-id")
    return render(request, "finance/overboughtsold_list.html", {"records": records})

def payment_history_update_view(request, pk):
    payment = get_object_or_404(Payment_History, pk=pk)
    if request.method == "POST":
        payment.status = request.POST.get("status", payment.status)
        payment.save()
        return redirect("finance:payment_history_update", pk=pk)  # or your list page
    return render(request, "finance/payment_history_update.html", {"payment": payment})
