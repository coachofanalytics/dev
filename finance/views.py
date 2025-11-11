from django.shortcuts import render
from .models import OverBoughtSold

# Create your views here.


def finance_dashboard(request):
    return render(request, "finance/finance_base.html")


# finance/views.py
def OverBoughtSold_list(request):
    records = OverBoughtSold.objects.order_by("-created_at", "-id")
    return render(request, "finance/overboughtsold_list.html", {"records": records})
