# Create your views here.
# dev/finance/views.py
from django.shortcuts import render,redirect,get_object_or_404
from .models import OverBoughtSold
from . forms import OverBoughtSoldForm


def finance_dashboard(request):
    return render(request, "finance/finance_base.html")


def OverBoughtSold_list(request):
    records = OverBoughtSold.objects.order_by("-created_at", "-id")
    return render(request, "finance/overboughtsold_list.html", {"records": records})

def overboughtsold_create(request):
    if request.method == "POST":
        form = OverBoughtSoldForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('OverBoughtSold_list') 
    else:
        form = OverBoughtSoldForm()  
    
    return render(request, 'finance/overboughtsold_create.html', {'form': form})



