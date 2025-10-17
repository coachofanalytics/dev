from django.test import TestCase, Client
from django.shortcuts import redirect
from accounts.models import All_transaction
from accounts.views import *



# class TestTrackView(TestCase):

#     def setUp(self):
#         self.client = Client()

#     def test_track_create_view(self):
    
#         self.tracker = Tracker.objects.create(
#             category= 'Job_Support',
#             task= 'database',
#         )

#         self.assertEqual(Tracker.objects.count(), 1)

#     def test_track_update_view(self):
#         self.tracker = Tracker.objects.create(
#             category= 'Job_Support',
#             task= 'database',
#         )
#         self.tracker_update = self.tracker
#         self.tracker_update.category = 'Interview'
#         self.tracker_update.save()

#         self.assertEqual(self.tracker_update.category, 'Interview')

#     def test_track_delete_view(self):
#         self.category = "Interview"
#         self.task = "database"
#         self.duration = 10
#         self.tracker = Tracker.objects.create(
#             category=self.category,
#             task=self.task,
#             )
#         self.tracker.delete()
#         self.assertEqual(Tracker.objects.count(), 0)

# class TestUserTrackerView(TestCase):

#     def setUp(self):
#         self.client = Client()
#         self.user_tracker_url = redirect('/accounts/tracker')

#     def test_user_tracker_view(self):
#         self.user =  CustomerUser.objects.create(
#             first_name='John',
#             last_name='Doe',
#             email= 'johndoe@gmail.com',
#             gender='1',
#             # is_employee=True,
#             is_active=True,
#             username='johndoee',
#         )

#         response = self.client.post(self.user_tracker_url)
#         self.assertEqual(CustomerUser.objects.count(), 1)

#         # self.assertEqual(response.status_code, 200)
#         # self.assertTemplateUsed(response, 'accounts/usertracker.html')

#         trackers = Tracker.objects.all().filter(author=self.user).count()
#         self.assertEqual(int(trackers), 0)

# class TestUserDeleteView(TestCase):
    
#     def setUp(self):
#         self.client = Client()

#     def test_user_delete_view(self):
#         self.user =  CustomerUser.objects.create(
#             first_name='John',
#             last_name='Doe',
#             email= 'johndoe@gmail.com',
#             gender='1',
#             # is_employee=True,
#             is_active=True,
#             username='johndoee',
#         )
#         self.assertEqual(CustomerUser.objects.all().count(), 1)
#         self.user.delete()
#         self.assertEqual(CustomerUser.objects.all().count(), 0)


# class TestClientView(TestCase):

#     def setUp(self):
#         self.client = Client()

#     def test_client_create_view(self):
#         self.user =  CustomerUser.objects.create(
#             first_name='John',
#             last_name='Doe',
#             email= 'johndoe@gmail.com',
#             category=1,
#             sub_category=4,
#             is_client=True,
#             username='johndoee',
#         )
#         self.assertEqual(CustomerUser.objects.all().count(), 1)
    
#     def test_client_update_view(self):
#         self.user =  CustomerUser.objects.create(
#             first_name='John',
#             last_name='Doe',
#             email= 'johndoe@gmail.com',
#             category=1,
#             sub_category=4,
#             is_client=True,
#             username='johndoee',
#         )
#         self.assertEqual(CustomerUser.objects.all().count(), 1)
#         self.user_update = self.user
#         self.user_update.first_name = 'Jane'
#         self.user_update.save()
#         self.assertEqual(self.user_update.first_name, 'Jane')
    
#     def test_client_delete_view(self):
#         self.user =  CustomerUser.objects.create(
#             first_name='John',
#             last_name='Doe',
#             email= 'johndoe@gmail.com',
#             category=1,
#             sub_category=4,
#             is_client=True,
#             username='johndoee',
#         )
#         self.assertEqual(CustomerUser.objects.all().count(), 1)
#         self.user.delete()
#         self.assertEqual(CustomerUser.objects.all().count(), 0)



class AllTransactionListViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        # ✅ Correct reverse call with namespace and route name
        self.url = reverse("accounts:all_transaction_list")

        # ✅ Create sample data
        All_transaction.objects.create(
            type="INCOME",
            category="Training",
            amount=1200.00,
            payment_method="Bank Transfer",
            description="Payment from CODA Analytics student"
        )
        All_transaction.objects.create(
            type="EXPENSE",
            category="Operations",
            amount=800.00,
            payment_method="Cash",
            description="Office maintenance cost"
        )

    def test_view_url_exists(self):
        """✅ Check that the view URL loads"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        """✅ Check the correct template"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "accounts/transaction_list.html")



    def test_transaction_list_display(self):
        """✅ Ensure transactions show in response"""
        response = self.client.get(self.url)
        self.assertContains(response, "Training")
        self.assertContains(response, "Operations")
        self.assertContains(response, "INCOME")
        self.assertContains(response, "EXPENSE")



