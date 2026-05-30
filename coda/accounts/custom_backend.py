from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend that:
    - Allows login by username or email
    - REQUIRES email verification before login
    """

    def authenticate(
        self,
        request,
        username=None,
        password=None,
        **kwargs,
    ):
        """
        Authenticate user by username or email,
        with email verification check.

        Returns:
            User object if authentication successful
            and email verified.

            None if authentication fails
            or email not verified.
        """

        UserModel = get_user_model()

        try:
            user = UserModel.objects.get(
                Q(username=username) | Q(email=username)
            )

        except UserModel.DoesNotExist:
            logger.warning(
                f"Authentication attempt with "
                f"non-existent user: {username}"
            )

            return None

        # Check password
        if not user.check_password(password):
            logger.warning(
                f"Authentication failed for user "
                f"{user.email}: incorrect password"
            )

            return None

        # CRITICAL: Check if email is verified
        if not user.email_verified:
            logger.warning(
                f"Authentication blocked for "
                f"unverified user: {user.email}"
            )

            # Return None to prevent login
            return None

        # Additional check: ensure user is active
        if not user.is_active:
            logger.warning(
                f"Authentication blocked for "
                f"inactive user: {user.email}"
            )

            return None

        logger.info(
            f"Authentication successful for "
            f"verified user: {user.email}"
        )

        return user

    def get_user(self, user_id):
        """
        Get user by ID.
        """

        UserModel = get_user_model()

        try:
            return UserModel.objects.get(pk=user_id)

        except UserModel.DoesNotExist:
            return None