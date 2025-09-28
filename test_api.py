import requests
import json
import uuid

BASE_URL = "http://127.0.0.1:8000/api"

def test_endpoint(url, method="GET", data=None, expected_status=200):
    """Test an API endpoint with customizable expected status"""
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        print(f"\nTesting: {url}")
        print(f"Status: {response.status_code}")
        if response.status_code == expected_status:
            print("✓ Success!")
            try:
                return response.json()
            except json.JSONDecodeError:
                print("Note: Response is not JSON")
                return response.text
        else:
            print("✗ Failed!")
            print(f"Expected: {expected_status}, Got: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print("=== Testing Movie Recommendation API ===\n")
    
    # Generate unique test data
    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "username": f"testuser_{unique_id}",
        "password": "testpass123", 
        "email": f"test_{unique_id}@example.com"
    }

    print(f"Testing with user: {user_data['username']}")

    # 1. Test public endpoints
    print("1. Testing public endpoints...")
    test_endpoint(f"{BASE_URL}/movies/health/")
    test_endpoint(f"{BASE_URL}/movies/trending/")
    test_endpoint(f"{BASE_URL}/movies/search/?q=avengers")
    test_endpoint(f"{BASE_URL}/docs/")

    # 2. Test user registration
    print("\n2. Testing user registration...")
    test_endpoint(f"{BASE_URL}/auth/register/", "POST", user_data, expected_status=201)

    # 3. Test user login
    print("\n3. Testing user login...")
    login_data = {"username": user_data["username"], "password": user_data["password"]}
    test_endpoint(f"{BASE_URL}/auth/login/", "POST", login_data, expected_status=200)

    # 4. Test with invalid credentials
    print("\n4. Testing with invalid credentials...")
    invalid_data = {"username": "nonexistent", "password": "wrongpass"}
    test_endpoint(f"{BASE_URL}/auth/login/", "POST", invalid_data, expected_status=401)

    print("\n=== Testing Complete ===")

if __name__ == "__main__":
    main()