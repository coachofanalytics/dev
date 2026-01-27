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
from .forms import JoinForm, PostForm, CommentForm, EventForm, ContactForm
from .models import Post, ForumCategory, CommentP, EventCalendar, CommunityMember  # Import Post, ForumCategory, ForumPost, Comment, and EventCalendar models
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
            region="To be updated"
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
    # Get all verified members who want to be in the directory
    members = CommunityMember.objects.filter(
        is_verified=True,
        is_public_directory=True
    ).order_by('-date_joined')

    # Initialize variables
    search_query = request.GET.get('search', '')
    region_filter = request.GET.get('region', '')
    profession_filter = request.GET.get('profession', '')
    
    # Handle search/filter from form
    if request.method == 'GET':
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
         # Get unique regions and professions for filter dropdowns
    unique_regions = CommunityMember.objects.filter(
        is_verified=True,
        is_public_directory=True
    ).values_list('region', flat=True).distinct().order_by('region')
    
    unique_professions = CommunityMember.objects.filter(
        is_verified=True,
        is_public_directory=True
    ).values_list('profession', flat=True).distinct().order_by('profession')

    #Add is_premium field (you'll need to add this to your model or calculate)
    # For now, let's assume premium status
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