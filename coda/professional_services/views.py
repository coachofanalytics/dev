from collections import defaultdict
import logging
import json
from django.db.models import Q
from django.utils.text import capfirst
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse,HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy
from coda_project.url_config import get_app_url, get_role_url
from main.models import ClientAvailability, Service,ServiceCategory
from .utils import *
from ai_services.models import OpenaiPrompt
from django.views.generic import (
        CreateView,
        DeleteView,
        ListView,
        DetailView,
        UpdateView,
    )

from professional_services.forms import (
    PrepQuestionsForm,TrainingResponseForm,
    InterviewForm, DSUForm ,RoleForm,UserAnswerForm
)
from main.utils import (generate_chatbot_response, data_interview,openai_user_message,
                    path_values,job_support,split_sentences,
                    today_date
                    )
from professional_services.models import (
    Correct_answers, FeaturedCategory,FeaturedSubCategory,FeaturedActivity,ActivityLinks,
    Interviews,Prep_Questions,UserAnswerStatus,
    Training_Responses,TrainingResponsesTracking,
    DSU,Job_Tracker,JobRole,JobRoles,BackgroundCheck
)
from professional_services.filters import InterviewFilter, BitrainingFilter,QuestionFilter,ResponseFilter


# User=settings.AUTH_USER_MODEL

from coda_project import settings


User = get_user_model()
logger = logging.getLogger(__name__)


def analysis(request):
    return render(
        request, "main/home_templates/analysis_home.html", {"title": "analysis"}
    )

def payroll(request):
    return render(request, "professional_services/deliverable/payroll.html", {"title": "payroll"})

def financialsystem(request):
    return render(
        request, "professional_services/deliverable/financialsystem.html", {"title": "financialsystem"}
    )

def deliverable(request):
    return render(
        request, "professional_services/deliverable/deliverable.html", {"title": "deliverable"}
    )

@login_required
def training(request):
    return render(request, "professional_services/training/training_progress/train.html", {"title": "training"})





@login_required
def start_training(request, slug=None, *args, **kwargs):
    try:
        service_shown = Service.objects.get(slug="data_analysis")
    except Service.DoesNotExist:
        return redirect('main:layout')
    service_categories = ServiceCategory.objects.filter(service=service_shown.id)
    # Initialize variables with default values
    category_slug = None
    category_name = None
    category_id = None
    description = ""
    
    for item in service_categories:
        if item.slug==slug:
            category_slug=item.slug
            category_name=item.name
            description=item.description
            data_items=data_interview,
            break  # Exit loop once found

    # Check if category was found
    if not category_slug:
        messages.error(request, f"Service category '{slug}' not found.")
        return redirect('professional_services:services')
    
    onboarding_description,troubleshooting_description,requirement_description=split_sentences(description)

    if category_slug == 'interview':
        data_items=data_interview
    else:
        data_items=job_support

    context = {}
    context = {
        "SITEURL": settings.SITEURL,
        "data_items":data_items,
        "title": category_name,
        "category_slug": category_slug,
        "description": description,
        "onboarding_description": onboarding_description,
        "requirement_description": requirement_description,
        "troubleshooting_description": troubleshooting_description
    }
    return render(request, "professional_services/interview/interview_progress/start_interview.html",context)


# Views on interview Section
@login_required
def uploadinterview(request):
    if request.method == "POST":
        data = Interviews.objects.all()
        form = InterviewForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("professional_services:interviewlist")
    else:
        form = InterviewForm()
    return render(request, "professional_services/interview/uploadinterview.html", {"form": form})
@login_required
def dsu_entry(request):
    if request.method == "POST":
        form = DSUForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("professional_services:dsu")
    else:
        form = DSUForm()
    return render(request, "professional_services/training/form_templates/dsu_form.html", {"form": form})
# for uploading interviews

"""================================My code=============================================================="""
def generate_question_response(request, question_id, new_prompt=None):
    question = get_object_or_404(Prep_Questions, id=question_id)
    
    # Use new_prompt if provided, otherwise generate message based on the question
    if new_prompt:
        user_message = new_prompt
    else:
        # Get resume information
        try:
            interview = Interviews.objects.filter(client=request.user, question_type="resume").latest('upload_date')
            user_resume_data = interview.dynamic_fields
        except ObjectDoesNotExist:
            user_resume_data = ""

        # Retrieve the context, clarification, and role from the OpenAI prompt
        try:
            prompt_obj = OpenaiPrompt.objects.get(category=question.category)
            context = prompt_obj.context_description
            clarification = prompt_obj.clarification_description
            role = prompt_obj.role
        except ObjectDoesNotExist:
            context = user_resume_data
            clarification = 'For above topic, generate a general response for data analysis|Business Analysis Interview'
            role = 'Data Analyst|IT Specialist|Business Analyst'
        except AttributeError:
            context = user_resume_data
            clarification = 'For above topic, generate a general response for data analysis|Business Analysis Interview'
            role = 'Data Analyst|IT Specialist|Business Analyst'
        
        # Prepare the prompt text
        user_message = f"Question: {question.question}\n\nContext:\n{context}\n\nClarification:\n{clarification}\n\nRole: {role}"
    
    # Generate response from OpenAI
    generated_response = generate_chatbot_response(user_message)

    # Check if response was generated successfully
    if generated_response:
        # Update or create UserAnswerStatus entry
        user_answer_status, created = UserAnswerStatus.objects.update_or_create(
            user=request.user,
            question=question,
            defaults={'is_answered': True, 'answer': generated_response}
        )
    
    return generated_response

@login_required
def userresponse(request, question_id):
    title = 'CODA: AN AI POWERED INTERVIEW PLATFORM'
    ad_title = 'Business Intelligence To Skyrocket\nYour Career Even If You Don’t Have Any Experience.'
    try:
        user_response = UserAnswerStatus.objects.filter(question=question_id, is_answered=True).order_by('-created_at').first()
        if user_response:
            context = {
                "title": title,
                "ad_title": ad_title,
                "category": user_response.question.category,
                "question": user_response.question,
                "date": user_response.created_at,
                "id": user_response.id,
                "user_response": user_response,
                "paragraphs": user_response.answer.split('\n') if user_response.answer else None
            }
            return render(request, "professional_services/interview/interview_progress/user_response.html", context)
    except UserAnswerStatus.DoesNotExist:
        pass

    # If no existing user response, generate a new one
    user_response = generate_question_response(request, question_id)
    latest_response = UserAnswerStatus.objects.filter().latest('created_at')
    context = {
        "title": title,
        "ad_title": ad_title,
        "category": latest_response.question.category if latest_response else None,
        "question": latest_response.question if latest_response else None,
        "date": latest_response.created_at if latest_response else None,
        "id": latest_response.id if latest_response else None,
        # "user_response": user_response,
        "response": user_response if user_response else None,
        "paragraphs": latest_response.answer.split('\n') if latest_response and latest_response.answer else None
    }
    return render(request, "professional_services/interview/interview_progress/user_response.html", context)

@login_required
def user_response_update_view(request, pk):
    user_answer = get_object_or_404(UserAnswerStatus, pk=pk)

    if request.method == 'POST':
        form = UserAnswerForm(request.POST, instance=user_answer)
        if form.is_valid():
            if 'regenerate' in request.POST:  # Check if "regenerate" flag is present
                logger.debug("regenerate")
                # Construct new prompt based on form data
                new_prompt = f'Based on the question: {form.instance.question.question} and the role: {form.instance.role}, please provide a detailed response.'
                # Generate response with new_prompt
                generate_question_response(request, form.instance.question.pk, new_prompt=new_prompt)
                # Redirect to userresponse view without passing new_prompt
                return redirect('professional_services:userresponse', question_id=user_answer.question.pk)
            else:
                logger.debug("regenerate")
                form.save()
                return redirect('professional_services:prepresponses')  # Redirect to success URL
    else:
        form = UserAnswerForm(instance=user_answer)

    context = {
        'form': form,
        'question': user_answer.question,
    }
    return render(request, 'professional_services/interview/interview_form.html', context)


# """================================User Response=============================================================="""
@login_required
def prepquestions(request,title='roles'):
    # Retrieve position
    position = request.GET.get('position', None)
    path_list, sub_title, pre_sub_title = path_values(request)
    # roles_positions=Prep_Questions.objects.filter().distinct()
    unique_roles_non_tech = Prep_Questions.objects.filter(is_tech=False,is_featured=True).order_by('position').values_list('position', flat=True).distinct()
    unique_roles_tech = Prep_Questions.objects.filter(is_tech=True,is_featured=True).order_by('position').values_list('position', flat=True).distinct()
    non_tech_questions= Prep_Questions.objects.filter(Q(is_featured=True) & Q(is_tech=False) ).order_by("date")
    tech_questions= Prep_Questions.objects.filter(Q(is_featured=True) & Q(is_tech=True) ).order_by("date")
    
    if position=='all':
        questions= Prep_Questions.objects.all().order_by("date")
    else:
        questions= Prep_Questions.objects.filter(Q(position=position) ).order_by("date")
    
    QuestionsFilter = QuestionFilter(request.GET, queryset=questions)
    questions = QuestionFilter.qs
    context = {
                "unique_roles_non_tech": unique_roles_non_tech, 
                "unique_roles_tech": unique_roles_tech, 
                "non_tech_questions": non_tech_questions, 
                "tech_questions": tech_questions, 
                "myFilter": QuestionsFilter,
                "questions": questions, 
                "myFilter": QuestionsFilter,       
                "title": "Training",
                "title_letter": "letter",
               }
    if sub_title=='prepquestions':
        return render(request, "professional_services/interview/interview_progress/prepquestions.html", context)
    if sub_title=='interview_roles':
        return render(request, "professional_services/interview/interview_roles.html",context)

def useruploads(request, username=None, *args, **kwargs):
    if username is None:
        useruploads = Interviews.objects.all().order_by("-upload_date")
    else:
        useruploads = Interviews.objects.filter(client__username=username).order_by("-upload_date")

    # Log the value of useruploads for debugging
    logger.debug("Value of useruploads: %s", useruploads)

    context = {
        "useruploads": useruploads,
    }
    return render(request, "professional_services/interview/useruploads.html", context)

@login_required
def prep_responses(request):
    # user_response.answer.split('\n')
    if request.user.is_superuser or request.user.is_staff:
        responses = UserAnswerStatus.objects.all().order_by("-created_at")
    else:
        responses = UserAnswerStatus.objects.filter(user=request.user).order_by("-created_at")
    ResFilter = ResponseFilter(request.GET, queryset=responses)
    context = {                
            # "companies": companies, 
            "responses": responses, 
            # "ResFilter": ResponseFilter(request.GET, queryset=responses),
    }
    return render(request, "professional_services/interview/interview_progress/prepresponses.html", context)
    
class PrepQuestionsCreateView(LoginRequiredMixin, CreateView):
    model = Prep_Questions
    success_url = "/professional_services/prepquestions/"
    template_name="professional_services/interview/interview_progress/prep_questions_form.html"
    form_class=PrepQuestionsForm

    def form_valid(self, form):
        form.instance.questioner = self.request.user
        return super().form_valid(form)
    
class PrepQuestionsUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Prep_Questions
    success_url = "/professional_services/prepquestions/"
    form_class=PrepQuestionsForm
    # fields = ["company", 'position','category',"question", "response","is_answered"]
    def form_valid(self, form):
        # form.instance.username = self.request.user
        return super().form_valid(form)
    def test_func(self):
        if self.request.user or self.request.user.is_admin or self.request.user.is_superuser:
            return True
        return False
    
class JobUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Prep_Questions
    success_url = "/professional_services/prepquestions/"
    # form_class=PrepQuestionsForm
    fields = ["company", 'position',"response","is_answered"]
    def form_valid(self, form):
        # form.instance.username = self.request.user
        return super().form_valid(form)
    def test_func(self):
        if self.request.user or self.request.user.is_admin or self.request.user.is_superuser:
            return True
        return False
    
# ==================================TRAINING VIEWS====================================
def courseoverivew(request): #, question_type=None, *args, **kwargs):
    instance = request.path
    value=request.path.split("/")
    instance = [i for i in value if i.strip()]
    context={
        "instance":instance
    }
    if instance is None:
        return render(request, "main/errors/404.html")
    else:
        return render(request, "professional_services/training/training_progress/courseoverview.html", context)

class TrainingView(LoginRequiredMixin, ListView):
    model = Interviews
    template_name = "professional_services/training/training_progress/train.html"
    success_url = "/professional_services/course"
    
    def get_context_data(self, **kwargs):
        try:
            context = super(TrainingView, self).get_context_data(**kwargs)
            featured_category = FeaturedCategory.objects.all().first()
            context['title'] = featured_category.title if featured_category else "Training"
            return context
        except Exception as e:
            # Return a proper context instead of redirect
            context = super(TrainingView, self).get_context_data(**kwargs)
            context['title'] = "Training"
            context['error'] = "Unable to load training data"
            return context

class CourseView(LoginRequiredMixin, ListView):
    model = Interviews
    template_name = "professional_services/training/training_progress/course.html"
    # success_url = "/professional_services/course"

# ==================================INTERVIEW VIEWS====================================
class RoleListView(LoginRequiredMixin, ListView):
    queryset = JobRole.objects.all()
    template_name = "professional_services/interview/interview_progress/interview_progress.html"
    success_url = "/professional_services/project_story"

class InterviewCreateView(LoginRequiredMixin, CreateView):
    model = Interviews
    form_class = InterviewForm
    template_name = "professional_services/interview/interview_form.html"
    success_url = "/professional_services/iuploads/"
    def form_valid(self, form):
        form.instance.client = self.request.user
        # form.instance.question_type = "testing"
        return super().form_valid(form)
    
@method_decorator(login_required, name="dispatch")
class InterviewListView(ListView):
    queryset = Interviews.objects.all()
    template_name = "professional_services/interview/interviewuploads.html"
    ordering = ["-upload_date"]

@login_required
def iuploads(request):
    logger.debug("HERE",request.user.category in [1, 3, 4, 5, 6, 7])  # Job_Applicant, Jobsupport, Student, Investor, Vendor, General_User
    # uploads={}
    if request.user.category in [1, 3, 4, 5, 6, 7]:  # Job_Applicant, Jobsupport, Student, Investor, Vendor, General_User
        usernames = ['coda','makied', 'Sipho','JudyG', 'coda_info']  # Add as many usernames as needed
        uploads = Interviews.objects.filter(client__username__in=usernames).order_by("-upload_date")
    else:
        uploads = Interviews.objects.all().order_by("-upload_date")
    # uploads = Interviews.objects.all().order_by("-upload_date")
    myFilter = InterviewFilter(request.GET, queryset=uploads)
    uploads = myFilter.qs
    context = {"uploads": uploads, "myFilter": myFilter}
    return render(request, "professional_services/interview/interviewuploads.html", context)

@method_decorator(login_required, name="dispatch")
class TrainingResponseListView(ListView):
    queryset =Training_Responses.objects.all()
    template_name = "professional_services/interview/interviewquestion_upload.html"
    ordering = ["-upload_date"]

@method_decorator(login_required, name="dispatch")
class TrainingResponseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Training_Responses
    # success_url = "/professional_services/iuploads"
    # success_url = f"/professional_services/student_feedback/{{request.user}}/"
    fields = [
                'user',
                'question',
                'question1',
                'is_active',
                'doc',
                'link',
                'comment',
                'score',
                'upload_date',
        
    ]
    def form_valid(self, form):
        # form.instance.author=self.request.user
        return super().form_valid(form)
    
    def test_func(self):
        responses = self.get_object()
        if self.request.user.is_superuser:
            return True
        elif self.request.user == responses.user:
            return True
        return False


class ClientInterviewListView(ListView):
    model = Interviews
    context_object_name = "client_interviews"
    template_name = "professional_services/interview/user_interviews.html"
    # paginate_by = 5
    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get("username"))
        # tasks=Task.objects.all().filter(client=client)
        return Interviews.objects.all().filter(user=user)

@method_decorator(login_required, name="dispatch")
class InterviewDetailView(DetailView):
    model = Interviews
    ordering = ["-upload_date"]

def courseview(request, question_type=None, *args, **kwargs):
    instance = JobRole.objects.get_by_question(question_type)
    form= InterviewForm
    questiontopic=['resume','methodology','testing']
    value=request.path.split("/")
    pathvalues = [i for i in value if i.strip()]
    path=pathvalues[-1]
    logger.debug(path)
    url=f'professional_services/interview/interview_progress/questions.html'
    logger.debug(url)
    context = {
        "form":form,
        "object": instance,
        "interviews": Interviews.objects.all(),
        "path":path
    }
    if instance is None:
        return render(request, "main/errors/404.html")
    return render(request, url, context)
import threading
def get_area_of_focus(question_type, field_name):
    area_of_focus = ""
    if question_type in areas_focus_performance:
        area_of_focus = areas_focus_performance.get(field_name, "")
    elif question_type in areas_focus_methodology:
        area_of_focus = areas_focus_methodology.get(field_name, "")
    elif question_type in areas_focus_project_story:
        area_of_focus = areas_focus_project_story.get(field_name, "")
    elif question_type in areas_focus_testing_project:
        area_of_focus = areas_focus_testing_project.get(field_name, "")
    elif question_type in areas_focus_resume:
        area_of_focus = areas_focus_resume.get(field_name, "")
    elif question_type in areas_focus_sdl:
        area_of_focus = areas_focus_sdl.get(field_name, "")
    
    return area_of_focus
from django.utils import timezone
def generate_review_sets():
    # Get all distinct question types (titles)
    question_types = Training_Responses.objects.values_list('title', flat=True).distinct()
    
    for question_type in question_types:
        # Get all reviews for this question type
        reviews = Training_Responses.objects.filter(
            Q(title=question_type),
            Q(review__isnull=False) & ~Q(review='')
        ).values_list('review', flat=True)
        
        if not reviews:
            continue  # Skip if there are no reviews
        
        # Combine the reviews into a single text
        combined_reviews = '\n\n'.join(reviews)
        
        # For this question type, generate 5 review sets
        for i in range(1, 6):
            # Prepare the prompt for OpenAI
            user_message = (
                f"As an expert educator, analyze the following student reviews for the question type '{question_type}'. "
                f"Identify common themes, strengths, and areas for improvement. Based on this analysis, generate Review Set {i} "
                f"that provides comprehensive feedback to students focusing on the key points they should consider.\n\n"
                f"Student Reviews:\n{combined_reviews}\n\n"
                f"Review Set {i}:"
            )
            
        response=generate_chatbot_response(user_message)
        generated_review = response.choices[0].text.strip()
                
                # Create a new Training_Responses instance
        new_title = f"{question_type}{i}"
        new_review = Training_Responses(
                    user=None,  # Optionally assign an admin user or leave as None
                    title=new_title,
                    review=generated_review,
                    upload_date=timezone.now(),
                    is_active=True,
                    comment='',  # Assuming comment can be empty
                    question='',  # Assuming question can be empty
                    question1='',  # Assuming question1 can be empty
                    response='',  # Assuming response can be empty
                    seen_notifications=False,
                    first_displayed_at=None,
                )
        new_review.save()
                
        logger.debug(f"Generated and saved review set '{new_title}'")
                    # Call OpenAI API
           
                
           
def generate_feedback_async(user_id, question_type, dynamic_fields, required_fields, prompt_data):
    # Extract data from prompt_data
    topic, question_text, context, role, description, word = prompt_data
    
    # Map question_type to a list of possible review titles
    question_type_to_titles = {
        'testing': ['testing1', 'testing2', 'testing3', 'testing4', 'testing5'],
        'performance': ['performance1', 'performance2', 'performance3', 'performance4', 'performance5'],
        'project_story': ['project_story1', 'project_story2', 'project_story3', 'project_story4', 'project_story5'],
        # Add more mappings as needed
    }
    
    # Get the list of possible titles for the given question_type
    possible_titles = question_type_to_titles.get(question_type, [])
    
    # Try to find existing reviews with the possible titles
    existing_response = None
    if possible_titles:
        existing_responses = Training_Responses.objects.filter(title__in=possible_titles)
        if existing_responses.exists():
            # Pick one of the existing reviews (you can randomize or use any selection criteria)
            existing_response = existing_responses.order_by('?').first()
            feedback_comment = existing_response.review
            logger.debug(f'Using existing review from title: {existing_response.title}')
        else:
            logger.debug(f'No existing reviews found for titles: {possible_titles}')
            logger.debug('Cannot proceed without existing reviews.')
            return  # Exit the function or handle the absence of reviews as needed
    else:
        logger.debug(f'No mapped titles found for question_type: {question_type}')
        logger.debug('Cannot proceed without mapped titles.')
        return  # Exit the function or handle the absence of mappings as needed
    
    # Save the feedback to the Training_Responses model with the question_type as the title
    response = Training_Responses(
        user_id=user_id,
        title=question_type,
        question1=json.dumps(required_fields),  # Save the list of questions as JSON
        review=feedback_comment  # Use the feedback from the existing review
    )
    response.save()
    
    logger.debug(f'Saved feedback for user {user_id} with title "{question_type}"')
from django.contrib import messages    
def questionview(request, question_type=None, *args, **kwargs):
    question_mapping = {
        'performance': ['tableau', 'alteryx', 'sql', 'python'],
        'testing': ['project', 'test_types', 'process'],
        'introduction': ['domain_industry', 'role', 'system_security', 'project_management', 'data_tools', 'communication'],
        'sdlc': ['initiation', 'planning', 'design', 'development', 'testing', 'deployment', 'maintenance'],
        'Project Story': ['description', 'deliverables', 'challenges', 'solutions'],
        'resume': ['summary', 'skills', 'responsibilities'],
        'methodology': ['projects', 'releases', 'sprints', 'stories'],
    }
    source = request.GET.get('source', False)

    def handle_next_topic():
        next_topic = JobRole.objects.filter(id__gt=JobRole.objects.get_by_question(question_type).id).order_by('id')
        if not next_topic.exists():
            return redirect('professional_services:user-list', username=request.user)
        return redirect('professional_services:question-detail', question_type=next_topic.first().question_type)
    
    data = Interviews.objects.filter(client=request.user, question_type=question_type).first()

    if request.method == 'GET':
        if data and source:
            try:
                dynamic_data = json.loads(data.dynamic_fields)
            except json.JSONDecodeError:
                dynamic_data = {}
            form = InterviewForm(instance=data)
            for field in form.fields:
                if field in dynamic_data:
                    form.fields[field].initial = dynamic_data[field]
        elif data:
            return handle_next_topic()
        else:
            form = InterviewForm()

        instance = JobRole.objects.get_by_question(question_type) 
        if instance is None:
            return render(request, "main/errors/404.html")

        context = {
            "form": form,
            "object": instance,
            "interviews": Interviews.objects.all(),
        }
        return render(request, 'professional_services/interview/interview_progress/questions.html', context)

    elif request.method == 'POST':
        form = InterviewForm(request.POST, request.FILES, instance=data)
        required_fields = question_mapping.get(question_type, [])
        
        if form.is_valid():
            instance = form.save(commit=False)
            instance.client = request.user
            instance.question_type = question_type

            dynamic_fields = {field: form.cleaned_data[field] for field in required_fields}

            prompt_obj = OpenaiPrompt.objects.get(category='Training')
            prompt_data = (
                prompt_obj.topic,
                prompt_obj.expert_question,
                prompt_obj.context_description,
                prompt_obj.role,
                prompt_obj.clarification_description,
                prompt_obj.words
            )

            # Start the feedback generation process in a separate thread
            threading.Thread(target=generate_feedback_async, args=(
                request.user.id, question_type, dynamic_fields, required_fields, prompt_data
            )).start()

            # Save dynamic fields in the original instance
            instance.dynamic_fields = json.dumps(dynamic_fields)
            instance.save()

            # Redirect after saving
            if source:
                return redirect('professional_services:user-list', username=request.user)
            return handle_next_topic()
        else:
            # Handle invalid form by re-rendering the form with errors
            messages.error(request, "Please correct the errors below.")
            instance = JobRole.objects.get_by_question(question_type)
            if instance is None:
                return render(request, "main/errors/404.html")
            context = {
                "form": form,
                "object": instance,
                "interviews": Interviews.objects.all(),
            }
            return render(request, 'professional_services/interview/interview_progress/questions.html', context)

    else:
        # Handle other HTTP methods if necessary
        return render(request, "main/errors/404.html", {"message": "Invalid request method."})
@method_decorator(login_required, name="dispatch")
class InterviewUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Interviews
    success_url = "/professional_services/iuploads"
    fields = [
        "client",
        "category",
        "question_type",
        "doc",
        "link",
    ]
    def form_valid(self, form):
        # form.instance.author=self.request.user
        return super().form_valid(form)
    def test_func(self):
        interview = self.get_object()
        if self.request.user.is_superuser:
            return True
        elif self.request.user == interview.client:
            return True
        return False
@method_decorator(login_required, name="dispatch")
class InterviewDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Interviews
    success_url = "/professional_services/iuploads"
    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return False
# ==================================TRAINING VIEWS====================================
@method_decorator(login_required, name="dispatch")
class RoleCreateView(LoginRequiredMixin, CreateView):
    model = JobRole
    form_class = RoleForm
    template_name = "professional_services/jobroles/role.html"
    success_url = "/professional_services/roles/"
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
@method_decorator(login_required, name="dispatch")
class ITrolesView(LoginRequiredMixin, ListView):
    queryset  = JobRoles.objects.all()
    template_name = "professional_services/jobroles/itroles.html"

@method_decorator(login_required, name="dispatch")
class RolesView(LoginRequiredMixin, ListView):
    queryset  = JobRole.objects.all()
    template_name = "professional_services/jobroles/roles.html"

@method_decorator(login_required, name="dispatch")
class RoleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = JobRole
    template_name = "professional_services/jobroles/role.html"
    success_url = "/professional_services/roles"
    fields ="__all__"
    # fields =['category','question_type','doc','doclink','doclink',"desc1","desc2"]

    def form_valid(self, form):
        form.instance.user=self.request.user
        return super().form_valid(form)
    
    def test_func(self):
        editor=self.request.user
        JobRole = self.get_object()
        if editor.is_superuser or  editor.is_admin :
            return True
        elif editor == JobRole.user:
            return True
        return redirect("professional_services:jobroles")
    
@method_decorator(login_required, name="dispatch")
class RoleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = JobRole
    template_name = "professional_services/jobroles/jobrole_confirm_delete.html"
    success_url = "/professional_services/roles"
    def test_func(self):
        editor=self.request.user
        JobRole = self.get_object()
        if editor.is_superuser or  editor.is_admin :
            return True
        elif editor == JobRole.user:
            return True
        return False
# ========================1. CREATION OF VIEWS============================
@method_decorator(login_required, name="dispatch")
class FeaturedCategoryCreateView(LoginRequiredMixin, CreateView):
    model = FeaturedCategory
    success_url = "/professional_services/bitraining"
    fields = ["title", "description"]
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

def categorydetail(request, title=None, *args, **kwargs):
    instance = FeaturedCategory.objects.get_by_category(title)
    tasks=FeaturedActivity.objects.all()

    form= InterviewForm
   
    url=f'professional_services/training/training_progress/training.html'
    context = {
        "form":form,
        "object": instance,
        # "categories": FeaturedCategory.objects.all()
    }
    if instance is None:
        return render(request, "main/errors/404.html")
    return render(request, url, context)

@method_decorator(login_required, name="dispatch")
class FeaturedSubCategoryCreateView(LoginRequiredMixin, CreateView):
    model = FeaturedSubCategory
    success_url = "/professional_services/bitraining2"
    fields = ["featuredcategory", "title", "description"]
    page_title = 'Add Sub Category'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title']=capfirst(self.page_title)


def feedback_review(request, pk=None):
    title = 'CODA: AN AI POWERED INTERVIEW PLATFORM'
    ad_title = 'Business Intelligence To Skyrocket Your Career Even If You Don’t Have Any Experience.'
    
    try:
        if pk:
            response = get_object_or_404(Training_Responses, pk=pk)
            
            # Check if the existing review is less than 25 words
            word_count = len(response.review.split()) if response.review else 0
            
            paragraphs = response.review.split('\n') if response.review else None
            
            # Gather requirements information
            user_title = response.title if response.title else ''
            subcat_instance = FeaturedSubCategory.objects.filter(title=user_title).first()
            topic_description = subcat_instance.description if subcat_instance else 'No description available'
            user_question = response.question if response.question else ''
            user_response = response.response if response.response else ''
            user_comments = response.comment if response.comment else ''
            
            context = {
                "title": title,
                "ad_title": ad_title,
                "category": response.title,
                "topic": response.title,
                "description": topic_description,
                "date": response.upload_date,
                "id": response.id,
                "user_response": response,
                "paragraphs": paragraphs,
               
            }
            
            if word_count > 25:
                return render(request, "professional_services/interview/interview_progress/user_response.html", context)
            
            # Generate a new review if the notification flag is set and word count is less than 25
            if response.notification_flag:
                openai_context = OpenaiPrompt.objects.filter(topic='Feedback').first()

                requirement = (
                    f"**Current subject/topic**: {user_title}.\n\n"
                    f"**Brief description of this topic/subject**: {topic_description}\n\n"
                    f"**Students' responses**: {user_response}.\n\n"
                    f"**Students' comments**: {user_comments}.\n\n"
                )
                user_message = openai_user_message(openai_context, requirement)
                try:
                    openai_response = user_message 
                    # openai_response = generate_chatbot_response(user_message) if requirement else "No further context provided."
                except Exception as e:
                    openai_response = f"Error generating response: {str(e)}"
                    
                response.review = openai_response
                response.upload_date = today_date
                response.save()
                
                paragraphs = response.review.split('\n')  
                context["paragraphs"] = paragraphs 

            return render(request, "professional_services/interview/interview_progress/user_response.html", context)
        else:
            return redirect('professional_services:student_feedback')
    except Exception as e:
        return render(request, "main/errors/404.html")

def feedback(request):
    username=request.user
    responses=None
    if request.user.is_staff:
        title='CLIENT RESPONSES'
        description='Summary of what clients/staff have accomplished on a daily/weekly basis.Gives the management a chance to deal with the challenges faced by clients/staff.'
        responses = Training_Responses.objects.all().order_by("-upload_date")
    else:
        title='MY RESPONSES'
        description='Students feedback/retrospective on how the course is progressing.'
        responses = Training_Responses.objects.filter(user__username=username).order_by("-upload_date")

    context={
                "title":title,
                "description":description,
                "responses":responses,
    }
    return render(request, "professional_services/training/feedback.html" ,context)

@login_required
@require_http_methods(["GET", "POST"])
def training_response_update_view(request, pk):
    user_response = get_object_or_404(Training_Responses, pk=pk)

    instance=FeaturedSubCategory.objects.get_by_subcategory(user_response.title)
    if not (request.user.is_superuser or request.user == user_response.user):
        return HttpResponseForbidden()
    
    if request.method == "POST":
        form = TrainingResponseForm(request.POST, request.FILES, instance=user_response)
        if form.is_valid():
            form.save()
            return redirect("professional_services:student_feedback")
    else:
        form = TrainingResponseForm(instance=user_response)
    tasks= FeaturedActivity.objects.filter(featuredsubcategory=instance.id)
    context = {
        "object": instance,
        "tasks": tasks,
        "form": form,
        "response": user_response,
    }
    
    return render(request, "professional_services/training/form_templates/course_update_form.html", context)


@login_required
def subcategorydetail(request, title=None, *args, **kwargs):
    instance = get_object_or_404(FeaturedSubCategory, title=title)
    logger.debug("training_question",instance,request.user.category)
    if request.user.category == 4:
        try:
            tracking = TrainingResponsesTracking.objects.get(user=request.user)
            if title != tracking.featuredsubcategory.title:
                return redirect('professional_services:subcategory-detail', title=tracking.featuredsubcategory.title)
        except TrainingResponsesTracking.DoesNotExist:
            tracking = TrainingResponsesTracking(user=request.user, featuredsubcategory=instance)
            tracking.save()

        if request.method == 'POST':
            try:
                form = TrainingResponseForm(request.POST, request.FILES)
                if form.is_valid():
                    training_question = request.POST.get('training_question').lower()
                    subcategory_title = instance.title

                    # Check if a similar record exists
                    existing_response = Training_Responses.objects.filter(
                        user=request.user,
                        question=training_question,
                        title=subcategory_title
                    ).first()

                    if existing_response:
                        form = TrainingResponseForm(request.POST, request.FILES, instance=existing_response)
                        if form.is_valid():
                            form.save()
                    else:
                        form_obj = form.save(commit=False)
                        form_obj.user = request.user
                        form_obj.title = subcategory_title
                        form_obj.question = training_question
                        form_obj.save()

            except Exception as e:
                return render(request, "main/errors/404.html")
            
            next_title = FeaturedSubCategory.objects.filter(order__gt=instance.order).order_by('order')
            if not next_title.exists():
                next_category = FeaturedCategory.objects.filter(title='Course Overview').first()
                tracking.featuredsubcategory = FeaturedSubCategory.objects.get(order='1')
                tracking.save()
                return redirect('professional_services:category-detail', title=next_category.title)
            next_title = next_title.first()
            tracking.featuredsubcategory = next_title
            tracking.save()
            return redirect('professional_services:subcategory-detail', title=next_title.title)
    else:
        instance = FeaturedSubCategory.objects.get_by_subcategory(title)
    
    tasks = FeaturedActivity.objects.filter(featuredsubcategory=instance.id)
    context = {
        "tasks": tasks,
        "form": TrainingResponseForm(),
        "object": instance,
        "title_": title
    }
    return render(request, 'professional_services/training/training_progress/course.html', context)


@method_decorator(login_required, name="dispatch")
class FeaturedActivityCreateView(LoginRequiredMixin, CreateView):
    model = FeaturedActivity
    success_url = "/professional_services/bitraining"
    fields = ["featuredsubcategory", "activity_name", "description","guiding_question","interview_question"]
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

def activitydetail(request, slug=None, *args, **kwargs):
    activities = FeaturedActivity.objects.all()
    url=f'professional_services/training/training_progress/activity.html'
    context = {
        "form":InterviewForm,
        "activities": activities,
        "categories": FeaturedSubCategory.objects.all(),
    }
    if activities is None:
        return render(request, "main/errors/404.html")
    return render(request, url, context)

@method_decorator(login_required, name="dispatch")
class FeaturedActivityLinksCreateView(LoginRequiredMixin, CreateView):
    model = ActivityLinks
    success_url = "/professional_services/bitraining2"
    # fields = ["Activity", "link_name", "doc", "link", "is_active"]
    fields = ["Activity", "link_name", "doc", "link"]
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
        
@method_decorator(login_required, name="dispatch")
class DSUCreateView(LoginRequiredMixin, CreateView):
    model = DSU
    success_url = "/professional_services/bitraining"
    fields = ["trained_by", "category", "task", "plan", "challenge", "is_active"]
    def form_valid(self, form):
        form.instance.trained_by = self.request.user
        return super().form_valid(form)
    
# ========================2. UPDATE VIEWS============================
@method_decorator(login_required, name="dispatch")
class FeaturedCategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = FeaturedCategory
    success_url = "/professional_services/updatelist"
    fields = ["title", "description"]
    def form_valid(self, form):
        # form.instance.author=self.request.user
        return super().form_valid(form)
    def test_func(self):
        FeaturedCategory = self.get_object()
        if self.request.user.is_superuser:
            return True
        elif self.request.user == FeaturedCategory.created_by:
            return True
        return redirect("professional_services:training-list")
    
@method_decorator(login_required, name="dispatch")
class FeaturedSubCategoryUpdateView(
    LoginRequiredMixin, UserPassesTestMixin,UpdateView
):
    model = FeaturedSubCategory
    success_url = "/professional_services/updatelist"
    fields = ["featuredcategory", "title", "description"]
    def form_valid(self, form):
        return super().form_valid(form)
    def test_func(self):
        FeaturedSubCategory = self.get_object()
        if self.request.user.is_superuser:
            return True
        elif self.request.user == FeaturedSubCategory.created_by:
            return True
        return redirect("professional_services:training-list")
    
@method_decorator(login_required, name="dispatch")
class FeaturedActivityUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = FeaturedActivity
    success_url = "/professional_services/updatelist"
    fields = ["featuredsubcategory", "activity_name","guiding_question","interview_question", "description"]
    def form_valid(self, form):
        # form.instance.author=self.request.user
        return super().form_valid(form)
    def test_func(self):
        FeaturedActivity = self.get_object()
        if self.request.user.is_superuser:
            return True
        elif self.request.user == FeaturedActivity.created_by:
            return True
        return redirect("professional_services:training-list")
    
@method_decorator(login_required, name="dispatch")
class FeaturedActivityLinksUpdateView(
    LoginRequiredMixin, UserPassesTestMixin, UpdateView
):
    model = ActivityLinks
    success_url = "/professional_services/updatelist"
    # fields=['group','category','employee','activity_name','description','point','mxpoint','mxearning']
    fields = ["Activity", "link_name", "doc", "link"]
    def form_valid(self, form):
        return super().form_valid(form)
    def test_func(self):
        ActivityLinks = self.get_object()
        if self.request.user.is_superuser:
            return True
        elif self.request.user == ActivityLinks.created_by:
            return True
        return redirect("professional_services:training-list")
    
# ========================3. DELETE VIEWS============================
@method_decorator(login_required, name="dispatch")
class FeaturedCategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = FeaturedCategory
    success_url = "/professional_services/updatelist"
    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return False
    
@method_decorator(login_required, name="dispatch")
class FeaturedSubCategoryDeleteView(
    LoginRequiredMixin, UserPassesTestMixin, DeleteView
):
    model = FeaturedCategory
    success_url = "/professional_services/updatelist"
    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return False
    
@method_decorator(login_required, name="dispatch")
class FeaturedActivityDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = FeaturedActivity
    success_url = "/professional_services/updatelist"
    def test_func(self):
        # timer = self.get_object()
        # if self.request.user == timer.author:
        # if self.request.user.is_superuser:
        if self.request.user.is_superuser:
            return True
        return False
@method_decorator(login_required, name="dispatch")
class FeaturedActivityLinksDeleteView(
    LoginRequiredMixin, UserPassesTestMixin, DeleteView
):
    model = ActivityLinks
    success_url = "/professional_services/updatelist"
    def test_func(self):
        # timer = self.get_object()
        # if self.request.user == timer.author:
        # if self.request.user.is_superuser:
        if self.request.user.is_superuser:
            return True
        return False
# ========================4. DISPLAY/LIST VIEWS============================
class FeaturedCategoryListView(ListView):
    queryset = FeaturedCategory.objects.all()
    template_name = "professional_services/training/updatelist.html"

def activity_view(request):
    categories = (
        FeaturedCategory.objects.prefetch_related("featuredsubcategory_set").all(),
    )
    cats = FeaturedCategory.objects.all().order_by("-created_at")
    BiFilter = BitrainingFilter(request.GET, queryset=cats)
    categories = BiFilter.qs
    context = {"categories": categories, "cats": cats, "BiFilter": BiFilter}
    return render(
        request=request, template_name="professional_services/training/bitraining.html", context=context
    )
def table_activity_view(request):
    categories = (
        FeaturedCategory.objects.prefetch_related("featuredsubcategory_set").all(),
    )
    cats = FeaturedCategory.objects.all()  # .order_by('-created_at')
    BiFilter = BitrainingFilter(request.GET, queryset=cats)
    categories = BiFilter.qs
    context = {"categories": categories, "cats": cats, "BiFilter": BiFilter}
    return render(
        request=request, template_name="professional_services/training/updatelist.html", context=context
    )
class LinksListView(ListView):
    model= ActivityLinks
    template_name = "professional_services/training/links.html"
    context_object_name='links'


# =============================Job===================
@method_decorator(login_required, name="dispatch")
class JobCreateView(LoginRequiredMixin, CreateView):
    model = Job_Tracker
    success_url = "/professional_services/job_tracker"
    fields = [
        "position",
        "recruiter",
        "vendor_phone",
        "primary_tool",
        "secondary_tool",
        "job_location",
        "offer",
        "description",
        "status",
        "updated_resume",
    ]
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
@method_decorator(login_required, name="dispatch")
class JobListView(ListView):
    queryset = Job_Tracker.objects.all()
    template_name = "professional_services/jobroles/job_tracker.html"
    ordering = ["-created_at"]

@method_decorator(login_required, name="dispatch")
class JobTrackerUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Job_Tracker
    fields = "__all__"

    def get_success_url(self):
        """Dynamically set the success URL with the username of the logged-in user."""
        return reverse_lazy("professional_services:userjoblist", kwargs={"username": self.request.user.username})

    def form_valid(self, form):
        """Ensure the form is valid before saving."""
        return super().form_valid(form)

    def test_func(self):
        """Restrict access: Allow only superusers or the user who created the job tracker."""
        job_tracker = self.get_object()
        return self.request.user.is_superuser or self.request.user == job_tracker.created_by

def userjobtracker(request, user=None, *args, **kwargs):
    user = get_object_or_404(User, username=kwargs.get("username"))
    jobs = Job_Tracker.objects.all().filter(created_by=user).order_by("-created_at")
    num = jobs.count()

    Usedtime = 1
    plantime = 1
    try:
        delta = round(plantime - Usedtime)
    except (TypeError, AttributeError):
        delta = 0
        return render(request, "testing/job_tracker.html")
    context = {
        "jobs": jobs,
        "num": num,
        "plantime": plantime,
        "Usedtime": Usedtime,
        "delta": delta,
    }
    return render(request, "professional_services/interview/userjobtracker.html", context)

def employetraining(request):
    request.session["siteurl"] = settings.SITEURL

    category_titles = ["VIDEOS", "POWER POINTS"]
    video_categories = FeaturedCategory.objects.filter(title__in=category_titles)
    subcategories = FeaturedSubCategory.objects.filter(featuredcategory__in=video_categories)
    links = ActivityLinks.objects.filter(Featuredsubcategory__in=subcategories).distinct()
    calender = ClientAvailability.objects.all()
    logger.debug(calender)
    context = {
        "categories": video_categories,
        "subcategories": subcategories,
        "title": "employeeetraining",
        "links": links,
    }
    return render(request, "professional_services/training/employeetraining.html", context)


def get_subcategories(request):
    featured_category_id = request.GET.get('category_id')  # This expects the `id` of the selected category.
    subcategories = FeaturedSubCategory.objects.filter(featuredcategory_id=featured_category_id).values('id', 'title')
    logger.debug(subcategories)
    return JsonResponse(list(subcategories), safe=False)

def get_activity_links(request):
    task_id = request.GET.get('task_id')  # Task ID from the AJAX request
    # Query the ManyToManyField 'Activity' to filter based on task ID
    links = ActivityLinks.objects.filter(Activity__id=task_id).values('id', 'link_name')
    return JsonResponse(list(links), safe=False)


def Schedule(request):
    # Fetch all active categories
    categories = FeaturedCategory.objects.filter(is_active=1)

    # Prepare a dictionary to hold the grouped data
    grouped_data = defaultdict(list)

    for category in categories:
        subcategories = category.featuredsubcategory_set.filter(is_active=True).order_by('order')
        for subcategory in subcategories:
            activities = subcategory.subcategories_fetured.filter(is_active=1).order_by('activity_name')
            for activity in activities:
                # Fetch related links
                powerpoints = ActivityLinks.objects.filter(
                    Activity=activity
                )
                videos = ActivityLinks.objects.filter(
                    Activity=activity
                )
                
                # Append the activity details to the grouped_data
                grouped_data[category.title].append({
                    "subcategory": subcategory.title,
                    "task": activity.activity_name,
                    "day": "n/a",
                    "date": "n/a",
                    "start_time": "n/a",
                    "end_time": "n/a",
                    "client": activity.created_by.username,
                    "powerpoints": powerpoints,
                    "videos": videos,
                })

    # Calculate rowspan for categories
    rowspan_data = {category: len(subcategories) for category, subcategories in grouped_data.items()}
    
    context = {
       'grouped_availability': list(grouped_data.items()),
       'rowspan_data': rowspan_data,
    }
    return render(request, "professional_services/training/schedule.html", context)


@csrf_exempt
def update_schedule_status(request):
    if request.method == 'POST' and request.user.is_superuser:
        try:
            data = json.loads(request.body)
            subcategory_id = data.get('id')
            is_active = data.get('is_active')

            # Update the subcategory's active status
            subcategory = FeaturedSubCategory.objects.get(id=subcategory_id)
            subcategory.is_active = is_active
            subcategory.save()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Unauthorized'})

correct_answers_performance = {
   'tableau': {
                        "Ideally, I would first run performance recording on the reports to identify performance bottlenecks."
                        "Since data is at the core of Tableau reports, I would ensure that the data is free of any errors and consistent for proper interpretation. "
                        "Use of data extracts as opposed to live connections will speed up response time. Finally, I will only select columns needed by using data source filters."
                        "At this level, I will insist on having a small number of simple charts on the dashboard. I will use action filters as opposed to quick filters and avoid context filters. "
                        "For calculations, I will ensure they are simple, and optimize for performance by favoring numbers and booleans over strings and dates."
                        "As a Tableau administrator, I would make proper use of the active directory, keep a close eye on data extracts, and ensure the implementation of user filters."
                   
                },
                'alteryx': {
                        "When connecting to databases, I will make use of cached data to eliminate repetitive fetching from the database each time the workflow runs."
                        "I will use the sample tool to limit the data in the workflow, remove unnecessary fields using the select tool, and eliminate the browser tool to reduce runtime. "
                        "Additionally, I will ensure there is adequate space in the local temporary directory and browse to the data file when using the spatial tool."
                    
                },
                'sql': {
                        "I will run the Query Store utility to check for performance bottlenecks."
                        "I would ensure that database tables have primary keys and efficient use of indexes. I will avoid using temporary tables wherever possible."
                        "When structuring my queries, I would focus on retrieving only the data I intend to use. I would avoid correlated subqueries and coding loops to optimize performance."
                   
                },
                'python': {
                        "Python has many optimized inbuilt functions, and for this reason, I would avoid defining my own functions when an inbuilt alternative exists. "
                        "When importing functions from modules, I will only import what is needed rather than the entire library. "
                        "I would use list comprehensions over for loops, and generators in memory-intensive tasks, in addition to itertools, sets, and unions."               
                }
}

correct_answers_testing = {
    'Project': {
            "The project was developed to establish reasons behind the employees leaving the company and which segment of employees was leaving. "
            "The project aimed at slowing down or eliminating employee attrition. The features of the Item to be tested (landing page) were tested "
            "to verify their functionality when manipulated and to display accurate reports."
        },
        'Test Types': {
            "Unit Testing was done to test each of the written scripts. During the process of developing reports, we did white box testing to verify "
            "key features of the landing page and to improve its design and usability. This was followed by regression testing to check if the new "
            "changes to the landing page report had any effect on the existing reports."
        },
        'Process': {
            "Through frequent communication with stakeholders and end users of the product, we were able to analyze the requirements, define expectations, "
            "and complete key documentation. We created test Scenarios for each feature of the landing page and a traceability matrix to ensure each "
            "requirement had a corresponding test scenario. Test Scripts were used to list out each step in testing and the results (actual and expected). "
            "A validation document was prepared to prove that the landing page met the needs of the client or user."
        }
}

correct_answers_project_story = {
    'Description': "The goal of the project was to create an Employee Performance report that tracks each employee’s productivity...",
    'Challenges': "There was a lack of clear communication from stakeholders regarding the creation of prototypes...",
    'Solutions': "To address the challenges, we established proper communication flows..."
}

correct_answers_methodology = {
    'Description': {
        "The goal of the project was to create an Employee Performance report that tracks each employee’s productivity through meetings attended, "
        "internal social media interactions, and daily activities in order to reward employees based on output."
    },
    'Report Structure': {
        "Showing description of the report below the title and the last updated on the top left corner. "
        "It shows various parameters linking to the employee productivity overview report, WhatsApp chats report, and DAF records report. "
        "Additionally, the company logo is shown on the top left corner with the report title beside it."
    },
    'Challenges': {
        "There was a lack of clear communication from stakeholders regarding the creation of prototypes/wireframes for the final product before development. "
        "Most activities were done at night due to the time difference between the company and the client, which added to the difficulty. "
        "Unrealistic deadlines also posed significant challenges during the project."
    },
    'Solutions': {
        "To address the challenges, we established proper communication flows for project members and the client and developed a way to inform the relevant information. "
        "We worked late hours to ensure the project timelines were met. Additionally, we shared detailed information with the client regarding the various phases of the project and the minimum time taken to complete each phase."
    }
}

correct_answers_sdlc = {
       'projects': {
        "Employee productivity report: CODA Management and other stakeholders were interested in having a platform "
        "that could track the productivity of each employee based on meetings, DAF, and Whatsapp Messages by providing "
        "high-level interactive reports such as Landing Page, Employee Executive Overview, and detailed reports such "
        "as Social media Report, DAF Records Report and meetings Report."
  },
    'releases': {
        "We subdivided the project into 3 Releases\n"
        "Release 1(Reports)\nLanding Page\nExecutive overview\nWhatsapp Report\n"
        "Release 2 (Database)\nEmployee Database\nReport Procedure\n"
        "Release 3 (ETL)\nMeetings Workflow\nWhatsapp Workflow\nDAF Workflow"
  },
    'sprints': {
        "We subdivided release into the following sprints:\n"
        "Release 1(Reports)\nSprint 1: Landing Page\nSprint 2: Executive\n"
        "Release 2 (Database)\nSprint 3: Database\nSprint 4: Retrieving of information\n"
        "Release 3 (ETL)\nSprint 5: Meeting workflow\nSprint 6: DAF workflow"
  },
    'stories': {
        "Each sprint had the following stories:\n"
        "Story 1\nStory 2\nStory 3"
  }
}


def populate_section_data(request):
    """View to populate SectionData model"""
        # Optional: Clear existing data if needed
    Correct_answers.objects.all().delete()
    logger.debug("All previous SectionData entries deleted.")
    try:
        populate_data('performance', correct_answers_performance)
        populate_data('testing', correct_answers_testing)
        populate_data('Project Story', correct_answers_project_story)
        populate_data('methodology', correct_answers_methodology)
        populate_data('sdlc', correct_answers_sdlc)
    except Exception as e:
        logger.debug(f"Error while populating data: {str(e)}")

    return render(request, 'professional_services/jobroles/job_tracker.html')


def populate_data(section, data_dict):
    """Helper function to save the data into the Correct_answers model"""
    entries = []
    for category, content in data_dict.items():
            logger.debug(f"Adding entry - Section: {section}, Category: {category}")
            if isinstance(content, (list, tuple, set)):
                cleaned_content = ' '.join(map(str, content))  # Convert list/tuple/set to string
            elif isinstance(content, dict):
                cleaned_content = ', '.join(f"{k}: {v}" for k, v in content.items())  # Convert dict to string
            else:
                cleaned_content = str(content)  # Convert other types to string
            
            cleaned_content = cleaned_content.replace('{', '').replace('}', '')  # Remove any remaining curly braces

            # Create each entry but do not save yet, just append it to a list
            entries.append(Correct_answers(
                section=section,
                categories=category,
                content=cleaned_content
            ))

    try:
        # Bulk create all entries at once for better performance
        Correct_answers.objects.bulk_create(entries)
        logger.debug(f"All entries for section '{section}' saved successfully.")
    except Exception as e:
        logger.debug(f"Error saving entries for section {section}: {str(e)}")

from django.views.decorators.http import require_POST        
def deactivate_notification(request, notification_id):
    if request.method == 'POST':
        try:
            # Find the notification by ID and update the is_active field to False
            notification = Training_Responses.objects.get(id=notification_id)
            notification.is_active = False
            notification.seen_notifications = True
            notification.save()
            return JsonResponse({'success': True, 'message': 'Notification deactivated successfully.'})
        except Training_Responses.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Notification not found.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})
def generate_review_sets(request):
    # if request.user.is_authenticated:
    #     logger.debug('ok')
    #     # Update all unseen notifications for the user
    #     Training_Responses.objects.filter(user=request.user, seen_notifications=False).update(seen_notifications=True)
    #     return JsonResponse({'success': True})
    # return JsonResponse({'success': False, 'message': 'User is not authenticated'})

    title_to_process = 'testing'  # Replace 'testing' with the desired title

    # Get up to 3 random reviews for the specified title
    student_responses = Training_Responses.objects.filter(
        title=title_to_process,
        review__isnull=False
    ).exclude(review__exact='').order_by('?')[:3]

    if not student_responses.exists():
        return JsonResponse({'success': False, 'message': f'No reviews found for title "{title_to_process}"'})

    # Collect the selected reviews into a list
    student_reviews = student_responses.values_list('review', flat=True)

    # Combine the selected reviews into a single text
    combined_reviews = '\n\n'.join(student_reviews)

    # Prepare the base prompt for OpenAI
    prompt_base = (
        f"As an experienced teacher, please analyze the following student reviews on the topic '{title_to_process}'. "
        f"Identify common strengths and areas for improvement. Based on this analysis, provide a comprehensive review "
        f"that offers actionable advice. Write in a professional and encouraging tone.\n\n"
        f"Students Reviews:\n{combined_reviews}\n\n"
    )

    # Generate five review sets
    for i in range(1, 6):
        try:
            # Prepare the prompt for this review set
            user_message = prompt_base + f"Review Set {i}:\n"

            # Call OpenAI to generate the review
            generated_review = generate_chatbot_response(user_message)

            # Save the generated review as a new Training_Responses instance
            new_review = Training_Responses(
                user=None,  # You can assign this to a system user or leave it as None
                title=f"{title_to_process}{i}",
                response='',
                question='',
                question1='',
                is_active=True,
                review=generated_review,
                link='',
                comment='',
                score=None,
                upload_date=timezone.now(),
                first_displayed_at=None,
                seen_notifications=False,
            )
            new_review.save()
            logger.debug(f"Generated and saved Review Set {i} for title '{title_to_process}'")

        except Exception as e:
            logger.debug(f"An error occurred while generating Review Set {i} for title '{title_to_process}': {e}")
            continue  # Proceed to the next review set

    return JsonResponse({'success': True, 'message': 'Review sets generated successfully'})

    
# def notify_admin_on_completion(check_id):
#     check = BackgroundCheck.objects.get(id=check_id)
#     send_mail(
#         'Background Check Completed',
#         f'The background check for {check.student.name} has been completed.',
#         'noreply@coda.com',
#         ['admin@coda.com']
#     )


# from weasyprint import HTML

# def generate_report(check_id):
#     check = BackgroundCheck.objects.get(id=check_id)
#     html_string = render_to_string('background_check_report.html', {'check': check})
#     html = HTML(string=html_string)
#     pdf = html.write_pdf()
#     with open(f'reports/check_{check_id}.pdf', 'wb') as f:
#         f.write(pdf)


