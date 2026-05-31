"""
Communities App URLs
Handles all routing for community features:
- Home: /communities/
- Member Directory: /communities/directory/
- Forum: /communities/forum/
- Events: /communities/events/
- Contact: /communities/contact/
"""

from django.urls import path
from main.views import (
    communities_home as home,
    communities_join as join,
    communities_member_directory as member_directory,
    communities_join_directory as join_directory,
    communities_join_directory_form as join_directory_form,
    communities_forum_home as forum_home,
    communities_category_detail as category_detail,
    communities_view_post as view_post,
    communities_add_comment as add_comment,
    communities_create_post as create_post,
    communities_event_calendar as event_calendar,
    communities_create_event as create_event,
    communities_event_detail as event_detail,
    communities_edit_event as edit_event,
    communities_delete_event as delete_event,
    communities_contact_view as contact_view,
    communities_message_compose as message_compose,
    communities_message_inbox as message_inbox,
    communities_message_sent as message_sent,
    communities_message_detail as message_detail,
    communities_message_reply as message_reply,
)

app_name = 'communities'

urlpatterns = [
    # Community Home
    path('', home, name='home'),
    
    # Join Community
    path('join/', join, name='join'),
    
    # Member Directory
    path('directory/', member_directory, name='member_directory'),
    path('directory/join/<int:member_id>/', join_directory, name='join_directory'),
    path('directory/join-form/', join_directory_form, name='join_directory_form'),
    
    # Forum
    path('forum/', forum_home, name='forum_home'),
    path('category/<slug:slug>/', category_detail, name='category_detail'),
    path('category/<slug:slug>/create/', create_post, name='create_post'),
    path('post/<int:post_id>/', view_post, name='view_post'),
    path('post/<int:post_id>/comment/', add_comment, name='add_comment'),
    
    # Events
    path('events/', event_calendar, name='event_calendar'),
    path('event/create/', create_event, name='create_event'),
    path('event/<int:id>/', event_detail, name='event_detail'),
    path('event/<int:id>/edit/', edit_event, name='edit_event'),
    path('event/<int:id>/delete/', delete_event, name='delete_event'),
    
    # Contact
    path('contact/', contact_view, name='contact'),

    # Messaging
    path('messages/inbox/', message_inbox, name='message_inbox'),
    path('messages/sent/', message_sent, name='message_sent'),
    path('messages/compose/<int:recipient_id>/', message_compose, name='message_compose'),
    path('messages/<int:message_id>/', message_detail, name='message_detail'),
    path('messages/<int:message_id>/reply/', message_reply, name='message_reply'),
]
