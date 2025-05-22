from django.shortcuts import render

# Create your views here.
def index(request):
    """View function to render the main event gallery page"""
    return render(request, 'gallery/index.html')
