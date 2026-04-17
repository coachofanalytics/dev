from django.urls import path, include
from . import views

urlpatterns = [
    path('',views.TaskList),
    path('create/',views.TaskCreate),
]
