import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from django.test import Client
from accounts.models import CustomerUser
from django.urls import resolve


def ensure_user(username='smoke_test_user', password='TestPass123!'):
    user, created = CustomerUser.objects.get_or_create(username=username, defaults={
        'first_name': 'Smoke',
        'last_name': 'Tester',
        'email': f'{username}@example.com',
        'accepted_terms': True,
    })
    if created:
        user.set_password(password)
        user.save()
    return user, password


def run_logout_flow():
    user, password = ensure_user()
    client = Client()

    # Diagnose which view is bound to /logout/
    try:
        resolved = resolve('/logout/')
        print('resolved_view:', resolved.view_name, resolved.func)
        try:
            view_class = resolved.func.view_class
            print('view_class:', view_class)
            print('http_method_names:', getattr(view_class, 'http_method_names', None))
        except Exception as e:
            print('view_class_info_error:', e)
    except Exception as e:
        print('resolve_error:', e)

    logged_in = client.login(username=user.username, password=password)
    print('logged_in_before_logout:', logged_in)

    r_home_before = client.get('/')
    try:
        auth_before = bool(r_home_before.context['user'].is_authenticated)
    except Exception:
        auth_before = 'no-context'
    print('user_authenticated_before_logout:', auth_before)

    r_logout = client.get('/logout/', follow=True)
    print('logout_status_code:', r_logout.status_code)
    print('logout_redirects:', [r[0] for r in r_logout.redirect_chain])

    r_home_after = client.get('/')
    try:
        auth_after = bool(r_home_after.context['user'].is_authenticated)
    except Exception:
        auth_after = 'no-context'
    print('user_authenticated_after_logout:', auth_after)


if __name__ == '__main__':
    run_logout_flow()
