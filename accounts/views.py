from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse  # Added reverse import
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import string
import secrets
import uuid

from .models import CustomerUser, Membership, Account
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserForm, LoginForm, AccountForm
from .choices import CategoryChoices
from .utils import get_exchange_rate, send_verification_email
from django.contrib.auth import logout

# Define category fees directly here
CATEGORY_FEES = {
    1: 5000.00,   # ORDINARY_MEMBER
    2: 10000.00,  # ACTIVE_MEMBER
    3: 15000.00,  # EXECUTIVE_MEMBER
    4: 20000.00,  # FBO_ORDINARY
    5: 25000.00,  # ACTIVE_ORGANIZATION
    6: 30000.00,  # ROYAL_ORGANIZATION
}

# Member CRUD views
class MemberListView(ListView):
    model = CustomerUser
    template_name = 'accounts/member_list.html'
    context_object_name = 'members'

# Add missing CRUD view classes
class MemberCreateView(CreateView):
    model = CustomerUser
    form_class = UserForm  # or CustomUserCreationForm depending on your needs
    template_name = 'accounts/member_form.html'
    success_url = reverse_lazy('accounts:member-list')

class MemberUpdateView(UpdateView):
    model = CustomerUser
    form_class = UserForm
    template_name = 'accounts/member_form.html'
    success_url = reverse_lazy('accounts:member-list')

class MemberDeleteView(DeleteView):
    model = CustomerUser
    template_name = 'accounts/member_confirm_delete.html'
    success_url = reverse_lazy('accounts:member-list')

def home(request):
    return render(request, "main/home_templates/layout.html")

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
        # Get credentials directly from POST data
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Check if fields are empty
        if not username or not password:
            messages.error(request, "Please enter both username/email and password.")
            return render(request, 'accounts/registration/DC48K/logins.html')
        
        # Find user by username or email
        user_obj = None
        try:
            # Try to find by username first
            user_obj = CustomerUser.objects.filter(username=username).first()
            if not user_obj:
                # If not found, try email
                user_obj = CustomerUser.objects.filter(email__iexact=username).first()
        except Exception:
            pass
        
        if not user_obj:
            messages.error(request, "No account found with this username/email. Please register first.")
            return render(request, 'accounts/registration/DC48K/logins.html')
        
        # Authenticate user
        user = authenticate(request, username=user_obj.username, password=password)
        
        if user is None:
            messages.error(request, "Invalid password. Please try again.")
            return render(request, 'accounts/registration/DC48K/logins.html')
        
        # Check if user is active
        if not user.is_active:
            messages.error(request, "Your account is not activated.")
            return render(request, 'accounts/registration/DC48K/logins.html')
        
        # Login the user
        login(request, user)
        
        # Check membership status
        try:
            membership = Membership.objects.get(member=user)
            if membership.status == 'NOT_PAID':
                messages.info(request, "Please complete your payment to access all features.")
                return redirect('finance:pay')
            else:
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                return redirect('main:layout')
        except Membership.DoesNotExist:
            messages.warning(request, "Welcome! Please complete your membership registration.")
            return redirect('finance:pay')
    
    # For GET requests, show empty form
    return render(request, 'accounts/registration/DC48K/logins.html')
# Function to generate a random password
def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + "!@#$%&"
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password

def join(request):
    if request.method == "POST":
        # Check if user already exists
        email = request.POST.get("email")
        if CustomerUser.objects.filter(email=email).exists():
            messages.error(request, "User already exists with this email. Please login instead.")
            return redirect("accounts:account-login")
        
        # Create form with POST data
        form = UserForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data.get("category")
            
            # Set category flags
            user = form.save(commit=False)
            if category == CategoryChoices.ORDINARY_MEMBER:
                user.is_ordinary_member = True
            elif category == CategoryChoices.ACTIVE_MEMBER:
                user.is_active_member = True
            elif category == CategoryChoices.EXECUTIVE_MEMBER:
                user.is_executive_member = True
            elif category == CategoryChoices.FBO_ORDINARY:
                user.is_fbo_ordinary = True
            elif category == CategoryChoices.ACTIVE_ORGANIZATION:
                user.is_active_organization = True
            elif category == CategoryChoices.ROYAL_ORGANIZATION:
                user.is_royal_organization = True
            
            # Save user (password is already handled by form.save)
            user.is_active = True
            user.save()
            
            # Create membership
            fee_kes = CATEGORY_FEES.get(category, 0.0)
            fee_usd = fee_kes / get_exchange_rate('USD', 'KES')
            Membership.objects.create(
                member=user,
                fee=fee_usd,
                currency="USD",
                status='NOT_PAID',
            )
            
            messages.success(request, "Registration successful! Please login.")
            return redirect('accounts:account-login')
        else:
            # Keep the form with errors to display in template
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserForm()
    
    return render(request, "accounts/registration/DC48K/joins.html", {"form": form})

def email_verification_notice(request, user_id):
    user = get_object_or_404(CustomerUser, id=user_id)
    messages.success(request, f"A verification email has been sent to {user.email}.")
    return render(request, 'accounts/registration/email_verification_notice.html', {'user': user})

def verify_email(request, token):
    try:
        user = get_object_or_404(CustomerUser, verification_token=token)
        if user.email_verified == True:
            print('email already verified')
            return render(request, "accounts/registration/email_verification_notice.html", {
                "verification_status": "already_verified",
                "user": user,
                "redirect_url": "/finance/pay/"
            })
        else:    
            user.email_verified = True
            user.is_active = True
            user.save()
            return render(request, "accounts/registration/email_verification_notice.html", {
                "verification_status": "success",
                "redirect_url": "/finance/pay/"
            })
    except CustomerUser.DoesNotExist:
        return render(request, "accounts/registration/email_verification_notice.html", {
            "verification_status": "failed"
        })

def login_view(request):
    form = LoginForm(request.POST or None)
    msg = None

    if request.method == 'GET':
        sociallogin = request.session.pop("socialaccount_sociallogin", None)
        if sociallogin is not None:
            msg = 'Error with social login. Check your credentials or try to sign up manually.'

    if request.method == "POST":
        if form.is_valid():
            print('Form is valid')
            request.session["siteurl"] = settings.SITEURL
            
            username_or_email = form.cleaned_data.get("enter_your_username_or_email")
            enter_your_password = form.cleaned_data.get("enter_your_password")
            print(f'Username or Email: {username_or_email}')
            
            user = authenticate(request, username=username_or_email, password=enter_your_password)
            
            if user is None:
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

                membership = get_object_or_404(Membership, member=user)
                if membership.status == 'NOT_PAID':
                    return redirect('finance:pay')
                else:
                    return redirect('main:layout')
            else:
                print('Authentication failed')
                msg = 'Invalid credentials'
        else:
            print('Form is invalid')
            msg = 'Error validating the form'

    return render(request, "accounts/registration/DC48K/login_page.html", {"form": form, "msg": msg})


def logout_view(request):
    logout(request)
    try:
        request.session.flush()
    except Exception:
        pass
    response = redirect('main:layout')
    try:
        from django.conf import settings
        response.delete_cookie(settings.SESSION_COOKIE_NAME)
    except Exception:
        pass
    return response

@login_required
def userlist(request):
    users = CustomerUser.objects.filter(transaction_sender__amount__gte=5000).distinct()
    template_name = "accounts/admin/processing_users.html"
    context = {
        "users": users,
    }
    if request.user.is_superuser:
        return render(request, template_name, context)
    else:
        return redirect("main:layout")

@login_required
def users(request):
    users = CustomerUser.objects.filter(is_active=True).order_by("-date_joined")
    template_name = "accounts/admin/adminpage.html"
    context = {
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
        Membership.objects.create(
            member=new_user,
            fee=fee_usd,
            currency="USD",
            status='NOT_PAID',
        )
        print(f"Membership created for user {new_user.username} with fee {fee_usd} USD")

        if existing_user:
            membership = Membership.objects.filter(member=existing_user).first()
            if membership and membership.status == 'NOT_PAID':
                print(f"User {existing_user.username} has unpaid membership. Redirecting to payment.")
                sociallogin.state['next'] = reverse('finance:pay')
            else:
                print('not a member')
        else:
            membership = Membership.objects.filter(member=new_user).first()
            if membership and membership.status == 'NOT_PAID':
                print(f"User {new_user.username} has unpaid membership. Redirecting to payment.")
                sociallogin.state['next'] = reverse('finance:pay')
            else:
                print('not a member')

def custom_social_login(request):   
    try:
        category = request.GET.get('category')
        if category is not None:
            request.session['category'] = request.GET.get('category')

        social_login_url = reverse('google_login')
        
        if request.GET.get('socialPlatform'):
            social_login_url = reverse(request.GET.get('socialPlatform'))

        return redirect(social_login_url)
    except:
        return render(request, "accounts/registration/join.html", {"form": UserForm()})

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

def membership_registration(request):
    """
    View for membership registration
    This matches the URL pattern in accounts/urls.py
    """
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
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
            
            password = generate_random_password()
            token = str(uuid.uuid4())
            
            user = form.save(commit=False)
            user.verification_token = token
            user.set_password(password)
            user.is_active = False
            user.save()
            
            fee_kes = CATEGORY_FEES.get(category, 0.0)
            fee_usd = fee_kes / get_exchange_rate('USD', 'KES')
            
            Membership.objects.create(
                member=user,
                fee=fee_usd,
                currency="USD",
                status='NOT_PAID',
            )
            
            send_verification_email(user, password=password)
            
            messages.success(request, f"Registration successful! Please check your email for verification.")
            return redirect('accounts:member-list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserForm()
    
    return render(request, 'accounts/membership_registration.html', {'form': form})