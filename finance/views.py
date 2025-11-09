from django.shortcuts import render
from .models import OverBoughtSold,PaymentInformation



# Create your views here.

from django.http import HttpResponse

def index(request):
    return HttpResponse("Finance app is working correctly.")

from django.shortcuts import render
from .models import OverBoughtSold

def OverBoughtSold_list(request):
    overbought = OverBoughtSold.objects.all()
    return render(request, "finance/OverBoughtSold/OverBought.html", {"overbought": overbought})


def home_view(request):
    return render(request, 'finance/home.html')


def PaymentInformation_list(request)  :
    payments=PaymentInformation.objects.all()
    return render(request,'finance/payments_information.html',{'payments':payments})
