
import requests
import sys
from datetime import datetime, timedelta
import json

class DashboardAPITester:
    def __init__(self, base_url="https://55c412e3-2b8e-4750-8c0e-a5c30dd61220.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.headers = {'Content-Type': 'application/json'}

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        
        if self.token:
            self.headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=self.headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=self.headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers)

            success = response.status_code == expected_status
            
            print(f"URL: {url}")
            print(f"Status Code: {response.status_code}")
            
            try:
                response_data = response.json()
                print(f"Response: {json.dumps(response_data, indent=2)}")
            except:
                print(f"Response: {response.text}")
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")

            return success, response.json() if 'application/json' in response.headers.get('Content-Type', '') else response.text

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
            return True
        return False

    def test_get_submissions_by_location(self, month=None, year=None):
        """Test getting submissions by location"""
        params = {}
        if month is not None:
            params['month'] = month
        if year is not None:
            params['year'] = year
            
        success, response = self.run_test(
            f"Get Submissions by Location (Month: {month}, Year: {year})",
            "GET",
            "dashboard/submissions-by-location",
            200,
            params=params
        )
        return success, response

    def test_get_missing_reports(self):
        """Test getting missing reports"""
        success, response = self.run_test(
            "Get Missing Reports",
            "GET",
            "dashboard/missing-reports",
            200
        )
        return success, response

    def test_set_report_deadline(self, deadline_date):
        """Test setting report deadline"""
        data = {
            "setting_key": "report_deadline",
            "setting_value": deadline_date.isoformat()
        }
        success, response = self.run_test(
            "Set Report Deadline",
            "POST",
            "admin/settings",
            200,
            data=data
        )
        return success, response

    def test_get_report_deadline(self):
        """Test getting report deadline"""
        success, response = self.run_test(
            "Get Report Deadline",
            "GET",
            "admin/settings/report_deadline",
            200
        )
        return success, response

def main():
    # Setup
    tester = DashboardAPITester()
    
    # Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Login failed, stopping tests")
        return 1

    # Test getting submissions by location (no filter)
    success_no_filter, response_no_filter = tester.test_get_submissions_by_location()
    if not success_no_filter:
        print("❌ Getting submissions by location failed")
    
    # Test getting submissions by location (with month filter)
    current_month = datetime.now().month
    current_year = datetime.now().year
    success_with_filter, response_with_filter = tester.test_get_submissions_by_location(month=current_month, year=current_year)
    if not success_with_filter:
        print("❌ Getting submissions by location with filter failed")
    
    # Test getting missing reports (before setting deadline)
    success_missing_before, response_missing_before = tester.test_get_missing_reports()
    if not success_missing_before:
        print("❌ Getting missing reports failed")
    
    # Test setting report deadline
    deadline_date = datetime.now() - timedelta(days=1)  # Yesterday
    success_set_deadline, response_set_deadline = tester.test_set_report_deadline(deadline_date)
    if not success_set_deadline:
        print("❌ Setting report deadline failed")
    
    # Test getting report deadline
    success_get_deadline, response_get_deadline = tester.test_get_report_deadline()
    if not success_get_deadline:
        print("❌ Getting report deadline failed")
    
    # Test getting missing reports (after setting deadline)
    success_missing_after, response_missing_after = tester.test_get_missing_reports()
    if not success_missing_after:
        print("❌ Getting missing reports after setting deadline failed")
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
