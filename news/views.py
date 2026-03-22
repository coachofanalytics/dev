from django.shortcuts import get_object_or_404, render
from django.views.generic.edit import CreateView,UpdateView,DeleteView
from django.views.generic import ListView,DetailView, TemplateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib.auth.mixins import (LoginRequiredMixin)
from django.core.mail import send_mail
from django.urls import reverse
from django.http import JsonResponse
from .models import Category, NewsArticle, Subscriber
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
                Q(title__icontains=query) |
                Q(content__icontains=query)
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
    form_class = ArticleForm
    template_name = 'article_form.html'
    success_url =reverse_lazy('news:dashboard')

    def form_valid(self, form):
        if not form.instance.author:
            form.instance.author = self.request.user
        return super().form_valid(form)
    
class ArticleEditView(LoginRequiredMixin, UpdateView):
    model = NewsArticle
    form_class = ArticleForm
    template_name = 'article_form.html'
    success_url = reverse_lazy('news:dashboard')

    
class ArticleDeleteView(LoginRequiredMixin, DeleteView):
    model = NewsArticle
    template_name = 'article_confirm_delete.html'
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
    model = Category
    fields = ['name', 'description']
    template_name = 'category_form.html'
    success_url = reverse_lazy('news:dashboard')

    
class CategoryEditView(LoginRequiredMixin, UpdateView):
    model = Category
    fields = ['name', 'description']
    template_name = 'category_form.html'
    success_url = reverse_lazy('news:dashboard')

class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'category_confirm_delete.html'
    success_url = reverse_lazy('news:dashboard')


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        query = self.request.GET.get('q')
        articles = NewsArticle.objects.all()
        
        if query:
           
            recent_articles = articles.filter(
                Q(title__icontains=query) | 
                Q(category__name__icontains=query)
            ).order_by('-created_at')
        else:
           
            recent_articles = articles.order_by('-created_at')[:10]

        context['total_count'] = articles.count()
        context['published_count'] = articles.filter(status='PUBLISHED').count()
        context['draft_count'] = articles.filter(status='DRAFT').count()
        context['subscriber_count'] = Subscriber.objects.filter(confirmed=True).count()
        context['categories'] = Category.objects.all()
        context['recent_articles'] = recent_articles
        context['query'] = query 
        
        return context

def subscribe(request):
    if request.method == "POST":
        email = request.POST.get('email')
        if email:
            sub, created = Subscriber.objects.get_or_create(email=email)
            if created:
                verify_url = request.build_absolute_uri(
                    reverse('news:confirm_email', args=[sub.conf_token])
                )

                send_mail(
                    "Action Required: Confirm your subscription",
                    f"Thanks for signing up! please Verify your email here: {verify_url}",
                    "noreply@dc48kcoda.dev",
                    [email]
                )

                return JsonResponse({"status": "success", "msg": "Check your email to confirm!"})
            return JsonResponse({"status": "exists", "msg": "you're already on the list."})
        return JsonResponse({"status": "error", "msg": "Invalid Request"})

    return JsonResponse({"status": "error", "msg": "Only POST allowed"}, status=405)

def confirm_email(request, token):
    subscriber = get_object_or_404(Subscriber, conf_token=token)
    subscriber.confirmed = True
    subscriber.save()

    return render(request, 'subscription_confirmed.html', {
        'email': subscriber.email
    })