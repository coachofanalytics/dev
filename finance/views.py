from django.shortcuts import render, redirect, get_object_or_404
from .models import OverBoughtSold, PaymentInformation
from .forms import OverBoughtSoldForm,PaymentInformationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from pytz import timezone
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Finance Dashboard (Placeholder)
@login_required
def finance_dashboard(request):
    # Example context data (you should replace with real calculations or queries)
    total_revenue = 500000
    total_expenses = 200000
    net_profit = total_revenue - total_expenses
    pending_invoices = 5
    
    # Example transactions (replace with actual transaction data)
    recent_transactions = [
        {'date': timezone.now(), 'description': 'Payment from Client A', 'category': 'Revenue', 'amount': 50000, 'status': 'Completed'},
        {'date': timezone.now(), 'description': 'Payment from Client B', 'category': 'Revenue', 'amount': 30000, 'status': 'Pending'},
    ]

    context = {
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'pending_invoices': pending_invoices,
        'recent_transactions': recent_transactions,
    }

    return render(request, "finance/finance_dashboard.html", context)

# OverBoughtSold List View
def OverBoughtSold_list(request):
    records = OverBoughtSold.objects.order_by("-created_at", "-id")
    return render(request, "finance/finance_dashboard.html", {"records": records})

# OverBoughtSold Create View
def overboughtsold_create(request):
    if request.method == "POST":
        form = OverBoughtSoldForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('OverBoughtSold_list')
    else:
        form = OverBoughtSoldForm()
    
    return render(request, 'finance/overboughtsold_create.html', {'form': form})


@login_required
def payment_list(request):
   
    q = (request.GET.get("q") or "").strip()


    qs = PaymentInformation.objects.select_related("customer").all()
    

    if q:
        qs = qs.filter(
            Q(customer__username__icontains=q) |
            Q(customer__email__icontains=q) |
            Q(payment_method__icontains=q)
        )

  
    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page")
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
    
        page_obj = paginator.page(1)
    except EmptyPage:
       
        page_obj = paginator.page(paginator.num_pages)

    context = {"page_obj": page_obj, "q": q}
    
    return render(request, "finance/payment_list.html", context)



@login_required


def payment_create(request):
    if request .method =="POST":
        form= PaymentInformationForm(request.POST)
        if form .is_valid():
            form.save()
            messages.success(request, "Payment record created successfully!")
            return redirect("finance:payment_list")
        messages.error(request, "please correct the error below.")
    else:
        form =PaymentInformationForm  ()
    
    return render(request, "finance/payment_create.html", {"form":form,"mode":"create"})      