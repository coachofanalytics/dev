"""
KYC URL Configuration
"""
from django.urls import path
from . import views

app_name = 'kyc'

urlpatterns = [
    # User views
    path('upload/', views.upload_document, name='upload'),
    path('my-documents/', views.my_documents, name='my_documents'),
    path('document/<uuid:document_id>/', views.document_detail, name='document_detail'),
    path('document/<uuid:document_id>/delete/', views.delete_document, name='delete_document'),
    path('status/', views.verification_status, name='verification_status'),

    # Staff views
    path('staff/review/', views.staff_review_list, name='staff_review_list'),
    path('staff/review/<uuid:document_id>/', views.staff_review_document, name='staff_review_document'),
]
