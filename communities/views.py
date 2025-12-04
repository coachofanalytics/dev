from django.shortcuts import render

# Create your views here.
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required

from .utils import send_email
from .forms import JoinForm, PostForm, CommentForm, EventForm, ContactForm
from .models import Post, ForumCategory, CommentP, EventCalendar  # Import Post, ForumCategory, ForumPost, Comment, and EventCalendar models

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