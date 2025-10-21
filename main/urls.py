from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.home_view, name='home'),

    # ====== Services ======
    path('servicecategory_list/', views.servicecategory_list, name='servicecategory_list'),
    path('servicecategory_create/', views.servicecategory_create, name='servicecategory_create'),
    path('services/<int:pk>/update/', views.servicecategory_update, name='servicecategory_update'),
    path('services/<int:pk>/delete/', views.servicecategory_delete, name='servicecategory_delete'),
    path('services/<int:pk>/detail/', views.servicecategory_detail, name='servicecategory_detail'),

    # ====== Locations ======
    path("location_list/", views.location_list, name="account-location_list"),
    path("location_create/", views.location_create, name="location_create"),
    path("location_update/<slug:slug>/", views.location_update, name="location_update"),  



       # ====== volunteer ======  
    path('volunteer_list/', views.volunteer_list, name='volunteer_list'),
    path('volunteer/create/', views.volunteer_create, name='volunteer_create'),
    path('volunteer/<int:pk>/', views.volunteer_update, name='volunteer_update'),
    path('volunteer/<int:pk>/delete/', views.volunteer_delete, name='volunteer_delete'),
    path('volunteer/<int:pk>/detail/', views.volunteer_detail, name='volunteer_detail'),

     # ====== Testimonials ======

    

    path('testimonials/', views.testimonials_list, name='testimonials_list'),
    path('testimonials/create/', views.testimonial_create, name='testimonial_create'),
    path('testimonials/<int:pk>/', views.testimonial_detail, name='testimonial_detail'),
    path('testimonials/<int:pk>/edit/', views.testimonial_update, name='testimonial_update'),
    path('testimonials/<int:pk>/delete/', views.testimonial_delete, name='testimonial_delete'),


    # ====== Other ======
    path('it/', views.it, name='it'),
    path('finance/', views.finance, name='finance'),
    path('hr/', views.hr, name='hr'),

    # ====== Error Pages ======
    path('400Error/', views.error400, name='400error'),
    path('403Error/', views.error403, name='403error'),
    path('404Error/', views.error404, name='404error'),
    path('500Error/', views.error500, name='500error'),
]
