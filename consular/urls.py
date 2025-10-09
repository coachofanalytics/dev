from django.urls import path
from . import views

app_name="consular"

urlpatterns = [
    path("",views.consular_view,name="consular"),
]
