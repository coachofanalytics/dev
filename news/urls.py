from django.urls import path

from .views import CategoryCreateView,CategoryEditView,CategoryDeleteView,CategoryArticleListView

urlpattern = [
    path('category/add/', CategoryCreateView.as_view(),name='category_add'),
    path('category/<int:pk>/edit/',CategoryEditView.as_view(),name='category_edit'),
    path('category/<int:pk>/delete/',CategoryDeleteView.as_view(), name ='category_delete'),
    path('category/<slug:slug>/', CategoryArticleListView.as_view(), name = 'category_detail')
]