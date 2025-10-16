from django.shortcuts import render

# Create your views here.


def member_home(request):
    return render(request, 'member_home.html')