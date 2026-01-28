from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from unittest.mock import patch

from accounts import views as accounts_views


class AccountsViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_membership_registration_get_renders_form(self):
        req = self.factory.get('/')
        with patch('accounts.views.render') as mock_render:
            mock_render.return_value = HttpResponse('ok')
            resp = accounts_views.membership_registration(req)
            self.assertEqual(resp.status_code, 200)

    def test_register_get_renders_form(self):
        req = self.factory.get('/')
        with patch('accounts.views.render') as mock_render:
            mock_render.return_value = HttpResponse('ok')
            resp = accounts_views.register(req)
            self.assertEqual(resp.status_code, 200)
