import math
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.utils.decorators import method_decorator
from .forms import UserForm, LoginForm
from coda_project import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .models import CustomerUser,Tracker
from .utils import agreement_data
from application.models import UserProfile,Assets
from .utils import generate_random_password
from django.contrib.admin.views.decorators import staff_member_required 

from.forms import Trackerform

from django.urls import reverse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from django.http import HttpResponseRedirect
from django.utils import timezone
from accounts.choices import CategoryChoices
# Create your views here..

# @allowed_users(allowed_roles=['admin'])
def home(request):
    return render(request, "main/home_templates/newlayout.html")


# @allowed_users(allowed_roles=['admin'])
def thank(request):
    return render(request, "accounts/clients/thank.html")


# ---------------ACCOUNTS VIEWS----------------------

def join(request):
    form = UserForm()  # Define form variable with initial value
    if request.method == "POST":
        previous_user = CustomerUser.objects.filter(email=request.POST.get("email"))
        if len(previous_user) > 0:
            messages.success(request, f'User already exists with this email')
            return redirect("/password-reset")
        else:
            contract_data, contract_date = agreement_data(request)
            form = UserForm(request.POST)  # Assign form with request.POST data
            if form.is_valid():
                form.save()
                return redirect('accounts:account-login')
    else:
        msg = "error validating form"
        print(msg)
    return render(request, "accounts/registration/coda/join.html", {"form": form})


# ---------------ACCOUNTS VIEWS----------------------
def create_profile():
    users = CustomerUser.objects.filter(profile=None)
    assets = Assets.objects.all()
    # print(assets)
    if not assets:
        Assets.objects.create(
            name='default',
            category='default',
            description='default',
            image_url='default',
        )
    for user in users:
        UserProfile.objects.create(user=user)


def login_view(request):
    form = LoginForm(request.POST or None)
    msg = None

    #when error occur while login/signup with social account, we are redirecting it to login page of website
    if request.method == 'GET':
        sociallogin = request.session.pop("socialaccount_sociallogin", None)
        
        if sociallogin is not None:
            msg = 'Error with social login. check your credential or try to sing up manually.'
    
    if request.method == "POST":
        if form.is_valid():
            request.session["siteurl"] = settings.SITEURL
            username_or_email = form.cleaned_data.get("enter_your_username_or_email")
            enter_your_password = form.cleaned_data.get("enter_your_password")
            account = authenticate(username=username_or_email, password=enter_your_password)
            create_profile()
            # If Category is Staff/employee
            if account is not None and account.category == CategoryChoices.Coda_Staff_Member:
                if account.is_staff and not account.is_employee_contract_signed:
                    login(request, account)
                    return redirect('main:layout')
                
                else:  # parttime (agents) & Fulltime
                    login(request, account)
                    return redirect('main:layout')

            # If Category is client/customer:# Student # Job Support
            elif account is not None and (account.category == CategoryChoices.Jobsupport or account.category == CategoryChoices.Student) :
                login(request, account)
                # if Payment_History.objects.filter(customer=account).exists():
                return redirect('main:layout')
            
            elif account is not None and (account.category == CategoryChoices.investor) :
                login(request, account)
                print("category,subcat",account.category,account.sub_category)
                # url = reverse('management:meetings', kwargs={'status': 'company'})
                return redirect('main:layout')
        
            elif account is not None and account.profile.section is not None and account.category == CategoryChoices.Job_Applicant:
              
                if account.profile.section == "A":
                    login(request, account)
                    return redirect('main:layout')
                elif account.profile.section == "B":
                    login(request, account)
                    return redirect('main:layout')
                elif account.profile.section == "C":
                    login(request, account)
                    return redirect('main:layout')
                else:
                    login(request, account)
                    return redirect('main:layout')

            elif account is not None and account.profile.section is not None and account.category == CategoryChoices.Job_Applicant and account.sub_category==0:
                login(request, account)
                # print("account.category",account.sub_category)
                return redirect('main:layout')
            
            elif account is not None and account.category == CategoryChoices.General_User:
                login(request, account)
                return redirect('main:layout')

            elif account is not None and account.is_admin:
                login(request, account)
                # return redirect('main:layout')
                return redirect('main:layout')
            else:
                # messages.success(request, f"Invalid credentials.Kindly Try again!!")
                msg=f"Invalid credentials.Kindly Try again!!"
                return render(
                        request, "accounts/registration/login_page.html", {"form": form, "msg": msg}
                    )
    return render(
        request, "accounts/registration/login_page.html", {"form": form, "msg": msg}
    )

def PasswordResetCompleteView(request):
    return render(request, "accounts/registration/password_reset_complete.html")


@login_required(login_url="accounts:account-login")
def profile(request):
    return render(request, "accounts/profile.html")


#custom adaptor for updating user object for category and subcategory field  
class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        
        print('inside pre social login')
        # Check if the user with the given email already exists in your custom User model
        user = sociallogin.user
        email = user.email
        existing_user = CustomerUser.objects.filter(email=email).first()
        category = request.session.get('category')
      
        if existing_user:
            print('existing user')
            # Link the social login to the existing user
            sociallogin.connect(request, existing_user)
        
        elif existing_user is None and category is None:
            redirect_url = reverse("accounts:join")  # Replace with your desired URL
            response = HttpResponseRedirect(redirect_url)
            raise ImmediateHttpResponse(response)
        
        else:
            print('inside else')
            
            # If the user doesn't exist, create a new user
            sociallogin.save(request, connect=False)
            
            existing_user = sociallogin.user
            existing_user.category = request.session.pop('category', default=None)
            existing_user.sub_category = request.session.pop('subcategory', default=None)
            if existing_user.email:
                existing_user.username = existing_user.email
                
            if existing_user.category == '2':
                existing_user.is_staff = True
                existing_user.category = int(existing_user.category)
                existing_user.sub_category = int(existing_user.sub_category)
            elif existing_user.category == '3' or existing_user.category == '4':
                existing_user.is_client = True
                existing_user.category = int(existing_user.category)
                existing_user.sub_category = int(existing_user.sub_category)
            else:
                existing_user.is_applicant = True
                existing_user.category = int(existing_user.category)
                existing_user.sub_category = int(existing_user.sub_category)

            existing_user.save()
            create_profile()
        
        # If Category is Staff/employee
        if existing_user is not None and existing_user.category == 2:
            if existing_user.is_staff and not existing_user.is_employee_contract_signed:
                
                sociallogin.state['next'] = reverse('main:layout')
            
            else:  # parttime (agents) & Fulltime
                
                sociallogin.state['next'] = reverse('main:layout')

        # If Category is client/customer:# Student # Job Support
        elif existing_user is not None and (existing_user.category == 3 or existing_user.category == 4) :
            
            sociallogin.state['next'] = reverse('main:layout')
        
        elif existing_user is not None and (existing_user.category == 5) :
            
            sociallogin.state['next'] = reverse('main:layout')
        
        elif existing_user is not None and existing_user.profile.section is not None and existing_user.category == 1 and existing_user.sub_category==0:

                sociallogin.state['next'] = reverse('main:layout')
        
        elif existing_user is not None and existing_user.is_admin:
            
            sociallogin.state['next'] = reverse('main:layout')
        
        else:
            sociallogin.state['next'] = reverse('main:layout')  # Redirect to your success page or handle as needed
 

def custom_social_login(request):   

    try:
        category = request.GET.get('category')
        subcategory = request.GET.get('subcategory')

        if category is not None and subcategory is not None:
            request.session['category'] = request.GET.get('category')
            request.session['subcategory'] = request.GET.get('subcategory')

        # Redirect to the built-in Google login view with the state parameter
        social_login_url = reverse('google_login')  # Use the name of the built-in Google login view
        
        if request.GET.get('socialPlatform'):
       
            social_login_url = reverse(request.GET.get('socialPlatform'))  # Use the name of the built-in Google login view

        return redirect(social_login_url)
    
    except:
    
        return render(request, "accounts/registration/coda/join.html", {"form": UserForm()})










@staff_member_required
def Tracker_list(request):    
    Trackers = Tracker.objects.all()
    return render(request, "accounts/admin/tracker_list.html", {"Trackers": Trackers})
# accounts/views.py


@staff_member_required
def Tracker_create(request):
    if request.method == 'POST':
        form = Trackerform(request.POST)
        if form.is_valid():
            new_tracker = form.save(commit=False)
            
            # This logic is essential for the test to pass:
            if not new_tracker.employee:
                new_tracker.employee = request.user.username
            
            new_tracker.save()
            
            messages.success(request, 'Record created successfully!')
            return redirect('accounts:account-Tracker_list')
    else:
        form = Trackerform()
    
    return render(request, "accounts/admin/tracker_create.html", {"form": form})



@staff_member_required
def Tracker_update(request,pk):
    Trackers=get_object_or_404(Tracker,pk=pk)
    if request.method =='POST':
        form=Trackerform(request.POST,instance=Trackers)
        if form.is_valid():
            form.save()
            messages.success(request, 'Record update successfully!')
            return redirect('accounts:account-Tracker_list')
    else:
        form= Trackerform(instance=Trackers) 
    return render(request, "accounts/admin/tracker_update.html", {"form": form})        


