from django.test import TestCase
from accounts.models import Payment_History
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import LoginHistory

from django.test import TestCase
from django.utils import timezone
from accounts.models import Tracker


User = get_user_model()
User = get_user_model()

# class TestDepartmentModel(TestCase):
#     def setUp(self):
#         self.department_obj = Department.objects.create(name='HR Department', slug='test_hr_department')
        

#     # def test_department_name(self):
#     #     self.assertEqual(self.department.name, 'Test Department')

#     def test_model_str(self):
        
#         self.assertTrue(isinstance(self.department_obj, Department))
#         self.assertEqual(str(self.department_obj.name), 'HR Department')

#     # def test_model_get_by_id(self):
#     #     import pdb; pdb.set_trace()
#     #     fetch_department_by_id = Department.objects.get_by_id(self.department_obj.id)

#     #     self.assertTrue(fetch_department_by_id, 1)
    
#     def test_model_get_by_wrong_id(self):
        
#         fetch_department_by_id = Department.objects.get_by_id(20)

        # self.assertEquals(fetch_department_by_id, None)


# class TestTaskGroups(TestCase):

#     def test_model_str(self):
#         title = TaskGroups.objects.create(title='Group X')
#         description = TaskGroups.objects.create(description='Dummy Description For Group X')
#         self.assertEqual(str(title), 'Group X')

# class TestTrackerModel(TestCase):

#     def test_model_create(self):
#         self.category = "Interview"
#         self.task = "database"
#         self.duration = 10
#         tracker = Tracker.objects.create(
#             category=self.category,
#             task=self.task,
#             )

    # def test_model_url(self):
    #     tracker = self.test_model_create()
    #     response = self.client.post(reverse('usertime', args=['johndoee']))
    #     self.assertEqual(response.status_code, 200)

# class TestCredentialCategory(TestCase):

#     def test_model_str(self):
#         self.category = CredentialCategory.objects.create(category='Test Category',slug='test-category',description='Test Description')
#         self.assertEqual(str(self.category), 'Test Category')

#     # def test_model_url(self):
#     #     self.category = CredentialCategory.objects.create(category='Test Category',slug='test-category',description='Test Description')
#     #     response = self.client.post(reverse('management:credentialcategorylist', args=["test-category"])) #set unit_view to the url name in the urls.py
#     #     self.assertEqual(response.status_code, 200)

# class TestCredential(TestCase):

#     def test_model_str(self):
#         self.user =  CustomerUser.objects.create(
#             first_name='John',
#             last_name='Doe',
#             email= 'johndoe@gmail.com',
#             gender='1',
#             is_staff=True,
#             is_active=True,
#             )
#         self.credential = Credential.objects.create(
#             added_by=self.user,
#             name='Test Credential',
#             slug='test-credential',
#             description='Test Description')
#         self.assertEqual(str(self.credential), 'Test Credential')

    # def test_model_url(self):
    #     self.category = CredentialCategory.objects.create(category='Test Category',slug='test-category',description='Test Description')
    #     self.user =  CustomerUser.objects.create(
    #         first_name='John',
    #         last_name='Doe',
    #         email= 'johndoe@gmail.com',
    #         gender='1',
    #         is_employee=True,
    #         is_active=True,
    #         )
    #     self.credential = Credential.objects.create(
    #         added_by=self.user,
    #         name='Test Credential',
    #         slug='test-credential',
    #         description='Test Description')
    #     response = self.client.post(reverse('management:credential'))
    #     self.assertEqual(response.status_code, 200)

    # accounts/tests/test_payment_history_model.py



class PaymentHistoryModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )

    def test_fee_balance_calculation_without_bonus(self):
        payment = Payment_History.objects.create(
            customer=self.user,
            payment_fees=5000,
            down_payment=500,
            plan=1,
            payment_method="Cash",
            client_signature="Client Sign",
            company_rep="Company Rep"
        )

        self.assertEqual(payment.fee_balance, 4500)

    def test_fee_balance_calculation_with_bonus(self):
        payment = Payment_History.objects.create(
            customer=self.user,
            payment_fees=5000,
            down_payment=500,
            student_bonus=1000,
            plan=1,
            payment_method="MPESA",
            client_signature="Client Sign",
            company_rep="Company Rep"
        )

        self.assertEqual(payment.fee_balance, 3500)

    def test_fee_balance_never_negative(self):
        payment = Payment_History.objects.create(
            customer=self.user,
            payment_fees=1000,
            down_payment=1500,
            student_bonus=500,
            plan=1,
            payment_method="Cash",
            client_signature="Client Sign",
            company_rep="Company Rep"
        )

        self.assertEqual(payment.fee_balance, 0)

    def test_string_representation(self):
        payment = Payment_History.objects.create(
            customer=self.user,
            payment_fees=3000,
            down_payment=500,
            plan=1,
            payment_method="Cash",
            client_signature="Client Sign",
            company_rep="Company Rep"
        )

        self.assertIn("Payment History", str(payment))





class LoginHistoryModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="angel",
            email="angel@example.com",
            password="testpass123"
        )

    def test_login_history_creation(self):
        """LoginHistory object is created correctly"""
        history = LoginHistory.objects.create(
            user=self.user,
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            login_time=timezone.now()
        )

        self.assertEqual(history.user, self.user)
        self.assertEqual(history.ip_address, "127.0.0.1")
        self.assertIsNotNone(history.login_time)

    def test_string_representation(self):
        """__str__ returns meaningful text"""
        history = LoginHistory.objects.create(
            user=self.user,
            ip_address="192.168.1.10",
            user_agent="Chrome"
        )

        self.assertIn(self.user.username, str(history))

    def test_default_login_time_is_set(self):
        """login_time is auto-set if not provided"""
        history = LoginHistory.objects.create(
            user=self.user,
            ip_address="10.0.0.1",
            user_agent="TestAgent"
        )

        self.assertIsNotNone(history.login_time)




class TrackerModelTest(TestCase):

    def setUp(self):
        """Create a sample Tracker instance for testing"""
        self.tracker = Tracker.objects.create(
            category="Training",
            sub_category="Data Analysis",
            plan="Monthly Plan",
            empname=101,
            author=1,
            employee="John Mwangi",
            login_date=timezone.now(),
            start_time=timezone.now().time(),
            duration=120,
            time=120,
        )

    def test_tracker_instance_created(self):
        """Tracker object should be created successfully"""
        self.assertEqual(Tracker.objects.count(), 1)

    def test_tracker_field_values(self):
        """Tracker fields should store correct values"""
        tracker = self.tracker

        self.assertEqual(tracker.category, "Training")
        self.assertEqual(tracker.sub_category, "Data Analysis")
        self.assertEqual(tracker.plan, "Monthly Plan")
        self.assertEqual(tracker.empname, 101)
        self.assertEqual(tracker.author, 1)
        self.assertEqual(tracker.employee, "John Mwangi")
        self.assertEqual(tracker.duration, 120)
        self.assertEqual(tracker.time, 120)

    def test_tracker_login_date_is_datetime(self):
        """login_date should be a datetime value"""
        self.assertIsNotNone(self.tracker.login_date)

    def test_duration_is_positive(self):
        """Duration should always be positive"""
        self.assertGreater(self.tracker.duration, 0)

    def test_time_matches_duration(self):
        """Time should match duration for single entry"""
        self.assertEqual(self.tracker.time, self.tracker.duration)

    def test_string_representation(self):
        """__str__ method should return a readable value"""
        tracker_str = str(self.tracker)
        self.assertIn("John Mwangi", tracker_str)
        self.assertIn("Training", tracker_str)
