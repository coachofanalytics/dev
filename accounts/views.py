from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import CustomerUser, Membership
# Member CRUD views
class MemberListView(ListView):
    model = CustomerUser
    template_name = 'accounts/member_list.html'
    context_object_name = 'members'

class MemberCreateView(CreateView):
    model = CustomerUser
    fields = ['username', 'email', 'first_name', 'last_name']
    template_name = 'accounts/member_form.html'
    success_url = reverse_lazy('accounts:member-list')

class MemberUpdateView(UpdateView):
    model = CustomerUser
    fields = ['username', 'email', 'first_name', 'last_name']
    template_name = 'accounts/member_form.html'
    success_url = reverse_lazy('accounts:member-list')

class MemberDeleteView(DeleteView):
    model = CustomerUser
    template_name = 'accounts/member_confirm_delete.html'
    context_object_name = 'member'
    success_url = reverse_lazy('accounts:member-list')
import secrets
import uuid
import string, random
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from flask import request
from accounts.choices import CategoryChoices
from accounts.utils import CATEGORY_FEES, convert_kes_to_usd, get_exchange_rate, send_verification_email
from coda_project import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpRequest
from django.contrib.auth.views import LoginView
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from .models import Account, CustomerUser, Membership
from .forms import AccountForm, CustomAuthenticationForm, CustomUserCreationForm, UserForm,LoginForm
from finance.utils import DYCDefaultPayments
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, get_user_model

from .forms import MembershipRegistrationForm

def membership_registration(request):
    if request.method == 'POST':
        form = MembershipRegistrationForm(request.POST)
        if form.is_valid():
            # Extract cleaned data
            data = form.cleaned_data
            # Here you can create a new CustomerUser or Membership as needed
            # Example: create a new CustomerUser (if you want to register a user)
            # user = CustomerUser.objects.create(
            #     email=data['email'],
            #     first_name=data['first_name'],
            #     last_name=data['last_name'],
            #     ...
            # )
            # Or just show a success page for now
            return render(request, 'accounts/membership_sucess.html', {'data': data})
        # If form is not valid, fall through to re-render with errors
    else:
        form = MembershipRegistrationForm()
    return render(request, 'accounts/membership_registration.html', {'form': form})
 


# Create your views here..


# path_values
# path_val,sub_title=path_values(request)

# @allowed_users(allowed_roles=['admin'])
def home(request):
    return render(request, "main/home_templates/layout.html")


# @allowed_users(allowed_roles=['admin'])
def thank(request):
    return render(request, "accounts/clients/thank.html")


# ---------------ACCOUNTS VIEWS----------------------
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts:member-list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/registration/DC48K/registers.html', {'form': form})

def custom_login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('main:layout')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'accounts/registration/DC48K/logins.html', {'form': form})


# Function to generate a random password
def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + "!@#$%&"
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password

def join(request):
    form = UserForm()  # Define form variable with initial value
    if request.method == "POST":
        previous_user = CustomerUser.objects.filter(email=request.POST.get("email"))
        if previous_user.exists():
            messages.success(request, "User already exists with this email")
            return redirect("/password-reset")
        else:
            form = UserForm(request.POST)  # Assign form with request.POST data
            if form.is_valid():
                # Check the selected category and update the form instance accordingly
                category = form.cleaned_data.get("category")
                if category == CategoryChoices.ORDINARY_MEMBER:
                    form.instance.is_ordinary_member = True
                elif category == CategoryChoices.ACTIVE_MEMBER:
                    form.instance.is_active_member = True
                elif category == CategoryChoices.EXECUTIVE_MEMBER:
                    form.instance.is_executive_member = True
                elif category == CategoryChoices.FBO_ORDINARY:
                    form.instance.is_fbo_ordinary = True
                elif category == CategoryChoices.ACTIVE_ORGANIZATION:
                    form.instance.is_active_organization = True
                elif category == CategoryChoices.ROYAL_ORGANIZATION:
                    form.instance.is_royal_organization = True

                # Generate a random password
                password = generate_random_password()
                print(password)

                # Save the password and username
                token = str(uuid.uuid4())

                user = form.save(commit=False)
                user.verification_token = token
                user.set_password(password) 
                user.is_active = False  # Set the generated password
                user.save()
                print(category)
                fee_kes = CATEGORY_FEES.get(category, 0.0)
                fee_usd = fee_kes / get_exchange_rate('USD', 'KES')  # Convert to USD
                membership = Membership.objects.create(
                    member=user,
                    fee=fee_usd,
                    currency="USD",  # Store in USD
                    status='NOT_PAID',
                )
                print(f"Membership created for user {user.username} with fee {fee_usd} USD")
                print(f"User {user.username} created and saved. Account is inactive until verification.")
                send_verification_email(user, password=password)
                # Redirect to member list after registration
                return redirect('accounts:member-list')
            else:
                msg = "Error validating form"
                print(msg)
    return render(request, "accounts/registration/DC48K/joins.html", {"form": form})

def email_verification_notice(request, user_id):
    user = get_object_or_404(CustomerUser, id=user_id)
    messages.success(request, f"A verification email has been sent to {user.email}.")

    return render(request, 'accounts/registration/email_verification_notice.html', {'user': user})
def verify_email(request, token):
    try:
        # Attempt to find the user by the verification token
        user = get_object_or_404(CustomerUser, verification_token=token)
        if user.email_verified ==True:
            print('email already verified')
            return render(request, "accounts/registration/email_verification_notice.html", {
                "verification_status": "already_verified",
                "user": user,
                "redirect_url": "/finance/pay/"
            })
        else:    
        
            # If the user is found, verify the email
            user.email_verified = True
            user.is_active = True  # Activate the account
            user.save()
            
            # Render the success message
            return render(request, "accounts/registration/email_verification_notice.html", {"verification_status": "success","redirect_url": "/finance/pay/"})
        
    except CustomerUser.DoesNotExist:
        # If the user doesn't exist, render the failure message
        return render(request, "accounts/registration/email_verification_notice.html", {"verification_status": "failed"})

from django.contrib.auth import authenticate, login, get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from .forms import LoginForm
from .models import Membership  # Replace with the actual import path for Membership

def login_view(request):
    form = LoginForm(request.POST or None)
    msg = None
   

    # Handle social loginpage errors on GET requests
    if request.method == 'GET':
        sociallogin = request.session.pop("socialaccount_sociallogin", None)
        if sociallogin is not None:
            msg = 'Error with social login. Check your credentials or try to sign up manually.'

    if request.method == "POST":
        if form.is_valid():
            print('Form is valid')
            request.session["siteurl"] = settings.SITEURL
            
            # Get form data
            username_or_email = form.cleaned_data.get("enter_your_username_or_email")
            enter_your_password = form.cleaned_data.get("enter_your_password")
            print(f'Username or Email: {username_or_email}')
            print(f'Password: {enter_your_password}')  # Note: Avoid logging sensitive info in production
            
            # Attempt authentication with username
            user = authenticate(request, username=username_or_email, password=enter_your_password)
            
            if user is None:
                # If username authentication fails, attempt email-based authentication
                UserModel = get_user_model()
                try:
                    user_obj = UserModel.objects.get(email__iexact=username_or_email)
                    print(f'User found with email: {user_obj.email}')
                    user = authenticate(request, username=user_obj.username, password=enter_your_password)
                except UserModel.DoesNotExist:
                    print(f'No user found with email: {username_or_email}')
            
            if user:
                print('User authenticated successfully')
                login(request, user)

                # Membership check
                membership = get_object_or_404(Membership, member=user)
                if membership.status == 'NOT_PAID':
                    return redirect('finance:pay')
                else:
                    return redirect('https://dc48k.org/')
            else:
                print('Authentication failed')
                msg = 'Invalid credentials'
        else:
            print('Form is invalid')
            msg = 'Error validating the form'

    # Render the login page with the form and any messages
    return render(request, "accounts/registration/DC48K/login_page.html", {"form": form, "msg": msg})



@login_required
def userlist(request):
    users = CustomerUser.objects.filter(transaction_sender__amount__gte=5000).distinct()
    template_name = "accounts/admin/processing_users.html"

    context={
        "users": users,
    }
    if request.user.is_superuser:
        return render(request, template_name, context)
    else:
        return redirect("main:layout")
    

@login_required
def users(request):
    users = CustomerUser.objects.filter(is_active=True).order_by("-date_joined")
    template_name="accounts/admin/adminpage.html"
    context={
        "users": users,
    }

    if request.user.is_superuser:
        return render(request, template_name, context)
    else:
        return redirect("main:layout")
    

def superuser_update_view(request, pk):
    user = get_object_or_404(CustomerUser, pk=pk)
    if not request.user.is_superuser:
        return redirect('main:layout')
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('/accounts/users')
    else:
        form = UserForm(instance=user)
    return render(request, 'accounts/admin/superuser_update.html', {'form': form, 'user': user})


def user_update_view(request, pk):
    user = get_object_or_404(CustomerUser, pk=pk)
    if not (request.user.is_superuser or request.user.is_admin):
        return redirect('main:layout')
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('/accounts/users')
    else:
        form = UserForm(instance=user)
    return render(request, 'accounts/admin/user_update.html', {'form': form, 'user': user})



def select_category(request):
    if request.method == "POST":
        selected_category = request.POST.get("category")
        if selected_category in [choice.value for choice in CategoryChoices]:
            request.session['category'] = selected_category
            return redirect("socialaccount_login", provider="google")
        else:
            messages.error(request, "Invalid category selected.")
    return render(request, "accounts/select_category.html")


from django.http import HttpResponseRedirect  
from django.http import HttpResponseRedirect  
def custom_social_account_adapter_pre_social_login(request, sociallogin):
    print('Inside pre_social_login')
    user = sociallogin.user
    email = user.email
    existing_user = CustomerUser.objects.filter(email=email).first()
    category = request.session.get('category')
    print(category)
    if existing_user:
        print('Existing user found. Connecting social account.')
        sociallogin.connect(request, existing_user)
    elif existing_user is None and category is None:
        print('No existing user and no category in session. Redirecting to category selection.')
    else:
        print('Creating a new user via social login.')
        sociallogin.save(request, connect=False)
        new_user = sociallogin.user
        selected_category = request.session.pop('category', None)
        print(selected_category)
        if selected_category == CategoryChoices.ORDINARY_MEMBER:
            new_user.is_ordinary_member = True
        elif selected_category == CategoryChoices.ACTIVE_MEMBER:
            new_user.is_active_member = True
        elif selected_category == CategoryChoices.EXECUTIVE_MEMBER:
            new_user.is_executive_member = True
        elif selected_category == CategoryChoices.FBO_ORDINARY:
            new_user.is_fbo_ordinary = True
        elif selected_category == CategoryChoices.ACTIVE_ORGANIZATION:
            new_user.is_active_organization = True
        elif selected_category == CategoryChoices.ROYAL_ORGANIZATION:
            new_user.is_royal_organization = True
        else:
            messages.error(request, "Invalid category selected.")
        if not new_user.username:
            new_user.username = new_user.email
        new_user.is_active = True
        new_user.verification_token = None
        new_user.save()
        cate = int(selected_category)
        fee_kes = CATEGORY_FEES.get(cate)
        print(fee_kes)
        fee_usd = fee_kes / get_exchange_rate('USD', 'KES')
        membership = Membership.objects.create(
            member=new_user,
            fee=fee_usd,
            currency="USD",
            status='NOT_PAID',
        )
        print(f"Membership created for user {new_user.username} with fee {fee_usd} USD")
            # self.send_welcome_email(new_user)


        # After obtaining the target_user (existing or new), check Membership status
        if existing_user:
            membership = Membership.objects.filter(member=existing_user).first()
            if membership and membership.status == 'NOT_PAID':
                print(f"User {existing_user.username} has unpaid membership. Redirecting to payment.")
                # Redirect to finance:pay with membership ID
                sociallogin.state['next'] = reverse('finance:pay')
            else:
                # Redirect based on user category
                print('not a member')


# allauth adapter shim: allauth expects a class at the path specified in settings
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Adapter shim that delegates to the module-level helper.

    allauth imports this class via the dotted path in settings. Implementing
    a thin adapter here keeps existing pre-social-login logic in
    `custom_social_account_adapter_pre_social_login` and avoids changing
    settings.
    """

    def pre_social_login(self, request, sociallogin):
        try:
            custom_social_account_adapter_pre_social_login(request, sociallogin)
        except Exception:
            # Avoid breaking login flow on adapter errors; let allauth proceed.
            pass
        else:
            membership = Membership.objects.filter(member=new_user).first()
            if membership and membership.status == 'NOT_PAID':
                print(f"User {new_user.username} has unpaid membership. Redirecting to payment.")
                # Redirect to finance:pay with membership ID
                sociallogin.state['next'] = reverse('finance:pay')
            else:
                # Redirect based on user category
                print('not a member')

def custom_social_login(request):   

    try:
        category = request.GET.get('category')

        if category is not None :
            request.session['category'] = request.GET.get('category')

        # Redirect to the built-in Google login view with the state parameter
        social_login_url = reverse('google_login')  # Use the name of the built-in Google login view
        
        if request.GET.get('socialPlatform'):
       
            social_login_url = reverse(request.GET.get('socialPlatform'))  # Use the name of the built-in Google login view

        return redirect(social_login_url)
    
    except:
    
        return render(request, "accounts/registration/join.html", {"form": UserForm()})
# account list view
def account_list(request):
    accounts = Account.objects.all().order_by('-created_at')
    return render(request, 'accounts/account_list.html', {'accounts': accounts})
def create_account(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('accounts:account_list')
    else:
        form = AccountForm()
    return render(request, 'accounts/create_account.html', {'form': form})
def account_details(request, pk):
    account = get_object_or_404(Account, pk=pk)
    return render(request, 'accounts/account_details.html', {'account': account})
