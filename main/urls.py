from django.urls import path
from main.views import AboutView

from . import views

from .views import update_volunteer,delete_volunteer  # ✅ if you want to import the view directly


# from .utils import convert_html_to_pdf

from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.layout, name='layout'),
    # Add more paths as needed, for example:
    # path('donations/', views.donation_list, name='donation_list'),
]
from django.urls import path
from . import views

app_name = 'main'

urlpatterns =[]
#   path('history/', views.history, name='history'),
#   path('team/', views.team_list, name='team_view'),
#   path('history/', views.history, name='history'),
    # path('services/', views.service_list, name='service_list'),
    # path('gallery/', views.gallery_list, name='gallery_list')   ('news/', views.news_list, name='news_list'),
    # path('contract-us/', views.contact_us_list, name='contact_us_list'),
    # path('about/', AboutView.as_view(), name='about'),
    # path('send_email/', views.send_notification, name='send_email'),
    # path('volunteer/', views.volunteer_list, name='volunteer_list'),
    # path('create_volunteer/', views.create_volunteer, name='create_volunteer'),
    # path('volunteers/update/<int:pk>/', update_volunteer, name='volunteer_update'),
    # path('volunteers/delete/<int:pk>/', delete_volunteer, name='volunteer_delete'),
    # path('detail_volunter/<int:pk>/', delete_volunteer, name='detail_volunter'),
    # path('donation_list/<int:pk>/', donation_list, name='donation_list')




           #==============ERRORS==============================================
    # path('400Error/', views.error400, name='400error'),
    # path('403Error/', views.error403, name='403error'),
    # path('404Error/', views.error404, name='404error'),
    # path('500Error/', views.error500, name='500error'),
    # path('errors/', views.template_errors, name='template_errors'),

    # path('400/', views.hendler400, name='400-error'),
    # path('403/', views.hendler403, name='403-error'),
    # path('404/', views.hendler404, name='404-error'),
    # path('500/', views.hendler500, name='500-error'),
