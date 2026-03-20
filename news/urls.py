from django.urls import path

from .views import CategoryCreateView,CategoryEditView,CategoryDeleteView,CategoryArticleListView
from .views import LandingPageView,ArticleHomeView,ArticleDetailView,ArticleCreateView,ArticleDeleteView
from .views import ArticleEditView
app_name = 'news'

urlpatterns = [

    path('news/', LandingPageView.as_view(), name='home'),
    path('news/details/', ArticleHomeView.as_view(), name ='news_listing'),
     path('news/details/<slug:slug>', ArticleDetailView.as_view(), name='article_detail'),
    path('article/<int:pk>/delete/', ArticleDeleteView.as_view(), name='article-delete'),
    path('dashboard/article<int:pk>/edit/', ArticleEditView, name='article_edit'),
    path('dashboard/article/add/', ArticleCreateView.as_view(), name='article_add'),
    path('category/add/', CategoryCreateView.as_view(),name='category_add'),
    path('category/<int:pk>/edit/',CategoryEditView.as_view(),name='category_edit'),
    path('category/<int:pk>/delete/',CategoryDeleteView.as_view(), name ='category_delete'),
    path('category/<slug:slug>/', CategoryArticleListView.as_view(), name = 'category_detail')
]