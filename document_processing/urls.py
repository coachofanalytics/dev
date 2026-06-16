from django.urls import path
from . import views

urlpatterns = [
    path(
        'applications/',
        views.document_application_list,
        name='document_application_list'
    ),
]