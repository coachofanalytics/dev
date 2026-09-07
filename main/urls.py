from django.urls import path
from . import views

app_name = "main"

urlpatterns = [
# <<<<<<< HEAD
    path("service-categories/", views.all_service_categories, name="all_service_categories"),
    path("service-categories/create/", views.servicecategory_create, name="servicecategory_create"),

    path("service-categories/<int:pk>/", views.service_category_detail, name="service_category_detail"),
    path("service-categories/<int:pk>/update/", views.servicecategory_update, name="servicecategory_update"),
    path("service-categories/<int:pk>/delete/", views.servicecategory_delete, name="servicecategory_delete"),

    path("services/<int:service_id>/categories/", views.service_category_list, name="servicecategory_by_service"),
]
# ======
[
    path('', views.layout, name='layout'),
   
    #=======================SERVICES=====================================
    # path('newservice/', views.ServiceCreateView.as_view(template_name='main/form.html'), name='newservice'),
    # path('services/', views.services, name='services'),


path('location/', views.location_list, name='location_list'),
path('location_create/', views.location_create, name='location_create'),
path("location_update/<int:pk>/", views.location_update, name="location_update"),
path("location_detail/<int:pk>/", views.location_detail, name="location_detail"),
path("location_delete/<int:pk>/", views.location_delete, name="location_delete"),
path('pricing/', views.pricing_list, name='pricing_list'),
# path('testimonials/', views.testimonials_list, name='testimonials_list'),

# path('testimonial_create/', views.testimonial_create, name='testimonial_create'),
# path("testimonial_update/<int:pk>/", views.testimonial_update, name="testimonial_update"),
path('planlist/', views.plan_list_view, name='plan_list'),
path('plancreate/', views.create_plan, name='plan_create'),
path("planupdate/<int:pk>/", views. plan_update, name="plan_update"),

path("plandelete/<int:pk>/", views.plan_delete, name="plan_delete"),
path('clientavailability/', views.clientavailability_list, name='clientavailability_list'),
path('clientavailability_create/', views.clientavailability_create, name='clientavailability_create'),
path("clientavailability_update/<int:pk>/", views. clientavailability_update, name="clientavailability_update"),
path("clientavailability_detail/<int:pk>/", views. clientavailability_detail, name="clientavailability_detail"),
path("clientavailability_delete/<int:pk>/", views. clientavailability_delete, name="clientavailability_delete"),
path('searchlist/', views.search_list, name='search_list'),
path('searchcreate/', views.search_create, name='search_create'),
path('searchupdate/<int:pk>/', views.search_update, name='search_update'),
path("searchdelete/<int:pk>/", views. search_delete, name="search_delete"),
path("search_detail/<int:pk>/", views. search_detail, name="search_detail"),
path('companylist/', views.company_list, name='company_list'),






    # # path("display_service/<str:slug>/", views.display_service, name="display_service"),
    # # path("display_plans/<str:slug>/", views.service_plans, name="service_plans"),
    # #==============DEPARTMENTS==============================================
    # #==============DEPARTMENTS==============================================
    # #---------------HUMAN RESOURCE--------------------#

    # #-----------------------------FINANCE--------------------#
       
    #     #--------------------------MANAGEMENT--------------------#
    # #----------------------------IT-------------------------#
    #     path('it/', views.it, name='it'),
    # #-----------------------README-------------------------#
    # path('newusecase/', views.UseCaseCreateView.as_view(template_name='main/form.html'), name='newusecase'),
    # path('display_usecases/', views.display_usecases, name='display_usecases'),

   #==============ERRORS==============================================
    # path('400Error/', views.error400, name='400error'),
    # path('403Error/', views.error403, name='403error'),
    # path('404Error/', views.error404, name='404error'),
    # path('500Error/', views.error500, name='500error'),

    # path('400/', views.hendler400, name='400-error'),
    # path('403/', views.hendler403, name='403-error'),
    # path('404/', views.hendler404, name='404-error'),
    # path('500/', views.hendler500, name='500-error'),

    #===========company records=======


]
# >>>>>>> e79fe45578418c384fbb84ca7760d91bef020a33
