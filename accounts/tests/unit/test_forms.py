from django.test import TestCase
# from accounts.forms import UserForm,CredentialForm
# from accounts.models import CustomerUser, Department, Credential, CredentialCategory, TaskGroups, Tracker

from accounts.forms import PaymentInformationForm
from accounts.forms import UserForm, PaymentInformationForm
from accounts.models import CustomerUser
from django.utils import timezone


from django.utils import timezone

# class TestForms(TestCase):

#     def test_user_form_valid_data(self):
#         form = UserForm(data={
#             'category': '1',
#             'sub_category': '1',
#             'first_name': 'john',
#             'last_name': 'doe',
#             'username': 'johndoeeeee',
#             'password1': 'Passw@rd123',
#             'password2': 'Passw@rd123',
#             'phone': '1234567890',
#             'gender': '1',
#             'email': 'johndoe@gmail.com',
#             'address': '1234 Main Street',
#             'city': 'New York',
#             'state': 'NY',
#             'country': 'US',
#         })

#         self.assertTrue(form.is_valid())

#     def test_user_form_no_data(self):
#         form = UserForm(data={})

#         self.assertFalse(form.is_valid())
#         self.assertEquals(len(form.errors), 10)
    
#     #########################################################################
#     # test cases for category in which username and password are not required
#     #########################################################################
#     def test_user_form_valid_data_Jobsupport(self):

#         form = UserForm(data={
#             'category': '3',
#             'sub_category': '6',
#             'first_name': 'cat',
#             'last_name': 'doe',
#             'email': 'johndoe@gmail.com',
#             'country': 'US',
#         })
#         self.assertTrue(form.is_valid())
    
#     def test_user_form_no_data_jobsupport(self):

#         form = UserForm(data={
#             'category': '3'
#         })
        
#         self.assertFalse(form.is_valid())
#         self.assertEquals(len(form.errors), 4)

# class TestCredentialForm(TestCase):

#     def test_user_form_valid_data(self):
#         self.category = CredentialCategory.objects.create(category='Test Category',slug='test-category',description='Test Description')
#         self.user =  CustomerUser.objects.create(
#             first_name='John',
#             last_name='Doe',
#             email= 'johndoe@gmail.com',
#             gender='1',
#             is_staff=True,
#             is_active=True,
#             )
#         self.credential = Credential.objects.create(
#             # category=self.category,
#             added_by=self.user,
#             name='Test Credential',
#             slug='test-credential',
#             description='Test Description')
#         self.assertEqual(str(self.credential), 'Test Credential')
     

class PaymentInformationFormTest(TestCase):
    """✅ Tests for the PaymentInformationForm"""

    def setUp(self):
        self.customer = CustomerUser.objects.create(
            first_name="Chris",
            last_name="Maghas",
            email="chris@example.com",
            is_active=True
        )

    def test_valid_form(self):
        """✅ Should be valid with proper data"""
        form_data = {
            "customer_id": self.customer,  # use the object, not .id
            "payment_fees": 10000.00,
            "down_payment": 500.00,
            "student_bonus": 200.00,
            "plan": 1,
            "subplan": 1,
            "payment_method": "Mpesa",
            "contract_submitted_date": timezone.now(),
            "client_signature": "Signed",
            "company_rep": "Manager",
            "client_date": "2025-10-21",
            "rep_date": "2025-10-21",
        }

        form = PaymentInformationForm(data=form_data)
        print("Form Errors (if any):", form.errors)
        self.assertTrue(form.is_valid())

    def test_invalid_form_missing_fields(self):
        """❌ Should fail when required fields are missing"""
        form = PaymentInformationForm(data={})
        self.assertFalse(form.is_valid())
        self.assertGreater(len(form.errors), 0)

