from datetime import date,datetime, timedelta
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404,render, redirect
from django.db.models import Q
from accounts.models import CustomerUser
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import CreateView,DeleteView, ListView, TemplateView, UpdateView
from .forms import (
    RatingForm,
    ReportingForm,
    ApplicantProfileFormA,
    ApplicantProfileFormB,
    ApplicantProfileFormC,
    TraineeAssessmentForm
)
from .models import Rated, Reporting, Trainee_Assessment, ApplicationWorkflow
from .services import workflow_service
from professional_services.models import ActivityLinks
from management.models import Policy,Task,TaskLinks
from accounts.models import UserProfile
from .utils import (alteryx_list,
                     dba_list,
                     posts,
                     tableau_list,
                    rewardpoints,
                    interview_description,
                    interview_view)
from main.utils import path_values
from application.permission import check_client_assesment
from accounts.mixins import FilteredListViewMixin
from django.views.generic import ListView


# User=settings.AUTH_USER_MODEL
User = get_user_model()


class application(TemplateView):
    template_name = "application.html"

class ApplicantListView(FilteredListViewMixin, ListView):
    """Consolidated applicant list view using generic mixin"""
    model = CustomerUser
    template_name = "application/applications/applicants.html"
    context_object_name = "applicants"
    category_filters = {
        1: None,  # Job Applicants
        4: 6,     # DCK Members (Student category, sub_category 6)
    }
    
    def get_context_data(self, **kwargs):
        """Add applicant-specific context data"""
        context = super().get_context_data(**kwargs)
        
        # Get path values for sub_title
        path_list, sub_title, pre_sub_title = path_values(self.request)
        
        # Filter applicants based on sub_title
        if sub_title == 'applicants':
            context['applicants'] = self.get_queryset().filter(
                category=1, 
                sub_category=None,
                is_active=True
            ).order_by("-date_joined")
        elif sub_title == 'dckmembers':
            context['applicants'] = self.get_queryset().filter(
                category=4,
                sub_category=6,
                is_active=True
            ).order_by("-date_joined")
        
        context.update({
            'sub_title': sub_title,
            'pre_sub_title': pre_sub_title,
        })
        
        return context


# ------------------------Interview Section-------------------------------------#.
def career(request):
    return render(request, "application/applications/career.html", {"title": "career"})

@login_required
def interview(request):
    context = {"posts": posts}
    return render(request, "application/interview_process/interview.html", context)

def firstinterview(request):
    return render(
        request,
        "application/interview_process/firstinterview.html",
        {"title": "first_interview"},
    )

@csrf_exempt
@login_required
@user_passes_test(lambda user: check_client_assesment(user), login_url='/management/newclient/')
def FI_sectionA(request):
    path_list,sub_title,pre_sub_title=path_values(request)
    categories,variable_title=interview_view(sub_title)

    form = ApplicantProfileFormA(
        request.POST, request.FILES, instance=request.user.profile
    )
    datalink=ActivityLinks.objects.filter(link_name='Data').first()
    if datalink:
        link_url = datalink.link
    else:
        # Handle the case where no matching row was found.
        link_url = None 
    if request.method == "POST":
        form = ApplicantProfileFormA(
            request.POST, request.FILES, instance=request.user.profile
        )
        if form.is_valid():
            data = form.cleaned_data["user"] = request.user
            section = data.profile.section
            if section == "A":
                if request.user.gender == 2:
                    data.profile.section = "C"
                    data.profile.save()
                else:
                    data.profile.section = "B"
                    data.profile.save()
            form.save()
            # subject = "Interview Message"
        
        return redirect("application:ratewid", pk="Alteryx")
    
    context={"title": "Section A",
             "categories": categories,
             "variable_title": variable_title,
             "interview_description": interview_description,
             "form": form,
             "link_url":link_url}
    return render(
        request,
        "application/interview_process/firstinterview/sectionA.html",context
        ,
    )


@login_required
@user_passes_test(lambda user: check_client_assesment(user), login_url='/management/newclient/')
def FI_sectionB(request):
    path_list,sub_title,pre_sub_title=path_values(request)
    categories,variable_title=interview_view(sub_title)
    form = ApplicantProfileFormB(
        request.POST, request.FILES, instance=request.user.profile
    )
    if request.method == "POST":
        form = ApplicantProfileFormB(
            request.POST, request.FILES, instance=request.user.profile
        )
        if form.is_valid():
            data = form.cleaned_data["user"] = request.user
            section = data.profile.section
            if section == "B":
                data.profile.section = "C"
                data.profile.save()
            form.save()
            # subject = "Interview Message"

        send_email(category= request.user.category,
            to_email=[request.user.email,],
            subject='Application Received for Interview B', 
            html_template='email/application/FI_sectionB.html',
            context={'user': request.user})
        return redirect("application:ratewid", pk="Tableau")
    
    context={"title": "First Section",
             "categories": categories,
             "variable_title": variable_title,
             "interview_description": interview_description,
             "form": form,
            #  "link_url":link_url
             }
    return render(
        request,
        "application/interview_process/firstinterview/sectionB.html",context
    )


@login_required
@user_passes_test(lambda user: check_client_assesment(user), login_url='/management/newclient/')
def FI_sectionC(request):
    path_list,sub_title,pre_sub_title=path_values(request)
    categories,variable_title=interview_view(sub_title)
    form = ApplicantProfileFormC(
        request.POST, request.FILES, instance=request.user.profile
    )
    if request.method == "POST":
        form = ApplicantProfileFormC(
            request.POST, request.FILES, instance=request.user.profile
        )
        if form.is_valid():
            data = form.cleaned_data["user"] = request.user
            section = data.profile.section
            if section == "C":
                data.profile.section = "D"
                data.profile.save()
            form.save()

            # subject = "Interview Message"
            send_email(category=request.user.category,
                to_email=[request.user.email,],
                subject='Application Received for Interview C', 
                html_template='email/application/FI_sectionC.html',
                context={'user': request.user})
            return redirect("application:ratewid", pk="Database")
        
    context={"title": "First Section",
             "categories": categories,
             "variable_title": variable_title,
             "interview_description": interview_description,
             "form": form,
            #  "link_url":link_url
             }
    return render(
        request,
        "application/interview_process/firstinterview/sectionC.html",context
    )


def first_interview(request):
    request.session["siteurl"] = settings.SITEURL
    section = UserProfile.objects.values_list("section", flat=True).get(
        user=request.user
    )

    context = {
        "alteryx_list": alteryx_list,
        "dba_list": dba_list,
        "tableau_list": tableau_list,
    }

    return render(
        request, "application/interview_process/first_interview.html", context
    )


# def uploadinterviewworks(request):
#     myfile = request.FILES["myfile"]
#     section = request.POST["section"]
#     profilename = myfile.name
#     extension = str(profilename[profilename.rindex(".") :])
#     allowed_extlist = [".zip"]
#     if extension not in allowed_extlist:
#         return JsonResponse(
#             {"success": False, "message": "Invalid file type.Formats allowed: zip."}
#         )

#     if myfile.size > 50000000:
#         context["success"] = False
#         context["message"] = "File size sholud be less than 50MB"
#         return JsonResponse(context)

#     filename = "".join(random.choices(string.digits, k=5))
#     des_path = "applicants/interview/" + str(request.user.id) + filename + ".zip"

#     s3 = boto3.resource(
#         "s3",
#         aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#         aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
#         region_name=settings.AWS_S3_REGION_NAME,
#     )
#     response = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME).put_object(
#         Key=des_path, Body=myfile
#     )
#     UserProfile.objects.filter(applicant=request.user).update(section=section)
#     return JsonResponse({"success": True})


def orientation(request):
    return render(
        request, "application/orientation/orientation.html", {"title": "orientation"}
    )

def internal_training(request):
    return render(
        request,
        "application/orientation/internal_training.html",
        {"title": "orientation"},
    )

def policies(request):
    reporting_date = date.today() + timedelta(days=7)
    policies =Policy.objects.filter(Q(is_active=True),Q(is_internal=False)).order_by("upload_date")
    context = {"policies": policies, "reporting_date": reporting_date}
    return render(request, "application/orientation/policies.html", context)


# -------------------------rating Section-------------------------------------#

def rate(request):
    if request.method == "POST":
        form = RatingForm(request.POST, request.FILES, request=request)
        if request.user.is_staff or request.user.category == 1:  # Job_Applicant category
            form.instance.employeename = request.user
            form.instance.rating_date = date.today()
            form.instance.type = 'Other'
        if form.is_valid():
            total_points=rewardpoints(form)
            form.instance.totalpoints = total_points
            
            # Saving form data to rating table only if the user is applicant
            if form.instance.employeename.category == 1:  # Job_Applicant category
                upload_link_url = form.cleaned_data.get('uploadlinkurl')
                if not upload_link_url:
                    return render(request, "application/orientation/rate.html", {"form": form, "applicant_error": "Please provide the evidence link"})
                form.save()
                
                # Update workflow with skills assessment score
                workflow_service.update_skills_score(form.instance.employeename, total_points)
                
                user_profile = UserProfile.objects.get(user__username=form.instance.employeename)
                if user_profile.section == "D":
                    return redirect("application:policies")
                else:
                    return redirect("application:section_"+user_profile.section.lower()+"")

            # For One on one sessions adding task points and increasing mxpoint if it is equal or near to points.
            try:
                task = Task.objects.filter(
                    Q(activity_name__icontains="one on")
                ).get(employee__username=form.instance.employeename)
                task.point += total_points
                if task.point >= task.mxpoint or task.point + 15 >= task.mxpoint:
                    task.mxpoint += 15
                task.save()
                return redirect("management:new_evidence", taskid=task.id)
            except Task.DoesNotExist:
                print("Task does not exist")
        else:
            # Form is not valid, print errors
            print("Form is not valid. Errors:")
            for field, errors in form.errors.items():
                print(f"Field: {field}")
                for error in errors:
                    print(f"- {error}")
    else:
        form = RatingForm(request=request)
    return render(request, "application/orientation/rate.html", {"form": form})

from mail.custom_email import send_email

def ratewid(request,pk):
    if request.method == "POST":
        form = RatingForm(request.POST, request.FILES)
        if request.user.is_staff or request.user.category == 1:  # Job_Applicant category
            print("employee or applicant",request.user)
            form.instance.employeename = request.user
        print(form.is_valid())

        improvement_area = []
        if form.is_valid():
            totalpoints = 0
            #link validity check
            try:

                link_exists = Rated.objects.filter(uploadlinkurl=form.instance.uploadlinkurl).exists()

                if link_exists:
                    # messages.error(request, "this link was already uploaded.")
                    return render(request, "application/orientation/rate.html", {"form": form,"error":True, "error_message": "this link was already uploaded."})
                
                result = link_validity_check(form.instance.uploadlinkurl)
                if result is not None:
                    # messages.error(request, "this link is invalid.")
                    return render(request, "application/orientation/rate.html", {"form": form,"error":True, "error_message": result})
                
            except Exception as e:
                print(e)
            try:
                if request.POST["projectDescription"] == "on":
                    totalpoints += 2
                else:
                    improvement_area.append('Project Description')
            except:
                improvement_area.append('Project Description')
            try:
                if request.POST["requirementsAnalysis"] == "on":
                    totalpoints += 3
                else:
                    improvement_area.append('Requirements Analysis')
            except:
                improvement_area.append('Requirements Analysis')
            try:
                if request.POST["development"] == "on":
                    totalpoints += 5
                else:
                    improvement_area.append('Development')
            except:
                improvement_area.append('Development')
            try:
                if request.POST["testing"] == "on":
                    totalpoints += 3
                else:
                    improvement_area.append('Testing')
            except:
                improvement_area.append('Testing')
            try:
                if request.POST["deployment"] == "on":
                    totalpoints += 2
                else:
                    improvement_area.append('Deployment')
            except:
                improvement_area.append('Deployment')

            form.instance.topic = pk
            form.instance.totalpoints = totalpoints
            # Saving form data to rating table only if the user is applicant
            if form.instance.employeename.category == 1:  # Job_Applicant category
                userprof = UserProfile.objects.get(user__username=form.instance.employeename)
                if totalpoints > 12:
                    form.save()
                    
                    # Update workflow with skills assessment score
                    workflow_service.update_skills_score(form.instance.employeename, totalpoints)

                    if userprof.section == "D":
                        return redirect("application:policies")
                    else:
                        #mail for going furthur in interview
                        subject = f"Congratulations! CODA Interview Next Section-{userprof.section}"
                        try:
                            send_email(category=request.user.category,
                                to_email=[request.user.email,],
                                subject=subject, 
                                html_template='email/application/FI_section.html',
                                context={
                                    'user': request.user,
                                    'company_name': 'coda',
                                    'previous_section': chr(ord(userprof.section.lower()) - 1).upper(),
                                    'next_section': userprof.section.upper()
                                    })
                        except Exception as e:
                            print(e)
                            pass
                        return redirect("application:section_"+userprof.section.lower()+"")
                else:
                    
                    user_section = userprof.section.lower()
                    if 'a' < user_section <= 'z':
                        
                        userprof.section =  chr(ord(user_section) - 1).upper()
                        userprof.save()
                        #feedback email
                        try:
                            send_email(category=request.user.category,
                                to_email=[request.user.email,],
                                subject=f"CODA Interview-{userprof.section} FeedBack", 
                                html_template='email/application/feedback.html',
                                context={
                                    'name': request.user,
                                    'company_name': 'coda',
                                    'topic': pk,
                                    'improvement_area': improvement_area,
                                    })
                        except Exception as e:
                            print(e)
                            pass
                        return redirect("application:section_"+userprof.section.lower()+"")
                    else:
                        return redirect("application:interview")
            # For One on one sessions adding task points and increasing mxpoint if it is equal or near to points.
            try:
                idval,point, mxpoint = Task.objects.values_list("id","point", "mxpoint").filter(
                    Q(activity_name="one on one sessions")
                    | Q(activity_name="One on one sessions")
                    | Q(activity_name="One On One Sessions")
                    | Q(activity_name="One On One")
                    | Q(activity_name="one on one"),
                    employee__username=form.instance.employeename,
                )[0]
                point = point + totalpoints
                if point >= mxpoint or point + 15 >= mxpoint:
                    mxpoint += 15
                
                Task.objects.filter(
                    Q(activity_name="one on one sessions")
                    | Q(activity_name="One on one sessions")
                    | Q(activity_name="One On One Sessions")
                    | Q(activity_name="One On One")
                    | Q(activity_name="one on one"),
                    employee__username=form.instance.employeename,
                ).update(point=point, mxpoint=mxpoint)
                        
                return redirect(
                            "management:new_evidence", taskid=idval
                        )
            except:
                form = RatingForm()
                return render(request, "application/orientation/rate.html", {"form": form,"error":True})
    else:
        form = RatingForm()
    return render(request, "application/orientation/rate.html", {"form": form})


def enter_score(request):
    if request.method == "POST":
        form = RatingForm(request.POST, request.FILES)
        print(form.errors)
        if form.is_valid():
            print("hello")
            print(form.instance.data_tools)
            form.save()
            return redirect("application:userscores", request.user )
    else:
        form = RatingForm()
    return render(request, "main/snippets_templates/generalform.html", {"form": form})

def rating(request):
    ratings = Rated.objects.all().order_by("-rating_date")

    context = {
        "ratings": ratings,
    }
    return render(request, "application/orientation/rating.html", context)


@login_required
def userscores(request, user=None, *args, **kwargs):
    request.session["siteurl"] = settings.SITEURL
    try:
        employee = get_object_or_404(User, username=kwargs.get("username"))
    except:
        context={
            "message":"User not allowed to access this page"
        }
        return render(request, "main/errors/generalerrors.html",context)
    
    user_ratings = Rated.objects.filter(employeename=employee)
    ratings = Rated.objects.all().order_by('-rating_date')

    scores_by_subject = {}

    total_scores = {}
    user_total_score=0

    for rating in user_ratings:
        employeename = rating.employeename.username
        type = rating.type
        topic = rating.topic
        totalpoints = rating.totalpoints

        # Check if the employeename is already in the dictionary, if not, initialize it with the totalpoints
        if employeename not in total_scores:
            total_scores[employeename] = totalpoints
        else:
        # If the employeename is already in the dictionary, add the totalpoints to the existing score
            total_scores[employeename] += totalpoints

        if employeename not in scores_by_subject:
            scores_by_subject[employeename] = {}

        if type not in scores_by_subject[employeename]:
            scores_by_subject[employeename][type] = {}

        scores_by_subject[employeename][type][topic] = totalpoints
        # Retrieve the total score for the specified user

        # Use 0 as the default value if the user doesn't exist
        user_total_score = total_scores.get(employeename, 0)  

    context = {
        'scores_by_subject': scores_by_subject,
        'total_score': total_scores,
        'user_total_score': user_total_score,
        'employeename': employee,
        'user_ratings': user_ratings,
        'ratings': ratings,
        "title": "Student Scores",
    }

    request.session["employee_name"] = kwargs.get("username")
    return render(request, "application/orientation/intermediary_training.html", context)


class ScoresUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Rated
    template_name = 'main/snippets_templates/generalform.html'
    form_class = RatingForm  # Assuming you have a RatingForm in forms.py

    # verify the user's permissions.
    def test_func(self):
        # Assuming every logged in user can update the score. 
        # Change this condition as per your requirement.
        return self.request.user.is_authenticated

    def get_success_url(self):
        # Adjust the reverse URL as per your URL configuration
        return reverse("application:userscores", args=[str(self.request.user)])

    def form_valid(self, form):
        # Any logic you want to apply when the form is valid
        # Example: Set some fields, log something, etc.
        return super().form_valid(form)


# -------------------------rating Section-------------------------------------#
def trainee(request):
    if request.method == "POST":
        form = ReportingForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("application:trainees")
    else:
        form = ReportingForm()
    return render(request, "application/orientation/trainee.html", {"form": form})


def trainees(request):
    trainees = Reporting.objects.all().order_by("-update_date")
    context={
        "trainees": trainees,
    }
    return render(request, "application/orientation/trainees.html",context)

class TraineeUpdateView(LoginRequiredMixin, UpdateView):
    model = Reporting
    fields = [
            "reporter",
            "name",
            "rate",
            "reporting_date",
            "method",
            "interview_type",
            "link",
            "comment",
    ]
    form = ReportingForm()

    def form_valid(self, form):
        form.instance.username = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("application:trainees")

    def test_func(self):
        employee = self.get_object()
        if self.request.firstname == employee.name:
            return True
        return False



class TraineeDeleteView(LoginRequiredMixin, DeleteView):
    model = Reporting

    def get_success_url(self):
        return reverse("application:trainees")
    
def training_assessment(request):
    if request.method == "POST":
        form = TraineeAssessmentForm(request.POST, request.FILES)
        print(form.errors)
        if form.is_valid():
            print("hello")
            print(form.instance.data_tools)
            form.save()
            return redirect("main:layout")
    else:
        form = TraineeAssessmentForm()
    return render(request, "main/snippets_templates/generalform.html", {"form": form})



class AssessmentListView(FilteredListViewMixin, ListView):
    model = Trainee_Assessment
    template_name = 'application/applications/trainingassessment.html'
    context_object_name = 'assessments'
    order_by = '-created_at'

# For creating a new Trainee_Assessment
class TraineeAssessmentCreateView(CreateView):
    model = Trainee_Assessment
    form_class = TraineeAssessmentForm
    template_name = 'main/snippets_templates/generalform.html'

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # Here you can add any additional processing before saving the object.
        return super().form_valid(form)

    def get_success_url(self):
        # Redirect to a success page of your choice
        return reverse('application:assessment_list')  # Replace with your view name or path

# For updating an existing Trainee_Assessment
class TraineeAssessmentUpdateView(UpdateView):
    model = Trainee_Assessment
    form_class = TraineeAssessmentForm
    template_name = 'main/snippets_templates/generalform.html'
    
    def get_object(self):
        # Override get_object to fetch the object based on the passed ID
        id_ = self.kwargs.get("id")
        return get_object_or_404(Trainee_Assessment, id=id_)

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # Here you can add any additional processing before saving the object.
        return super().form_valid(form)

    def get_success_url(self):
        # Redirect to a success page of your choice
        # return reverse('assessment_detail', kwargs={'id': self.object.id})  # Replace with your view name or path
        return reverse('application:assessment_list')  # Replace with your view name or path
