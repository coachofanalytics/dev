from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from  . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('join/', views.join, name='join'),
    path('forum/', views.forum_home, name='forum_home'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('post/<int:post_id>/', views.view_post, name='view_post'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('category/<slug:slug>/create/', views.create_post, name='create_post'),
    path('events/', views.event_calendar, name='event_calendar'),
    path('events/create/', views.create_event, name='create_event'),
    path('event/<int:id>/', views.event_detail, name='event_detail'),
    path('contact/', views.contact_view, name='contact'),
    
     # Directory URLs
    path('directory/', views.directory, name='directory'),
    path('directory/join/', views.join_directory, name='join_directory'),
    path('directory/edit/<int:pk>/', views.edit_directory_profile, name='edit_directory_profile'),
    path('directory/delete/<int:pk>/', views.delete_directory_profile, name='delete_directory_profile'),
    
    # Event CRUD URLs
    path('events/update/<int:id>/', views.update_event, name='update_event'),
    path('events/delete/<int:id>/', views.delete_event, name='delete_event'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
