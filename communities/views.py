from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q

from main.forms import MessageForm
from .utils import send_email
from .forms import JoinForm, PostForm, CommentForm, EventForm, ContactForm
from .models import Post, ForumCategory, CommentP, EventCalendar, CommunityMember, DirectoryProfile


def home(request):
	return render(request, 'home.html')


def join(request):
	if request.method == 'POST':
		form = JoinForm(request.POST, request.FILES or None)
		if form.is_valid():
			member = form.save()

			# remember joined member for directory profile flow
			request.session['joined_member_id'] = member.id

			# send welcome email using utils.send_email
			subject = 'Thank you for joining the community!'
			recipient_list = [form.cleaned_data.get('email')]
			context = {'name': form.cleaned_data.get('name'), 'dashboard_url': 'http://127.0.0.1:8000/communities/'}

			send_email(
				subject=subject,
				recipient_list=recipient_list,
				context=context,
				html_template='email.html',
				plain_template='email.txt',
			)

			messages.success(request, 'You have successfully joined the community. A confirmation email has been sent!')
			return redirect('communities:member_directory')
	else:
		form = JoinForm()
		# Clear model-level default values so form inputs start empty
		if 'profession' in form.fields:
			form.initial['profession'] = ''
		if 'region' in form.fields:
			form.initial['region'] = ''

	return render(request, 'join.html', {'form': form})


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
	event = get_object_or_404(EventCalendar, id=id)
	return render(request, 'event_detail.html', {'event': event})


def edit_event(request, id):
	event = get_object_or_404(EventCalendar, id=id)
	if request.method == 'POST':
		form = EventForm(request.POST, instance=event)
		if form.is_valid():
			form.save()
			messages.success(request, 'Event updated successfully')
			return redirect('communities:event_detail', id=event.id)
		else:
			messages.error(request, 'There was an error in your form.')
	else:
		form = EventForm()
	return render(request, 'create_event.html', {'form': form, 'event': event})


def delete_event(request, id):
	event = get_object_or_404(EventCalendar, id=id)
	if request.method == 'POST':
		event.delete()
		messages.success(request, 'Event deleted successfully')
		return redirect('communities:event_calendar')
	return render(request, 'delete_event.html', {'event': event})


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

