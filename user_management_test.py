import requests
import json
import sys
from datetime import datetime, timedelta

class ClientServicesAPITester:
    def __init__(self, base_url="https://function-check-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_info = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if not success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.json()}")
                except:
                    print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_login(self, username, password):
        """Test login and get token"""
        success, response = self.run_test(
            "Login",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_info = response['user']
            print(f"Logged in as {self.user_info['username']} with role {self.user_info['role']}")
            return True
        return False

def test_user_registration_flow(tester):
    """Test the complete user registration, approval, and login flow"""
    print("\n" + "=" * 50)
    print("TESTING USER REGISTRATION FLOW")
    print("=" * 50)
    
    timestamp = datetime.now().strftime("%H%M%S")
    test_username = f"testuser_{timestamp}"
    test_password = "Test123!"
    
    # Step 1: Register a new user
    success, response = tester.run_test(
        "User Registration",
        "POST",
        "auth/register",
        200,
        data={
            "username": test_username,
            "password": test_password,
            "full_name": "Test User",
            "email": "test@example.com"
        }
    )
    
    if not success:
        print("❌ User registration failed, skipping related tests")
        return False
    
    print(f"✅ User registered successfully with status: {response.get('status')}")
    user_id = response.get('user_id')
    
    # Step 2: Try to login with pending user (should fail)
    success, response = tester.run_test(
        "Login with Pending User (should fail)",
        "POST",
        "auth/login",
        401,
        data={"username": test_username, "password": test_password}
    )
    
    if not success:
        print("❌ Login with pending user succeeded but should have failed")
        return False
    
    print("✅ Login with pending user correctly failed")
    
    # Step 3: Get pending users as admin
    success, response = tester.run_test(
        "Get Pending Users",
        "GET",
        "admin/pending-users",
        200
    )
    
    if not success or not isinstance(response, list):
        print("❌ Failed to get pending users")
        return False
    
    print(f"✅ Found {len(response)} pending users")
    
    # Find our test user in the pending users list
    pending_user = None
    for user in response:
        if user.get('username') == test_username:
            pending_user = user
            break
    
    if not pending_user:
        print(f"❌ Could not find our test user '{test_username}' in pending users list")
        return False
    
    print(f"✅ Found our test user in pending users list with ID: {pending_user.get('id')}")
    
    # Step 4: Approve the user
    success, response = tester.run_test(
        "Approve User",
        "POST",
        "admin/approve-user",
        200,
        data={
            "user_id": pending_user.get('id'),
            "status": "approved",
            "role": "data_entry",
            "assigned_location": "Central Hub"
        }
    )
    
    if not success:
        print("❌ Failed to approve user")
        return False
    
    print(f"✅ User approved successfully: {response.get('message')}")
    
    # Step 5: Login with approved user (should succeed)
    success, _ = tester.run_test(
        "Login with Approved User",
        "POST",
        "auth/login",
        200,
        data={"username": test_username, "password": test_password}
    )
    
    if not success:
        print("❌ Login with approved user failed")
        return False
    
    print("✅ Login with approved user succeeded")
    
    # Step 6: Test rejecting a user
    # First, register another test user
    reject_username = f"rejectuser_{timestamp}"
    success, response = tester.run_test(
        "Register User for Rejection",
        "POST",
        "auth/register",
        200,
        data={
            "username": reject_username,
            "password": test_password
        }
    )
    
    if not success:
        print("❌ Failed to register user for rejection test")
        return False
    
    reject_user_id = response.get('user_id')
    
    # Get pending users again
    success, response = tester.run_test(
        "Get Pending Users Again",
        "GET",
        "admin/pending-users",
        200
    )
    
    if not success:
        print("❌ Failed to get pending users for rejection test")
        return False
    
    # Find our reject test user
    reject_user = None
    for user in response:
        if user.get('username') == reject_username:
            reject_user = user
            break
    
    if not reject_user:
        print(f"❌ Could not find our reject test user '{reject_username}' in pending users list")
        return False
    
    # Reject the user
    success, response = tester.run_test(
        "Reject User",
        "POST",
        "admin/approve-user",
        200,
        data={
            "user_id": reject_user.get('id'),
            "status": "rejected",
            "role": "data_entry"
        }
    )
    
    if not success:
        print("❌ Failed to reject user")
        return False
    
    print(f"✅ User rejected successfully: {response.get('message')}")
    
    # Try to login with rejected user (should fail)
    success, _ = tester.run_test(
        "Login with Rejected User (should fail)",
        "POST",
        "auth/login",
        401,
        data={"username": reject_username, "password": test_password}
    )
    
    if not success:
        print("❌ Login with rejected user succeeded but should have failed")
        return False
    
    print("✅ Login with rejected user correctly failed")
    
    return True

def test_password_reset_flow(tester):
    """Test the password reset flow"""
    print("\n" + "=" * 50)
    print("TESTING PASSWORD RESET FLOW")
    print("=" * 50)
    
    # Create a test user first through registration
    timestamp = datetime.now().strftime("%H%M%S")
    test_username = f"resetuser_{timestamp}"
    original_password = "Original123!"
    new_password = "NewPass456!"
    
    # Register a user
    success, response = tester.run_test(
        "Register User for Password Reset",
        "POST",
        "auth/register",
        200,
        data={
            "username": test_username,
            "password": original_password
        }
    )
    
    if not success:
        print("❌ Failed to register user for password reset")
        return False
    
    user_id = response.get('user_id')
    
    # Approve the user so we can test login
    success, response = tester.run_test(
        "Get Pending Users for Password Reset Test",
        "GET",
        "admin/pending-users",
        200
    )
    
    if not success:
        print("❌ Failed to get pending users for password reset test")
        return False
    
    # Find our test user
    pending_user = None
    for user in response:
        if user.get('username') == test_username:
            pending_user = user
            break
    
    if not pending_user:
        print(f"❌ Could not find our test user '{test_username}' in pending users list")
        return False
    
    # Approve the user
    success, _ = tester.run_test(
        "Approve User for Password Reset Test",
        "POST",
        "admin/approve-user",
        200,
        data={
            "user_id": pending_user.get('id'),
            "status": "approved",
            "role": "data_entry",
            "assigned_location": "Central Hub"
        }
    )
    
    if not success:
        print("❌ Failed to approve user for password reset test")
        return False
    
    print(f"✅ Created and approved test user for password reset: {test_username}")
    
    # Step 1: Initiate password reset
    success, response = tester.run_test(
        "Initiate Password Reset",
        "POST",
        "auth/forgot-password",
        200,
        data={"username": test_username}
    )
    
    if not success:
        print("❌ Failed to initiate password reset")
        return False
    
    reset_code = response.get('reset_code')
    if not reset_code:
        print("❌ No reset code returned")
        return False
    
    print(f"✅ Password reset initiated with code: {reset_code}")
    
    # Step 2: Try an invalid reset code (should fail)
    success, _ = tester.run_test(
        "Reset Password with Invalid Code (should fail)",
        "POST",
        "auth/reset-password",
        400,
        data={
            "username": test_username,
            "reset_code": "000000",  # Invalid code
            "new_password": new_password
        }
    )
    
    if not success:
        print("❌ Password reset with invalid code succeeded but should have failed")
        return False
    
    print("✅ Password reset with invalid code correctly failed")
    
    # Step 3: Reset password with valid code
    success, response = tester.run_test(
        "Reset Password with Valid Code",
        "POST",
        "auth/reset-password",
        200,
        data={
            "username": test_username,
            "reset_code": reset_code,
            "new_password": new_password
        }
    )
    
    if not success:
        print("❌ Failed to reset password with valid code")
        return False
    
    print("✅ Password reset successfully")
    
    # Step 4: Try to login with old password (should fail)
    success, _ = tester.run_test(
        "Login with Old Password (should fail)",
        "POST",
        "auth/login",
        401,
        data={"username": test_username, "password": original_password}
    )
    
    if not success:
        print("❌ Login with old password succeeded but should have failed")
        return False
    
    print("✅ Login with old password correctly failed")
    
    # Step 5: Login with new password (should succeed)
    success, _ = tester.run_test(
        "Login with New Password",
        "POST",
        "auth/login",
        200,
        data={"username": test_username, "password": new_password}
    )
    
    if not success:
        print("❌ Login with new password failed")
        return False
    
    print("✅ Login with new password succeeded")
    
    # Step 6: Try to use the same reset code again (should fail - one-time use)
    success, _ = tester.run_test(
        "Reuse Reset Code (should fail)",
        "POST",
        "auth/reset-password",
        400,
        data={
            "username": test_username,
            "reset_code": reset_code,
            "new_password": "AnotherPass789!"
        }
    )
    
    if not success:
        print("❌ Reusing reset code succeeded but should have failed")
        return False
    
    print("✅ Reusing reset code correctly failed")
    
    return True

def test_duplicate_username_registration(tester):
    """Test that registering with an existing username fails"""
    print("\n" + "=" * 50)
    print("TESTING DUPLICATE USERNAME REGISTRATION")
    print("=" * 50)
    
    # First, create a user
    timestamp = datetime.now().strftime("%H%M%S")
    test_username = f"dupuser_{timestamp}"
    test_password = "Test123!"
    
    success, response = tester.run_test(
        "Register First User",
        "POST",
        "auth/register",
        200,
        data={
            "username": test_username,
            "password": test_password
        }
    )
    
    if not success:
        print("❌ Failed to register first user")
        return False
    
    print("✅ First user registered successfully")
    
    # Now try to register another user with the same username
    success, _ = tester.run_test(
        "Register Duplicate Username (should fail)",
        "POST",
        "auth/register",
        400,  # Should return 400 Bad Request
        data={
            "username": test_username,
            "password": "DifferentPass456!"
        }
    )
    
    if not success:
        print("❌ Duplicate username registration succeeded but should have failed")
        return False
    
    print("✅ Duplicate username registration correctly failed")
    
    return True

def main():
    # Setup
    tester = ClientServicesAPITester()
    
    print("=" * 50)
    print("CLIENT SERVICES PLATFORM API TESTS - USER MANAGEMENT")
    print("=" * 50)
    
    # Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return 1
    
    # Test 1: Test user registration flow
    registration_success = test_user_registration_flow(tester)
    
    # Test 2: Test password reset flow
    password_reset_success = test_password_reset_flow(tester)
    
    # Test 3: Test duplicate username registration
    duplicate_username_success = test_duplicate_username_registration(tester)
    
    # Print results
    print("\n" + "=" * 50)
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run} ({tester.tests_passed/tester.tests_run*100:.1f}%)")
    print("=" * 50)
    
    print("\nTest Summary:")
    print(f"User Registration Flow: {'✅ Passed' if registration_success else '❌ Failed'}")
    print(f"Password Reset Flow: {'✅ Passed' if password_reset_success else '❌ Failed'}")
    print(f"Duplicate Username Registration: {'✅ Passed' if duplicate_username_success else '❌ Failed'}")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())