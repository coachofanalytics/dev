from django.shortcuts import render, redirect, get_object_or_404


from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import InvestmentStrategy
from django.utils import timezone
from .forms import  InvestmentStrategyForm
from pytz import timezone

from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger




from django.shortcuts import render


def investments_dashboard(request):
    return render(request, "investments/home.html")



def InvestmentStrategy_list(request):
    investments = InvestmentStrategy.objects.all()
    return render(request, "investments/investments_list.html", {"investments": investments})

def InvestmentStrategy_create(request):
    if request.method == "POST":
        form = InvestmentStrategyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("investments:InvestmentStrategy_list")
    
    else:
        form = InvestmentStrategyForm()
    
    return render(request, "investments/investments_create.html", {"form": form})

def InvestmentStrategy_update(request, pk):
 
    investment = get_object_or_404(InvestmentStrategy, pk=pk)
    
    if request.method == "POST":
    
        form = InvestmentStrategyForm(request.POST, instance=investment)
        if form.is_valid():
            form.save()
            return redirect("investments:InvestmentStrategy_list")
    else:
  
        form = InvestmentStrategyForm(instance=investment) 
        
    return render(request, "investments/investment_update.html", {"form": form})
