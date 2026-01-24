from django.shortcuts import render

# Create your views here.
from sched import Event
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from main.forms import MessageForm
from .utils import send_email
from .forms import JoinForm, PostForm, CommentForm, EventForm, ContactForm,DirectoryMemberForm, EventUpdateForm
from .models import Post, ForumCategory, CommentP, EventCalendar, DirectoryMember  # Import Post, ForumCategory, ForumPost, Comment, and EventCalendar models
from django.db.models import Q



# Create your views here.
def home(request):
    return render(request, 'home.html')

# community views
def join(request):
    if request.method == 'POST':
        form = JoinForm(request.POST)
        if form.is_valid():
            # Save the form data (e.g., save the new user)
            form.save()

            # Send the confirmation email
            subject = 'Thank you for joining the community!'
            recipient_list = [form.cleaned_data['email']]  # Get the email from form
            context = {
                'name': form.cleaned_data['name'],
                'dashboard_url': 'http://127.0.0.1:8080/community/',  # Update with the actual URL
            }

            # Call the send_email function
            send_email(
                subject,
                recipient_list,
                context,
                'email.html',  # Path to the HTML template
                'email.txt'    # Path to the plain text template
            )

            messages.success(request, 'You have successfully joined the community. A confirmation email has been sent!')
            return redirect('join')  # Redirect to a page after successful form submission
    else:
        form = JoinForm()

    return render(request, 'join.html', {'form': form})
# Forum Home Page
def forum_home(request):
    # Fetch all categories for the homepage
    forum_categories = ForumCategory.objects.all()
    return render(request, 'forum_home.html', {'forum_categories': forum_categories})

#category detail view
def category_detail(request, slug):
    category = ForumCategory.objects.get(slug=slug)
    posts = Post.objects.filter(category=category).order_by('-created_at')

    # Pagination
    paginator = Paginator(posts, 5)  # Show 5 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'category_detail.html', {
        'category': category,
        'posts': page_obj
    })
# View a single post and its comments
def view_post(request, post_id):
    # Get the post based on the post ID
    post = get_object_or_404(Post, id=post_id)

    # Retrieve comments related to the post, ordered by date
    comments = CommentP.objects.filter(post=post).order_by('-created_at')

    # Handle comment form submission
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user  # Assuming the user is logged in
            comment.save()
            # Redirect to the same post page after comment submission
            return redirect('view_post', post_id=post.id)  # Corrected: 'post_id' instead of 'id'
    else:
        form = CommentForm()

    return render(request, 'view_post.html', {
        'post': post,
        'comments': comments,
        'form': form
    })

# Create a new post in a category
def create_post(request, slug):
    # Get the category based on the slug
    category = get_object_or_404(ForumCategory, slug=slug)

    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            # Save the form data but associate the category with the post
            post = form.save(commit=False)
            post.category = category  # Associate the post with the category
            post.save()  # Save the post to the database
            return render(request, 'category_detail.html', {'category': category})
    else:
        form = PostForm()

    return render(request, 'create_post.html', {'form': form, 'category': category})

@login_required
def add_comment(request, post_id):
    # Get the post to which the comment will be added
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            # Create a new comment and associate it with the post
            comment = form.save(commit=False)
            comment.post = post  # Associate the comment with the post
            comment.author = request.user  # Associate the comment with the logged-in user
            comment.save()

            # Redirect to the post detail page
            return redirect('view_post', post_id=post.id)  # Corrected: 'post_id' instead of 'id'
    else:
        form = CommentForm()

    return render(request, 'add_comment.html', {
        'form': form,
        'post': post
    })
# Event Calendar Views
def event_calendar(request):
    # Fetch all events from the EventCalendar model, paginated
    events = EventCalendar.objects.all().order_by('start_date')

    # Add pagination
    from django.core.paginator import Paginator
    paginator = Paginator(events, 5)  # Show 5 events per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'event_calendar.html', {'events': page_obj})
# Create a new event
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()  # Save the event to the database
            messages.success(request, "Event created successfully!")
            return redirect('event_calendar')  # Redirect to the event calendar page
        else:
            messages.error(request, "There was an error with your form. Please try again.")
    else:
        form = EventForm()
    return render(request, 'create_event.html', {'form': form})
# View event details
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
            contact = form.save()  # Save the form data to DB

            # Prepare email context
            context = {
                'name': contact.name,
                'email': contact.email,
                'message': contact.message,
            }

            # Email details
            subject = f"Hello {contact.name}, thank you for contacting us!"
            recipient_list = [contact.email]

            # Send confirmation email
            send_email(
                subject=subject,
                recipient_list=recipient_list,
                context=context,
                html_template='contact_response.html',  # HTML version
                plain_template='contact_response.txt'   # Plain-text version
            )

            # Optionally, send a notification to admin too:
            admin_subject = f"New Contact Message from {contact.name}"
            admin_recipient = ['info@gcicrwanda.com']  # or settings.DEFAULT_FROM_EMAIL
            send_email(
                subject=admin_subject,
                recipient_list=admin_recipient,
                context=context,
                html_template='emails/admin_contact_notification.html',
                plain_template='emails/admin_contact_notification.txt'
            )

            return redirect('home')  # Redirect after success

    else:
        form = ContactForm()

    return render(request, 'contact_form.html', {'form': form})


# ============================================
# views.py - Add these views to your existing views.py
# ============================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import DirectoryMember, EventCalendar
from .forms import DirectoryMemberForm, EventUpdateForm

# ============== DIRECTORY VIEWS ==============

def directory(request):
    """Display all directory members with search and filter functionality"""
    members = DirectoryMember.objects.filter(is_active=True)
    
    # Apply search filter
    search = request.GET.get('search', '').strip()
    if search:
        members = members.filter(
            Q(full_name__icontains=search) | 
            Q(profession__icontains=search) |
            Q(expertise__icontains=search)
        )
    
    # Apply region filter
    region = request.GET.get('region', '').strip()
    if region:
        members = members.filter(region__icontains=region)
    
    # Apply profession/category filter
    profession = request.GET.get('profession', '').strip()
    if profession:
        members = members.filter(category=profession)
    
    # Get unique regions and categories for dropdowns
    regions = DirectoryMember.objects.values_list('region', flat=True).distinct()
    categories = DirectoryMember.CATEGORY_CHOICES
    
    # Pagination
    paginator = Paginator(members, 12)  # 12 members per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'members': page_obj,
        'regions': regions,
        'professions': categories,
    }
    return render(request, 'directory.html', context)


def join_directory(request):
    """Allow users to join the professional directory - No login required"""
    # Check if user is authenticated and already has a profile
    if request.user.is_authenticated:
        existing_profile = DirectoryMember.objects.filter(user=request.user, is_active=True).first()
        if existing_profile:
            messages.info(request, 'You already have an active directory profile.')
            return redirect('directory')
    
    if request.method == 'POST':
        form = DirectoryMemberForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save(commit=False)
            # Associate with user if logged in, otherwise set to None
            member.user = request.user if request.user.is_authenticated else None
            member.is_verified = True  # Auto-verify or set to False for manual approval
            member.save()
            
            messages.success(request, 'Your profile has been submitted successfully!')
            return redirect('directory')
    else:
        # Pre-fill form with user data if available
        initial_data = {}
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            initial_data['full_name'] = request.user.profile.full_name
            initial_data['region'] = request.user.profile.county_city
        
        form = DirectoryMemberForm(initial=initial_data)
    
    return render(request, 'join_directory.html', {'form': form})


def edit_directory_profile(request, pk):
    """Edit existing directory profile - No login required"""
    member = get_object_or_404(DirectoryMember, pk=pk)
    
    # If user is authenticated, verify ownership
    if request.user.is_authenticated and member.user and member.user != request.user:
        messages.error(request, 'You do not have permission to edit this profile.')
        return redirect('directory')
    
    if request.method == 'POST':
        form = DirectoryMemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('directory')
    else:
        form = DirectoryMemberForm(instance=member)
    
    return render(request, 'join_directory.html', {'form': form, 'edit_mode': True})


def delete_directory_profile(request, pk):
    """Delete/deactivate directory profile - No login required"""
    member = get_object_or_404(DirectoryMember, pk=pk)
    
    # If user is authenticated, verify ownership
    if request.user.is_authenticated and member.user and member.user != request.user:
        messages.error(request, 'You do not have permission to delete this profile.')
        return redirect('directory')
    
    if request.method == 'POST':
        member.is_active = False
        member.save()
        messages.success(request, 'Your profile has been removed from the directory.')
        return redirect('directory')
    
    return render(request, 'confirm_delete_profile.html', {'member': member})


# ============== EVENT CALENDAR CRUD ==============

def update_event(request, id):
    """Update an existing event - No login required"""
    event = get_object_or_404(EventCalendar, id=id)
    
    if request.method == 'POST':
        form = EventUpdateForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Event updated successfully!")
            return redirect('event_detail', id=event.id)
        else:
            messages.error(request, "There was an error updating the event.")
    else:
        form = EventUpdateForm(instance=event)
    
    return render(request, 'update_event.html', {'form': form, 'event': event})


def delete_event(request, id):
    """Delete an event - No login required"""
    event = get_object_or_404(EventCalendar, id=id)
    
    if request.method == 'POST':
        event.delete()
        messages.success(request, "Event deleted successfully!")
        return redirect('event_calendar')
    
    return render(request, 'confirm_delete_event.html', {'event': event})
