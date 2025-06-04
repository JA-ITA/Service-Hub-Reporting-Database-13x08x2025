
import requests
import json
import sys
from datetime import datetime, timedelta

class ClientServicesAPITester:
    def __init__(self, base_url="https://55c412e3-2b8e-4750-8c0e-a5c30dd61220.preview.emergentagent.com"):
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

    def test_get_current_user(self):
        """Test getting current user info"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_create_user(self, username, password, role, page_permissions=None):
        """Test creating a new user"""
        data = {
            "username": username,
            "password": password,
            "role": role
        }
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
            "submissions/detailed",
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

def main():
    # Setup
    tester = ClientServicesAPITester()
    
    print("=" * 50)
    print("CLIENT SERVICES PLATFORM API TESTS")
    print("=" * 50)
    
    # Test 1: Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return 1
    
    # Test 2: Get current user info
    tester.test_get_current_user()
    
    # Test 3: Get all users
    tester.test_get_users()
    
    # Test 4: Get all locations
    tester.test_get_locations()
    
    # Test 5: Get all templates
    tester.test_get_templates()
    
    # Test 6: Get submissions
    tester.test_get_submissions()
    
    # Test 7: Get detailed submissions with usernames
    tester.test_get_detailed_submissions()
    
    # Test 8: Create a statistician user
    timestamp = datetime.now().strftime("%H%M%S")
    statistician_id = tester.test_create_user(
        f"statistician_{timestamp}",
        "Test123!",
        "statistician"
    )
    
    # Test 9: Create a user with custom permissions
    custom_user_id = tester.test_create_user(
        f"custom_user_{timestamp}",
        "Test123!",
        "manager",
        page_permissions=["dashboard", "reports", "statistics"]
    )
    
    # Test 10: Update user
    if custom_user_id:
        tester.test_update_user(
            custom_user_id,
            {"assigned_location": "Central Hub"}
        )
    
    # Test 11: Get statistics options
    tester.test_get_statistics_options()
    
    # Test 12: Generate statistics
    tester.test_generate_statistics({
        "date_from": (datetime.now() - timedelta(days=30)).isoformat(),
        "date_to": datetime.now().isoformat(),
        "locations": [],
        "user_roles": [],
        "templates": [],
        "status": [],
        "group_by": "location"
    })
    
    # Test 13: Dashboard data
    tester.test_dashboard_submissions_by_location()
    
    # Print results
    print("\n" + "=" * 50)
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run} ({tester.tests_passed/tester.tests_run*100:.1f}%)")
    print("=" * 50)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
