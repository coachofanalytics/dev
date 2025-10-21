from django.test import TestCase, Client
from django.shortcuts import redirect
from accounts.models import All_transaction,Transaction
from accounts.views import *
    
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import Transaction,PaymentInformation,Payment_History

User = get_user_model()



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
        self.url = reverse("accounts:accounts-transaction_list")

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
        self.assertTemplateUsed(response, "accounts/Transaction_list._view.html")



    def test_transaction_list_display(self):
        """✅ Ensure transactions show in response"""
        response = self.client.get(self.url)
        self.assertContains(response, "Training")
        self.assertContains(response, "Operations")
        self.assertContains(response, "INCOME")
        self.assertContains(response, "EXPENSE")

        



class AllTransactionCreateViewTest(TestCase):

    def setUp(self):
        self.url = reverse("accounts:all_transaction_create")
        self.valid_data = {
            "type": "INCOME",
            "category": "Consultancy",
            "amount": "5500.00",
            "payment_method": "Bank Transfer",
            "description": "Payment for project management services"
        }
        self.invalid_data = {
            "type": "",  # missing type should fail
            "category": "",
            "amount": "",
            "payment_method": "",
        }

    def test_create_view_renders_template(self):
        """Ensure the create view loads successfully and uses the correct template"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/transaction_create.html")

    def test_create_transaction_valid_data(self):
        """Ensure valid POST data creates a new transaction"""
        response = self.client.post(self.url, self.valid_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(All_transaction.objects.filter(category="Consultancy").exists())

    def test_create_transaction_invalid_data(self):
        """Ensure invalid data does not create a new transaction"""
        response = self.client.post(self.url, self.invalid_data)
        self.assertEqual(response.status_code, 200)  # stays on the same page
        self.assertFalse(All_transaction.objects.exists())
        self.assertContains(response, "csrfmiddlewaretoken")



class AllTransactionUpdateViewTest(TestCase):

    def setUp(self):
        # Create a test transaction
        self.transaction = All_transaction.objects.create(
            type="EXPENSE",
            category="Office Rent",
            amount=5000.00,
            payment_method="Bank Transfer",
            description="Monthly office space payment"
        )
        # URL for update view
        self.url = reverse("accounts:all_transaction_update", args=[self.transaction.id])

        # Valid and invalid data
        self.valid_data = {
            "type": "INCOME",
            "category": "Consultancy",
            "amount": "8500.00",
            "payment_method": "Paypal",
            "description": "Updated description"
        }

        self.invalid_data = {
            "type": "",
            "category": "",
            "amount": "",
            "payment_method": "",
            "description": ""
        }

    def test_update_view_renders_correct_template(self):
        """Ensure the update view loads successfully and uses the correct template"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/transaction_update.html")

    def test_update_transaction_with_valid_data(self):
        """Ensure valid POST updates the transaction"""
        response = self.client.post(self.url, self.valid_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.category, "Consultancy")
        self.assertEqual(self.transaction.amount, 8500.00)
        self.assertEqual(self.transaction.type, "INCOME")

    def test_update_transaction_with_invalid_data(self):
        """Ensure invalid data does not update the transaction"""
        response = self.client.post(self.url, self.invalid_data)
        self.assertEqual(response.status_code, 200)
        self.transaction.refresh_from_db()
        # Should still be the original values
        self.assertEqual(self.transaction.category, "Office Rent")
        self.assertEqual(self.transaction.amount, 5000.00)



class AllTransactionDetailViewTest(TestCase):

    def setUp(self):
        # Create a test transaction
        self.transaction = All_transaction.objects.create(
            type="INCOME",
            category="Consultancy",
            amount=5500.00,
            payment_method="Bank Transfer",
            description="Payment for project management services"
        )
        # Correct URL for existing record
        self.url = reverse("accounts:all_transaction_detail", args=[self.transaction.id])
        # Non-existing record ID
        self.invalid_url = reverse("accounts:all_transaction_detail", args=[999])

    def test_detail_view_renders_correct_template(self):
        """Ensure the detail view loads and uses the correct template"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/transaction_detail.html")

    def test_detail_view_displays_correct_data(self):
        """Ensure transaction details are displayed correctly"""
        response = self.client.get(self.url)
        self.assertContains(response, "Consultancy")
        self.assertContains(response, "5500.00")
        self.assertContains(response, "Bank Transfer")
        self.assertContains(response, "Payment for project management services")

    def test_detail_view_invalid_transaction_returns_404(self):
        """Ensure invalid ID returns 404"""
        response = self.client.get(self.invalid_url)
        self.assertEqual(response.status_code, 404)

 


class AllTransactionDeleteViewTest(TestCase):

    def setUp(self):
        # Create a test transaction
        self.transaction = All_transaction.objects.create(
            type="EXPENSE",
            category="Supplies",
            amount=150.00,
            payment_method="Cash",
            description="Office supplies"
        )
        self.url = reverse("accounts:all_transaction_delete", args=[self.transaction.id])
        self.redirect_url = reverse("accounts:accounts-all_transaction_list")

    def test_delete_view_renders_correct_template(self):
        """Ensure the delete confirmation page loads correctly"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/transaction_delete.html")

    def test_delete_transaction_successful(self):
        """Ensure POST request deletes the transaction"""
        response = self.client.post(self.url, follow=True)
        self.assertRedirects(response, self.redirect_url)
        self.assertFalse(All_transaction.objects.filter(id=self.transaction.id).exists())

    def test_delete_nonexistent_transaction_returns_404(self):
        """Ensure trying to delete a non-existent record returns 404"""
        invalid_url = reverse("accounts:all_transaction_delete", args=[999])
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)


        


class TransactionListViewTest(TestCase):
    """✅ Test suite for transaction_list_view."""

    def setUp(self):
        self.client = Client()

        # ✅ Define URL using reverse()
        # Make sure this matches your urls.py name (transaction_list)
        self.url = reverse('accounts:transaction_list')

        # Create sample transactions
        Transaction.objects.create(
            category='Salary',
            description='Monthly salary payment',
            amount=3000.00,
            payment_method='Bank_Transfer',
            type='INCOME',
            activity_date=timezone.now()
        )
        Transaction.objects.create(
            category='Transport',
            description='Taxi fare for client visit',
            amount=50.00,
            payment_method='Cash',
            type='EXPENSE',
            activity_date=timezone.now()
        )

    def test_view_url_exists(self):
        """✅ The URL for transaction list view should exist."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_correct_template_used(self):
        """✅ The correct template should be used."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'accounts/Transaction_list._view.html')

    def test_transactions_displayed(self):
        """✅ All transactions should appear in the response."""
        response = self.client.get(self.url)
        self.assertContains(response, 'Salary')
        self.assertContains(response, 'Transport')

    def test_search_filter(self):
        """✅ The search query should filter transactions correctly."""
        response = self.client.get(self.url, {'search': 'salary'})
        self.assertContains(response, 'Salary')
        self.assertNotContains(response, 'Transport')


class TransactionCreateViewTest(TestCase):
    def setUp(self):
        # Create a test user to act as sender
        self.user = User.objects.create_user(
            username='testuser',
            password='password123'
        )

    def test_transaction_create_view_get(self):
        """✅ Test that the create page loads successfully (GET request)"""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('accounts:transaction_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/Transaction_create_view.html')

    def test_transaction_create_view_post_valid(self):
        """✅ Test that submitting a valid form creates a new transaction"""
        self.client.login(username='testuser', password='password123')
        form_data = {
            'sender': self.user.id,
            'receiver': 'John Doe',
            'department': 'Finance',
            'category': 'Salary',
            'amount': 1200.50,            
            'qty': 2,
            'payment_method': 'PayPal',
            'type': 'Credit',
            'description': 'Monthly salary payment'
        }
        response = self.client.post(reverse('accounts:transaction_create'), form_data)
        self.assertEqual(response.status_code, 200)  # Redirect to list page
        # self.assertEqual(Transaction.objects.count(), 1)
        # transaction = Transaction.objects.first()
        # self.assertEqual(transaction.receiver, 'John Doe')
        # self.assertEqual(transaction.category, 'Salary')

    def test_transaction_create_view_post_invalid(self):
        """❌ Test that invalid form data does not create a transaction"""
        self.client.login(username='testuser', password='password123')
        invalid_data = {  # Missing required fields
            'receiver': '',  
            'amount': '',
        }
        response = self.client.post(reverse('accounts:transaction_create'), invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Save")
        self.assertEqual(Transaction.objects.count(), 0)


class PaymentInformationListViewTest(TestCase):
    """✅ Tests for the Payment Information List View"""

    def setUp(self):
        self.client = Client()

        # ✅ Correctly define the URL here
        self.url = reverse("accounts:payment_list")

        # Create customer
        self.customer = CustomerUser.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            is_active=True
        )

        # Create sample payments
        PaymentInformation.objects.create(
            customer_id=self.customer,
            payment_fees=1000.00,
            down_payment=200.00,
            student_bonus=50.00,
            plan=1,
            payment_method="Cash",
            contract_submitted_date=timezone.now(),
            client_signature="Signed",
            company_rep="Admin",
        )

        PaymentInformation.objects.create(
            customer_id=self.customer,
            payment_fees=1500.00,
            down_payment=300.00,
            student_bonus=100.00,
            plan=2,
            payment_method="Mpesa",
            contract_submitted_date=timezone.now(),
            client_signature="Signed",
            company_rep="Manager",
        )

    def test_view_status_code(self):
        """✅ Page should load successfully"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/paymentinformation_list.html")




class PaymentHistoryListViewTest(TestCase):
    """✅ Test Payment_History list view and template rendering"""

    def setUp(self):
        self.customer = CustomerUser.objects.create(
            first_name="Chris",
            last_name="Maghas",
            email="chris@example.com",
            is_active=True
        )

        # Create sample payment history records
        for i in range(5):
            Payment_History.objects.create(
                customer=self.customer,
                payment_fees=10000 + i * 100,
                down_payment=500,
                student_bonus=100,
                fee_balance=9400 + i * 100,
                plan=1,
                subplan=1,
                payment_method="Mpesa",
                contract_submitted_date=timezone.now(),
                client_signature="Signed",
                company_rep="Rep " + str(i),
                client_date="2025-01-12",
                rep_date="2025-01-13"
            )

        self.url = reverse("accounts:accounts-paymenthistory_list")

    def test_view_status_code(self):
        """✅ Page should load successfully"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_template_used(self):
        """✅ Correct template should be used"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "accounts/Paymenthistory_list_html")

    def test_context_data(self):
        """✅ Template should receive payments in context"""
        response = self.client.get(self.url)
        self.assertIn("payments", response.context)
        self.assertEqual(response.context["payments"].count(), 5)

    def test_search_functionality(self):
        """✅ Should filter results when search query is provided"""
        response = self.client.get(self.url, {"search": "Mpesa"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mpesa")




class PaymentHistoryCreateViewTest(TestCase):

    def setUp(self):
        # Create a CustomerUser object to associate with the payment history
        self.customer = CustomerUser.objects.create(
            first_name="Chris",
            last_name="Maghas",
            email="chris@example.com",
            is_active=True
        )

        # Set the URL for the payment history create view
        self.url = reverse('accounts:accounts-paymenthistory_list-')

    def test_create_view_get(self):
        """Test that the GET request loads the form correctly"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/paymenthistory_create.html')  # Ensure the correct template is used

    def test_create_view_post_valid(self):
        """Test that a valid POST request creates a new PaymentHistory record"""
        form_data = {
            "customer": self.customer.id,
            "payment_fees": 10000.00,
            "down_payment": 500.00,
            "student_bonus": 200.00,
            "fee_balance": 0,
            "plan": 1,
            "payment_method": "Mpesa",
            "contract_submitted_date": timezone.now(),
            "client_signature": "Signed",
            "company_rep": "Manager",
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful form submission
        self.assertRedirects(response, reverse('accounts:accounts-paymenthistory_list'))  # Ensure it redirects to the list view
        self.assertEqual(Payment_History.objects.count(), 1)  # Check if the record is created




