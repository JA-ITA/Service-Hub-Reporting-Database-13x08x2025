
import requests
import sys
import json
from datetime import datetime

class ReportsAPITester:
    def __init__(self, base_url="https://e2f25f62-fd90-478f-a483-cf62a80407f6.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_token = None
        self.manager_token = None
        self.data_entry_token = None

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        elif self.token:
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

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if response.content:
                    try:
                        return success, response.json()
                    except:
                        return success, response.content
                return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def login(self, username, password):
        """Login and get token"""
        success, response = self.run_test(
            f"Login as {username}",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True, response
        return False, {}

    def login_as_all_roles(self):
        """Login as admin, manager, and data_entry"""
        success, response = self.login("admin", "admin123")
        if success:
            self.admin_token = self.token
            print("✅ Admin login successful")
        else:
            print("❌ Admin login failed")
            return False

        success, response = self.login("manager", "manager123")
        if success:
            self.manager_token = self.token
            print("✅ Manager login successful")
        else:
            print("❌ Manager login failed")
            return False

        success, response = self.login("data_entry", "data123")
        if success:
            self.data_entry_token = self.token
            print("✅ Data entry login successful")
        else:
            print("❌ Data entry login failed")
            return False

        # Reset token to admin for subsequent tests
        self.token = self.admin_token
        return True

    def test_get_submissions(self):
        """Test getting submissions"""
        success, response = self.run_test(
            "Get Submissions",
            "GET",
            "submissions",
            200
        )
        return success, response

    def test_get_detailed_submissions(self):
        """Test getting detailed submissions with username"""
        success, response = self.run_test(
            "Get Detailed Submissions",
            "GET",
            "submissions/detailed",
            200
        )
        
        if success:
            # Verify that submissions have username field
            if len(response) > 0:
                if "submitted_by_username" in response[0]:
                    print("✅ Submissions include username field")
                else:
                    print("❌ Submissions missing username field")
                    success = False
        
        return success, response

    def test_submissions_filtering(self):
        """Test submissions filtering"""
        # Get all submissions first to find valid filter values
        _, all_submissions = self.test_get_submissions()
        
        if not all_submissions or len(all_submissions) == 0:
            print("❌ No submissions found to test filtering")
            return False
        
        # Extract filter values from first submission
        sample = all_submissions[0]
        location = sample.get("service_location")
        month_year = sample.get("month_year")
        template_id = sample.get("template_id")
        status = sample.get("status")
        
        # Test location filter
        if location:
            success, filtered = self.run_test(
                "Filter by Location",
                "GET",
                "submissions/detailed",
                200,
                params={"location": location}
            )
            if success and len(filtered) > 0:
                all_match = all(s.get("service_location") == location for s in filtered)
                print(f"✅ Location filter working: {all_match}")
            else:
                print("❌ Location filter not working properly")
        
        # Test month_year filter
        if month_year:
            success, filtered = self.run_test(
                "Filter by Month/Year",
                "GET",
                "submissions/detailed",
                200,
                params={"month_year": month_year}
            )
            if success and len(filtered) > 0:
                all_match = all(s.get("month_year") == month_year for s in filtered)
                print(f"✅ Month/Year filter working: {all_match}")
            else:
                print("❌ Month/Year filter not working properly")
        
        # Test template_id filter
        if template_id:
            success, filtered = self.run_test(
                "Filter by Template",
                "GET",
                "submissions/detailed",
                200,
                params={"template_id": template_id}
            )
            if success and len(filtered) > 0:
                all_match = all(s.get("template_id") == template_id for s in filtered)
                print(f"✅ Template filter working: {all_match}")
            else:
                print("❌ Template filter not working properly")
        
        return True

    def test_role_based_access(self):
        """Test role-based access to submissions"""
        # Test admin access (should see all submissions)
        success, admin_submissions = self.run_test(
            "Admin Access to Submissions",
            "GET",
            "submissions/detailed",
            200,
            token=self.admin_token
        )
        
        # Test manager access (should only see their location's submissions)
        success, manager_submissions = self.run_test(
            "Manager Access to Submissions",
            "GET",
            "submissions/detailed",
            200,
            token=self.manager_token
        )
        
        # Test data_entry access (should only see their location's submissions)
        success, data_entry_submissions = self.run_test(
            "Data Entry Access to Submissions",
            "GET",
            "submissions/detailed",
            200,
            token=self.data_entry_token
        )
        
        # Verify that admin sees more or equal submissions than manager and data_entry
        if len(admin_submissions) >= len(manager_submissions) and len(admin_submissions) >= len(data_entry_submissions):
            print("✅ Role-based access control working correctly")
            return True
        else:
            print("❌ Role-based access control issue detected")
            return False

    def test_csv_export(self):
        """Test CSV export functionality"""
        success, response = self.run_test(
            "Export CSV",
            "GET",
            "reports/csv",
            200
        )
        
        # Check if response is not empty
        if success and response:
            print("✅ CSV export working")
            return True
        else:
            print("❌ CSV export not working")
            return False

def main():
    tester = ReportsAPITester()
    
    # Login as admin
    success, _ = tester.login("admin", "admin123")
    if not success:
        print("❌ Login failed, stopping tests")
        return 1
    
    # Login as all roles for role-based tests
    tester.login_as_all_roles()
    
    # Test getting submissions
    tester.test_get_submissions()
    
    # Test getting detailed submissions with username
    tester.test_get_detailed_submissions()
    
    # Test submissions filtering
    tester.test_submissions_filtering()
    
    # Test role-based access
    tester.test_role_based_access()
    
    # Test CSV export
    tester.test_csv_export()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
