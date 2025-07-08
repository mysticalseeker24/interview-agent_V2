#!/usr/bin/env python3
"""
Manual test script for User Service API endpoints.

This script tests the User Service by making HTTP requests to verify
all endpoints work correctly. Run this after starting the service.

Usage:
    python manual_test.py
"""
import requests
import json
import time
from typing import Dict, Any


class UserServiceTester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    def test_service_health(self) -> bool:
        """Test if service is running."""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("Service Health Check", True, f"Service: {data.get('service', 'Unknown')}")
                return True
            else:
                self.log_test("Service Health Check", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Service Health Check", False, f"Error: {str(e)}")
            return False
    
    def test_user_signup(self) -> Dict[str, Any]:
        """Test user registration."""
        user_data = {
            "email": f"test_{int(time.time())}@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/auth/signup", json=user_data)
            if response.status_code == 200:
                user = response.json()
                self.log_test("User Signup", True, f"Created user: {user['email']}")
                return {"success": True, "user": user, "password": user_data["password"]}
            else:
                self.log_test("User Signup", False, f"Status: {response.status_code}, Response: {response.text}")
                return {"success": False}
        except Exception as e:
            self.log_test("User Signup", False, f"Error: {str(e)}")
            return {"success": False}
    
    def test_duplicate_signup(self, email: str) -> bool:
        """Test duplicate email signup."""
        user_data = {
            "email": email,
            "password": "anotherpassword",
            "full_name": "Duplicate User"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/auth/signup", json=user_data)
            if response.status_code == 400:
                self.log_test("Duplicate Email Signup", True, "Correctly rejected duplicate email")
                return True
            else:
                self.log_test("Duplicate Email Signup", False, f"Expected 400, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Duplicate Email Signup", False, f"Error: {str(e)}")
            return False
    
    def test_user_login(self, email: str, password: str) -> Dict[str, Any]:
        """Test user login."""
        login_data = {
            "username": email,
            "password": password
        }
        
        try:
            response = self.session.post(f"{self.base_url}/auth/login", data=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.log_test("User Login", True, f"Token type: {token_data['token_type']}")
                return {"success": True, "token": token_data["access_token"]}
            else:
                self.log_test("User Login", False, f"Status: {response.status_code}, Response: {response.text}")
                return {"success": False}
        except Exception as e:
            self.log_test("User Login", False, f"Error: {str(e)}")
            return {"success": False}
    
    def test_bad_login(self) -> bool:
        """Test login with bad credentials."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/auth/login", data=login_data)
            if response.status_code == 401:
                self.log_test("Bad Credentials Login", True, "Correctly rejected bad credentials")
                return True
            else:
                self.log_test("Bad Credentials Login", False, f"Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Bad Credentials Login", False, f"Error: {str(e)}")
            return False
    
    def test_get_user_profile(self, token: str) -> Dict[str, Any]:
        """Test getting user profile."""
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = self.session.get(f"{self.base_url}/users/me", headers=headers)
            if response.status_code == 200:
                user_data = response.json()
                self.log_test("Get User Profile", True, f"Email: {user_data['email']}")
                return {"success": True, "user": user_data}
            else:
                self.log_test("Get User Profile", False, f"Status: {response.status_code}")
                return {"success": False}
        except Exception as e:
            self.log_test("Get User Profile", False, f"Error: {str(e)}")
            return {"success": False}
    
    def test_unauthorized_access(self) -> bool:
        """Test accessing protected endpoint without token."""
        try:
            response = self.session.get(f"{self.base_url}/users/me")
            if response.status_code == 401:
                self.log_test("Unauthorized Access", True, "Correctly rejected request without token")
                return True
            else:
                self.log_test("Unauthorized Access", False, f"Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Unauthorized Access", False, f"Error: {str(e)}")
            return False
    
    def test_update_user_profile(self, token: str) -> bool:
        """Test updating user profile."""
        headers = {"Authorization": f"Bearer {token}"}
        update_data = {"full_name": "Updated Test User"}
        
        try:
            response = self.session.put(f"{self.base_url}/users/me", json=update_data, headers=headers)
            if response.status_code == 200:
                user_data = response.json()
                if user_data["full_name"] == "Updated Test User":
                    self.log_test("Update User Profile", True, f"Updated name: {user_data['full_name']}")
                    return True
                else:
                    self.log_test("Update User Profile", False, "Name not updated correctly")
                    return False
            else:
                self.log_test("Update User Profile", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Update User Profile", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests and return overall success."""
        print("🚀 Starting User Service Manual Tests")
        print("=" * 50)
        
        # Test 1: Service health
        if not self.test_service_health():
            print("\n❌ Service is not running. Please start the service first.")
            return False
        
        # Test 2: User signup
        signup_result = self.test_user_signup()
        if not signup_result["success"]:
            print("\n❌ Cannot continue tests without successful signup")
            return False
        
        user = signup_result["user"]
        password = signup_result["password"]
        
        # Test 3: Duplicate signup
        self.test_duplicate_signup(user["email"])
        
        # Test 4: User login
        login_result = self.test_user_login(user["email"], password)
        if not login_result["success"]:
            print("\n❌ Cannot continue tests without successful login")
            return False
        
        token = login_result["token"]
        
        # Test 5: Bad login
        self.test_bad_login()
        
        # Test 6: Get user profile
        self.test_get_user_profile(token)
        
        # Test 7: Unauthorized access
        self.test_unauthorized_access()
        
        # Test 8: Update user profile
        self.test_update_user_profile(token)
        
        # Summary
        print("\n" + "=" * 50)
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! User Service is working correctly.")
            return True
        else:
            print("❌ Some tests failed. Please check the service implementation.")
            return False


def main():
    """Main function to run tests."""
    tester = UserServiceTester()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
