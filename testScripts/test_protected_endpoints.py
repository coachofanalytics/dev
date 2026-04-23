"""Test protected transaction endpoints with JWT token"""
import requests

BASE_URL = "http://127.0.0.1:8000"

def get_token():
    """Login and get JWT token"""
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "newuser",
        "password": "mypassword123"
    })
    
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_create_transaction(token):
    """Test creating a transaction with valid token"""
    headers = {"Authorization": f"Bearer {token}"}
    
    transaction_data = {
        "sender": "Test Sender",
        "receiver": "Test Receiver",
        "phone": "+1234567890",
        "type": "test",
        "activity_date": "2026-04-23T10:00:00Z",
        "receipt_link": "https://test.com/receipt",
        "qty": 1,
        "amount": 100.50,
        "transaction_cost": 5.00,
        "description": "Test transaction",
        "payment_method": "credit_card",
        "sender_id": 1,
        "department_id": 1,
        "category_id": 1,
        "subcategory_id": 1
    }
    
    response = requests.post(f"{BASE_URL}/transaction", json=transaction_data, headers=headers)
    
    if response.status_code == 201:
        print("✅ Create transaction: SUCCESS")
        print(f"   Response ID: {response.json().get('id')}")
        return response.json().get("id")
    else:
        print(f"❌ Create transaction failed: {response.status_code}")
        print(f"   {response.text}")
        return None

def test_get_transactions(token):
    """Test getting transactions with valid token"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/transaction", headers=headers)
    
    if response.status_code == 200:
        print(f"✅ Get transactions: SUCCESS ({len(response.json())} transactions)")
        return True
    else:
        print(f"❌ Get transactions failed: {response.status_code}")
        return False

def test_without_token():
    """Test accessing endpoint without token (should fail)"""
    transaction_data = {
        "sender": "Unauthorized Test",
        "receiver": "Test",
        "phone": "+1234567890",
        "type": "test",
        "activity_date": "2026-04-23T10:00:00Z",
        "receipt_link": "https://test.com",
        "qty": 1,
        "amount": 100,
        "transaction_cost": 5,
        "description": "This should fail",
        "payment_method": "cash",
        "sender_id": 1,
        "department_id": 1,
        "category_id": 1,
        "subcategory_id": 1
    }
    
    response = requests.post(f"{BASE_URL}/transaction", json=transaction_data)
    
    # HTTPBearer returns 403 when no credentials provided
    if response.status_code == 403:
        print("✅ Without token: REJECTED (403 Forbidden) - Good!")
        return True
    else:
        print(f"❌ Without token: Should fail with 403 but got {response.status_code}")
        return False

def test_invalid_token():
    """Test with invalid token"""
    headers = {"Authorization": "Bearer invalid-token-12345"}
    
    response = requests.get(f"{BASE_URL}/transaction", headers=headers)
    
    if response.status_code == 401:
        print("✅ Invalid token: REJECTED (401 Unauthorized) - Good!")
        return True
    else:
        print(f"❌ Invalid token: Should fail with 401 but got {response.status_code}")
        return False

if __name__ == "__main__":
    print("\n🚀 Testing Protected Endpoints\n")
    
    print("1. Getting JWT token...")
    token = get_token()
    
    if not token:
        print("❌ Could not get token. Make sure server is running and user exists.")
        exit(1)
    
    print(f"   Token acquired: {token[:50]}...\n")
    
    print("2. Testing without token:")
    test_without_token()
    
    print("\n3. Testing with invalid token:")
    test_invalid_token()
    
    print("\n4. Testing with valid token:")
    test_get_transactions(token)
    test_create_transaction(token)
    
    print("\n✅ Protected endpoints test complete!")
