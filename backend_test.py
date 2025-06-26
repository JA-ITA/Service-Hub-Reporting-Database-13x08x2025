import requests
import json
import sys
import time
from datetime import datetime, timedelta

class ClientServicesAPITester:
    def __init__(self, base_url="https://e2f25f62-fd90-478f-a483-cf62a80407f6.preview.emergentagent.com"):
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
            self.test_users[username]["reset_code"] = reset_code
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

    def test_get_statistics_options(self):
        """Test getting statistics options"""
        success, response = self.run_test(
            "Get Statistics Options",
            "GET",
            "statistics/options",
            200
        )
        if success:
            print(f"Available options: {json.dumps(response, indent=2)}")
            return True
        return False

    def test_generate_statistics(self, query_params):
        """Test generating statistics"""
        success, response = self.run_test(
            "Generate Statistics",
            "POST",
            "statistics/generate",
            200,
            data=query_params
        )
        if success:
            print(f"Statistics summary: {json.dumps(response['summary'], indent=2)}")
            return True
        return False

    def test_dashboard_submissions_by_location(self):
        """Test getting dashboard submissions by location"""
        success, response = self.run_test(
            "Dashboard Submissions by Location",
            "GET",
            "dashboard/submissions-by-location",
            200
        )
        return success and isinstance(response, list)

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
    
    # Step 2: Login as admin to approve the user
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
    
    # Step 5: Approve the user
    if not tester.test_approve_user(
        user_id, 
        status="approved", 
        role="data_entry",
        location="Central Hub"
    ):
        print("❌ User approval failed")
        return False
    
    print(f"✅ User {test_username} approved successfully")
    
    # Step 6: Test login with the approved user
    tester.token = None
    if not tester.test_login(test_username, test_password):
        print(f"❌ Login with approved user {test_username} failed")
        return False
    
    print(f"✅ Successfully logged in with approved user {test_username}")
    
    # Step 7: Test password reset flow
    # First, logout and login as admin again
    tester.token = None
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping password reset tests")
        return False
    
    # Step 8: Initiate password reset
    reset_code = tester.test_forgot_password(test_username)
    if not reset_code:
        print(f"❌ Password reset initiation failed for {test_username}")
        return False
    
    # Step 9: Reset password
    new_password = "NewPass456!"
    if not tester.test_reset_password(test_username, reset_code, new_password):
        print(f"❌ Password reset failed for {test_username}")
        return False
    
    # Step 10: Test login with new password
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
    login_success, _ = tester.run_test(
        f"Login with rejected user {test_username}",
        "POST",
        "auth/login",
        401,  # Expecting 401 Unauthorized
        data={"username": test_username, "password": test_password}
    )
    
    if login_success:
        print(f"❌ Login with rejected user {test_username} should have failed but succeeded")
        return False
    
    print(f"✅ Login with rejected user {test_username} correctly failed")
    
    return True

def test_invalid_password_reset():
    """Test invalid password reset scenarios"""
    tester = ClientServicesAPITester()
    
    print("=" * 50)
    print("TESTING INVALID PASSWORD RESET SCENARIOS")
    print("=" * 50)
    
    # Step 1: Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # Step 2: Test with non-existent user
    non_existent_user = f"nonexistent_{datetime.now().strftime('%H%M%S')}"
    success, response = tester.run_test(
        f"Forgot Password for non-existent user {non_existent_user}",
        "POST",
        "auth/forgot-password",
        200,  # Should still return 200 for security reasons
        data={"username": non_existent_user}
    )
    
    if not success:
        print("❌ Forgot password for non-existent user should return 200 for security")
        return False
    
    print("✅ Forgot password for non-existent user correctly handled")
    
    # Step 3: Test with invalid reset code
    timestamp = datetime.now().strftime("%H%M%S")
    test_username = f"resettest_{timestamp}"
    test_password = "Test123!"
    
    # Create and approve a user for testing
    user_id = tester.test_register_user(test_username, test_password)
    if not user_id:
        print("❌ User registration failed, stopping tests")
        return False
    
    tester.test_approve_user(user_id, status="approved", role="data_entry")
    
    # Generate a valid reset code
    reset_code = tester.test_forgot_password(test_username)
    if not reset_code:
        print(f"❌ Password reset initiation failed for {test_username}")
        return False
    
    # Test with invalid reset code
    invalid_code = "000000"
    success, _ = tester.run_test(
        f"Reset Password with invalid code for {test_username}",
        "POST",
        "auth/reset-password",
        400,  # Expecting 400 Bad Request
        data={
            "username": test_username,
            "reset_code": invalid_code,
            "new_password": "NewPass789!"
        }
    )
    
    if not success:
        print("❌ Reset password with invalid code should return 400")
        return False
    
    print("✅ Reset password with invalid code correctly handled")
    
    return True

def test_deleted_users_functionality():
    """Test the deleted users functionality"""
    tester = ClientServicesAPITester()
    
    print("=" * 50)
    print("TESTING DELETED USERS FUNCTIONALITY")
    print("=" * 50)
    
    # Step 1: Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # Step 2: Create a test user
    timestamp = datetime.now().strftime("%H%M%S")
    test_username = f"deletetest_{timestamp}"
    test_password = "Test123!"
    
    user_id = tester.test_create_user(
        test_username,
        test_password,
        "data_entry",
        "Central Hub"
    )
    
    if not user_id:
        print("❌ User creation failed, stopping tests")
        return False
    
    print(f"✅ Created test user {test_username} with ID: {user_id}")
    
    # Step 3: Test deleting the user
    success, response = tester.run_test(
        f"Delete User {test_username}",
        "DELETE",
        f"users/{user_id}",
        200
    )
    
    if not success:
        print(f"❌ Failed to delete user {test_username}")
        return False
    
    print(f"✅ User {test_username} deleted successfully")
    
    # Step 4: Test getting deleted users
    success, deleted_users = tester.run_test(
        "Get Deleted Users",
        "GET",
        "admin/deleted-users",
        200
    )
    
    if not success:
        print("❌ Failed to get deleted users")
        return False
    
    # Step 5: Verify our test user is in the deleted users list
    deleted_user = next((user for user in deleted_users if user.get('id') == user_id), None)
    if not deleted_user:
        print(f"❌ Test user {test_username} not found in deleted users list")
        return False
    
    print(f"✅ Found deleted test user in deleted users list")
    
    # Step 6: Verify audit trail fields
    if 'deleted_at' not in deleted_user or 'deleted_by' not in deleted_user:
        print(f"❌ Audit trail missing for deleted user")
        return False
    
    print(f"✅ Audit trail present - Deleted at: {deleted_user['deleted_at']}, Deleted by: {deleted_user['deleted_by']}")
    
    # Step 7: Test that deleted user cannot login
    tester.token = None  # Clear token for login test
    success, _ = tester.run_test(
        f"Login with deleted user {test_username} (should fail)",
        "POST",
        "auth/login",
        401,  # Expect unauthorized
        data={"username": test_username, "password": test_password}
    )
    
    if not success:
        print(f"❌ Login with deleted user should have failed but succeeded")
        return False
    
    print(f"✅ Login with deleted user correctly failed")
    
    # Step 8: Login as admin again to restore the user
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # Step 9: Test restoring the user
    success, response = tester.run_test(
        f"Restore User {test_username}",
        "POST",
        f"admin/restore-user/{user_id}",
        200
    )
    
    if not success:
        print(f"❌ Failed to restore user {test_username}")
        return False
    
    print(f"✅ User {test_username} restored successfully")
    
    # Step 10: Verify restoration audit trail
    if 'restored_at' not in response or 'restored_by' not in response:
        print(f"❌ Restoration audit trail missing")
        return False
    
    print(f"✅ Restoration audit trail present - Restored at: {response['restored_at']}, Restored by: {response['restored_by']}")
    
    # Step 11: Test that restored user can login
    tester.token = None  # Clear token for login test
    success, _ = tester.run_test(
        f"Login with restored user {test_username}",
        "POST",
        "auth/login",
        200,
        data={"username": test_username, "password": test_password}
    )
    
    if not success:
        print(f"❌ Login with restored user failed")
        return False
    
    print(f"✅ Login with restored user succeeded")
    
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
    
    # Test invalid password reset scenarios
    invalid_reset_success = test_invalid_password_reset()
    
    # Test deleted users functionality
    deleted_users_success = test_deleted_users_functionality()
    
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
    print("Invalid reset tests success: ", "✅" if invalid_reset_success else "❌")
    print("Deleted users functionality success: ", "✅" if deleted_users_success else "❌")
    print("=" * 50)
    
    overall_success = (
        registration_flow_success and 
        rejection_flow_success and 
        invalid_reset_success and 
        deleted_users_success and
        tester.tests_passed == tester.tests_run
    )
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())
