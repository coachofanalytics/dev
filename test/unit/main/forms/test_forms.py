from django.test import TestCase
from main.forms import ContactForm, ScholarshipSearchForm


class MainFormsTests(TestCase):
    def test_contact_form_defaults_not_required(self):
        form = ContactForm(data={})
        # user and topic are not required per __init__
        self.assertTrue('user' in form.fields)
        self.assertFalse(form.fields['user'].required)

    def test_scholarship_search_form_fields(self):
        form = ScholarshipSearchForm(data={'search_keyword': 'STEM'})
        self.assertTrue(form.is_valid())
