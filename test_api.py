import requests
import json

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

# Test all endpoints
print("=== Testing Movie Recommendation API ===\n")

# Test with unique username to avoid "already exists" error
user_data = {
    "username": f"testuser_{requests.get('http://httpbin.org/uuid').json()['uuid'][:8]}",
    "password": "testpass123", 
    "email": f"test_{requests.get('http://httpbin.org/uuid').json()['uuid'][:8]}@example.com"
}

print(f"Testing with user: {user_data['username']}")

# Public endpoints (no auth required)
print("1. Testing public endpoints...")
test_endpoint(f"{BASE_URL}/movies/trending/")
test_endpoint(f"{BASE_URL}/movies/search/?q=avengers")
test_endpoint(f"{BASE_URL}/docs/")

# Test user registration
print("\n2. Testing user registration...")
test_endpoint(f"{BASE_URL}/auth/register/", "POST", user_data, expected_status=201)

# Test user login
print("\n3. Testing user login...")
login_data = {"username": user_data["username"], "password": user_data["password"]}
test_endpoint(f"{BASE_URL}/auth/login/", "POST", login_data, expected_status=200)

print("\n=== Testing Complete ===")