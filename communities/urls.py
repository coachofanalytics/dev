from django.urls import path
from  . import views

app_name = 'communities'

urlpatterns = [
    path('', views.home, name='home'),
    path('join/', views.join, name='join'),
    path('directory/', views.member_directory, name='member_directory'),
    path('directory/join/<int:member_id>/', views.join_directory, name='join_directory'),
    path('directory/join-form/', views.join_directory_form, name='join_directory_form'),
    path('forum/', views.forum_home, name='forum_home'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('post/<int:post_id>/', views.view_post, name='view_post'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('category/<slug:slug>/create/', views.create_post, name='create_post'),
    path('events/', views.event_calendar, name='event_calendar'),
    path('event/create/', views.create_event, name='create_event'),
    path('event/<int:id>/', views.event_detail, name='event_detail'),
    path('event/<int:id>/edit/', views.edit_event, name='edit_event'),
    path('event/<int:id>/delete/', views.delete_event, name='delete_event'),
    path('contact/', views.contact_view, name='contact'),
   
]