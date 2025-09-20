from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from coda_project import settings

from . import views
# from .views import (CategoriesCreate, CategoriesListView, CategoriesUpdate,
#                     SubCategoriesListView)

app_name = 'marketing'
urlpatterns = [
    # PAGE FOR ADMIN
    path('',views.marketing,name="marketing"),
     path('update-category/', views.marketing, name='update_user_category'),
    path('search-users/', views.search_users, name='search_users'),
    
    
    #---------------WHATSAPP--------------------#
    path('email_ads/', views.send_email_ads, name='email_ads'),
    path('email_training/', views.send_training_ad, name='email_training'),
    path('whatsapp/', views.runwhatsapp, name='whatsapp'),
    path('groups/<str:title>', views.whatsapp_groups, name='whatsapp_list'),
    path('refresh_groups/', views.refresh_whatsapp_groups, name='refresh_groups'),
    path('newwhatsapp/', views.whatsappCreateView.as_view(template_name='main/form.html'), name='whatsapp_new'),
    # path('whatsapp/<str:slug>/', views.whatsappUpdateView.as_view(template_name='main/snippets_templates/form.html'), name='whatsapp_update'),
    path('delete_whatsapp/<str:slug>/', views.delete_whatsapp, name='delete_whatsapp'),
    path('adslist/', views.ads, name='ads_list'),
    path('newad/', views.AdsCreateView.as_view(template_name='main/form.html'), name='ads_new'),
    path('ad/<int:pk>/', views.AdsUpdateView.as_view(template_name='main/form.html'), name='ad_update'),
    path('whatsapp/<int:pk>/', views.whatsappUpdateView.as_view(template_name='main/form.html'), name='whatsapp_update'),
    path('delete_ad/<int:id>/', views.delete_ads, name='delete_ad'),
    # path('whatsapp_status/', views.whatsapp_status, name='whatsapp_status'),

]

'''
urlpatterns = [
    # PAGE FOR ADMIN
    path('',views.store_home,name="store_home"),
    
    #CATEGORIES
    path('category_list',CategoriesListView.as_view(),name="category_list"),
    path('category_create',CategoriesCreate.as_view(),name="category_create"),
    path('category_update/<slug:pk>',CategoriesUpdate.as_view(),name="category_update"),

    #SUBCATEGORIES

    path('sub_category_list',views.SubCategoriesListView.as_view(),name="sub_category_list"),
    path('sub_category_create',views.SubCategoriesCreate.as_view(),name="sub_category_create"),
    path('sub_category_update/<slug:pk>',views.SubCategoriesUpdate.as_view(),name="sub_category_update"),
    
]
'''