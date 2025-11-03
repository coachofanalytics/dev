from django.urls import path

from .views import member_home


urlpatterns = [

    # Define your URL patterns here
    path('membership', member_home, name='member_home'),
    
]