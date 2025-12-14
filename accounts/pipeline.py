"""
Social Authentication Pipeline
Custom pipeline functions for social auth integration
"""
from accounts.models import UserProfile, Category


def create_user_profile(backend, user, response, *args, **kwargs):
    """
    Create UserProfile for users who register via social authentication.
    This function is called during the social auth pipeline.
    """
    if user and not hasattr(user, 'userprofile'):
        # Get or create a default category for social auth users
        default_category, _ = Category.objects.get_or_create(
            slug='individual',
            defaults={
                'name': 'Individual',
                'description': 'Individual users',
                'icon': 'bi-person',
                'is_active': True
            }
        )

        # Create the user profile
        profile = UserProfile.objects.create(
            user=user,
            category=default_category
        )

        # Extract additional information from social auth response
        if backend.name == 'google-oauth2':
            # Google OAuth2 specific data
            if 'given_name' in response:
                user.first_name = response.get('given_name', '')
            if 'family_name' in response:
                user.last_name = response.get('family_name', '')
            if 'picture' in response:
                profile.profile_image = response.get('picture', '')

        elif backend.name == 'facebook':
            # Facebook specific data
            if 'first_name' in response:
                user.first_name = response.get('first_name', '')
            if 'last_name' in response:
                user.last_name = response.get('last_name', '')
            if 'picture' in response and 'data' in response['picture']:
                profile.profile_image = response['picture']['data'].get('url', '')

        # Save the updated user and profile
        user.save()
        profile.save()

    return {'user': user}
