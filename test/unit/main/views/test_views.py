from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from unittest.mock import patch

import main.views as main_views


class MainViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_healthcare_info_renders(self):
        req = self.factory.get('/')
        with patch('main.views.render') as mock_render:
            mock_render.return_value = HttpResponse('ok')
            resp = main_views.healthcare_info(req)
            self.assertEqual(resp.status_code, 200)

    def test_scholarship_search_get(self):
        req = self.factory.get('/')
        with patch('main.views.render') as mock_render:
            mock_render.return_value = HttpResponse('ok')
            resp = main_views.scholarship_search(req)
            self.assertEqual(resp.status_code, 200)
