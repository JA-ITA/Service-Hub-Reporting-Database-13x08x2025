import requests
import json
import sys
import time
from datetime import datetime

class RoleManagementTester:
    def __init__(self, base_url="https://e2f25f62-fd90-478f-a483-cf62a80407f6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_token = None
        self.custom_role_id = None
        self.created_user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        elif self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
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

    def test_admin_login(self):
        """Test admin login and get token"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.admin_token = response['access_token']
            print(f"Admin user info: {response['user']}")
            return True
        return False

    def test_get_roles(self):
        """Test getting all roles"""
        success, response = self.run_test(
            "Get All Roles",
            "GET",
            "roles",
            200
        )
        if success:
            print(f"Found {len(response)} roles:")
            for role in response:
                print(f"  - {role['name']} ({role['display_name']}): System Role: {role.get('is_system_role', False)}")
            return response
        return []

    def test_create_custom_role(self):
        """Test creating a custom role"""
        timestamp = int(time.time())
        role_data = {
            "name": f"test_role_{timestamp}",
            "display_name": f"Test Role {timestamp}",
            "description": "A test role created by automated testing",
            "permissions": ["dashboard", "submit", "reports"]
        }
        
        success, response = self.run_test(
            "Create Custom Role",
            "POST",
            "roles",
            200,
            data=role_data
        )
        
        if success and 'id' in response:
            self.custom_role_id = response['id']
            print(f"Created custom role with ID: {self.custom_role_id}")
            return response
        return None

    def test_get_custom_role(self):
        """Test getting a specific role"""
        if not self.custom_role_id:
            print("❌ No custom role ID available for testing")
            return None
            
        success, response = self.run_test(
            "Get Custom Role",
            "GET",
            f"roles/{self.custom_role_id}",
            200
        )
        
        if success:
            print(f"Custom role details: {response}")
            return response
        return None

    def test_update_custom_role(self):
        """Test updating a custom role"""
        if not self.custom_role_id:
            print("❌ No custom role ID available for testing")
            return False
            
        update_data = {
            "name": f"updated_role_{int(time.time())}",
            "display_name": "Updated Test Role",
            "description": "An updated test role",
            "permissions": ["dashboard", "submit", "reports", "statistics"]
        }
        
        success, response = self.run_test(
            "Update Custom Role",
            "PUT",
            f"roles/{self.custom_role_id}",
            200,
            data=update_data
        )
        
        return success

    def test_update_system_role(self, system_roles):
        """Test attempting to update a system role (should fail)"""
        if not system_roles:
            print("❌ No system roles available for testing")
            return False
            
        # Find the first system role
        system_role = next((role for role in system_roles if role.get('is_system_role', False)), None)
        if not system_role:
            print("❌ No system role found for testing")
            return False
            
        update_data = {
            "name": system_role['name'],
            "display_name": "Attempted Update",
            "description": "This update should fail",
            "permissions": ["dashboard"]
        }
        
        success, response = self.run_test(
            "Update System Role (Should Fail)",
            "PUT",
            f"roles/{system_role['id']}",
            403,
            data=update_data
        )
        
        # This test passes if the update fails with 403
        return success

    def test_delete_custom_role(self):
        """Test deleting a custom role"""
        if not self.custom_role_id:
            print("❌ No custom role ID available for testing")
            return False
            
        success, response = self.run_test(
            "Delete Custom Role",
            "DELETE",
            f"roles/{self.custom_role_id}",
            200
        )
        
        return success

    def test_delete_system_role(self, system_roles):
        """Test attempting to delete a system role (should fail)"""
        if not system_roles:
            print("❌ No system roles available for testing")
            return False
            
        # Find the first system role
        system_role = next((role for role in system_roles if role.get('is_system_role', False)), None)
        if not system_role:
            print("❌ No system role found for testing")
            return False
            
        success, response = self.run_test(
            "Delete System Role (Should Fail)",
            "DELETE",
            f"roles/{system_role['id']}",
            403
        )
        
        # This test passes if the delete fails with 403
        return success

    def test_create_user_with_custom_role(self):
        """Test creating a user with a custom role"""
        if not self.custom_role_id:
            print("❌ No custom role ID available for testing")
            return False
            
        # First, get the custom role to get its name
        success, role = self.run_test(
            "Get Custom Role for User Creation",
            "GET",
            f"roles/{self.custom_role_id}",
            200
        )
        
        if not success or 'name' not in role:
            return False
            
        timestamp = int(time.time())
        user_data = {
            "username": f"test_user_{timestamp}",
            "password": "Test123!",
            "role": role['name']
        }
        
        success, response = self.run_test(
            "Create User with Custom Role",
            "POST",
            "users",
            200,
            data=user_data
        )
        
        if success and 'id' in response:
            self.created_user_id = response['id']
            print(f"Created user with ID: {self.created_user_id}")
            return True
        return False

    def test_login_with_custom_role(self):
        """Test login with the custom role user"""
        if not self.created_user_id:
            print("❌ No user ID available for testing")
            return False
            
        # First, get the user to get its username
        success, user = self.run_test(
            "Get User for Login",
            "GET",
            f"users/{self.created_user_id}",
            200
        )
        
        if not success or 'username' not in user:
            return False
            
        success, response = self.run_test(
            "Login with Custom Role User",
            "POST",
            "auth/login",
            200,
            data={"username": user['username'], "password": "Test123!"}
        )
        
        if success and 'access_token' in response:
            custom_user_token = response['access_token']
            print(f"Custom role user info: {response['user']}")
            
            # Test accessing a page the user should have access to
            success, _ = self.run_test(
                "Access Allowed Page",
                "GET",
                "dashboard/submissions-by-location",
                200,
                token=custom_user_token
            )
            
            return success
        return False

def main():
    # Setup
    tester = RoleManagementTester()
    
    print("=" * 50)
    print("ROLE MANAGEMENT SYSTEM TESTS")
    print("=" * 50)
    
    # Run tests
    if not tester.test_admin_login():
        print("❌ Admin login failed, stopping tests")
        return 1

    # Test getting all roles
    all_roles = tester.test_get_roles()
    
    # Test creating a custom role
    custom_role = tester.test_create_custom_role()
    
    if custom_role:
        # Test getting the custom role
        tester.test_get_custom_role()
        
        # Test updating the custom role
        tester.test_update_custom_role()
        
        # Test creating a user with the custom role
        tester.test_create_user_with_custom_role()
        
        # Test logging in with the custom role user
        tester.test_login_with_custom_role()
    
    # Test updating a system role (should fail)
    tester.test_update_system_role(all_roles)
    
    # Test deleting a system role (should fail)
    tester.test_delete_system_role(all_roles)
    
    # Test deleting the custom role
    if custom_role:
        tester.test_delete_custom_role()
    
    # Print results
    print("\n" + "=" * 50)
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run} ({tester.tests_passed/tester.tests_run*100:.1f}%)")
    print("=" * 50)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())