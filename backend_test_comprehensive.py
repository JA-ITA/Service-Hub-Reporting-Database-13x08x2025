import requests
import json
import sys
import time
from datetime import datetime, timedelta

class ClientServicesAPITester:
    def __init__(self, base_url="https://site-optimizer-7.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_info = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_resources = {
            "users": [],
            "locations": [],
            "templates": [],
            "submissions": []
        }
        self.test_users = {}

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
            if success:
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

    def test_login_failure(self, username, password, expected_message=None):
        """Test login failure scenarios"""
        success, response = self.run_test(
            f"Login Failure: {username}",
            "POST",
            "auth/login",
            401,  # Expecting 401 Unauthorized
            data={"username": username, "password": password}
        )
        
        if success and expected_message:
            detail = response.get('detail', '')
            if expected_message in detail:
                print(f"✅ Correct error message: {detail}")
                return True
            else:
                print(f"❌ Unexpected error message: {detail}, expected: {expected_message}")
                return False
        return success

    def test_register_user(self, username, password, full_name=None, email=None):
        """Test user registration"""
        data = {
            "username": username,
            "password": password
        }
        if full_name:
            data["full_name"] = full_name
        if email:
            data["email"] = email
            
        success, response = self.run_test(
            f"Register User: {username}",
            "POST",
            "auth/register",
            200,
            data=data
        )
        
        if success and 'user_id' in response:
            self.test_users[username] = {
                "user_id": response['user_id'],
                "password": password,
                "status": response['status']
            }
            print(f"User registered with ID: {response['user_id']}, Status: {response['status']}")
            return response['user_id']
        return None

    def test_duplicate_registration(self, username, password):
        """Test registering with an existing username"""
        data = {
            "username": username,
            "password": password
        }
        
        success, response = self.run_test(
            f"Duplicate Registration: {username}",
            "POST",
            "auth/register",
            400,  # Expecting 400 Bad Request
            data=data
        )
        
        if success and 'detail' in response and 'already exists' in response['detail']:
            print(f"✅ Correct error for duplicate username: {response['detail']}")
            return True
        return False

    def test_forgot_password(self, username):
        """Test forgot password functionality"""
        success, response = self.run_test(
            f"Forgot Password for {username}",
            "POST",
            "auth/forgot-password",
            200,
            data={"username": username}
        )
        
        if success and 'reset_code' in response:
            reset_code = response['reset_code']
            if username in self.test_users:
                self.test_users[username]["reset_code"] = reset_code
            else:
                self.test_users[username] = {"reset_code": reset_code}
            print(f"Password reset code generated: {reset_code}")
            return reset_code
        return None

    def test_reset_password(self, username, reset_code, new_password):
        """Test password reset with code"""
        success, response = self.run_test(
            f"Reset Password for {username}",
            "POST",
            "auth/reset-password",
            200,
            data={
                "username": username,
                "reset_code": reset_code,
                "new_password": new_password
            }
        )
        
        if success:
            self.test_users[username]["password"] = new_password
            print(f"Password reset successfully for {username}")
            return True
        return False

    def test_reset_password_validation(self, username, reset_code, new_password, expected_status=400):
        """Test password reset validation"""
        success, response = self.run_test(
            f"Reset Password Validation for {username}",
            "POST",
            "auth/reset-password",
            expected_status,
            data={
                "username": username,
                "reset_code": reset_code,
                "new_password": new_password
            }
        )
        return success

    def test_get_pending_users(self):
        """Test getting pending user registrations"""
        success, response = self.run_test(
            "Get Pending Users",
            "GET",
            "admin/pending-users",
            200
        )
        
        if success and isinstance(response, list):
            print(f"Found {len(response)} pending users")
            return response
        return []

    def test_approve_user(self, user_id, status="approved", role="data_entry", location=None):
        """Test approving or rejecting a pending user"""
        data = {
            "user_id": user_id,
            "status": status,
            "role": role
        }
        if location:
            data["assigned_location"] = location
            
        success, response = self.run_test(
            f"{status.capitalize()} User {user_id}",
            "POST",
            "admin/approve-user",
            200,
            data=data
        )
        
        if success:
            print(f"User {status} successfully: {response.get('username', 'Unknown')}")
            return True
        return False

    def test_get_current_user(self):
        """Test getting current user info"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_create_user(self, username, password, role, assigned_location=None, page_permissions=None):
        """Test creating a new user"""
        data = {
            "username": username,
            "password": password,
            "role": role
        }
        if assigned_location:
            data["assigned_location"] = assigned_location
        if page_permissions:
            data["page_permissions"] = page_permissions
            
        success, response = self.run_test(
            f"Create {role} User",
            "POST",
            "users",
            200,
            data=data
        )
        if success and 'id' in response:
            self.created_resources["users"].append(response['id'])
            return response['id']
        return None

    def test_get_users(self):
        """Test getting all users"""
        success, response = self.run_test(
            "Get All Users",
            "GET",
            "users",
            200
        )
        return success and isinstance(response, list)

    def test_get_user(self, user_id):
        """Test getting a specific user"""
        success, response = self.run_test(
            "Get User",
            "GET",
            f"users/{user_id}",
            200
        )
        return success and 'id' in response

    def test_update_user(self, user_id, update_data):
        """Test updating a user"""
        success, _ = self.run_test(
            "Update User",
            "PUT",
            f"users/{user_id}",
            200,
            data=update_data
        )
        return success

    def test_get_locations(self):
        """Test getting all locations"""
        success, response = self.run_test(
            "Get Locations",
            "GET",
            "locations",
            200
        )
        return success and isinstance(response, list)

    def test_get_templates(self):
        """Test getting all templates"""
        success, response = self.run_test(
            "Get Templates",
            "GET",
            "templates",
            200
        )
        return success and isinstance(response, list)

    def test_get_submissions(self, params=None):
        """Test getting submissions"""
        success, response = self.run_test(
            "Get Submissions",
            "GET",
            "submissions",
            200,
            params=params
        )
        return success and isinstance(response, list)

    def test_get_detailed_submissions(self, params=None):
        """Test getting detailed submissions with usernames"""
        success, response = self.run_test(
            "Get Detailed Submissions",
            "GET",
            "submissions-detailed",
            200,
            params=params
        )
        if success and isinstance(response, list) and len(response) > 0:
            # Check if submissions include username field
            has_username = 'submitted_by_username' in response[0]
            if has_username:
                print(f"✅ Submissions include username field: {response[0]['submitted_by_username']}")
            else:
                print("❌ Submissions do not include username field")
            return success and has_username
        return False

def test_user_registration_approval_flow():
    """Test the complete user registration, approval, and password reset flow"""
    tester = ClientServicesAPITester()
    
    print("=" * 50)
    print("TESTING USER REGISTRATION, APPROVAL, AND PASSWORD RESET FLOW")
    print("=" * 50)
    
    # Step 1: Register a new user
    timestamp = datetime.now().strftime("%H%M%S")
    test_username = f"testuser_{timestamp}"
    test_password = "Test123!"
    
    user_id = tester.test_register_user(
        test_username, 
        test_password,
        full_name="Test User",
        email="test@example.com"
    )
    
    if not user_id:
        print("❌ User registration failed, stopping tests")
        return False
    
    # Step 2: Try to login with pending user (should fail)
    login_success, _ = tester.run_test(
        f"Login with pending user {test_username}",
        "POST",
        "auth/login",
        401,  # Expecting 401 Unauthorized
        data={"username": test_username, "password": test_password}
    )
    
    if not login_success:
        print("❌ Login with pending user should be rejected with 401")
        return False
    
    print(f"✅ Login with pending user {test_username} correctly failed")
    
    # Step 3: Login as admin to approve the user
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # Step 4: Get pending users
    pending_users = tester.test_get_pending_users()
    
    # Step 5: Find our test user in pending users
    test_user_pending = None
    for user in pending_users:
        if user.get('id') == user_id:
            test_user_pending = user
            break
    
    if not test_user_pending:
        print(f"❌ Test user {test_username} not found in pending users")
        return False
    
    print(f"✅ Found test user in pending users: {test_username}")
    
    # Step 6: Approve the user
    if not tester.test_approve_user(
        user_id, 
        status="approved", 
        role="data_entry",
        location="Central Hub"
    ):
        print("❌ User approval failed")
        return False
    
    print(f"✅ User {test_username} approved successfully")
    
    # Step 7: Test login with the approved user
    tester.token = None
    if not tester.test_login(test_username, test_password):
        print(f"❌ Login with approved user {test_username} failed")
        return False
    
    print(f"✅ Successfully logged in with approved user {test_username}")
    
    # Step 8: Test password reset flow
    # First, logout and login as admin again
    tester.token = None
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping password reset tests")
        return False
    
    # Step 9: Initiate password reset
    reset_code = tester.test_forgot_password(test_username)
    if not reset_code:
        print(f"❌ Password reset initiation failed for {test_username}")
        return False
    
    # Step 10: Test password validation - too short
    if not tester.test_reset_password_validation(test_username, reset_code, "short"):
        print("❌ Password validation failed - should reject short passwords")
        return False
    
    print("✅ Password validation correctly rejected short password")
    
    # Step 11: Reset password
    new_password = "NewPass456!"
    if not tester.test_reset_password(test_username, reset_code, new_password):
        print(f"❌ Password reset failed for {test_username}")
        return False
    
    # Step 12: Test login with new password
    tester.token = None
    if not tester.test_login(test_username, new_password):
        print(f"❌ Login with new password failed for {test_username}")
        return False
    
    print(f"✅ Successfully logged in with new password for {test_username}")
    
    return True

def test_user_rejection_flow():
    """Test the user registration and rejection flow"""
    tester = ClientServicesAPITester()
    
    print("=" * 50)
    print("TESTING USER REGISTRATION AND REJECTION FLOW")
    print("=" * 50)
    
    # Step 1: Register a new user
    timestamp = datetime.now().strftime("%H%M%S")
    test_username = f"rejectuser_{timestamp}"
    test_password = "Test123!"
    
    user_id = tester.test_register_user(
        test_username, 
        test_password,
        full_name="Reject Test User",
        email="reject@example.com"
    )
    
    if not user_id:
        print("❌ User registration failed, stopping tests")
        return False
    
    # Step 2: Login as admin to reject the user
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # Step 3: Get pending users
    pending_users = tester.test_get_pending_users()
    
    # Step 4: Find our test user in pending users
    test_user_pending = None
    for user in pending_users:
        if user.get('id') == user_id:
            test_user_pending = user
            break
    
    if not test_user_pending:
        print(f"❌ Test user {test_username} not found in pending users")
        return False
    
    print(f"✅ Found test user in pending users: {test_username}")
    
    # Step 5: Reject the user
    if not tester.test_approve_user(
        user_id, 
        status="rejected"
    ):
        print("❌ User rejection failed")
        return False
    
    print(f"✅ User {test_username} rejected successfully")
    
    # Step 6: Test login with the rejected user (should fail)
    tester.token = None
    if not tester.test_login_failure(test_username, test_password, "Account has been rejected"):
        print(f"❌ Login with rejected user {test_username} should fail with 'Account has been rejected'")
        return False
    
    print(f"✅ Login with rejected user {test_username} correctly failed")
    
    return True

def test_duplicate_registration():
    """Test duplicate username registration"""
    tester = ClientServicesAPITester()
    
    print("=" * 50)
    print("TESTING DUPLICATE USERNAME REGISTRATION")
    print("=" * 50)
    
    # Step 1: Register a new user
    timestamp = datetime.now().strftime("%H%M%S")
    test_username = f"dupuser_{timestamp}"
    test_password = "Test123!"
    
    user_id = tester.test_register_user(
        test_username, 
        test_password,
        full_name="Duplicate Test User",
        email="dup@example.com"
    )
    
    if not user_id:
        print("❌ User registration failed, stopping tests")
        return False
    
    # Step 2: Try to register with the same username
    if not tester.test_duplicate_registration(test_username, "DifferentPass456!"):
        print("❌ Duplicate username registration should be rejected")
        return False
    
    print("✅ Duplicate username registration correctly rejected")
    
    return True

def test_password_reset_flow():
    """Test the password reset flow in detail"""
    tester = ClientServicesAPITester()
    
    print("=" * 50)
    print("TESTING PASSWORD RESET FLOW")
    print("=" * 50)
    
    # Step 1: Create and approve a test user
    timestamp = datetime.now().strftime("%H%M%S")
    test_username = f"pwreset_{timestamp}"
    test_password = "Test123!"
    
    # Login as admin first
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # Create a user directly (admin can create active users)
    user_id = tester.test_create_user(
        test_username,
        test_password,
        "data_entry",
        "Central Hub"
    )
    
    if not user_id:
        print("❌ User creation failed, stopping tests")
        return False
    
    # Step 2: Test login with the new user
    tester.token = None
    if not tester.test_login(test_username, test_password):
        print(f"❌ Login with new user {test_username} failed")
        return False
    
    # Step 3: Initiate password reset
    tester.token = None  # Clear token to simulate unauthenticated request
    reset_code = tester.test_forgot_password(test_username)
    if not reset_code:
        print(f"❌ Password reset initiation failed for {test_username}")
        return False
    
    # Step 4: Test invalid reset code
    if not tester.test_reset_password_validation(test_username, "000000", "NewPass789!"):
        print("❌ Invalid reset code test failed")
        return False
    
    print("✅ Invalid reset code correctly rejected")
    
    # Step 5: Test password too short
    if not tester.test_reset_password_validation(test_username, reset_code, "short"):
        print("❌ Short password test failed")
        return False
    
    print("✅ Short password correctly rejected")
    
    # Step 6: Reset with valid code and password
    new_password = "NewPass789!"
    if not tester.test_reset_password(test_username, reset_code, new_password):
        print(f"❌ Password reset failed for {test_username}")
        return False
    
    # Step 7: Test login with new password
    if not tester.test_login(test_username, new_password):
        print(f"❌ Login with new password failed for {test_username}")
        return False
    
    print(f"✅ Successfully logged in with new password for {test_username}")
    
    # Step 8: Try to use the same reset code again (should fail)
    if not tester.test_reset_password_validation(test_username, reset_code, "AnotherPass123!"):
        print("❌ Used reset code test failed")
        return False
    
    print("✅ Used reset code correctly rejected")
    
    return True

def main():
    # Setup
    print("=" * 50)
    print("CLIENT SERVICES PLATFORM API TESTS")
    print("=" * 50)
    
    # Test the complete user registration, approval, and password reset flow
    registration_flow_success = test_user_registration_approval_flow()
    
    # Test the user rejection flow
    rejection_flow_success = test_user_rejection_flow()
    
    # Test duplicate username registration
    duplicate_registration_success = test_duplicate_registration()
    
    # Test password reset flow in detail
    password_reset_success = test_password_reset_flow()
    
    # Test basic API functionality
    tester = ClientServicesAPITester()
    
    # Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping basic API tests")
        return 1
    
    # Get current user info
    tester.test_get_current_user()
    
    # Get all users
    tester.test_get_users()
    
    # Get all locations
    tester.test_get_locations()
    
    # Get all templates
    tester.test_get_templates()
    
    # Get submissions
    tester.test_get_submissions()
    
    # Print results
    print("\n" + "=" * 50)
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run} ({tester.tests_passed/tester.tests_run*100:.1f}%)")
    print("Registration flow success: ", "✅" if registration_flow_success else "❌")
    print("Rejection flow success: ", "✅" if rejection_flow_success else "❌")
    print("Duplicate registration success: ", "✅" if duplicate_registration_success else "❌")
    print("Password reset flow success: ", "✅" if password_reset_success else "❌")
    print("=" * 50)
    
    overall_success = (
        registration_flow_success and 
        rejection_flow_success and 
        duplicate_registration_success and
        password_reset_success and
        tester.tests_passed == tester.tests_run
    )
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())