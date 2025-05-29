from core.db.database import SessionLocal
from models.accounts.users import CustomerUser
from datetime import datetime
import uuid

def init_test_data():
    """Initialize test data in the database."""
    print("Starting test data initialization...")
    
    db = SessionLocal()
    try:
        # Create test users
        test_users = [
            CustomerUser(
                username="testuser1",
                email="test1@example.com",
                first_name="Test",
                last_name="User1",
                is_admin=False,
                is_staff=False,
                is_client=True,
                is_applicant=False,
                is_employee_contract_signed=False,
                email_verified=True
            ),
            CustomerUser(
                username="testuser2",
                email="test2@example.com",
                first_name="Test",
                last_name="User2",
                is_admin=False,
                is_staff=True,
                is_client=True,
                is_applicant=False,
                is_employee_contract_signed=False,
                email_verified=True
            ),
            CustomerUser(
                username="admin",
                email="admin@example.com",
                first_name="Admin",
                last_name="User",
                is_admin=True,
                is_staff=True,
                is_client=False,
                is_applicant=False,
                is_employee_contract_signed=True,
                email_verified=True
            )
        ]
        
        # Add users to database
        for user in test_users:
            db.add(user)
        
        db.commit()
        print("Test data initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing test data: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_test_data() 