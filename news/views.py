from django.shortcuts import render,get_object_or_404
from .models import Category, NewsArticle
from django.views.generic.edit import CreateView,UpdateView,DeleteView
from django.views.generic import ListView,DetailView, TemplateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib.auth.mixins import (LoginRequiredMixin)
from .forms import ArticleForm

# Create your views here.


class LandingPageView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_news'] = NewsArticle.objects.filter(status = 'PUBLISHED').order_by('created_at')[:3]
        context['categories'] = Category.objects.all()
        return context


class ArticleHomeView(ListView):
    model = NewsArticle
    template_name = 'news_listing.html'
    context_object_name = 'articles'
    paginate_by = 7

    def get_queryset(self):
        queryset = NewsArticle.objects.filter(status = 'PUBLISHED').order_by('created_at')

        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title_icontains=query) |
                Q(content_icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
    
        all_articles = context['articles']
        if all_articles:
            context['hero_article'] = all_articles[0]
            context['grid_articles'] = all_articles[1:]
        return context

class ArticleDetailView(DetailView):
    model = NewsArticle 
    template_name = 'article_detail.html'
    context_object_name = 'article'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_articles'] = NewsArticle.objects.filter(
            category=self.object.category
        ).exclude(
            id=self.object.id
        )[:3]
        return context

class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = NewsArticle
    fields = ['name', 'description']
    template_name = 'news/category_form.html'
    success_url =reverse_lazy('news:dashboard')

    def form_valid(self, form):
        if not form.instance.author:
            form.instance.author = self.request.user
        return super().form_valid(form)
    
class ArticleEditView(LoginRequiredMixin):
    model = NewsArticle
    form_class = ArticleForm
    template_name = 'news/article_form.html'
    success_url = reverse_lazy('news:dashboard')

    
class ArticleDeleteView(LoginRequiredMixin, DeleteView):
    model = NewsArticle
    success_url = reverse_lazy('news:dashboard')



# Category Views
class CategoryArticleListView(ListView):
    model = NewsArticle
    template_name = 'category_articles.html'
    context_object_name = 'articles'
    paginate_by = 6 

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return NewsArticle.objects.filter(category=self.category, status = 'PUBLISHED').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context
        


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model =Category
    fields = ['name', 'description']
    template_name = 'news/category_form.html'
    success_url = reverse_lazy('news:dashboard')

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return NewsArticle.objects.filter(category=self.category, status ='PUBLISHED').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context =super().get_context_data(**kwargs)
        context ['category'] = self.category
        return context
    
class CategoryEditView(LoginRequiredMixin, UpdateView):
    model = Category
    fields = ['name', 'description']
    template_name = 'news/category_form.html'
    success_url = reverse_lazy('news:dashboard')

class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    success_url = reverse_lazy('news:dashboard')

