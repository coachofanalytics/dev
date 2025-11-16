from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.models import User
from .models import BusinessProfile, InvestmentOpportunity, JobOpportunity, JobApplication, SavedItem
from django.contrib.contenttypes.models import ContentType


def browse_businesses(request):
    businesses = BusinessProfile.objects.all()
    industry = request.GET.get('industry')
    funding_stage = request.GET.get('funding_stage')
    search = request.GET.get('search')
    
    if industry:
        businesses = businesses.filter(industry__icontains=industry)
    if funding_stage:
        businesses = businesses.filter(funding_stage=funding_stage)
    if search:
        businesses = businesses.filter(
            Q(company_name__icontains=search) | Q(industry__icontains=search)
        )
    
    industries = BusinessProfile.objects.values_list('industry', flat=True).distinct()
    context = {'businesses': businesses, 'industries': industries}
    return render(request, 'marketplace/browse_businesses.html', context)


def browse_opportunities(request):
    opportunities = InvestmentOpportunity.objects.filter(status='open')
    industry = request.GET.get('industry')
    search = request.GET.get('search')
    
    if industry:
        opportunities = opportunities.filter(industry__icontains=industry)
    if search:
        opportunities = opportunities.filter(Q(title__icontains=search) | Q(description__icontains=search))
    
    industries = InvestmentOpportunity.objects.values_list('industry', flat=True).distinct()
    context = {'opportunities': opportunities, 'industries': industries}
    return render(request, 'marketplace/browse_opportunities.html', context)


def browse_jobs(request):
    jobs = JobOpportunity.objects.filter(status='open')
    job_type = request.GET.get('job_type')
    search = request.GET.get('search')
    
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if search:
        jobs = jobs.filter(Q(title__icontains=search) | Q(description__icontains=search))
    
    context = {'jobs': jobs}
    return render(request, 'marketplace/browse_jobs.html', context)


def business_detail(request, business_id):
    business = get_object_or_404(BusinessProfile, user_id=business_id)
    business.increment_views()
    opportunities = InvestmentOpportunity.objects.filter(business=business.user, status='open')
    jobs = JobOpportunity.objects.filter(business=business.user, status='open')
    context = {'business': business, 'opportunities': opportunities, 'jobs': jobs}
    return render(request, 'marketplace/business_detail.html', context)


def opportunity_detail(request, slug):
    opportunity = get_object_or_404(InvestmentOpportunity, slug=slug)
    opportunity.increment_views()
    context = {'opportunity': opportunity}
    return render(request, 'marketplace/opportunity_detail.html', context)


def job_detail(request, slug):
    job = get_object_or_404(JobOpportunity, slug=slug)
    job.increment_views()
    # Only check if user has applied if they are authenticated
    has_applied = False
    if request.user.is_authenticated:
        has_applied = JobApplication.objects.filter(job=job, applicant=request.user).exists()
    context = {'job': job, 'has_applied': has_applied}
    return render(request, 'marketplace/job_detail.html', context)


@login_required
def my_saved_items(request):
    saved_items = SavedItem.objects.filter(user=request.user)
    context = {'saved_items': saved_items}
    return render(request, 'marketplace/my_saved_items.html', context)


@login_required
def update_business_profile(request):
    """Update business profile"""
    try:
        business_profile = BusinessProfile.objects.get(user=request.user)
    except BusinessProfile.DoesNotExist:
        business_profile = None
    
    from .forms import BusinessProfileForm
    
    if request.method == 'POST':
        form = BusinessProfileForm(request.POST, instance=business_profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Business profile updated successfully!')
            return redirect('business_dashboard')
    else:
        form = BusinessProfileForm(instance=business_profile)
    
    context = {'form': form, 'business_profile': business_profile}
    return render(request, 'marketplace/update_business_profile.html', context)


@login_required
def post_investment_opportunity(request):
    """Create new investment opportunity"""
    from .forms import InvestmentOpportunityForm
    
    if request.method == 'POST':
        form = InvestmentOpportunityForm(request.POST)
        if form.is_valid():
            opportunity = form.save(commit=False)
            opportunity.business = request.user
            opportunity.status = 'open'
            opportunity.save()
            messages.success(request, 'Investment opportunity posted successfully!')
            return redirect('business_dashboard')
    else:
        form = InvestmentOpportunityForm()
    
    context = {'form': form}
    return render(request, 'marketplace/post_investment_opportunity.html', context)


@login_required
def post_job_opportunity(request):
    """Create new job opportunity"""
    from .forms import JobOpportunityForm
    
    if request.method == 'POST':
        form = JobOpportunityForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.business = request.user
            job.status = 'open'
            job.save()
            messages.success(request, 'Job opportunity posted successfully!')
            return redirect('business_dashboard')
    else:
        form = JobOpportunityForm()
    
    context = {'form': form}
    return render(request, 'marketplace/post_job_opportunity.html', context)


def find_investors(request):
    """Browse investors - filter users by investor category"""
    from accounts.models import UserProfile
    
    investors = UserProfile.objects.filter(category__slug='investor').select_related('user')
    search = request.GET.get('search')
    
    if search:
        investors = investors.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search)
        )
    
    context = {'investors': investors}
    return render(request, 'marketplace/find_investors.html', context)
