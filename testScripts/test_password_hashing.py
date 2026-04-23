"""Simple test to verify password hashing works"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_password_hashing():
    print("=" * 50)
    print("TEST 3: Password Hashing")
    print("=" * 50)
    
    test_password = "MySecretPassword123!"
    
    try:
        from app.core.security.hashing import get_password_hash, verify_password
        
        # Test 1: Hash password
        print("\n1. Hashing password...")
        hashed = get_password_hash(test_password)
        print(f"   Original: {test_password}")
        print(f"   Hashed: {hashed[:50]}...")
        print("   ✅ Hash created successfully")
        
        # Test 2: Verify correct password
        print("\n2. Verifying correct password...")
        is_valid = verify_password(test_password, hashed)
        print(f"   Result: {is_valid}")
        print("   ✅ Correct password verified" if is_valid else "   ❌ Failed!")
        
        # Test 3: Verify wrong password
        print("\n3. Verifying wrong password...")
        is_valid = verify_password("WrongPassword", hashed)
        print(f"   Result: {is_valid}")
        print("   ✅ Wrong password rejected" if not is_valid else "   ❌ Failed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    test_password_hashing()
