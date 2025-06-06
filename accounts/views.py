import secrets
import uuid
import string, random
from django.core.paginator import Paginator
from django.contrib.auth import (
    authenticate,
    login,
    logout,
    get_user_model,
    get_backends,
)
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from accounts.choices import CategoryChoices
from accounts.utils import (
    CATEGORY_FEES,
    convert_kes_to_usd,
    get_exchange_rate,
    send_verification_email,
    generate_random_password,
)
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
from .models import CustomerUser, Membership
from .forms import (
    CustomAuthenticationForm,
    CustomUserCreationForm,
    UserForm,
    LoginForm,
    OTPForm,
)
from finance.utils import DYCDefaultPayments
import logging
from main.views import send_notification, send_welcome_email
from mail.custom_email import send_email

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.http import Http404
from django.contrib import messages



logger = logging.getLogger(__name__)
# Create your views here..


# path_values
# path_val,sub_title=path_values(request)


# @allowed_users(allowed_roles=['admin'])
def home(request):
    password = generate_random_password()
    print(password)
    return render(request, "main/home_templates/home.html")


# @allowed_users(allowed_roles=['admin'])
def thank(request):
    return render(request, "accounts/clients/thank.html")


# ---------------ACCOUNTS VIEWS----------------------
# @login_required
def security_verification(request):
    form = OTPForm(request.POST or None)
    subject = "Your one-time verification code is: "
    # otp = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))


                
    password, otp = generate_random_password(8)
    print("This is Registration")
    print(password, otp)
    request.session["security_otp"] = otp
    request.session["siteurl"] = settings.SITEURL

    # Pass the OTP directly to the template
    context = {"otp": otp, "subject": subject, "form": form}
    # return render(request, "accounts/admin/email_verification.html", context)


    if request.method == "POST":
        try:
            #user = None  # Initialize user variable

            user_email = request.POST.get("email")
            user = CustomerUser.objects.filter(email=user_email).first()
        except:
            pass

        
        url = 'email/otp.html'
        # new_user = CustomerUser.objects.all().order_by('-id').first()
        print(user)
        
        print(user)
        print(user.id, user.first_name, user.category, user.member_number, user.email)


        user_category = "Ordinary"
        # first_name = user.first_name
        # last_name = user.last_name
        # user_id = user.member_number
        user_email = user.email
        subject = "One Time Password(OTP)"

        print(user.id)


        context = {
            # 'user_category': user_category,
            # 'first_name': first_name,
            # 'last_name': last_name,
            'otp': otp,
            'subject': subject,
            'request': request
        }
        try:
            send_email(
                category=user_category,
                to_email=[user_email],
                subject=subject,
                html_template=url,
                context=context
            )

            print("EMAIL SENT")
            # return render(request,url, context)
            # return render(request, 'main/messages/message.html', context)
        except Exception as e:
            error_message = (
                f'Hi {request.user.first_name}, Your message to '
                f'{request.user.email} was unsuccessful. '
                f'Please try again or contact info@diasporacounty48.org. Thank You. '
                f'Error: {e}'
            )
            return render(request, 'main/messages/message.html', {"message": error_message})


    return render(request, "accounts/registration/DC48K/sign_in.html", context)


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("")
    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/registration/DC48K/registers.html", {"form": form})


class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = "accounts/registration/DC48K/logins.html"


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

                print(category)

                # if category == CategoryChoices.ORDINARY_MEMBERSHIP:
                #     form.instance.is_ORDINARY_MEMBERSHIP = True
                # elif category == CategoryChoices.LEADERS_MEMBERSHIP:
                #     form.instance.is_active_member = True
                # elif category == CategoryChoices.ORGANIZATIONAL_MEMBERSHIP:
                #     form.instance.is_executive_member = True
                # elif category == CategoryChoices.FBO_ORDINARY:
                #     form.instance.is_fbo_ordinary = True
                # elif category == CategoryChoices.ACTIVE_ORGANIZATION:
                #     form.instance.is_active_organization = True
                # elif category == CategoryChoices.ROYAL_ORGANIZATION:
                #     form.instance.is_royal_organization = True

                user = form.save(commit=False)  # Don't save yet
                user.is_active = True  # Set is_active explicitly

                user = form.save()

                # Send a welcoming email
                # new_user = CustomerUser.objects.all().order_by('-id').first()
                # print(new_user)
                # print(new_user.id, new_user.first_name, new_user.category, new_user.member_number, new_user.email)
                send_notification(request)

                # Provide the backend parameter when logging in the user
                login(
                    request, user, backend="django.contrib.auth.backends.ModelBackend"
                )

                if category == CategoryChoices.ORDINARY_MEMBERSHIP:
                    return redirect("main:layout")

                elif category == CategoryChoices.LEADERS_MEMBERSHIP:
                    # return redirect('finance:pay')
                    return redirect("main:layout")

                elif category == CategoryChoices.ORGANIZATIONAL_MEMBERSHIP:
                    return redirect("main:layout")

            else:
                msg = "Error validating form"
                print(msg)

    return render(request, "accounts/registration/DC48K/join.html", {"form": form})


# def join(request):
#     form = UserForm()  # Define form variable with initial value
#     if request.method == "POST":
#         previous_user = CustomerUser.objects.filter(email=request.POST.get("email"))
#         if previous_user.exists():
#             messages.success(request, "User already exists with this email")
#             return redirect("/password-reset")
#         else:
#             form = UserForm(request.POST)  # Assign form with request.POST data
#             if form.is_valid():
#                 # Check the selected category and update the form instance accordingly
#                 category = form.cleaned_data.get("category")

#                 if category == CategoryChoices.ORDINARY_MEMBER:
#                     form.instance.is_ordinary_member = True
#                 elif category == CategoryChoices.ACTIVE_MEMBER:
#                     form.instance.is_active_member = True
#                 elif category == CategoryChoices.EXECUTIVE_MEMBER:
#                     form.instance.is_executive_member = True
#                 elif category == CategoryChoices.FBO_ORDINARY:
#                     form.instance.is_fbo_ordinary = True
#                 elif category == CategoryChoices.ACTIVE_ORGANIZATION:
#                     form.instance.is_active_organization = True
#                 elif category == CategoryChoices.ROYAL_ORGANIZATION:
#                     form.instance.is_royal_organization = True

#                 # Generate a random password
#                 password = generate_random_password()
#                 print(password)

#                 # Save the password and username
#                 token = str(uuid.uuid4())

#                 user = form.save(commit=False)
#                 user.verification_token = token
#                 user.set_password(password)
#                 user.is_active = False  # Set the generated password
#                 user.save()
#                 print(category)
#                 fee_kes = CATEGORY_FEES.get(category, 0.0)

#                 fee_usd = fee_kes / get_exchange_rate('USD', 'KES')  # Convert to USD
#                 membership = Membership.objects.create(
#                     member=user,
#                     fee=fee_usd,
#                     currency="USD",  # Store in USD
#                     status='NOT_PAID',
#                 )
#                 print(f"Membership created for user {user.username} with fee {fee_usd} USD")

#                 print(f"User {user.username} created and saved. Account is inactive until verification.")

#                 send_verification_email(user, password=password)


#                 return redirect('accounts:email-verification-notice', user.id)
#             else:
#                 msg = "Error validating form"
#                 print(msg)

#     return render(request, "accounts/registration/DC48K/joins.html", {"form": form})


def email_verification_notice(request, user_id):
    user = get_object_or_404(CustomerUser, id=user_id)
    messages.success(request, f"A verification email has been sent to {user.email}.")

    return render(
        request, "accounts/registration/email_verification_notice.html", {"user": user}
    )


def verify_email(request, token):
    try:
        # Attempt to find the user by the verification token
        user = get_object_or_404(CustomerUser, verification_token=token)
        if user.email_verified == True:
            print("email already verified")
            return render(
                request,
                "accounts/registration/email_verification_notice.html",
                {
                    "verification_status": "already_verified",
                    "user": user,
                    "redirect_url": "/finance/pay/",
                },
            )
        else:
            # If the user is found, verify the email
            user.email_verified = True
            user.is_active = True  # Activate the account
            user.save()

            # Render the success message
            return render(
                request,
                "accounts/registration/email_verification_notice.html",
                {"verification_status": "success", "redirect_url": "/finance/pay/"},
            )

    except CustomerUser.DoesNotExist:
        # If the user doesn't exist, render the failure message
        return render(
            request,
            "accounts/registration/email_verification_notice.html",
            {"verification_status": "failed"},
        )


def login_view(request):
    form = LoginForm(request.POST or None)
    msg = None

    if request.method == "GET":
        sociallogin = request.session.pop("socialaccount_sociallogin", None)
        if sociallogin is not None:
            msg = "Error with social login. Check your credentials or try to sign up manually."

    if request.method == "POST":
        try:
            user = None  # Initialize user variable

            # Handle One-Time Code (OTP) Login
            # otp_entered = request.POST.get('otp')
            otp_entered = request.POST.get("otp")
            stored_otp = request.session.get(
                "security_otp"
            )  # Get OTP stored in session
            username_or_email = request.POST.get("email")

            if otp_entered == stored_otp and username_or_email:
                user = CustomerUser.objects.filter(email=username_or_email).first()
                if user is None:
                    print("The provided email is Invalid")
                else:
                    if user.is_active:
                        backend = get_backends()[0]
                        user.backend = (
                            f"{backend.__module__}.{backend.__class__.__name__}"
                        )
                        login(request, user)
                        if user.is_authenticated:
                            # Redirect based on user category
                            # return redirect(get_redirect_url(user))
                            return redirect("main:layout")
                    else:
                        msg = "Authentication failed"
                        print(msg)
                        return render(
                            request, "main/home_templates/home.html", {"msg": msg}
                        )

            elif form.is_valid():
                request.session["siteurl"] = settings.SITEURL
                username_or_email = form.cleaned_data.get(
                    "enter_your_username_or_email"
                )
                enter_your_password = form.cleaned_data.get("enter_your_password")

                # Try to get the user by username
                user = authenticate(
                    request, username=username_or_email, password=enter_your_password
                )
                if user is None:
                    # If authentication with username failed, try email
                    UserModel = get_user_model()
                    try:
                        user_obj = UserModel.objects.get(
                            email__iexact=username_or_email
                        )
                        user = authenticate(
                            request,
                            username=user_obj.username,
                            password=enter_your_password,
                        )
                    except UserModel.DoesNotExist:
                        pass

                if user:
                    print("User authenticated")
                    login(request, user)

                    # membership = get_object_or_404(Membership, member=user)
                    # if membership.status == 'NOT_PAID':
                    #     return redirect('finance:pay')
                    # else:
                    #    return redirect('main:layout')
                    return redirect("main:layout")
                else:
                    print("Authentication failed")
                    msg = "Invalid credentials"

        except CustomerUser.DoesNotExist:
            msg = "User does not exist. Please check your email or sign up."
            logger.warning(f"Login failed: User {username_or_email} does not exist.")

        except Exception as e:
            msg = "An unexpected error occurred. Please try again later."
            logger.error(f"Unexpected login error: {str(e)}")

        else:
            print("Form is invalid")
            msg = "Error validating the form"

    return render(
        request,
        "accounts/registration/DC48K/login_page.html",
        {"form": form, "msg": msg},
    )


def custom_logout(request):
    logout(request)  # Log out the user
    # return redirect("accounts:security")  # Redirect to the login page
    return redirect('accounts:account-login') 


@login_required
def userlist(request):
    users = CustomerUser.objects.filter(transaction_sender__amount__gte=5000).distinct()
    template_name = "accounts/admin/processing_users.html"

    context = {
        "users": users,
    }
    # if request.user.is_superuser:
    #     return render(request, template_name, context)
    # else:
    #     return redirect("main:layout")
    return render(request, template_name, context)


@login_required
def users(request):
    users = CustomerUser.objects.filter(is_active=True).order_by("-date_joined")
    template_name = "accounts/admin/adminpage.html"
    context = {
        "users": users,
    }

    # if request.user.is_superuser:
    #     return render(request, template_name, context)
    # else:
    #     return redirect("main:layout")
    return render(request, template_name, context)


class SuperuserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CustomerUser
    success_url = "/accounts/users"
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
        "is_superuser",
        "is_admin",
        "is_staff",
        "is_client",
        "is_applicant",
        "is_active",
        "is_staff",
    ]

    def form_valid(self, form):
        # form.instance.username=self.request.user
        # if request.user.is_authenticated:
        if self.request.user.is_superuser:  # or self.request.user.is_authenticated :
            return super().form_valid(form)
        #  elif self.request.user.is_authenticated:
        #      return super().form_valid(form)
        return False

    def test_func(self):
        user = self.get_object()
        # if self.request.user == client.username:
        #     return True
        if self.request.user.is_superuser:  # or self.request.user == user.username:
            return True
        return False


class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CustomerUser
    success_url = "/accounts/users"
    # fields=['category','address','city','state','country']
    fields = [
        # "category",
        # "sub_category",
        "first_name",
        "last_name",
        "date_joined",
        "email",
        "gender",
        "phone",
        # "address",
        # "city",
        # "state",
        # "country",
        "is_admin",
        "is_staff",
        "is_client",
        "is_applicant",
    ]

    def form_valid(self, form):
        # form.instance.username=self.request.user
        # if request.user.is_authenticated:
        if self.request.user.is_superuser or self.request.user.is_admin:
            return super().form_valid(form)
        #  elif self.request.user.is_admin:
        #       return super().form_valid(form)
        return False

    def test_func(self):
        user = self.get_object()
        # if self.request.user == client.username:
        #     return True
        if self.request.user.is_superuser or self.request.user.is_admin:
            return True
        return False


def select_category(request):
    if request.method == "POST":
        selected_category = request.POST.get("category")
        if selected_category in [choice.value for choice in CategoryChoices]:
            request.session["category"] = selected_category
            return redirect("socialaccount_login", provider="google")
        else:
            messages.error(request, "Invalid category selected.")
    return render(request, "accounts/select_category.html")


from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from django.http import HttpResponseRedirect


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        print("Inside pre_social_login")

        # Extract user information from sociallogin
        user = sociallogin.user
        email = user.email

        # Attempt to find an existing user with the same email
        existing_user = CustomerUser.objects.filter(email=email).first()
        category = request.session.get("category")
        print(category)

        if existing_user:
            print("Existing user found. Connecting social account.")
            # Link the social login to the existing user
            sociallogin.connect(request, existing_user)
            target_user = existing_user
        elif existing_user is None and category is None:
            print(
                "No existing user and no category in session. Redirecting to category selection."
            )

        else:
            print("Creating a new user via social login.")
            # If the user doesn't exist and a category is provided, create a new user
            sociallogin.save(request, connect=False)

            new_user = sociallogin.user
            selected_category = request.session.pop("category", None)
            print(selected_category)

            # Assign category based on your CategoryChoices
            if selected_category == CategoryChoices.ORDINARY_MEMBERSHIP:
                new_user.is_ORDINARY_MEMBERSHIPSHIPSHIPSHIPSHIPSHIPSHIPSHIP = True
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

            # Assign username if not set
            if not new_user.username:
                new_user.username = new_user.email

            # Since email is verified by Google, set user as active
            new_user.is_active = True  # No need for verification token
            new_user.verification_token = None  # Clear any token if previously set
            new_user.save()

            cate = int(selected_category)
            fee_kes = CATEGORY_FEES.get(cate)
            print(fee_kes)
            fee_usd = fee_kes / get_exchange_rate(
                "USD", "KES"
            )  # Ensure get_exchange_rate is defined
            membership = Membership.objects.create(
                member=new_user,
                fee=fee_usd,
                currency="USD",
                status="NOT_PAID",
            )
            print(
                f"Membership created for user {new_user.username} with fee {fee_usd} USD"
            )

            # Optionally send a welcome email
            # self.send_welcome_email(new_user)

            target_user = new_user

        # After obtaining the target_user (existing or new), check Membership status
        if existing_user:
            membership = Membership.objects.filter(member=existing_user).first()
            if membership and membership.status == "NOT_PAID":
                print(
                    f"User {target_user.username} has unpaid membership. Redirecting to payment."
                )
                # Redirect to finance:pay with membership ID
                sociallogin.state["next"] = reverse("finance:pay")
            else:
                # Redirect based on user category
                print("not a member")
        else:
            membership = Membership.objects.filter(member=new_user).first()
            if membership and membership.status == "NOT_PAID":
                print(
                    f"User {target_user.username} has unpaid membership. Redirecting to payment."
                )
                # Redirect to finance:pay with membership ID
                sociallogin.state["next"] = reverse("finance:pay")
            else:
                # Redirect based on user category
                print("not a member")


def custom_social_login(request):
    try:
        category = request.GET.get("category")

        if category is not None:
            request.session["category"] = request.GET.get("category")

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





def password_reset_request(request):

    if request.method == "POST":

        user_email = request.POST.get("email")
        print('user_email: ', user_email)
        user = CustomerUser.objects.filter(email=user_email).first()
        print('user: ', user)

        if user == None:
            raise Http404('The Provided Email Does Not Exist')
       

        # Generate UID (base64-encoded user ID) and token
        uid = urlsafe_base64_encode(str(user.pk).encode())
        token = default_token_generator.make_token(user)

        print(uid)
        print(token)
        # Generate the password reset link and send the emai
        subject = "Password Reset Request"
        email_template_name = "accounts/registration/password_reset_email.html"
        category = user.category

        context = {
            'protocol': request.scheme,
            'domain': request.get_host(),
            'uid': uid,  
            'token': token,  
            'request': request,
        }

        try:
            send_email(
                category=category,
                to_email=[user_email],
                subject=subject,
                html_template= email_template_name,
                context=context,
            )

            print("EMAIL SENT")

            return render(request, 'accounts/registration/password_reset_done.html', {'email': user_email})


        except Exception as e:
            error_message = (
                f'Please try again or contact info@diasporacounty48.org. Thank You. '
            )
            return render(request, 'main/messages/message.html', {"message": error_message})


    return redirect("main:layout")


from django.shortcuts import render
from .models import Tracker

def tracker_list(request):
    trackers = Tracker.objects.all().order_by('-login_date')  # you can order by any field
    return render(request, 'accounts/tracker_list.html', {'trackers': trackers})



from django.shortcuts import get_object_or_404, redirect, render
from .models import Tracker

def tracker_delete(request, pk):
    tracker = get_object_or_404(Tracker, pk=pk)
    if request.method == 'POST':
        tracker.delete()
        return redirect('tracker_list')  # This should match your list view's URL name
    return render(request, 'accounts/tracker_confirm_delete.html', {'tracker': tracker})
