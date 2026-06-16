from django.urls import path
from . import views

app_name = 'document_processing'
urlpatterns = [
    path(
        'document_applications/',
        views.document_application_list,
        name='DocumentApplication'
    ),
]