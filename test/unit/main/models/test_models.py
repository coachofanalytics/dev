from django.test import TestCase
from main.models import Assets, Content


class AssetsModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.asset1 = Assets.objects.create(name='background_image', category='bg')
        cls.asset2 = Assets.objects.create(name='singleword', category='bg')

    def test_split_name_returns_list_when_underscore(self):
        parts = self.asset1.split_name
        self.assertIsInstance(parts, list)

    def test_split_name_returns_string_when_no_underscore(self):
        parts = self.asset2.split_name
        self.assertIsInstance(parts, str)


class ContentModelTests(TestCase):
    def test_str_when_title_missing(self):
        content = Content.objects.create(section='Our Story', description='desc')
        self.assertIn('Content', str(content))
