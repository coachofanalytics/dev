from django.test import TestCase
from finance.forms import DepartmentFilterForm, InflowForm


class FinanceFormsTests(TestCase):
    def test_department_filter_form_field_exists(self):
        form = DepartmentFilterForm()
        self.assertIn('name', form.fields)

    def test_inflow_form_initializes(self):
        form = InflowForm()
        self.assertIn('method', form.fields)
