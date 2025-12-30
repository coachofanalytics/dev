from django.shortcuts import render, redirect, get_object_or_404


from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from pytz import timezone
from .models import investment_content
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger




from django.shortcuts import render


def investments_dashboard(request):
    return render(request, "investments/home.html")


def investment_list(request):
    invest = investment_content.objects.all()
    return render(request,"investments/invest_list.html",{"invest": invest})
