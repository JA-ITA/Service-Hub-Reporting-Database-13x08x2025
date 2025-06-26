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
        self.system_role_id = None

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

    def test_get_system_role(self, system_roles):
        """Get a system role for testing"""
        if not system_roles:
            print("❌ No roles available for testing")
            return None
            
        # Find the first system role
        system_role = next((role for role in system_roles if role.get('is_system_role', False)), None)
        if not system_role:
            print("❌ No system role found for testing")
            return None
            
        self.system_role_id = system_role['id']
        print(f"Selected system role: {system_role['name']} ({system_role['display_name']})")
        return system_role

    def test_update_system_role_display_name(self, system_role):
        """Test updating a system role's display name (should succeed)"""
        if not system_role:
            print("❌ No system role available for testing")
            return False
            
        update_data = {
            "name": system_role['name'],  # Keep the original name
            "display_name": f"Updated {system_role['display_name']} {int(time.time())}",
            "description": system_role['description'],
            "permissions": system_role['permissions']
        }
        
        success, response = self.run_test(
            "Update System Role Display Name (Should Succeed)",
            "PUT",
            f"roles/{system_role['id']}",
            200,
            data=update_data
        )
        
        return success

    def test_update_system_role_permissions(self, system_role):
        """Test updating a system role's permissions (should succeed)"""
        if not system_role:
            print("❌ No system role available for testing")
            return False
            
        # Add 'statistics' permission if not already present
        new_permissions = system_role['permissions'].copy()
        if 'statistics' not in new_permissions:
            new_permissions.append('statistics')
        elif 'templates' not in new_permissions:
            new_permissions.append('templates')
        else:
            # Remove a permission if all are already present
            if len(new_permissions) > 1:
                new_permissions.pop()
        
        update_data = {
            "name": system_role['name'],  # Keep the original name
            "display_name": system_role['display_name'],
            "description": system_role['description'],
            "permissions": new_permissions
        }
        
        success, response = self.run_test(
            "Update System Role Permissions (Should Succeed)",
            "PUT",
            f"roles/{system_role['id']}",
            200,
            data=update_data
        )
        
        return success

    def test_update_system_role_name(self, system_role):
        """Test attempting to update a system role's name (should fail or be ignored)"""
        if not system_role:
            print("❌ No system role available for testing")
            return False
            
        update_data = {
            "name": f"changed_{system_role['name']}_{int(time.time())}",  # Try to change the name
            "display_name": system_role['display_name'],
            "description": system_role['description'],
            "permissions": system_role['permissions']
        }
        
        # This should either succeed (200) but ignore the name change, or return an error
        success, response = self.run_test(
            "Update System Role Name (Should Be Protected)",
            "PUT",
            f"roles/{system_role['id']}",
            200,
            data=update_data
        )
        
        # Verify the name wasn't changed
        if success:
            success_verify, updated_role = self.run_test(
                "Verify System Role Name Unchanged",
                "GET",
                f"roles/{system_role['id']}",
                200
            )
            
            if success_verify:
                if updated_role['name'] == system_role['name']:
                    print("✅ System role name was protected as expected")
                    return True
                else:
                    print(f"❌ System role name was changed from {system_role['name']} to {updated_role['name']}")
                    return False
        
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

    def test_delete_system_role(self, system_role):
        """Test attempting to delete a system role (should fail)"""
        if not system_role:
            print("❌ No system role available for testing")
            return False
            
        success, response = self.run_test(
            "Delete System Role (Should Fail)",
            "DELETE",
            f"roles/{system_role['id']}",
            403
        )
        
        # This test passes if the delete fails with 403
        return success

    def test_create_user_with_role(self, role):
        """Test creating a user with a specific role"""
        if not role:
            print("❌ No role available for testing")
            return False
            
        timestamp = int(time.time())
        user_data = {
            "username": f"test_user_{timestamp}",
            "password": "Test123!",
            "role": role['name']
        }
        
        success, response = self.run_test(
            f"Create User with {role.get('is_system_role', False) and 'System' or 'Custom'} Role",
            "POST",
            "users",
            200,
            data=user_data
        )
        
        if success and 'id' in response:
            self.created_user_id = response['id']
            print(f"Created user with ID: {self.created_user_id}")
            return response
        return None

    def test_login_with_role(self, user):
        """Test login with a specific user"""
        if not user:
            print("❌ No user available for testing")
            return False
            
        success, response = self.run_test(
            "Login with Role User",
            "POST",
            "auth/login",
            200,
            data={"username": user['username'], "password": "Test123!"}
        )
        
        if success and 'access_token' in response:
            user_token = response['access_token']
            print(f"User info: {response['user']}")
            
            # Test accessing a page the user should have access to based on permissions
            if 'dashboard' in user.get('page_permissions', []):
                success, _ = self.run_test(
                    "Access Dashboard",
                    "GET",
                    "dashboard/submissions-by-location",
                    200,
                    token=user_token
                )
                
                return success
            return True
        return False

def main():
    # Setup
    tester = RoleManagementTester()
    
    print("=" * 50)
    print("UPDATED ROLE MANAGEMENT SYSTEM TESTS")
    print("=" * 50)
    
    # Run tests
    if not tester.test_admin_login():
        print("❌ Admin login failed, stopping tests")
        return 1

    # Test getting all roles
    all_roles = tester.test_get_roles()
    
    # Get a system role for testing
    system_role = tester.test_get_system_role(all_roles)
    
    if system_role:
        # Test 1: Update system role display name (should succeed)
        tester.test_update_system_role_display_name(system_role)
        
        # Test 2: Update system role permissions (should succeed)
        tester.test_update_system_role_permissions(system_role)
        
        # Test 3: Update system role name (should be protected)
        tester.test_update_system_role_name(system_role)
        
        # Test 4: Delete system role (should still fail)
        tester.test_delete_system_role(system_role)
        
        # Test 5: Create user with updated system role
        user = tester.test_create_user_with_role(system_role)
        
        # Test 6: Login with system role user
        if user:
            tester.test_login_with_role(user)
    
    # Test custom role functionality still works
    custom_role = tester.test_create_custom_role()
    
    if custom_role:
        # Test getting the custom role
        tester.test_get_custom_role()
        
        # Test updating the custom role
        tester.test_update_custom_role()
        
        # Test deleting the custom role
        tester.test_delete_custom_role()
    
    # Print results
    print("\n" + "=" * 50)
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run} ({tester.tests_passed/tester.tests_run*100:.1f}%)")
    print("=" * 50)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
