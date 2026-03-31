from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter for Google/Facebook login
    Automatically connects social accounts by email.
    """

    def pre_social_login(self, request, sociallogin):
        # If user already logged in → do nothing
        if request.user.is_authenticated:
            return

        email = sociallogin.account.extra_data.get("email")

        if not email:
            return

        try:
            user = User.objects.get(email=email)
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass