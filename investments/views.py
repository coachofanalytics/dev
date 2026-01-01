from django.shortcuts import render, redirect, get_object_or_404


from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import InvestmentStrategy
from django.utils import timezone
from pytz import timezone

from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger




from django.shortcuts import render


def investments_dashboard(request):
    return render(request, "investments/home.html")



def InvestmentStrategy_list(request):
    investments = InvestmentStrategy.objects.all()
    return render(request, "investments/investments_list.html", {"investments": investments})