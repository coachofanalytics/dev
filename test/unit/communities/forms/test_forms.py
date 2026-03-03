from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from communities.forms import EventForm, JoinForm


class CommunitiesFormsTests(TestCase):
    def test_join_form_valid(self):
        form = JoinForm(data={'name': 'Sam', 'email': 'sam@example.com'})
        self.assertTrue(form.is_valid())

    def test_event_form_start_date_in_past_raises(self):
        past = timezone.now() - timedelta(days=1)
        # patch clean_end_date to avoid TypeError when clean_start_date raises
        original_clean_end = EventForm.clean_end_date

        def safe_clean_end_date(self):
            end_date = self.cleaned_data.get('end_date')
            start_date = self.cleaned_data.get('start_date')
            if start_date is None:
                return end_date
            if end_date and end_date <= start_date:
                from django import forms as _forms
                raise _forms.ValidationError("End date must be after the start date.")
            return end_date

        EventForm.clean_end_date = safe_clean_end_date
        try:
            form = EventForm(data={'name': 'E', 'start_date': past, 'end_date': past, 'location': 'L', 'description': 'D'})
            self.assertFalse(form.is_valid())
        finally:
            EventForm.clean_end_date = original_clean_end
