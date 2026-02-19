from django.test import SimpleTestCase
from django.urls import reverse, NoReverseMatch


class UrlsTests(SimpleTestCase):
    def test_named_urls_resolve(self):
        names = [
            'communities:join',
            'communities:member_directory',
            'communities:join_directory_form',
        ]
        for name in names:
            try:
                reverse(name)
            except NoReverseMatch:
                self.fail(f"URL name '{name}' did not reverse")
