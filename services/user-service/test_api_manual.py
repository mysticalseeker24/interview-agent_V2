"""
Manual API Test Script for User Service
Tests login functionality with pre-seeded users.
"""
import asyncio
import httpx


async def test_user_service():
    """Test the user service API endpoints."""
    
    base_url = "http://localhost:8001"
    
    print("🧪 Testing TalentSync User Service API")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: Health check
        print("\n1. 🏥 Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/")
            print(f"✅ Root endpoint: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"❌ Root endpoint failed: {e}")
        
        # Test 2: Login with pre-seeded users
        test_users = [
            {"username": "saksham.mishra2402@gmail.com", "password": "12345678"},
            {"username": "georgidimitroviliev2002@gmail.com", "password": "12345678"},
            {"username": "george.iliev.24@ucl.ac.uk", "password": "12345678"},
            {"username": "sakshamm510@gmail.com", "password": "12345678"}
        ]
        
        tokens = {}
        
        for i, user in enumerate(test_users, 1):
            print(f"\n{i+1}. 🔐 Testing login for {user['username']}...")
            try:
                response = await client.post(
                    f"{base_url}/auth/login",
                    data=user  # form data for OAuth2PasswordRequestForm
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    tokens[user['username']] = token_data['access_token']
                    print(f"✅ Login successful - Token: {token_data['access_token'][:20]}...")
                else:
                    print(f"❌ Login failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"❌ Login error: {e}")
        
        # Test 3: Access protected endpoints with tokens
        if tokens:
            first_email = list(tokens.keys())[0]
            token = tokens[first_email]
            
            print(f"\n{len(test_users)+2}. 👤 Testing /users/me endpoint with {first_email}...")
            try:
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(f"{base_url}/users/me", headers=headers)
                
                if response.status_code == 200:
                    user_data = response.json()
                    print(f"✅ Profile retrieved: {user_data['email']} - {user_data['full_name']}")
                    print(f"   Admin: {user_data.get('is_admin', False)}")
                    print(f"   Active: {user_data.get('is_active', True)}")
                else:
                    print(f"❌ Profile access failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"❌ Profile access error: {e}")
        
        # Test 4: Update profile
        if tokens:
            first_email = list(tokens.keys())[0]
            token = tokens[first_email]
            
            print(f"\n{len(test_users)+3}. ✏️ Testing profile update...")
            try:
                headers = {"Authorization": f"Bearer {token}"}
                update_data = {"full_name": "Updated Test Name"}
                response = await client.put(
                    f"{base_url}/users/me", 
                    headers=headers,
                    json=update_data
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    print(f"✅ Profile updated: {user_data['full_name']}")
                else:
                    print(f"❌ Profile update failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"❌ Profile update error: {e}")
        
        # Test 5: Test invalid login
        print(f"\n{len(test_users)+4}. 🚫 Testing invalid login...")
        try:
            response = await client.post(
                f"{base_url}/auth/login",
                data={"username": "invalid@email.com", "password": "wrongpassword"}
            )
            
            if response.status_code == 401:
                print("✅ Invalid login correctly rejected")
            else:
                print(f"❌ Invalid login should return 401, got {response.status_code}")
                
        except Exception as e:
            print(f"❌ Invalid login test error: {e}")

    print("\n🎉 API testing completed!")
    print("\n📋 Summary:")
    print("- All users have password: 12345678")
    print("- First user (saksham.mishra2402@gmail.com) has admin privileges")
    print("- All endpoints tested: /, /auth/login, /users/me")


if __name__ == "__main__":
    print("Starting User Service API tests...")
    print("Make sure the service is running on http://localhost:8001")
    print("Run 'python seed_users.py' first to populate the database")
    print()
    
    asyncio.run(test_user_service())
