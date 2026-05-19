import math
import uuid
import logging

logger = logging.getLogger(__name__)
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, get_backends, authenticate, logout
from django.utils.decorators import method_decorator
from .forms import (
    UserForm,
    LoginForm,
    LoginHistoryForm,
    CredentialCategoryForm,
    CredentialForm,
)
from coda_project import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum, F, ExpressionWrapper, fields, Q
from django.utils.text import slugify
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from django.urls import reverse
from .models import (
    CustomerUser,
    LoginHistory,
    Tracker,
    CredentialCategory,
    Credential,
    Department,
    UserGroups,
)
from .utils import (
    employees,
    get_clients_time,
    JOB_SUPPORT_CATEGORIES,
    send_verification_email,
)
from .user_utils import get_redirect_url
from core.utils import generate_otp
from main.filters import CredentialFilter
from accounts.models import UserProfile
from main.models import Assets
from management.models import Task
from finance.models import Payment_History, Payment_Information
from mail.custom_email import send_email

# from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
# from allauth.core.exceptions import ImmediateHttpResponse

from django.http import HttpResponseRedirect
from accounts.choices import UserCategory as CategoryChoices

from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.http import Http404

from .mixins import FilteredListViewMixin

logger = logging.getLogger(__name__)


def email_verification_required(view_func):
    """
    Decorator to check if user has verified their email.
    Redirects to email verification notice if not verified.
    """

    def wrapper(request, *args, **kwargs):
        # Email verification check - handled by allauth settings
        if request.user.is_authenticated and not request.user.email_verified:
            logger.warning(
                f"User {request.user.email} attempted to access protected view without email verification"
            )
            return redirect(
                "accounts:email-verification-notice", user_id=request.user.id
            )
        return view_func(request, *args, **kwargs)

    return wrapper


def home(request):
    return render(request, "main/home_templates/newlayout.html")


def thank(request):
    return render(request, "accounts/clients/thank.html")


def join(request):
    logger.debug("=" * 50)
    logger.debug("🔍 DEBUG: join function called")
    logger.debug(f"🔍 DEBUG: request.method = {request.method}")
    logger.debug(f"🔍 DEBUG: request.user = {request.user}")
    logger.debug(
        f"🔍 DEBUG: request.POST = {dict(request.POST) if request.method == 'POST' else 'N/A'}"
    )
    logger.debug("=" * 50)

    form = UserForm()

    if request.method == "POST":
        logger.debug("🔍 DEBUG: Processing POST request")
        email = request.POST.get("email")
        logger.debug(f"🔍 DEBUG: Email = {email}")

        if CustomerUser.objects.filter(email=email).exists():
            logger.debug("🔍 DEBUG: User already exists with this email")
            messages.warning(request, "User already exists with this email")
            return redirect("/password-reset")

        # Update subcategory choices based on selected category BEFORE form validation
        category_id = request.POST.get("category")
        sub_category_id = request.POST.get("sub_category")
        logger.debug(f"🔍 DEBUG: Category = {category_id}, Sub Category = {sub_category_id}")

        form = UserForm(request.POST)

        if category_id:
            logger.debug(f"🔍 DEBUG: Updating subcategory choices for category {category_id}")
            form.update_subcategory_choices(category_id)
        logger.debug(f"🔍 DEBUG: Form is_valid = {form.is_valid()}")

        if form.is_valid():
            logger.debug("🔍 DEBUG: Form is valid, creating user")
            user = form.save(commit=False)
            user.username = user.email
            user.set_password(form.cleaned_data["password2"])

            # Generate verification token
            token = str(uuid.uuid4())
            user.verification_token = token
            
            # User activation handled by allauth settings based on environment
            # In development/testing: allauth will auto-verify
            # In production: allauth will require email verification

            logger.debug("🔍 DEBUG: User details before save:")
            logger.debug(f"  Username: {user.username}")
            logger.debug(f"  Email: {user.email}")
            logger.debug(f"  Category: {user.category}")
            logger.debug(f"  Sub Category: {user.sub_category}")
            logger.debug(f"  First Name: {user.first_name}")
            logger.debug(f"  Last Name: {user.last_name}")
            logger.debug(f"  Is Active: {user.is_active}")
            logger.debug(f"  Email Verified: {user.email_verified}")
            logger.debug(f"  Verification Token: {user.verification_token}")

            # Save user with all fields including category and sub_category
            user.save()
            logger.debug(f"🔍 DEBUG: User saved successfully with ID: {user.id}")

            # Email verification handled by allauth settings
            # In development/testing: allauth will auto-verify
            # In production: allauth will require email verification
            logger.debug("🔍 DEBUG: User registration complete, redirecting to dashboard")

            try: 
                email_sent = send_verification_email(request=request, user=user)
                if email_sent:
                    logger.info(f'Verification email sent to {user.email}')
                    messages.success(
                        request,
                        f'A verification email has been sent to {user.email}. Please check your inbox.'
                    )
                else:
                    logger.warning(f'Email function returned False for {user.email}')
                    messages.warning(
                        request,
                        'Account created, but verification email could not be sent. Please check your email settings.'
                    )
            except Exception as e:
                logger.error(f'Exception while sending verification email: {e}', exc_info=True)
                messages.warning(
                    request,
                    'Account created, but verification email could not be sent.'
                )


            return redirect(get_redirect_url(user))

        else:
            # Log form errors for debugging
            logger.debug(f"🔍 DEBUG: Form validation failed: {form.errors}")
            logger.error(f"Form validation failed: {form.errors}")

    # Force logout any existing user before registration
    if request.user.is_authenticated:
        logger.debug(f"🔍 DEBUG: Force logging out existing user {request.user.username}")
        logout(request)
        logger.info(
            f"Force logged out existing user {request.user.username} before registration"
        )
        messages.info(
            request,
            "You have been logged out. Please complete the registration process.",
        )

    # Get choices data for JavaScript
    logger.debug("🔍 DEBUG: Getting choices data for JavaScript")
    choices_data = form.get_choices_data()
    logger.debug(
        f"🔍 DEBUG: Choices data keys: {list(choices_data.keys()) if choices_data else 'None'}"
    )

    logger.debug("🔍 DEBUG: Rendering registration template")
    return render(
        request,
        "accounts/registration/join.html",
        {"form": form, "choices_data": choices_data},
    )


def email_verification_notice(request, user_id):
    user = get_object_or_404(CustomerUser, id=user_id)

    # Force logout any existing user to ensure proper verification flow
    if request.user.is_authenticated:
        from django.contrib.auth import logout

        logout(request)
        logger.info(
            f"Force logged out existing user {request.user.username} for email verification flow"
        )

    messages.success(request, f"A verification email has been sent to {user.email}.")

    return render(
        request, "accounts/registration/email_verification_notice.html", {"user": user}
    )


def populate_verification_tokens():
    results = []

    for user in CustomerUser.objects.filter(verification_token__isnull=True):
        old_token = user.verification_token
        new_token = str(uuid.uuid4())
        user.verification_token = new_token
        user.save()
        results.append(
            {
                "user_id": user.id,
                "old_token": old_token,
                "new_token": new_token,
                "status": "Token generated" if old_token is None else "Token replaced",
            }
        )

    return results


def populate_tokens_view(request):
    results = populate_verification_tokens()
    return render(request, "populate_tokens_results.html", {"results": results})


def verify_email(request, token):
    try:
        # Attempt to find the user by the verification token
        user = get_object_or_404(CustomerUser, verification_token=token)

        logger.info(f"Email verification attempt for user: {user.email}")
        logger.info(
            f"Current status - email_verified: {user.email_verified}, is_active: {user.is_active}"
        )

        if user.email_verified == True:
            logger.info(
                f"User {user.email} is already verified, showing already_verified message"
            )
            return render(
                request,
                "accounts/registration/email_verification_notice.html",
                {"verification_status": "already_verified", "user": user},
            )
        else:
            logger.info(f"Verifying user {user.email}...")
            # If the user is found, verify the email
            user.email_verified = True
            user.is_active = True  # Activate the account
            user.save()

            logger.info(f"User {user.email} verified successfully")

            # Check if this is a guarantor verification
            loan_id = request.GET.get("loan_id")
            if loan_id:
                try:
                    from finance.models import LoanApplication

                    loan_app = LoanApplication.objects.get(id=loan_id, guarantor=user)

                    # Send verification success email for guarantor
                    try:
                        from finance.utils import (
                            send_guarantor_verification_success_email,
                        )

                        send_guarantor_verification_success_email(loan_app, user)
                    except Exception as e:
                        logger.error(
                            f"Failed to send guarantor verification success email: {e}"
                        )

                    # Redirect to guarantor approval page
                    return redirect("finance:guarantor-approve-loan", loan_id=loan_id)
                except LoanApplication.DoesNotExist:
                    logger.warning(
                        f"No loan application found for guarantor {user.email} with loan_id {loan_id}"
                    )

            # Create user profile if it doesn't exist
            create_profile()

            # Automatically log in the user
            backend = get_backends()[0]
            user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
            login(request, user)

            logger.info(
                f"User {user.email} logged in automatically, redirecting to management:meetings"
            )

            # Redirect to management meetings page
            redirect_url = reverse("management:meetings", kwargs={"status": "company"})
            logger.info(f"Redirect URL generated: {redirect_url}")

            response = redirect("management:meetings", "company")
            logger.info(f"Redirect response created: {response}")
            logger.info(f"Redirect response URL: {response.url}")

            return response

    except CustomerUser.DoesNotExist:
        logger.error(f"Verification failed: User not found for token {token}")
        # If the user doesn't exist, render the failure message
        return render(
            request,
            "accounts/registration/email_verification_notice.html",
            {"verification_status": "failed"},
        )


def create_profile():
    users = CustomerUser.objects.filter(profile=None)
    assets = Assets.objects.all()
    if not assets:
        Assets.objects.create(
            name="default",
            category="default",
            description="default",
            image_url="default",
        )
    for user in users:
        UserProfile.objects.create(user=user)


def Usergroup():
    categories = CategoryChoices
    for category in categories:
        user = CustomerUser.objects.filter(category=category).order_by("date_joined")
        paginator = Paginator(user, 30)
        for page in paginator.page_range:
            group_name = (
                f"{slugify(dict(CategoryChoices.choices)[category])} Group {page}"
            )
            user_group, created = UserGroups.objects.get_or_create(
                name=group_name, defaults={"is_active": True, "is_featured": True}
            )
            # Add users to this group
            user_group.users.add(*paginator.page(page).object_list)
            user_group.save()


def login_view(request):
    form = LoginForm(request.POST or None)
    msg = None

    # Handle social login error
    if request.method == "GET":
        if request.session.pop("socialaccount_sociallogin", None):
            msg = "Error with social login. Check your credentials or try to sign up manually."

    if request.method == "POST":
        try:
            user = None  # Initialize user variable

            # Handle One-Time Code (OTP) Login
            otp_entered = request.POST.get("otp")
            stored_otp = request.session.get(
                "security_otp"
            )  # Get OTP stored in session
            username_or_email = request.session.get("email")

            if otp_entered == stored_otp and username_or_email:
                user = CustomerUser.objects.filter(email=username_or_email).first()
                if user:
                    backend = get_backends()[0]
                    user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
                    login(request, user)

                    # Redirect to unified dashboard
                    return redirect("dashboard:unified_dashboard")

            # Handle Username/Password Login
            elif form.is_valid():
                request.session["siteurl"] = settings.SITEURL
                username_or_email = form.cleaned_data.get(
                    "enter_your_username_or_email"
                )
                enter_your_password = form.cleaned_data.get("enter_your_password")
                user = authenticate(
                    username=username_or_email, password=enter_your_password
                )

                if user is not None:
                    # User authenticated successfully
                    create_profile()
                    login(request, user)
                    # Redirect to unified dashboard
                    return redirect("dashboard:unified_dashboard")
                else:
                    # Authentication failed
                    msg = "Invalid username/email or password. Please try again."
                    logger.warning(
                        f"Login failed: Invalid credentials for {username_or_email}"
                    )

            # Clear session data after login
            request.session.flush()

        except CustomerUser.DoesNotExist:
            msg = "User does not exist. Please check your email or sign up."
            logger.warning(f"Login failed: User {username_or_email} does not exist.")

        except Exception as e:
            msg = "An unexpected error occurred. Please try again later."
            logger.error(f"Unexpected login error: {str(e)}")

    return render(
        request, "accounts/registration/login_page.html", {"form": form, "msg": msg}
    )


def users(request):
    if request.user.is_superuser:
        # Redirect to Django Admin user list
        return redirect("admin:accounts_customeruser_changelist")
    else:
        return redirect("main:layout")


class SuperuserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CustomerUser
    success_url = "/accounts/users"
    # fields=['category','address','city','state','country']
    fields = [
        "category",
        "sub_category",
        "first_name",
        "last_name",
        "username",
        "date_joined",
        "email",
        "gender",
        "phone",
        "address",
        "city",
        "state",
        "country",
        "zipcode",
        "is_superuser",
        "is_admin",
        "is_active",
        "is_staff",
    ]

    def form_valid(self, form):
        # form.instance.username=self.request.user
        # if request.user.is_authenticated:
        if self.request.user.is_superuser or self.request.user.is_admin:
            return super().form_valid(form)
        #  elif self.request.user.is_authenticated:
        #      return super().form_valid(form)
        return False

    def test_func(self):
        user = self.get_object()
        # if self.request.user == client.username:
        #     return True
        if (
            self.request.user.is_superuser or self.request.user.is_admin
        ):  # or self.request.user == user.username:
            return True
        return False


class UserProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = UserProfile
    success_url = "/accounts/users"
    fields = "__all__"

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            return super().form_valid(form)
        return False

    def test_func(self):
        if self.request.user.is_authenticated:
            return True
        return False


class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CustomerUser
    success_url = "/accounts/users"
    fields = [
        "category",
        "sub_category",
        "first_name",
        "last_name",
        "date_joined",
        "email",
        "gender",
        "phone",
        "address",
        "city",
        "state",
        "country",
        "is_admin",
        "is_staff",
    ]

    def form_valid(self, form):
        if self.request.user.is_superuser or self.request.user.is_admin:
            return super().form_valid(form)
        return False

    def test_func(self):
        user = self.get_object()
        if self.request.user.is_superuser or self.request.user.is_admin:
            return True
        return False


@method_decorator(login_required, name="dispatch")
class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = CustomerUser
    success_url = "/accounts/users"

    def test_func(self):
        user = self.get_object()
        if self.request.user.is_superuser:
            return True
        return False


def PasswordResetCompleteView(request):
    return render(request, "accounts/registration/password_reset_complete.html")


def newcredentialCategory(request):
    if request.method == "POST":
        form = CredentialCategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("accounts:account-crendentials")
    else:
        form = CredentialCategoryForm()
    return render(
        request, "accounts/admin/forms/credentialCategory_form.html", {"form": form}
    )


@login_required
def newcredential(request):
    if request.method == "POST":
        form = CredentialForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.added_by = request.user
            instance.save()
            return redirect("accounts:account-crendentials")
    else:
        form = CredentialForm()
    return render(request, "accounts/admin/forms/credential_form.html", {"form": form})


@login_required
def credential_view(request):
    if (
        not request.user.is_superuser
        and not request.user.is_admin
        and not request.user.is_staff
    ):
        message = "You are not allowed to access this page. Contact admin: info@codanalytics.net"
        return render(request, "main/errors/generalerrors.html", {"message": message})
    else:
        message = "Please Contact Admin, if you fail to find access"
        categories = CredentialCategory.objects.all().order_by("-entry_date")
        departments = Department.objects.all()

        if request.user.is_superuser:
            credentials = Credential.objects.all().order_by("-entry_date")
        elif request.user.is_admin:
            credentials = Credential.objects.filter(
                Q(user_types="Admin") | Q(user_types="Employee")
            ).order_by("-entry_date")
        elif request.user.is_staff:
            credentials = Credential.objects.filter(user_types="Employee").order_by(
                "-entry_date"
            )
        else:
            credentials = Credential.objects.none()

        credential_filters = CredentialFilter(request.GET, queryset=credentials)

        # Step 1: Create a list of credentials
        credentials_list = list(credentials)

        # Step 2: Determine specific records to be moved to the center
        specific_records = ["boa", "experian", "betterment", "robin", "citi"]

        # Step 3: Remove specific records from the credentials list
        for record in specific_records:
            if record in credentials_list:
                credentials_list.remove(record)

        # Step 4: Sort the credentials list
        credentials_list.sort(key=lambda cred: cred.entry_date, reverse=True)

        # Step 5: Calculate the index for inserting the specific records
        center_index = math.ceil(len(credentials_list) / 2)

        # Step 6: Insert the specific records at the center index
        for record in specific_records:
            credentials_list.insert(center_index, record)

        context = {
            "departments": departments,
            "categories": categories,
            "credentials": credentials_list,
            "show_password": False,
            "credential_filters": credential_filters,
            "message": message,
        }

        try:
            request.session["siteurl"] = settings.SITEURL
            otp = request.POST.get("otp")
            if otp == request.session.get("security_otp"):
                del request.session["security_otp"]
                context["show_password"] = True
                return render(request, "accounts/admin/credentials.html", context)
            else:
                error_context = {"message": "Invalid OTP"}
                return render(
                    request, "accounts/admin/email_verification.html", error_context
                )

        except Exception as e:
            logger.error(f"Error in credential_view: {e}")
            return render(request, "accounts/admin/credentials.html", context)


@login_required
def security_verification(request):
    subject = "One time verification code to view passwords"
    otp = generate_otp(8)
    request.session["security_otp"] = otp
    request.session["siteurl"] = settings.SITEURL

    # Pass the OTP directly to the template
    context = {"otp": otp, "subject": subject}
    return render(request, "accounts/admin/email_verification.html", context)


@method_decorator(login_required, name="dispatch")
class CredentialUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Credential
    form_class = CredentialForm
    success_url = "/accounts/credentials"

    def form_valid(self, form):
        # if form.instance.added_by==self.request.user:
        if self.request.user.is_superuser or self.request.user.is_admin:
            return super().form_valid(form)
        else:
            return False

    def test_func(self):
        credential = self.get_object()
        # if self.request.user ==credential.added_by:
        if self.request.user.is_superuser or self.request.user.is_admin:
            return True
        else:
            return False


# ================================EMPLOYEE SECTION================================
class EmployeeListView(FilteredListViewMixin, ListView):
    """Consolidated employee list view using generic mixin"""

    model = CustomerUser
    template_name = "accounts/employees/employeelist.html"
    context_object_name = "employees"
    category_filters = {
        2: None,  # Staff members
    }

    def get_context_data(self, **kwargs):
        """Add employee-specific context data"""
        context = super().get_context_data(**kwargs)

        # Get employee data using existing utility function
        employee_subcategories, active_employees = employees()

        context.update(
            {
                "employee_subcategories": employee_subcategories,
                "active_employees": active_employees,
            }
        )

        return context


# ================================CLIENT SECTION================================
class ClientListView(FilteredListViewMixin, ListView):
    """Consolidated client list view using generic mixin"""

    model = CustomerUser
    template_name = "accounts/clients/clientlist.html"
    category_filters = {
        4: None,  # Students
        3: None,  # Jobsupport
    }

    def get_context_data(self, **kwargs):
        """Add client-specific context data"""
        context = super().get_context_data(**kwargs)

        # Add client categories for template
        context["clients"] = {
            "students": self.get_queryset().filter(category=2, is_active=True),  # STUDENT category
            "jobsupport": self.get_queryset().filter(category=3, is_active=True),  # CONSULTANT category
            "interview": self.get_queryset().filter(category=1, is_active=True),  # APPLICANT category (job interviews)
            "past": self.get_queryset().filter(
                category__in=[1, 2, 3, 4, 5], is_active=False  # Updated to use valid categories
            ),
        }

        return context


@method_decorator(login_required, name="dispatch")
class ClientDetailView(DetailView):
    template_name = "accounts/clients/client_detail.html"
    model = CustomerUser
    ordering = ["-date_joined "]


@method_decorator(login_required, name="dispatch")
class ClientUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CustomerUser
    success_url = "/accounts/clients"
    fields = ["category", "address", "city", "state", "country"]
    form = UserForm

    def form_valid(self, form):
        if self.request.user.is_superuser or self.request.user.is_admin:
            return super().form_valid(form)
        else:
            return False

    def test_func(self):
        if self.request.user.is_superuser or self.request.user.is_admin:
            return True
        else:
            return False


@method_decorator(login_required, name="dispatch")
class ClientDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = CustomerUser
    success_url = "/accounts/clients"

    def test_func(self):
        client = self.get_object()
        if self.request.user.is_superuser:
            return True
        return False


@login_required
def user_login_history(request, username="eunice"):
    login_history = LoginHistory.objects.filter(user__username=username).order_by(
        "-login_time"
    )
    for entry in login_history:
        logger.info(f"Login history entry ID: {entry.id}")

    context = {"login_history": login_history}

    return render(request, "accounts/login_history.html", context)


@login_required
def profile(request, username=None):
    userprofile = UserProfile.objects.filter(user__username=username)
    login_history = (
        LoginHistory.objects.filter(
            user__username=username, login_time__isnull=False, logout_time__isnull=False
        )
        .annotate(day=TruncDate("login_time"))
        .values("day", "id")
        .annotate(
            total_duration=Sum(
                ExpressionWrapper(
                    F("logout_time") - F("login_time"),
                    output_field=fields.DurationField(),
                )
            ),
            first_login_time=F("login_time"),
            last_logout_time=F("logout_time"),
        )
        .order_by("-day")
    )
    unique_login_history = []
    seen_days = set()
    for entry in login_history:
        if entry["total_duration"]:
            total_seconds = entry["total_duration"].total_seconds()
            total_hours = round(total_seconds / 3600, 2)
            if total_hours < 0:
                continue
            entry["total_hours"] = total_hours
            if entry["day"] not in seen_days:
                seen_days.add(entry["day"])
                unique_login_history.append(entry)

    if request.method == "POST":
        login_time = request.POST.get("login_time")
        logout_time = request.POST.get("logout_time")
        LoginHistory.objects.create(
            user=request.user,
            login_time=login_time,
            logout_time=logout_time,
        )
        return redirect("accounts:account-profile", username=username)

    context = {
        "user": request.user,
        "username": username,
        "login_history": unique_login_history,
    }
    return render(request, "accounts/profile.html", context)


@login_required
def edit_login_logout_time(request, pk):
    login_history = get_object_or_404(LoginHistory, pk=pk)
    username = login_history.user.username

    if request.method == "POST":
        form = LoginHistoryForm(request.POST, instance=login_history)
        if form.is_valid():
            form.save()
            return redirect("accounts:account-profile", username=username)
        else:
            logger.error(f"Form validation failed: {form.errors}")
    else:
        form = LoginHistoryForm(instance=login_history)

    return render(
        request,
        "main/snippets_templates/table/logging.html",
        {"form": form, "login_history": login_history},
    )


@method_decorator(login_required, name="dispatch")
class TrackDetailView(DetailView):
    model = Tracker
    ordering = ["-login_date"]


@method_decorator(login_required, name="dispatch")
class TrackListView(ListView):
    model = Tracker
    template_name = "accounts/tracker.html"
    context_object_name = "trackers"
    ordering = ["-login_date"]


def usertracker(request, user=None, *args, **kwargs):
    user = get_object_or_404(CustomerUser, username=kwargs.get("username"))
    trackers = Tracker.objects.all().filter(author=user).order_by("-login_date")
    try:
        em = Tracker.objects.all().values().order_by("-pk")[0]
    except:
        return redirect("accounts:tracker-create")
    customer_get = CustomerUser.objects.values_list("username", "email").get(
        id=em.get("author_id")
    )
    try:
        history_info = Payment_History.objects.filter(customer_id=user.id).order_by(
            "-contract_submitted_date"
        )[1]
    except IndexError:
        # Handle the case when there is no previous payment record
        history_info = None  # Or assign a default value
    current_info = Payment_Information.objects.filter(customer_id=user.id).first()
    plantime, history_time, added_time, Usedtime, delta, num = get_clients_time(
        current_info, history_info, trackers
    )
    if delta < 15:
        subject = "New Contract Alert!"
        try:
            send_email(
                category=request.user.category,
                to_email=customer_get[1],
                subject=subject,
                html_template="email/usertracker.html",
                context={"user": request.user},
            )
        except Exception as e:
            # Handle any other exceptions
            logger.error(f"An unexpected error occurred: {e}")

    context = {
        "trackers": trackers,
        "num": num,
        "plantime": plantime,
        "Usedtime": Usedtime,
        "delta": delta,
    }

    return render(request, "accounts/usertracker.html", context)


class TrackCreateView(LoginRequiredMixin, CreateView):
    model = Tracker
    success_url = "/accounts/tracker"
    fields = [
        "empname",
        "employee",
        "author",
        "category",
        "sub_category",
        "task",
        "duration",
        "plan",
    ]

    def __init__(self, *args, **kwargs):
        super(TrackCreateView, self).__init__(*args, **kwargs)
        self.idval = None  # Initialize idval

    def form_valid(self, form):
        form.instance.author = self.request.user
        if form.instance.category == "Job_Support":
            self.update_job_support_points(form)
        return super().form_valid(form)

    def update_job_support_points(self, form):
        try:
            task_id, current_points, target_points = self.get_task_details(
                form.instance.empname, form.instance.category
            )
            self.idval = task_id
            updated_points = self.calculate_updated_points(
                form.instance.sub_category, form.instance.duration, current_points
            )
            self.update_task_points(task_id, updated_points, target_points)
        except Exception:
            # Handle specific exceptions or log them
            pass

    def get_task_details(self, empname, category):
        return Task.objects.values_list("id", "point", "mxpoint").filter(
            Q(activity_name__in=JOB_SUPPORT_CATEGORIES), employee__username=empname
        )[0]

    def calculate_updated_points(self, sub_category, duration, current_points):
        if sub_category in ["Development", "Testing"]:
            return float(current_points) + (0.5 * duration)
        return float(current_points) + duration

    def update_task_points(self, task_id, updated_points, target_points):
        if updated_points >= target_points:
            target_points += 10
        Task.objects.filter(id=task_id).update(
            point=updated_points, mxpoint=target_points
        )

    def get_success_url(self):
        if self.request.user.category in [
            1,
            3,
            4,
            5,
            6,
            7,
        ]:  # Job_Applicant, Jobsupport, Student, Investor, Vendor, General_User
            return reverse(
                "accounts:user-list", kwargs={"username": self.request.user.username}
            )
        elif self.request.user.is_staff:
            if not self.idval:
                return reverse("accounts:tracker-list")
            else:
                return reverse("management:new_evidence", kwargs={"taskid": self.idval})
        else:
            return reverse("management:companyagenda")


@method_decorator(login_required, name="dispatch")
class TrackUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Tracker
    success_url = "/accounts/tracker"

    fields = [
        "employee",
        "empname",
        "author",
        "plan",
        "category",
        "task",
        "duration",
        "time",
        "login_date",
    ]

    def form_valid(self, form):
        # form.instance.author=self.request.user
        if (
            self.request.user.is_superuser
            or self.request.user.is_admin
            or self.request.user.is_staff
        ):
            return super().form_valid(form)
        else:
            return False

    def test_func(self):
        track = self.get_object()
        if (
            self.request.user.is_superuser
            or self.request.user.is_admin
            or self.request.user.is_staff
        ):
            return True
        else:
            return False


@method_decorator(login_required, name="dispatch")
class TrackDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Tracker
    success_url = "/accounts/tracker"

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return False


# class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
#     def pre_social_login(self, request, sociallogin):

#         logger.info("inside pre social login")
#         # Check if the user with the given email already exists in your custom User model
#         user = sociallogin.user
#         email = user.email
#         existing_user = CustomerUser.objects.filter(email=email).first()
#         category = request.session.get("category")

        if existing_user:
            logger.info("existing user")
            # Link the social login to the existing user
            sociallogin.connect(request, existing_user)

        elif existing_user is None and category is None:
            redirect_url = reverse("accounts:join")  # Replace with your desired URL
            response = HttpResponseRedirect(redirect_url)
            raise ImmediateHttpResponse(response)

        else:
            logger.info("inside else")

            # If the user doesn't exist, create a new user
            sociallogin.save(request, connect=False)

            existing_user = sociallogin.user
            existing_user.category = request.session.pop("category", default=None)
            existing_user.sub_category = request.session.pop(
                "subcategory", default=None
            )
            if existing_user.email:
                existing_user.username = existing_user.email

            if existing_user.category == "2":
                existing_user.is_staff = True
                existing_user.category = int(existing_user.category)
                existing_user.sub_category = int(existing_user.sub_category)
            elif existing_user.category == "3" or existing_user.category == "4":
                existing_user.category = int(existing_user.category)
                existing_user.sub_category = int(existing_user.sub_category)
            else:
                existing_user.category = int(existing_user.category)
                existing_user.sub_category = int(existing_user.sub_category)

            existing_user.save()
            create_profile()

        # If Category is Staff/employee
        if existing_user is not None and existing_user.category == 2:
            if existing_user.is_staff and not existing_user.is_employee_contract_signed:

                sociallogin.state["next"] = reverse("management:employee_contract")

            else:  # parttime (agents) & Fulltime

                sociallogin.state["next"] = reverse("management:companyagenda")

        # If Category is client/customer:# Student # Job Support
        elif existing_user is not None and existing_user.category == 3:
            sociallogin.state["next"] = reverse("management:companyagenda")

        # If Category is investor - redirect based on KCC membership
        elif existing_user is not None and existing_user.category == 4:
            # Check if user is a KCC member
            is_kcc_member = False
            if hasattr(existing_user, "profile") and existing_user.profile:
                profile = existing_user.profile
                if profile.is_karen_country_club_member:
                    if profile.kcc_membership_expiry:
                        from django.utils import timezone

                        is_kcc_member = (
                            profile.kcc_membership_expiry >= timezone.now().date()
                        )
                    else:
                        is_kcc_member = True

            if is_kcc_member:
                sociallogin.state["next"] = reverse(
                    "finance:loan-home"
                )  # KCC members go to loan system
            else:
                sociallogin.state["next"] = reverse(
                    "investing:investment_dashboard"
                )  # Non-KCC investors go to investment system

        elif existing_user is not None and (existing_user.category == 5):

            sociallogin.state["next"] = reverse("management:companyagenda")

        elif (
            existing_user is not None
            and existing_user.profile.section is not None
            and existing_user.category == 1
        ):

            if existing_user.profile.section == "A":

                sociallogin.state["next"] = reverse("application:section_a")

            elif existing_user.profile.section == "B":

                sociallogin.state["next"] = reverse("application:section_b")

            elif existing_user.profile.section == "C":

                sociallogin.state["next"] = reverse("application:policies")
            else:

                sociallogin.state["next"] = reverse("application:interview")

        elif (
            existing_user is not None
            and existing_user.profile.section is not None
            and existing_user.category == 1
            and existing_user.sub_category == 0
        ):

            sociallogin.state["next"] = reverse("application:policies")

        elif existing_user is not None and existing_user.is_admin:

            sociallogin.state["next"] = reverse("management:companyagenda")

        else:
            sociallogin.state["next"] = reverse(
                "main:layout"
            )  # Redirect to your success page or handle as needed


def custom_social_login(request):

    try:
        category = request.GET.get("category")
        subcategory = request.GET.get("subcategory")

        if category is not None and subcategory is not None:
            request.session["category"] = request.GET.get("category")
            request.session["subcategory"] = request.GET.get("subcategory")

        # Redirect to the built-in Google login view with the state parameter
        social_login_url = reverse(
            "google_login"
        )  # Use the name of the built-in Google login view

        if request.GET.get("socialPlatform"):

            social_login_url = reverse(
                request.GET.get("socialPlatform")
            )  # Use the name of the built-in Google login view

        return redirect(social_login_url)

    except:

        return render(request, "accounts/registration/join.html", {"form": UserForm()})


def one_time_code(request):
    return render(request, "accounts/admin/email_verification_copy.html")


# Student auto signup and logged in
def register_and_login_user(request):
    if request.method == "POST":
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        logger.info(f"Registration attempt for: {email} - {first_name} {last_name}")

        # Generate a random password
        otp = generate_otp(8)

        # Create the user
        previous_user = CustomerUser.objects.filter(email=email).first()

        if previous_user:
            logger.info("Existing user confirmed, sending OTP")
            request.session["security_otp"] = otp
            request.session["email"] = email
            request.session["siteurl"] = settings.SITEURL

            context = {
                "otp": otp,
                "purpose": "code",
            }

            subject = "OTP CODE"
            email_template_name = "email/security_verification.html"

            html_message = render_to_string(email_template_name, context)
            logger.info("Email message rendered.")

            try:
                logger.info("Starting email sending process")
                # Create an email backend using the EMAIL_INFO configuration
                email_backend = EmailBackend(
                    host=settings.EMAIL_INFO["HOST"],
                    port=settings.EMAIL_INFO["PORT"],
                    username=settings.EMAIL_INFO["USER"],
                    password=settings.EMAIL_INFO["PASS"],
                    use_tls=settings.EMAIL_INFO["USE_TLS"],
                    use_ssl=settings.EMAIL_INFO["USE_SSL"],
                )

                email_backend.open()
                logger.info("Email backend opened successfully")

                email = EmailMultiAlternatives(
                    subject=subject,
                    body=html_message,  # This will be used as plain text fallback
                    from_email=settings.EMAIL_INFO["USER"],
                    to=[previous_user.email],
                    connection=email_backend,
                )

                logger.info("Email setup complete, adding attachments")
                email.attach_alternative(
                    html_message, "text/html"
                )  # Attach the HTML version

                # Send the email
                email.send()
                logger.info(f"OTP code sent to {previous_user.email}.")

                email_backend.close()

                return render(request, "accounts/registration/login_page.html", context)

            except Exception as e:
                logger.error(f"Email sending failed: {e}")
                return render(
                    request,
                    "accounts/registration/login_page.html",
                    {"error": "Failed to send OTP"},
                )

        else:
            logger.info("New user confirmed, redirecting to registration page")
            return redirect("accounts:join")

    return JsonResponse({"success": False, "message": "Invalid request method."})


def password_reset_request(request):

    if request.method == "POST":

        user_email = request.POST.get("email")
        logger.info(f"Password reset requested for: {user_email}")
        user = CustomerUser.objects.filter(email=user_email).first()

        if user == None:
            raise Http404("The Provided Email Does Not Exist")

        # Generate UID (base64-encoded user ID) and token
        uid = urlsafe_base64_encode(str(user.pk).encode())
        token = default_token_generator.make_token(user)

        logger.info(f"Password reset token generated - UID: {uid}, Token: {token}")

        # Generate the password reset link and send the email
        subject = "Password Reset Request"
        email_template_name = "accounts/registration/password_reset_email.html"

        html_message = render_to_string(
            email_template_name,
            {
                "protocol": request.scheme,
                "domain": request.get_host(),
                "uid": uid,
                "token": token,
                "request": request,
            },
        )
        logger.info("Password reset email message rendered.")

        try:
            # Create an email backend using the EMAIL_INFO configuration
            email_backend = EmailBackend(
                host=settings.EMAIL_INFO["HOST"],
                port=settings.EMAIL_INFO["PORT"],
                username=settings.EMAIL_INFO["USER"],
                password=settings.EMAIL_INFO["PASS"],
                use_tls=settings.EMAIL_INFO["USE_TLS"],
                use_ssl=settings.EMAIL_INFO["USE_SSL"],
            )
            logger.info("Opening email backend connection")
            # Explicitly open the connection
            email_backend.open()
            logger.info("Email backend connection opened")

            email = EmailMultiAlternatives(
                subject=subject,
                body=html_message,  # This will be used as plain text fallback
                from_email=settings.EMAIL_INFO["USER"],
                to=[user.email],
                connection=email_backend,
            )
            email.attach_alternative(
                html_message, "text/html"
            )  # Attach the HTML version

            # Send the email
            email.send()
            logger.info(f"Password Reset email sent to {user.email}.")

            # Close the connection after sending the email
            email_backend.close()
            return render(
                request,
                "accounts/registration/password_reset_done.html",
                {"email": user.email},
            )

        except Exception as e:
            logger.error(f"Password reset email failed: {e}")
            return render(
                request,
                "accounts/registration/password_reset_done.html",
                {"error": "Failed to send password reset email"},
            )
