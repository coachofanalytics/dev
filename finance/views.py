from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from .models import OverBoughtSold, PaymentInformation, Default_Payment_Fees
from .forms import Default_Payment_Fees_form


# Create your views here.

from django.http import HttpResponse


def index(request):
    return HttpResponse("Finance app is working correctly.")


from django.shortcuts import render
from .models import OverBoughtSold


def OverBoughtSold_list(request):
    overbought = OverBoughtSold.objects.all()
    return render(
        request, "finance/OverBoughtSold/OverBought.html", {"overbought": overbought}
    )


def home_view(request):
    return render(request, "finance/home.html")


def PaymentInformation_list(request):
    payments = PaymentInformation.objects.all()
    return render(request, "finance/payments_information.html", {"payments": payments})


from django.shortcuts import render
from .models import Default_Payment_Fees


def Default_Payment_Fees_list(request):
    payments = Default_Payment_Fees.objects.all()
    return render(
        request, "finance/Default_Payment_Fees_list.html", {"payments": payments}
    )


# create view
def Default_Payment_Fees_create(request):
    if request.method == "POST":
        form = Default_Payment_Fees_form(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Default_Payment_Fees successfully")
            return redirect("Default_Payment_Fees_list")
    else:
        form = Default_Payment_Fees_form()
    return render(request, "finance/Default_Payment_Fees_create.html", {"form": form})


# update view


def Default_Payment_Fees_update(request, pk):
    payments = get_object_or_404(Default_Payment_Fees, pk=pk)
    if request.method == "POST":
        form = Default_Payment_Fees_form(request.POST, instance=payments)
        if form.is_valid():
            form.save()
            messages.success(request, "Default_Payment_Fees successfully")
            return redirect("Default_Payment_Fees_list")
    else:
        form = Default_Payment_Fees_form(instance=payments)
    return render(request, "finance/Default_Payment_Fees_update.html", {"form": form})
