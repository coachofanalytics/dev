"""Simple test to verify User model creation"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.db.database import SessionLocal, engine
from app.core.models.users.user import User
from app.core.security.hashing import get_password_hash
from app.core.db.database import Base

def test_user_model():
    print("=" * 50)
    print("TEST 2: User Model Creation")
    print("=" * 50)
    
    # Create tables if they don't exist
    print("\nCreating missing tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created/verified")
    
    db = SessionLocal()
    
    try:
        # Verify table exists
        from sqlalchemy import inspect
        inspector = inspect(db.bind)
        tables = inspector.get_table_names(schema='public')
        
        if 'users' in tables:
            print("✅ Users table exists in database")
        else:
            print("❌ Users table still not found")
            print(f"   Available tables: {tables}")
            return False
        
        # Create a test user
        test_email = "test@example.com"
        test_username = "testuser"
        
        # Delete if already exists
        existing = db.query(User).filter(User.username == test_username).first()
        if existing:
            print(f"⚠️ Test user already exists, deleting first...")
            db.delete(existing)
            db.commit()
        
        # Create new test user
        new_user = User(
            email=test_email,
            username=test_username,
            hashed_password=get_password_hash("testpassword123")
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"\n✅ User created successfully")
        print(f"   ID: {new_user.id}")
        print(f"   Email: {new_user.email}")
        print(f"   Username: {new_user.username}")
        print(f"   Hashed password: {new_user.hashed_password[:50]}...")
        
        # Test password verification
        from app.core.security.hashing import verify_password
        is_valid = verify_password("testpassword123", new_user.hashed_password)
        print(f"\n✅ Password verification test: {is_valid}")
        
        # Clean up - delete test user
        db.delete(new_user)
        db.commit()
        print(f"\n✅ Test user cleaned up (deleted)")
        
        return True
        
    except Exception as e:
        print(f"❌ User model test FAILED")
        print(f"   Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    test_user_model()
