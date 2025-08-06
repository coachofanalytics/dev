import random
import string
import boto3
from datetime import date, timedelta
from multiprocessing import context
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404,render, redirect
from django.db.models import Q
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .models import UserProfile,JobDetails
from datetime import datetime, timedelta
from main.utils import path_values
from django.contrib import messages

# User=settings.AUTH_USER_MODEL
User = get_user_model()

def apply(request):
    return redirect("accounts:join")

# ------------------------Interview Section-------------------------------------#.
def career(request):
    return render(request, "application/applications/career.html", {"title": "career"})



def job_list(request):
    jobs = JobDetails.objects.all()
    return render(request,"application/job_list.html",{'jobs':jobs})
