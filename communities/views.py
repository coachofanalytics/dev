from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q

from main.forms import MessageForm
from .utils import send_email
from .forms import JoinForm, PostForm, CommentForm, EventForm, ContactForm, DirectoryProfileForm
from .models import Post, ForumCategory, CommentP, EventCalendar, CommunityMember, DirectoryProfile  # Import Post, ForumCategory, ForumPost, Comment, and EventCalendar models
from django.db.models import Q
# Create your views here.
def home(request):
	return render(request, 'home.html')


# community views
# views.py - Minimal join view with only 2 fields
def join(request):
    if request.method == 'POST':
        # Get ONLY the 2 fields from request
        name = request.POST.get('name')
        email = request.POST.get('email')
        agree_to_directory = request.POST.get('agree_to_directory') == 'true'
        
        # Simple validation
        if not name or not email:
            messages.error(request, 'Please fill in all required fields')
            return redirect('join')
        
        # Check if email already exists
        if CommunityMember.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered')
            return redirect('join')
        
        # Create member with ONLY the 2 fields
        member = CommunityMember.objects.create(
            name=name,
            email=email,
            is_public_directory=agree_to_directory,
            profession="To be updated",  # Default values for other fields
            region="Global"
        )
        
        # Send email
        subject = 'Welcome to Our Community!'
        recipient_list = [email]
        context = {'name': name}
        
        send_email(
            subject,
            recipient_list,
            context,
            'email.html',
            'email.txt'
        )
        
        messages.success(request, f'Welcome {name}! You have joined the community.')
        return redirect('member_directory')
    
    return render(request, 'join.html')

def member_directory(request):
    """
    Verified Member Directory with search functionality
    """
    # Start with ALL members (remove restrictive filters temporarily)
    members = CommunityMember.objects.all().order_by('-date_joined')

    # Initialize variables
    search_query = request.GET.get('search', '')
    region_filter = request.GET.get('region', '')
    profession_filter = request.GET.get('profession', '')
    
    # Apply search by name or profession
    if search_query:
        members = members.filter(
            Q(name__icontains=search_query) |
            Q(profession__icontains=search_query) |
            Q(specialization__icontains=search_query) |
            Q(bio__icontains=search_query)
        )

    # Apply region filter
    if region_filter:
        members = members.filter(region__icontains=region_filter)
    
    # Apply profession filter
    if profession_filter:
        members = members.filter(profession__icontains=profession_filter)
    
    # OPTIONAL: Only show members who want to be in directory
    # Uncomment this line if you want directory-only members
    # members = members.filter(is_public_directory=True)
    
    # Get unique regions and professions for filter dropdowns
    unique_regions = CommunityMember.objects.values_list('region', flat=True).distinct().order_by('region')
    unique_professions = CommunityMember.objects.values_list('profession', flat=True).distinct().order_by('profession')

    # Add is_premium field (temporary)
    for member in members:
        member.is_premium = member.id % 3 == 0  # Every 3rd member is premium for demo

    context = {
        'members': members,
        'search_query': search_query,
        'region_filter': region_filter,
        'profession_filter': profession_filter,
        'unique_regions': unique_regions,
        'unique_professions': unique_professions,
        'total_members': members.count(),
    }
    
    return render(request, 'member_directory.html', context)

def join_directory(request, member_id):
    """
    Allow members to join the public directory
    """
    if request.method == 'POST':
        member = get_object_or_404(CommunityMember, id=member_id)
        member.is_public_directory = True
        member.save()
        messages.success(request, 'Your profile is now visible in the directory!')
        return redirect('member_directory')
    return redirect('member_directory')

# REMOVE @login_required OR update to:
def join_directory_form(request):
    """
    Form for joining the professional directory
    """
    # Check if user just joined (has member_id in session)
    member_id = request.session.get('joined_member_id')
    
    if member_id:
        try:
            member = CommunityMember.objects.get(id=member_id)
        except CommunityMember.DoesNotExist:
            member = None
    else:
        member = None
    
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        profession = request.POST.get('profession')
        region = request.POST.get('region')
        category = request.POST.get('category')
        expertise = request.POST.get('expertise')
        
        # Update the member if exists
        if member:
            member.name = name
            member.profession = profession
            member.region = region
            member.save()
            
            # Create or update DirectoryProfile
            DirectoryProfile.objects.update_or_create(
                community_member=member,
                defaults={
                    'full_name': name,
                    'profession': profession,
                    'region_city': region,
                    'category': category,
                    'expertise_summary': expertise,
                    'is_approved': True,
                }
            )
            
            messages.success(request, f'Profile updated for {name}!')
        else:
            messages.success(request, 'Profile information saved!')
        
        return redirect('member_directory')
    
    # Pre-fill with member data if exists
    initial_data = {}
    if member:
        initial_data = {
            'name': member.name,
            'profession': member.profession,
            'region': member.region,
        }
    
    context = {
        'name': initial_data.get('name', 'Your Name'),
        'profession': initial_data.get('profession', ''),
        'region': initial_data.get('region', ''),
        'categories': ['Tech & IT', 'Legal', 'Finance', 'Healthcare', 'Education', 'Business', 'Creative & Media', 'Engineering', 'Other'],
    }
    
    return render(request, 'join_directory_form.html', context)

# Forum Home Page
def forum_home(request):
	forum_categories = ForumCategory.objects.all()
	return render(request, 'forum_home.html', {'forum_categories': forum_categories})


def category_detail(request, slug):
	category = get_object_or_404(ForumCategory, slug=slug)
	posts = Post.objects.filter(category=category).order_by('-created_at')
	paginator = Paginator(posts, 5)
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	return render(request, 'category_detail.html', {'category': category, 'posts': page_obj})


def view_post(request, post_id):
	post = get_object_or_404(Post, id=post_id)
	comments = CommentP.objects.filter(post=post).order_by('-created_at')
	if request.method == 'POST':
		form = CommentForm(request.POST)
		if form.is_valid():
			comment = form.save(commit=False)
			comment.post = post
			comment.author = request.user
			comment.save()
			return redirect('communities:view_post', post_id=post.id)
	else:
		form = CommentForm()
	return render(request, 'view_post.html', {'post': post, 'comments': comments, 'form': form})


def create_post(request, slug):
	category = get_object_or_404(ForumCategory, slug=slug)
	if request.method == 'POST':
		form = PostForm(request.POST)
		if form.is_valid():
			post = form.save(commit=False)
			post.category = category
			post.save()
			return redirect('communities:category_detail', slug=category.slug)
	else:
		form = PostForm()
	return render(request, 'create_post.html', {'form': form, 'category': category})


@login_required
def add_comment(request, post_id):
	post = get_object_or_404(Post, id=post_id)
	if request.method == 'POST':
		form = CommentForm(request.POST)
		if form.is_valid():
			comment = form.save(commit=False)
			comment.post = post
			comment.author = request.user
			comment.save()
			return redirect('communities:view_post', post_id=post.id)
	return redirect('communities:view_post', post_id=post.id)


def event_calendar(request):
	events = EventCalendar.objects.all().order_by('start_date')
	return render(request, 'event_calendar.html', {'events': events})


def create_event(request):
	if request.method == 'POST':
		form = EventForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Event created successfully')
			return redirect('communities:event_calendar')
		else:
			messages.error(request, 'There was an error in your form.')
	else:
		form = EventForm()
	return render(request, 'create_event.html', {'form': form})


def event_detail(request, id):
    # Fetch the event by ID
    event = get_object_or_404(EventCalendar, id=id)
    
    return render(request, 'event_detail.html', {'event': event})

# Edit event
def edit_event(request, id):
    # Fetch the event by ID
    event = get_object_or_404(EventCalendar, id=id)
    
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()  # Save the updated event to the database
            messages.success(request, "Event updated successfully!")
            return redirect('event_detail', id=event.id)  # Redirect to event detail page
        else:
            messages.error(request, "There was an error with your form. Please try again.")
    else:
        form = EventForm(instance=event)
    
    return render(request, 'edit_event.html', {'form': form, 'event': event})

# Delete event
def delete_event(request, id):
    # Fetch the event by ID
    event = get_object_or_404(EventCalendar, id=id)
    
    if request.method == 'POST':
        event.delete()  # Delete the event from the database
        messages.success(request, "Event deleted successfully!")
        return redirect('event_calendar')  # Redirect to the event calendar page
    
    return render(request, 'delete_event.html', {'event': event})

# Contact Regional Coordinator
def contact_view(request):
	if request.method == 'POST':
		form = ContactForm(request.POST)
		if form.is_valid():
			contact = form.save()
			context = {'name': contact.name, 'email': contact.email, 'message': contact.message}
			subject = f'Hello {contact.name}, thank you for contacting us!'
			recipient_list = [contact.email]
			send_email(subject=subject, recipient_list=recipient_list, context=context, html_template='contact_response.html', plain_template='contact_response.txt')
			admin_subject = f'New Contact Message from {contact.name}'
			admin_recipient = ['info@gcicrwanda.com']
			send_email(subject=admin_subject, recipient_list=admin_recipient, context=context, html_template='emails/admin_contact_notification.html', plain_template='emails/admin_contact_notification.txt')
			return redirect('communities:home')
	else:
		form = ContactForm()
	return render(request, 'contact_form.html', {'form': form})


def member_directory(request):
	members = CommunityMember.objects.all().order_by('-date_joined')
	search_query = request.GET.get('search', '')
	region_filter = request.GET.get('region', '')
	profession_filter = request.GET.get('profession', '')
	if search_query:
		members = members.filter(
			Q(name__icontains=search_query) | Q(profession__icontains=search_query) | Q(specialization__icontains=search_query) | Q(bio__icontains=search_query)
		)
	if region_filter:
		members = members.filter(region__icontains=region_filter)
	if profession_filter:
		members = members.filter(profession__icontains=profession_filter)
	unique_regions = CommunityMember.objects.values_list('region', flat=True).distinct().order_by('region')
	unique_professions = CommunityMember.objects.values_list('profession', flat=True).distinct().order_by('profession')
	for member in members:
		member.is_premium = member.id % 3 == 0
	context = {'members': members, 'search_query': search_query, 'region_filter': region_filter, 'profession_filter': profession_filter, 'unique_regions': unique_regions, 'unique_professions': unique_professions, 'total_members': members.count()}
	return render(request, 'member_directory.html', context)


def join_directory(request, member_id):
	if request.method == 'POST':
		member = get_object_or_404(CommunityMember, id=member_id)
		member.is_public_directory = True
		member.save()
		messages.success(request, 'Your profile is now visible in the directory!')
		return redirect('communities:member_directory')
	return redirect('communities:member_directory')


def join_directory_form(request):
	member_id = request.session.get('joined_member_id')
	member = None
	if member_id:
		try:
			member = CommunityMember.objects.get(id=member_id)
		except CommunityMember.DoesNotExist:
			member = None
	if request.method == 'POST':
		name = request.POST.get('name', '').strip()
		profession = request.POST.get('profession', '').strip()
		region = request.POST.get('region', '').strip()
		category = request.POST.get('category', '').strip()
		expertise = request.POST.get('expertise', '').strip()

		# Basic validation: required fields
		errors = []
		if not name:
			errors.append('Name is required.')
		if not profession:
			errors.append('Profession is required.')
		if not region:
			errors.append('Region is required.')

		if errors:
			for e in errors:
				messages.error(request, e)
			# re-render form with submitted values
			context = {
				'name': name,
				'profession': profession,
				'region': region,
				'categories': ['Tech & IT', 'Legal', 'Finance', 'Healthcare', 'Education', 'Business', 'Creative & Media', 'Engineering', 'Other'],
			}
			return render(request, 'join_directory_form.html', context)

		if member:
			member.name = name
			member.profession = profession
			member.region = region
			member.save()

			DirectoryProfile.objects.update_or_create(
				community_member=member,
				defaults={'full_name': name, 'profession': profession, 'region_city': region, 'category': category, 'expertise_summary': expertise, 'is_approved': True},
			)
			messages.success(request, f'Profile updated for {name}!')
		return redirect('communities:member_directory')
	context = {'name': member.name if member else '', 'profession': member.profession if member else '', 'region': member.region if member else '', 'categories': ['Tech & IT', 'Legal', 'Finance', 'Healthcare', 'Education', 'Business', 'Creative & Media', 'Engineering', 'Other']}
	return render(request, 'join_directory_form.html', context)

