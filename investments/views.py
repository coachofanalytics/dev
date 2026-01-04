from django.shortcuts import render, redirect, get_object_or_404


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Sum

from .models import Daily_Trades
from .forms import DailyTradesForm

from investments.models import Daily_Trades

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




def InvestmentStrategy_delete(request, pk):   
    investment = get_object_or_404(InvestmentStrategy, pk=pk)    
    if request.method == "POST":       
        investment.delete()
       
        return redirect("investments:InvestmentStrategy_list")
        
 
    return render(request, "investments/investment_delete.html", {"investment": investment})





def InvestmentStrategy_detail(request, pk):
  
    investment = get_object_or_404(InvestmentStrategy, pk=pk)
    return render(request, "investments/investment_dfetail.html", {"investment": investment})    






def daily_trades_list(request):
    trades_qs = Daily_Trades.objects.all().order_by("-date")

   
    symbol = request.GET.get("symbol")
    action = request.GET.get("action")
    account_type = request.GET.get("account_type")
    start = request.GET.get("start")
    end = request.GET.get("end")

    if symbol:
        trades_qs = trades_qs.filter(symbol__icontains=symbol)

    if action:
        trades_qs = trades_qs.filter(action=action)

    if account_type:
        trades_qs = trades_qs.filter(account_type__icontains=account_type)

    if start:
        trades_qs = trades_qs.filter(date__gte=start)

    if end:
        trades_qs = trades_qs.filter(date__lte=end)

    
    totals = trades_qs.aggregate(
        total_credit=Sum("credit"),
        total_debit=Sum("debit"),
    )

    total_credit = totals["total_credit"] or 0
    total_debit = totals["total_debit"] or 0
    total_net = total_credit - total_debit

    
    paginator = Paginator(trades_qs, 25)
    page_number = request.GET.get("page")
    trades = paginator.get_page(page_number)

    context = {
        "trades": trades,
        "total_credit": total_credit,
        "total_debit": total_debit,
        "total_net": total_net,
    }

    return render(request, "investments/trade_list.html", context)








from django.shortcuts import render, redirect
from django.contrib import messages

def daily_trades_create(request):
    if request.method == "POST":
        form = DailyTradesForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Trade created successfully.")
            return redirect("investments:daily_trades_list")

        # 🔒 IMPORTANT: invalid form → re-render (NO save)
        messages.error(request, "Please correct the errors below.")

    else:
        form = DailyTradesForm()

    return render(
        request,
        "investments/trades_create.html",  # ✅ singular
        {"form": form}
    )



