from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

# Create your views here.


def hendler400(request, exception):
    return render(request, "400.html")


def hendler403(request, exception):
    return render(request, "403.html", status=403)


def hendler404(request, exception):
    return render(request, "404.html")