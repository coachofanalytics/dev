from django.shortcuts import render

# Create your views here.
def consular_view(request):
    return render(request,"consular/consular.html")