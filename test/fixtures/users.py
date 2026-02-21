from django.contrib.auth import get_user_model


def create_user(username='testuser', password='password123'):
    User = get_user_model()
    user = User.objects.create_user(username=username, password=password)
    return user
