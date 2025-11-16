from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


class CaseInsensitiveAuthBackend(ModelBackend):
    """
    Custom authentication backend that allows case-insensitive login
    with username or email.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user with case-insensitive username or email.
        """
        if username is None or password is None:
            return None

        try:
            # Try to find user by case-insensitive username or email
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # If somehow multiple users exist (shouldn't happen with proper validation)
            # try username first, then email
            try:
                user = User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                try:
                    user = User.objects.get(email__iexact=username)
                except (User.DoesNotExist, User.MultipleObjectsReturned):
                    return None

        # Check password and return user if valid
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
