import requests
import sys
from datetime import datetime

class ClientServicesAPITester:
    def __init__(self, base_url="https://function-check-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_info = None
        self.tests_run = 0
        self.tests_passed = 0
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

    def test_login_failure(self, username, password, expected_status=401):
        """Test login failure scenarios"""
        success, response = self.run_test(
            f"Login Failure: {username}",
            "POST",
            "auth/login",
            expected_status,
            data={"username": username, "password": password}
        )
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
            if username in self.test_users:
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
    if not tester.test_login_failure(test_username, test_password):
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
    
    # Step 10: Reset password
    new_password = "NewPass456!"
    if not tester.test_reset_password(test_username, reset_code, new_password):
        print(f"❌ Password reset failed for {test_username}")
        return False
    
    # Step 11: Test login with new password
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
    if not tester.test_login_failure(test_username, test_password):
        print(f"❌ Login with rejected user {test_username} should fail")
        return False
    
    print(f"✅ Login with rejected user {test_username} correctly failed")
    
    return True

def main():
    # Test the complete user registration, approval, and password reset flow
    registration_flow_success = test_user_registration_approval_flow()
    
    # Test the user rejection flow
    rejection_flow_success = test_user_rejection_flow()
    
    # Print results
    print("\n" + "=" * 50)
    print("Registration flow success: ", "✅" if registration_flow_success else "❌")
    print("Rejection flow success: ", "✅" if rejection_flow_success else "❌")
    print("=" * 50)
    
    return 0 if registration_flow_success and rejection_flow_success else 1

if __name__ == "__main__":
    sys.exit(main())