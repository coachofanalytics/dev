"""
Core app URL Configuration
Public-facing pages including landing page and all website pages
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('about/', views.about_page, name='about'),
    path('services/', views.services_page, name='services'),
    path('projects/', views.projects_page, name='projects'),
    path('projects/<slug:slug>/', views.project_detail, name='project_detail'),
    path('partners/', views.partners_page, name='partners'),
    path('gallery/', views.gallery_page, name='gallery'),
    path('news/', views.news_page, name='news'),
    path('news/<slug:slug>/', views.news_detail, name='news_detail'),
    path('contact/', views.contact_page, name='contact'),
]
