import pytest


def test_create_user(db, django_user_model):
    user = django_user_model.objects.create_user(username='u1', password='pass')
    assert user.pk is not None
    assert user.check_password('pass') is True


def test_user_str(db, django_user_model):
    user = django_user_model.objects.create_user(username='u2', password='p')
    assert str(user.username) == 'u2'
