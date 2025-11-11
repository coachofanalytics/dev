# Create your views here.
# dev/finance/views.py
from django.shortcuts import render
from .models import OverBoughtSold


def finance_dashboard(request):
    return render(request, "finance/finance_base.html")


def OverBoughtSold_list(request):
    records = OverBoughtSold.objects.order_by("-created_at", "-id")
    return render(request, "finance/overboughtsold_list.html", {"records": records})
