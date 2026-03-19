from django.shortcuts import render,get_object_or_404
from .models import Category, NewsArticle
from django.views.generic.edit import CreateView,UpdateView,DeleteView
from django.views.generic import ListView,DetailView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import (LoginRequiredMixin)


# Create your views here.

class CategoryArticleListView(ListView):
    model: NewsArticle
    template = 'category_articles.html'
    context_object_name = 'articles'
    paginate_by = 6 


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
