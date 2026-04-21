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
    
]
