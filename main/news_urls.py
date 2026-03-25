from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('news/', views.LandingPageView.as_view(), name='home'),
    path('news/details/', views.ArticleHomeView.as_view(), name='news_listing'),
    path('news/details/<slug:slug>', views.ArticleDetailView.as_view(), name='article_detail'),
    path('article/<int:pk>/delete/', views.ArticleDeleteView.as_view(), name='article_delete'),
    path('news/subscribe/', views.subscribe, name='subscribe'),
    path('confirm/<str:token>/', views.confirm_email, name='confirm_email'),
    path('news/dashboard/', views.AdminDashboardView.as_view(), name='dashboard'),
    path('dashboard/article<int:pk>/edit/', views.ArticleEditView.as_view(), name='article_edit'),
    path('dashboard/article/add/', views.ArticleCreateView.as_view(), name='article_add'),
    path('category/add/', views.CategoryCreateView.as_view(), name='category_add'),
    path('category/<int:pk>/edit/', views.CategoryEditView.as_view(), name='category_edit'),
    path('category/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    path('category/<slug:slug>/', views.CategoryArticleListView.as_view(), name='category_detail'),
]
