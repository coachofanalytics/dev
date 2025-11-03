from django.shortcuts import render
from .models import Scholarship, Course

def home(request):
    scholarships = Scholarship.objects.all()
    courses = Course.objects.all()

    # filters
    level = request.GET.get('level')
    location = request.GET.get('location')
    field = request.GET.get('field')

    if level and level != 'All':
        scholarships = scholarships.filter(level=level)
    if location and location != 'All':
        scholarships = scholarships.filter(location=location)
    if field and field != 'All':
        scholarships = scholarships.filter(field=field)

    context = {
        'scholarships': scholarships,
        'courses': courses,
        'levels': ['All', 'Undergraduate', 'Masters', 'PhD', 'Vocational'],
        'locations': Scholarship.objects.values_list('location', flat=True).distinct(),
        'fields': Scholarship.objects.values_list('field', flat=True).distinct(),
    }
    return render(request, 'index.html', context)
