import requests
import json
import sys
import time
from datetime import datetime, timedelta

class ClientServicesAPITester:
    def __init__(self, base_url="https://default-submit.preview.emergentagent.com"):
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

    def test_get_user_profile(self):
        """Test getting current user's profile"""
        success, response = self.run_test(
            "Get User Profile",
            "GET",
            "users/profile",
            200
        )
        
        if success:
            # Verify profile contains expected fields
            required_fields = ['id', 'username', 'role']
            optional_fields = ['full_name', 'email', 'assigned_locations', 'created_at']
            
            for field in required_fields:
                if field not in response:
                    print(f"❌ Profile missing required field: {field}")
                    return False
            
            print(f"✅ Profile retrieved successfully for user: {response.get('username')}")
            print(f"   - Full Name: {response.get('full_name', 'Not set')}")
            print(f"   - Email: {response.get('email', 'Not set')}")
            print(f"   - Role: {response.get('role')}")
            print(f"   - Assigned Locations: {response.get('assigned_locations', [])}")
            
            return True
        
        return False

    def test_update_user_profile(self, full_name=None, email=None):
        """Test updating current user's profile"""
        update_data = {}
        if full_name is not None:
            update_data["full_name"] = full_name
        if email is not None:
            update_data["email"] = email
        
        if not update_data:
            print("❌ No profile data provided for update")
            return False
        
        success, response = self.run_test(
            "Update User Profile",
            "PUT",
            "users/profile",
            200,
            data=update_data
        )
        
        if success:
            print(f"✅ Profile updated successfully")
            if full_name:
                print(f"   - Full Name updated to: {full_name}")
            if email:
                print(f"   - Email updated to: {email}")
            return True
        
        return False

    def test_change_password(self, current_password, new_password):
        """Test changing user's own password"""
        success, response = self.run_test(
            "Change Own Password",
            "POST",
            "users/change-password",
            200,
            data={
                "current_password": current_password,
                "new_password": new_password
            }
        )
        
        if success:
            print(f"✅ Password changed successfully")
            return True
        
        return False

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
    
    if not login_success:
        print(f"❌ Login test with rejected user {test_username} failed - expected 401 but got different status")
        return False
    
    print(f"✅ Login with rejected user {test_username} correctly failed with 401")
    
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

def test_role_management():
    """Test role management functionality"""
    tester = ClientServicesAPITester()
    
    print("=" * 50)
    print("TESTING ROLE MANAGEMENT FUNCTIONALITY")
    print("=" * 50)
    
    # Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # Test getting all roles
    success, roles = tester.run_test(
        "Get All Roles",
        "GET",
        "roles",
        200
    )
    
    if not success or not isinstance(roles, list):
        print("❌ Failed to get roles")
        return False
    
    print(f"✅ Found {len(roles)} roles")
    
    # Test creating a custom role
    timestamp = datetime.now().strftime("%H%M%S")
    custom_role_name = f"custom_role_{timestamp}"
    
    role_data = {
        "name": custom_role_name,
        "display_name": f"Custom Role {timestamp}",
        "description": "Test custom role",
        "permissions": ["dashboard", "submit"]
    }
    
    success, response = tester.run_test(
        "Create Custom Role",
        "POST",
        "roles",
        200,
        data=role_data
    )
    
    if not success or 'id' not in response:
        print("❌ Failed to create custom role")
        return False
    
    role_id = response['id']
    print(f"✅ Created custom role with ID: {role_id}")
    
    # Test getting specific role
    success, role = tester.run_test(
        "Get Specific Role",
        "GET",
        f"roles/{role_id}",
        200
    )
    
    if not success or role.get('name') != custom_role_name:
        print("❌ Failed to get specific role")
        return False
    
    print("✅ Successfully retrieved specific role")
    
    # Test updating role
    updated_role_data = {
        "name": custom_role_name,
        "display_name": f"Updated Custom Role {timestamp}",
        "description": "Updated test custom role",
        "permissions": ["dashboard", "submit", "reports"]
    }
    
    success, _ = tester.run_test(
        "Update Custom Role",
        "PUT",
        f"roles/{role_id}",
        200,
        data=updated_role_data
    )
    
    if not success:
        print("❌ Failed to update custom role")
        return False
    
    print("✅ Successfully updated custom role")
    
    # Test deleting custom role
    success, _ = tester.run_test(
        "Delete Custom Role",
        "DELETE",
        f"roles/{role_id}",
        200
    )
    
    if not success:
        print("❌ Failed to delete custom role")
        return False
    
    print("✅ Successfully deleted custom role")
    
    # Test that system roles cannot be deleted
    system_role_id = None
    for role in roles:
        if role.get('is_system_role', False):
            system_role_id = role['id']
            break
    
    if system_role_id:
        success, _ = tester.run_test(
            "Try to Delete System Role (should fail)",
            "DELETE",
            f"roles/{system_role_id}",
            403  # Expecting forbidden
        )
        
        if not success:
            print("❌ System role deletion should have been forbidden")
            return False
        
        print("✅ System role deletion correctly forbidden")
    
    return True

def test_location_management():
    """Test service location management functionality"""
    tester = ClientServicesAPITester()
    
    print("=" * 50)
    print("TESTING LOCATION MANAGEMENT FUNCTIONALITY")
    print("=" * 50)
    
    # Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # Test creating a location
    timestamp = datetime.now().strftime("%H%M%S")
    location_name = f"Test Location {timestamp}"
    
    location_data = {
        "name": location_name,
        "description": f"Test location created at {timestamp}"
    }
    
    success, response = tester.run_test(
        "Create Location",
        "POST",
        "locations",
        200,
        data=location_data
    )
    
    if not success or 'id' not in response:
        print("❌ Failed to create location")
        return False
    
    location_id = response['id']
    print(f"✅ Created location with ID: {location_id}")
    
    # Test getting all locations
    success, locations = tester.run_test(
        "Get All Locations",
        "GET",
        "locations",
        200
    )
    
    if not success or not isinstance(locations, list):
        print("❌ Failed to get locations")
        return False
    
    # Verify our location is in the list
    created_location = next((loc for loc in locations if loc.get('id') == location_id), None)
    if not created_location:
        print("❌ Created location not found in locations list")
        return False
    
    print(f"✅ Found created location in locations list: {created_location['name']}")
    
    # Test updating location
    updated_location_data = {
        "name": f"Updated {location_name}",
        "description": f"Updated test location at {timestamp}"
    }
    
    success, _ = tester.run_test(
        "Update Location",
        "PUT",
        f"locations/{location_id}",
        200,
        data=updated_location_data
    )
    
    if not success:
        print("❌ Failed to update location")
        return False
    
    print("✅ Successfully updated location")
    
    # Test deleting location (soft delete)
    success, _ = tester.run_test(
        "Delete Location",
        "DELETE",
        f"locations/{location_id}",
        200
    )
    
    if not success:
        print("❌ Failed to delete location")
        return False
    
    print("✅ Successfully deleted location")
    
    return True

def test_template_management():
    """Test form template management functionality"""
    tester = ClientServicesAPITester()
    
    print("=" * 50)
    print("TESTING TEMPLATE MANAGEMENT FUNCTIONALITY")
    print("=" * 50)
    
    # Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # Get locations for template assignment
    success, locations = tester.run_test(
        "Get Locations for Template",
        "GET",
        "locations",
        200
    )
    
    if not success or not locations:
        print("❌ Failed to get locations for template assignment")
        return False
    
    location_names = [loc['name'] for loc in locations[:2]]  # Use first 2 locations
    
    # Test creating a template
    timestamp = datetime.now().strftime("%H%M%S")
    template_name = f"Test Template {timestamp}"
    
    template_data = {
        "name": template_name,
        "description": f"Test template created at {timestamp}",
        "fields": [
            {
                "name": "client_name",
                "type": "text",
                "label": "Client Name",
                "required": True
            },
            {
                "name": "service_date",
                "type": "date",
                "label": "Service Date",
                "required": True
            },
            {
                "name": "service_type",
                "type": "select",
                "label": "Service Type",
                "options": ["Consultation", "Treatment", "Follow-up"],
                "required": True
            },
            {
                "name": "notes",
                "type": "textarea",
                "label": "Notes",
                "required": False
            }
        ],
        "assigned_locations": location_names
    }
    
    success, response = tester.run_test(
        "Create Template",
        "POST",
        "templates",
        200,
        data=template_data
    )
    
    if not success or 'id' not in response:
        print("❌ Failed to create template")
        return False
    
    template_id = response['id']
    print(f"✅ Created template with ID: {template_id}")
    
    # Test getting all templates
    success, templates = tester.run_test(
        "Get All Templates",
        "GET",
        "templates",
        200
    )
    
    if not success or not isinstance(templates, list):
        print("❌ Failed to get templates")
        return False
    
    # Verify our template is in the list
    created_template = next((tmpl for tmpl in templates if tmpl.get('id') == template_id), None)
    if not created_template:
        print("❌ Created template not found in templates list")
        return False
    
    print(f"✅ Found created template in templates list: {created_template['name']}")
    
    # Test getting specific template
    success, template = tester.run_test(
        "Get Specific Template",
        "GET",
        f"templates/{template_id}",
        200
    )
    
    if not success or template.get('name') != template_name:
        print("❌ Failed to get specific template")
        return False
    
    print("✅ Successfully retrieved specific template")
    
    # Test updating template
    updated_template_data = {
        "name": f"Updated {template_name}",
        "description": f"Updated test template at {timestamp}",
        "fields": template_data["fields"] + [
            {
                "name": "priority",
                "type": "select",
                "label": "Priority",
                "options": ["Low", "Medium", "High"],
                "required": False
            }
        ],
        "assigned_locations": location_names
    }
    
    success, _ = tester.run_test(
        "Update Template",
        "PUT",
        f"templates/{template_id}",
        200,
        data=updated_template_data
    )
    
    if not success:
        print("❌ Failed to update template")
        return False
    
    print("✅ Successfully updated template")
    
    # Test deleting template
    success, _ = tester.run_test(
        "Delete Template",
        "DELETE",
        f"templates/{template_id}",
        200
    )
    
    if not success:
        print("❌ Failed to delete template")
        return False
    
    print("✅ Successfully deleted template")
    
    return True

def test_data_submission_system():
    """Test data submission functionality"""
    tester = ClientServicesAPITester()
    
    print("=" * 50)
    print("TESTING DATA SUBMISSION SYSTEM")
    print("=" * 50)
    
    # Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # Get existing locations
    success, locations = tester.run_test("Get Locations", "GET", "locations", 200)
    
    if not success or not locations:
        print("❌ Failed to get locations for submission test")
        return False
    
    location_name = locations[0]['name']
    
    # Create a template for testing submissions
    timestamp = datetime.now().strftime("%H%M%S")
    template_name = f"Submission Test Template {timestamp}"
    
    template_data = {
        "name": template_name,
        "description": f"Template for submission testing created at {timestamp}",
        "fields": [
            {
                "name": "client_name",
                "type": "text",
                "label": "Client Name",
                "required": True
            },
            {
                "name": "service_date",
                "type": "date",
                "label": "Service Date",
                "required": True
            },
            {
                "name": "service_type",
                "type": "select",
                "label": "Service Type",
                "options": ["Consultation", "Treatment", "Follow-up"],
                "required": True
            },
            {
                "name": "notes",
                "type": "textarea",
                "label": "Notes",
                "required": False
            }
        ],
        "assigned_locations": [location_name]
    }
    
    success, template_response = tester.run_test(
        "Create Template for Submission Test",
        "POST",
        "templates",
        200,
        data=template_data
    )
    
    if not success or 'id' not in template_response:
        print("❌ Failed to create template for submission test")
        return False
    
    template_id = template_response['id']
    print(f"✅ Created template for submission test with ID: {template_id}")
    
    # Test creating a submission
    month_year = datetime.now().strftime("%Y-%m")
    
    submission_data = {
        "template_id": template_id,
        "service_location": location_name,
        "month_year": month_year,
        "form_data": {
            "client_name": "John Doe",
            "service_date": "2025-01-15",
            "service_type": "Consultation",
            "notes": "Initial consultation completed successfully"
        }
    }
    
    success, response = tester.run_test(
        "Create Submission",
        "POST",
        "submissions",
        200,
        data=submission_data
    )
    
    if not success or 'id' not in response:
        print("❌ Failed to create submission")
        return False
    
    submission_id = response['id']
    print(f"✅ Created submission with ID: {submission_id}")
    
    # Test getting submissions
    success, submissions = tester.run_test(
        "Get All Submissions",
        "GET",
        "submissions",
        200
    )
    
    if not success or not isinstance(submissions, list):
        print("❌ Failed to get submissions")
        return False
    
    print(f"✅ Retrieved {len(submissions)} submissions")
    
    # Test getting specific submission
    success, submission = tester.run_test(
        "Get Specific Submission",
        "GET",
        f"submissions/{submission_id}",
        200
    )
    
    if not success or submission.get('id') != submission_id:
        print("❌ Failed to get specific submission")
        return False
    
    print("✅ Successfully retrieved specific submission")
    
    # Test updating submission
    updated_submission_data = {
        "form_data": {
            "client_name": "John Doe",
            "service_date": "2025-01-15",
            "service_type": "Treatment",
            "notes": "Updated: Treatment provided after consultation"
        },
        "status": "reviewed"
    }
    
    success, _ = tester.run_test(
        "Update Submission",
        "PUT",
        f"submissions/{submission_id}",
        200,
        data=updated_submission_data
    )
    
    if not success:
        print("❌ Failed to update submission")
        return False
    
    print("✅ Successfully updated submission")
    
    # Test getting detailed submissions
    success, detailed_submissions = tester.run_test(
        "Get Detailed Submissions",
        "GET",
        "submissions-detailed",
        200
    )
    
    if not success or not isinstance(detailed_submissions, list):
        print("❌ Failed to get detailed submissions")
        return False
    
    if detailed_submissions and 'submitted_by_username' in detailed_submissions[0]:
        print("✅ Detailed submissions include username information")
    else:
        print("❌ Detailed submissions missing username information")
        return False
    
    # Test deleting submission (admin only)
    success, response = tester.run_test(
        "Delete Submission",
        "DELETE",
        f"submissions/{submission_id}",
        200
    )
    
    if not success:
        print("❌ Failed to delete submission")
        return False
    
    print("✅ Successfully deleted submission")
    
    return True

def test_file_upload_system():
    """Test file upload functionality"""
    tester = ClientServicesAPITester()
    
    print("=" * 50)
    print("TESTING FILE UPLOAD SYSTEM")
    print("=" * 50)
    
    # Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # Create a test CSV file (which is allowed)
    test_content = "Name,Age,City\nJohn Doe,30,New York\nJane Smith,25,Los Angeles"
    test_filename = f"test_file_{datetime.now().strftime('%H%M%S')}.csv"
    
    with open(f"/tmp/{test_filename}", "w") as f:
        f.write(test_content)
    
    # Test file upload
    try:
        url = f"{tester.api_url}/upload"
        headers = {'Authorization': f'Bearer {tester.token}'}
        
        with open(f"/tmp/{test_filename}", "rb") as f:
            files = {'file': (test_filename, f, 'text/csv')}
            response = requests.post(url, files=files, headers=headers)
        
        print(f"Upload response status: {response.status_code}")
        if response.status_code != 200:
            try:
                print(f"Upload response: {response.json()}")
            except:
                print(f"Upload response text: {response.text}")
        
        if response.status_code == 200:
            upload_response = response.json()
            uploaded_filename = upload_response.get('filename')
            print(f"✅ File uploaded successfully: {uploaded_filename}")
            
            # Test file retrieval
            file_url = f"{tester.api_url}/files/{uploaded_filename}"
            file_response = requests.get(file_url)
            
            if file_response.status_code == 200:
                print("✅ File retrieved successfully")
                return True
            else:
                print(f"❌ Failed to retrieve file: {file_response.status_code}")
                return False
        else:
            print(f"❌ File upload failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ File upload test failed with error: {str(e)}")
        return False
    
    finally:
        # Clean up test file
        try:
            import os
            os.remove(f"/tmp/{test_filename}")
        except:
            pass

def test_reporting_system():
    """Test reporting and statistics functionality"""
    tester = ClientServicesAPITester()
    
    print("=" * 50)
    print("TESTING REPORTING SYSTEM")
    print("=" * 50)
    
    # Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # Test CSV export
    success, _ = tester.run_test(
        "Export CSV Report",
        "GET",
        "reports/csv",
        200
    )
    
    if not success:
        print("❌ Failed to export CSV report")
        return False
    
    print("✅ CSV report exported successfully")
    
    # Test statistics options
    success, options = tester.run_test(
        "Get Statistics Options",
        "GET",
        "statistics/options",
        200
    )
    
    if not success or not isinstance(options, dict):
        print("❌ Failed to get statistics options")
        return False
    
    required_keys = ['locations', 'templates', 'user_roles', 'status_options', 'group_by_options']
    if all(key in options for key in required_keys):
        print("✅ Statistics options retrieved successfully")
    else:
        print("❌ Statistics options missing required keys")
        return False
    
    # Test statistics generation
    stats_query = {
        "group_by": "location",
        "date_from": "2025-01-01T00:00:00Z",
        "date_to": "2025-12-31T23:59:59Z"
    }
    
    success, stats = tester.run_test(
        "Generate Statistics",
        "POST",
        "statistics/generate",
        200,
        data=stats_query
    )
    
    if not success or 'summary' not in stats:
        print("❌ Failed to generate statistics")
        return False
    
    print("✅ Statistics generated successfully")
    
    # Test dashboard endpoints
    success, dashboard_data = tester.run_test(
        "Get Dashboard Submissions by Location",
        "GET",
        "dashboard/submissions-by-location",
        200
    )
    
    if not success or not isinstance(dashboard_data, list):
        print("❌ Failed to get dashboard submissions by location")
        return False
    
    print("✅ Dashboard submissions by location retrieved successfully")
    
    # Test missing reports
    success, missing_reports = tester.run_test(
        "Get Missing Reports",
        "GET",
        "dashboard/missing-reports",
        200
    )
    
    if not success or 'missing_locations' not in missing_reports:
        print("❌ Failed to get missing reports")
        return False
    
    print("✅ Missing reports retrieved successfully")
    
    return True

def test_admin_settings():
    """Test admin settings functionality"""
    tester = ClientServicesAPITester()
    
    print("=" * 50)
    print("TESTING ADMIN SETTINGS")
    print("=" * 50)
    
    # Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # Test creating/updating a setting
    setting_data = {
        "setting_key": "test_setting",
        "setting_value": "test_value",
        "description": "Test setting for API testing"
    }
    
    success, _ = tester.run_test(
        "Create/Update Setting",
        "POST",
        "admin/settings",
        200,
        data=setting_data
    )
    
    if not success:
        print("❌ Failed to create/update setting")
        return False
    
    print("✅ Setting created/updated successfully")
    
    # Test getting specific setting
    success, setting = tester.run_test(
        "Get Specific Setting",
        "GET",
        "admin/settings/test_setting",
        200
    )
    
    if not success or setting.get('setting_value') != 'test_value':
        print("❌ Failed to get specific setting")
        return False
    
    print("✅ Specific setting retrieved successfully")
    
    # Test getting all settings
    success, all_settings = tester.run_test(
        "Get All Settings",
        "GET",
        "admin/settings",
        200
    )
    
    if not success or not isinstance(all_settings, list):
        print("❌ Failed to get all settings")
        return False
    
    print(f"✅ Retrieved {len(all_settings)} settings")
    
    return True

def test_enhanced_statistics_custom_fields():
    """Test enhanced statistics with custom field analysis"""
    tester = ClientServicesAPITester()
    
    print("=" * 50)
    print("TESTING ENHANCED STATISTICS WITH CUSTOM FIELD ANALYSIS")
    print("=" * 50)
    
    # Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # First, create a template with custom fields for testing
    timestamp = datetime.now().strftime("%H%M%S")
    template_name = f"Custom Field Test Template {timestamp}"
    
    template_data = {
        "name": template_name,
        "description": "Template for custom field analysis testing",
        "fields": [
            {
                "name": "client_age",
                "type": "number",
                "label": "Client Age",
                "required": True
            },
            {
                "name": "service_rating",
                "type": "number", 
                "label": "Service Rating (1-10)",
                "required": True
            },
            {
                "name": "service_category",
                "type": "select",
                "label": "Service Category",
                "options": ["Healthcare", "Education", "Social Services", "Legal Aid"],
                "required": True
            },
            {
                "name": "feedback_text",
                "type": "text",
                "label": "Client Feedback",
                "required": False
            }
        ],
        "assigned_locations": ["Central Hub", "North Branch"]
    }
    
    success, template_response = tester.run_test(
        "Create Template for Custom Field Analysis",
        "POST",
        "templates",
        200,
        data=template_data
    )
    
    if not success or 'id' not in template_response:
        print("❌ Failed to create template for custom field analysis")
        return False
    
    template_id = template_response['id']
    print(f"✅ Created template for custom field analysis with ID: {template_id}")
    
    # Create test submissions with custom field data
    test_submissions = [
        {
            "template_id": template_id,
            "service_location": "Central Hub",
            "month_year": "2025-01",
            "form_data": {
                "client_age": "25",
                "service_rating": "8",
                "service_category": "Healthcare",
                "feedback_text": "Excellent service provided"
            }
        },
        {
            "template_id": template_id,
            "service_location": "Central Hub", 
            "month_year": "2025-01",
            "form_data": {
                "client_age": "45",
                "service_rating": "9",
                "service_category": "Education",
                "feedback_text": "Very helpful staff"
            }
        },
        {
            "template_id": template_id,
            "service_location": "North Branch",
            "month_year": "2025-01", 
            "form_data": {
                "client_age": "35",
                "service_rating": "7",
                "service_category": "Healthcare",
                "feedback_text": "Good overall experience"
            }
        },
        {
            "template_id": template_id,
            "service_location": "North Branch",
            "month_year": "2025-01",
            "form_data": {
                "client_age": "55",
                "service_rating": "10",
                "service_category": "Social Services",
                "feedback_text": "Outstanding support"
            }
        }
    ]
    
    submission_ids = []
    for i, submission_data in enumerate(test_submissions):
        success, response = tester.run_test(
            f"Create Test Submission {i+1}",
            "POST",
            "submissions",
            200,
            data=submission_data
        )
        
        if success and 'id' in response:
            submission_ids.append(response['id'])
            print(f"✅ Created test submission {i+1} with ID: {response['id']}")
        else:
            print(f"❌ Failed to create test submission {i+1}")
            return False
    
    # Test getting custom fields for statistics
    success, custom_fields = tester.run_test(
        "Get Custom Fields for Statistics",
        "GET",
        "statistics/custom-fields",
        200
    )
    
    if not success or 'custom_fields' not in custom_fields:
        print("❌ Failed to get custom fields for statistics")
        return False
    
    print(f"✅ Retrieved {len(custom_fields['custom_fields'])} custom fields")
    
    # Test frequency analysis for service_category
    frequency_query = {
        "custom_field_name": "service_category",
        "custom_field_analysis_type": "frequency",
        "date_from": "2025-01-01T00:00:00Z",
        "date_to": "2025-01-31T23:59:59Z"
    }
    
    success, frequency_results = tester.run_test(
        "Generate Custom Field Frequency Analysis",
        "POST",
        "statistics/generate-custom-field",
        200,
        data=frequency_query
    )
    
    if not success or 'results' not in frequency_results:
        print("❌ Failed to generate frequency analysis")
        return False
    
    print("✅ Frequency analysis generated successfully")
    print(f"Field analyzed: {frequency_results['field_name']}")
    print(f"Analysis type: {frequency_results['analysis_type']}")
    
    # Test numerical analysis for client_age
    numerical_query = {
        "custom_field_name": "client_age",
        "custom_field_analysis_type": "numerical",
        "date_from": "2025-01-01T00:00:00Z",
        "date_to": "2025-01-31T23:59:59Z"
    }
    
    success, numerical_results = tester.run_test(
        "Generate Custom Field Numerical Analysis",
        "POST",
        "statistics/generate-custom-field",
        200,
        data=numerical_query
    )
    
    if not success or 'results' not in numerical_results:
        print("❌ Failed to generate numerical analysis")
        return False
    
    print("✅ Numerical analysis generated successfully")
    if numerical_results['results']:
        result = numerical_results['results'][0]
        print(f"Average age: {result.get('average', 'N/A')}")
        print(f"Min age: {result.get('min', 'N/A')}")
        print(f"Max age: {result.get('max', 'N/A')}")
    
    # Test trend analysis for service_rating
    trend_query = {
        "custom_field_name": "service_rating",
        "custom_field_analysis_type": "trend",
        "date_from": "2025-01-01T00:00:00Z",
        "date_to": "2025-01-31T23:59:59Z"
    }
    
    success, trend_results = tester.run_test(
        "Generate Custom Field Trend Analysis",
        "POST",
        "statistics/generate-custom-field",
        200,
        data=trend_query
    )
    
    if not success or 'results' not in trend_results:
        print("❌ Failed to generate trend analysis")
        return False
    
    print("✅ Trend analysis generated successfully")
    print(f"Trend data points: {len(trend_results['results'])}")
    
    return True

def test_location_restore_functionality():
    """Test location restore functionality"""
    tester = ClientServicesAPITester()
    
    print("=" * 50)
    print("TESTING LOCATION RESTORE FUNCTIONALITY")
    print("=" * 50)
    
    # Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # Create a test location
    timestamp = datetime.now().strftime("%H%M%S")
    location_name = f"Restore Test Location {timestamp}"
    
    location_data = {
        "name": location_name,
        "description": f"Location for restore testing created at {timestamp}"
    }
    
    success, response = tester.run_test(
        "Create Location for Restore Test",
        "POST",
        "locations",
        200,
        data=location_data
    )
    
    if not success or 'id' not in response:
        print("❌ Failed to create location for restore test")
        return False
    
    location_id = response['id']
    print(f"✅ Created location for restore test with ID: {location_id}")
    
    # Delete the location (soft delete)
    success, _ = tester.run_test(
        "Delete Location for Restore Test",
        "DELETE",
        f"locations/{location_id}",
        200
    )
    
    if not success:
        print("❌ Failed to delete location")
        return False
    
    print("✅ Location deleted successfully")
    
    # Test getting deleted locations
    success, deleted_locations = tester.run_test(
        "Get Deleted Locations",
        "GET",
        "locations/deleted",
        200
    )
    
    if not success or not isinstance(deleted_locations, list):
        print("❌ Failed to get deleted locations")
        return False
    
    # Find our deleted location
    deleted_location = next((loc for loc in deleted_locations if loc.get('id') == location_id), None)
    if not deleted_location:
        print("❌ Deleted location not found in deleted locations list")
        return False
    
    print(f"✅ Found deleted location in deleted locations list: {deleted_location['name']}")
    
    # Test restoring the location
    success, restore_response = tester.run_test(
        "Restore Location",
        "POST",
        f"locations/{location_id}/restore",
        200
    )
    
    if not success:
        print("❌ Failed to restore location")
        return False
    
    print("✅ Location restored successfully")
    print(f"Restored by: {restore_response.get('restored_by', 'Unknown')}")
    
    # Verify location is back in active locations
    success, active_locations = tester.run_test(
        "Get Active Locations After Restore",
        "GET",
        "locations",
        200
    )
    
    if not success:
        print("❌ Failed to get active locations after restore")
        return False
    
    restored_location = next((loc for loc in active_locations if loc.get('id') == location_id), None)
    if not restored_location:
        print("❌ Restored location not found in active locations list")
        return False
    
    print("✅ Restored location found in active locations list")
    
    return True

def test_template_restore_functionality():
    """Test template restore functionality"""
    tester = ClientServicesAPITester()
    
    print("=" * 50)
    print("TESTING TEMPLATE RESTORE FUNCTIONALITY")
    print("=" * 50)
    
    # Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # Create a test template
    timestamp = datetime.now().strftime("%H%M%S")
    template_name = f"Restore Test Template {timestamp}"
    
    template_data = {
        "name": template_name,
        "description": f"Template for restore testing created at {timestamp}",
        "fields": [
            {
                "name": "test_field",
                "type": "text",
                "label": "Test Field",
                "required": True
            }
        ],
        "assigned_locations": ["Central Hub"]
    }
    
    success, response = tester.run_test(
        "Create Template for Restore Test",
        "POST",
        "templates",
        200,
        data=template_data
    )
    
    if not success or 'id' not in response:
        print("❌ Failed to create template for restore test")
        return False
    
    template_id = response['id']
    print(f"✅ Created template for restore test with ID: {template_id}")
    
    # Delete the template (soft delete)
    success, _ = tester.run_test(
        "Delete Template for Restore Test",
        "DELETE",
        f"templates/{template_id}",
        200
    )
    
    if not success:
        print("❌ Failed to delete template")
        return False
    
    print("✅ Template deleted successfully")
    
    # Test getting deleted templates
    success, deleted_templates = tester.run_test(
        "Get Deleted Templates",
        "GET",
        "templates/deleted",
        200
    )
    
    if not success or not isinstance(deleted_templates, list):
        print("❌ Failed to get deleted templates")
        return False
    
    # Find our deleted template
    deleted_template = next((tmpl for tmpl in deleted_templates if tmpl.get('id') == template_id), None)
    if not deleted_template:
        print("❌ Deleted template not found in deleted templates list")
        return False
    
    print(f"✅ Found deleted template in deleted templates list: {deleted_template['name']}")
    
    # Test restoring the template
    success, restore_response = tester.run_test(
        "Restore Template",
        "POST",
        f"templates/{template_id}/restore",
        200
    )
    
    if not success:
        print("❌ Failed to restore template")
        return False
    
    print("✅ Template restored successfully")
    print(f"Restored by: {restore_response.get('restored_by', 'Unknown')}")
    
    # Verify template is back in active templates
    success, active_templates = tester.run_test(
        "Get Active Templates After Restore",
        "GET",
        "templates",
        200
    )
    
    if not success:
        print("❌ Failed to get active templates after restore")
        return False
    
    restored_template = next((tmpl for tmpl in active_templates if tmpl.get('id') == template_id), None)
    if not restored_template:
        print("❌ Restored template not found in active templates list")
        return False
    
    print("✅ Restored template found in active templates list")
    
    return True

def test_pdf_report_generation():
    """Test PDF report generation functionality"""
    tester = ClientServicesAPITester()
    
    print("=" * 50)
    print("TESTING PDF REPORT GENERATION")
    print("=" * 50)
    
    # Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # Test basic PDF report generation
    success, _ = tester.run_test(
        "Generate Basic PDF Report",
        "GET",
        "reports/pdf?report_type=statistics",
        200
    )
    
    if not success:
        print("❌ Failed to generate basic PDF report")
        return False
    
    print("✅ Basic PDF report generated successfully")
    
    # Test PDF report with query parameters
    import json
    query_params = {
        "group_by": "location",
        "date_from": "2025-01-01T00:00:00Z",
        "date_to": "2025-01-31T23:59:59Z"
    }
    
    params = {
        "report_type": "statistics",
        "query_params": json.dumps(query_params)
    }
    
    success, _ = tester.run_test(
        "Generate PDF Report with Parameters",
        "GET",
        "reports/pdf",
        200,
        params=params
    )
    
    if not success:
        print("❌ Failed to generate PDF report with parameters")
        return False
    
    print("✅ PDF report with parameters generated successfully")
    
    # Test PDF report generation with different report types
    success, _ = tester.run_test(
        "Generate Custom PDF Report",
        "GET",
        "reports/pdf?report_type=custom",
        200
    )
    
    if not success:
        print("❌ Failed to generate custom PDF report")
        return False
    
    print("✅ Custom PDF report generated successfully")
    
    return True

def main():
    # Setup
    print("=" * 50)
    print("CLIENT SERVICES PLATFORM API COMPREHENSIVE TESTS")
    print("=" * 50)
    
    # Test results tracking
    test_results = {}
    
    # Test the complete user registration, approval, and password reset flow
    test_results['registration_flow'] = test_user_registration_approval_flow()
    
    # Test the user rejection flow
    test_results['rejection_flow'] = test_user_rejection_flow()
    
    # Test invalid password reset scenarios
    test_results['invalid_reset'] = test_invalid_password_reset()
    
    # Test deleted users functionality
    test_results['deleted_users'] = test_deleted_users_functionality()
    
    # Test role management
    test_results['role_management'] = test_role_management()
    
    # Test location management
    test_results['location_management'] = test_location_management()
    
    # Test template management
    test_results['template_management'] = test_template_management()
    
    # Test data submission system
    test_results['data_submission'] = test_data_submission_system()
    
    # Test file upload system
    test_results['file_upload'] = test_file_upload_system()
    
    # Test reporting system
    test_results['reporting_system'] = test_reporting_system()
    
    # Test admin settings
    test_results['admin_settings'] = test_admin_settings()
    
    # Test new enhanced features
    test_results['enhanced_statistics'] = test_enhanced_statistics_custom_fields()
    test_results['location_restore'] = test_location_restore_functionality()
    test_results['template_restore'] = test_template_restore_functionality()
    test_results['pdf_generation'] = test_pdf_report_generation()
    
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
    print("COMPREHENSIVE TEST RESULTS")
    print("=" * 50)
    print(f"Basic API Tests: {tester.tests_passed}/{tester.tests_run} ({tester.tests_passed/tester.tests_run*100:.1f}%)")
    
    for test_name, result in test_results.items():
        status = "✅" if result else "❌"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print("=" * 50)
    
    # Calculate overall success
    all_tests_passed = all(test_results.values()) and (tester.tests_passed == tester.tests_run)
    
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED! CLIENT SERVICES Platform is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the results above.")
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())
