import requests
import sys
import time
import uuid
from datetime import datetime

class ClientServicesAPITester:
    def __init__(self, base_url="https://restore-hub.preview.emergentagent.com/api"):
        self.base_url = base_url
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

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    # For file uploads, don't use JSON content type
                    headers.pop('Content-Type', None)
                    response = requests.post(url, files=files, headers=headers)
                else:
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
                    return success, response.json() if response.content else {}
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json().get('detail', 'No detail provided')
                    print(f"Error detail: {error_detail}")
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
            print(f"Logged in as {username} with role {response['user']['role']}")
            return True
        return False

    def test_get_submission(self, submission_id):
        """Test getting a submission by ID (Feature 1: Detailed Submission View)"""
        success, response = self.run_test(
            "Get Submission Detail",
            "GET",
            f"submissions/{submission_id}",
            200
        )
        if success:
            print(f"Submission details retrieved successfully:")
            print(f"  - Template ID: {response.get('template_id')}")
            print(f"  - Location: {response.get('service_location')}")
            print(f"  - Month/Year: {response.get('month_year')}")
            print(f"  - Status: {response.get('status')}")
            print(f"  - Submitted by: {response.get('submitted_by')}")
            print(f"  - Form data fields: {len(response.get('form_data', {}))}")
            print(f"  - Attachments: {len(response.get('attachments', []))}")
            return True, response
        return False, {}

    def test_update_submission(self, submission_id, update_data):
        """Test updating a submission (Feature 2: Submission Editing)"""
        success, response = self.run_test(
            "Update Submission",
            "PUT",
            f"submissions/{submission_id}",
            200,
            data=update_data
        )
        if success:
            print(f"Submission updated successfully")
            return True, response
        return False, {}

    def test_get_user(self, user_id):
        """Test getting a user by ID (Feature 3: User Profile Editing)"""
        success, response = self.run_test(
            "Get User Detail",
            "GET",
            f"users/{user_id}",
            200
        )
        if success:
            print(f"User details retrieved successfully:")
            print(f"  - Username: {response.get('username')}")
            print(f"  - Role: {response.get('role')}")
            print(f"  - Assigned location: {response.get('assigned_location')}")
            return True, response
        return False, {}

    def test_update_user(self, user_id, update_data):
        """Test updating a user (Feature 3: User Profile Editing)"""
        success, response = self.run_test(
            "Update User",
            "PUT",
            f"users/{user_id}",
            200,
            data=update_data
        )
        if success:
            print(f"User updated successfully")
            return True, response
        return False, {}

    def test_create_user(self, username, password, role, location=None):
        """Test creating a new user"""
        user_data = {
            "username": username,
            "password": password,
            "role": role
        }
        if location:
            user_data["assigned_location"] = location
            
        success, response = self.run_test(
            f"Create User ({role})",
            "POST",
            "users",
            200,
            data=user_data
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
        if success:
            return success, response
        return False, []

    def test_get_locations(self):
        """Test getting all locations"""
        success, response = self.run_test(
            "Get All Locations",
            "GET",
            "locations",
            200
        )
        if success:
            return success, response
        return False, []

    def test_create_template(self, name, description, fields, locations):
        """Test creating a new template"""
        template_data = {
            "name": name,
            "description": description,
            "fields": fields,
            "assigned_locations": locations
        }
        success, response = self.run_test(
            "Create Template",
            "POST",
            "templates",
            200,
            data=template_data
        )
        if success and 'id' in response:
            self.created_resources["templates"].append(response['id'])
            return response['id']
        return None

    def test_create_submission(self, template_id, location, month_year, form_data):
        """Test creating a data submission"""
        submission_data = {
            "template_id": template_id,
            "service_location": location,
            "month_year": month_year,
            "form_data": form_data
        }
        success, response = self.run_test(
            "Create Submission",
            "POST",
            "submissions",
            200,
            data=submission_data
        )
        if success and 'id' in response:
            self.created_resources["submissions"].append(response['id'])
            return response['id']
        return None

    def test_get_submissions(self, location=None, month_year=None, template_id=None):
        """Test getting submissions with filters"""
        endpoint = "submissions"
        params = []
        if location:
            params.append(f"location={location}")
        if month_year:
            params.append(f"month_year={month_year}")
        if template_id:
            params.append(f"template_id={template_id}")
        
        if params:
            endpoint += "?" + "&".join(params)
            
        success, response = self.run_test(
            "Get Submissions",
            "GET",
            endpoint,
            200
        )
        if success:
            return success, response
        return False, []

    def cleanup(self):
        """Clean up created resources"""
        print("\n🧹 Cleaning up resources...")
        
        for submission_id in self.created_resources["submissions"]:
            print(f"Leaving submission {submission_id} for future reference")
            
        for template_id in self.created_resources["templates"]:
            print(f"Leaving template {template_id} for future reference")
            
        for user_id in self.created_resources["users"]:
            print(f"Leaving user {user_id} for future reference")

def test_feature_1_detailed_submission_view():
    """Test Feature 1: Detailed Submission View (All Users)"""
    print("\n🔍 TESTING FEATURE 1: DETAILED SUBMISSION VIEW")
    
    tester = ClientServicesAPITester()
    
    # Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # Get locations
    success, locations = tester.test_get_locations()
    if not success or not locations:
        print("❌ Failed to get locations")
        return False
    
    location_name = locations[0]['name']
    
    # Create a template
    fields = [
        {"name": "text_field", "type": "text", "label": "Text Field", "required": True},
        {"name": "number_field", "type": "number", "label": "Number Field", "required": False},
        {"name": "date_field", "type": "date", "label": "Date Field", "required": True}
    ]
    
    template_id = tester.test_create_template(
        f"Test Template {datetime.now().strftime('%H%M%S')}",
        "Test template for detailed view",
        fields,
        [location_name]
    )
    
    if not template_id:
        print("❌ Failed to create template")
        return False
    
    # Create a submission
    current_month = datetime.now().strftime('%Y-%m')
    form_data = {
        "text_field": "Test text value",
        "number_field": 42,
        "date_field": "2025-02-15"
    }
    
    submission_id = tester.test_create_submission(
        template_id,
        location_name,
        current_month,
        form_data
    )
    
    if not submission_id:
        print("❌ Failed to create submission")
        return False
    
    # Test getting submission details as admin
    success, submission = tester.test_get_submission(submission_id)
    if not success:
        print("❌ Admin failed to view submission details")
        return False
    
    # Create a manager user
    manager_username = f"manager_{datetime.now().strftime('%H%M%S')}"
    manager_id = tester.test_create_user(manager_username, "Password123!", "manager", location_name)
    
    if not manager_id:
        print("❌ Failed to create manager user")
        return False
    
    # Login as manager
    if not tester.test_login(manager_username, "Password123!"):
        print("❌ Manager login failed")
        return False
    
    # Test getting submission details as manager
    success, submission = tester.test_get_submission(submission_id)
    if not success:
        print("❌ Manager failed to view submission details")
        return False
    
    # Create a data entry user
    data_entry_username = f"data_entry_{datetime.now().strftime('%H%M%S')}"
    data_entry_id = tester.test_create_user(data_entry_username, "Password123!", "data_entry", location_name)
    
    if not data_entry_id:
        print("❌ Failed to create data entry user")
        return False
    
    # Login as data entry
    if not tester.test_login(data_entry_username, "Password123!"):
        print("❌ Data entry login failed")
        return False
    
    # Test getting submission details as data entry
    success, submission = tester.test_get_submission(submission_id)
    if not success:
        print("❌ Data entry failed to view submission details")
        return False
    
    print("✅ Feature 1 tests passed: All user roles can view submission details")
    return True

def test_feature_2_submission_editing():
    """Test Feature 2: Submission Editing (Managers & Admins)"""
    print("\n🔍 TESTING FEATURE 2: SUBMISSION EDITING")
    
    tester = ClientServicesAPITester()
    
    # Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # Get locations
    success, locations = tester.test_get_locations()
    if not success or not locations:
        print("❌ Failed to get locations")
        return False
    
    location_name = locations[0]['name']
    location_name_2 = locations[1]['name'] if len(locations) > 1 else None
    
    # Create a template
    fields = [
        {"name": "text_field", "type": "text", "label": "Text Field", "required": True},
        {"name": "number_field", "type": "number", "label": "Number Field", "required": False},
        {"name": "date_field", "type": "date", "label": "Date Field", "required": True}
    ]
    
    template_id = tester.test_create_template(
        f"Test Template {datetime.now().strftime('%H%M%S')}",
        "Test template for submission editing",
        fields,
        [location_name, location_name_2] if location_name_2 else [location_name]
    )
    
    if not template_id:
        print("❌ Failed to create template")
        return False
    
    # Create a submission
    current_month = datetime.now().strftime('%Y-%m')
    form_data = {
        "text_field": "Original text value",
        "number_field": 42,
        "date_field": "2025-02-15"
    }
    
    submission_id = tester.test_create_submission(
        template_id,
        location_name,
        current_month,
        form_data
    )
    
    if not submission_id:
        print("❌ Failed to create submission")
        return False
    
    # Test updating submission as admin
    update_data = {
        "form_data": {
            "text_field": "Updated by admin",
            "number_field": 100,
            "date_field": "2025-02-20"
        },
        "status": "approved"
    }
    
    success, _ = tester.test_update_submission(submission_id, update_data)
    if not success:
        print("❌ Admin failed to update submission")
        return False
    
    # Verify the update
    success, submission = tester.test_get_submission(submission_id)
    if not success:
        print("❌ Failed to get updated submission")
        return False
    
    if submission['form_data']['text_field'] != "Updated by admin" or submission['status'] != "approved":
        print("❌ Submission update verification failed")
        return False
    
    print("✅ Admin can edit submissions")
    
    # Create a manager user for the location
    manager_username = f"manager_{datetime.now().strftime('%H%M%S')}"
    manager_id = tester.test_create_user(manager_username, "Password123!", "manager", location_name)
    
    if not manager_id:
        print("❌ Failed to create manager user")
        return False
    
    # Login as manager
    if not tester.test_login(manager_username, "Password123!"):
        print("❌ Manager login failed")
        return False
    
    # Test updating submission as manager
    update_data = {
        "form_data": {
            "text_field": "Updated by manager",
            "number_field": 200,
            "date_field": "2025-02-25"
        },
        "status": "reviewed"
    }
    
    success, _ = tester.test_update_submission(submission_id, update_data)
    if not success:
        print("❌ Manager failed to update submission")
        return False
    
    # Verify the update
    success, submission = tester.test_get_submission(submission_id)
    if not success:
        print("❌ Failed to get updated submission")
        return False
    
    if submission['form_data']['text_field'] != "Updated by manager" or submission['status'] != "reviewed":
        print("❌ Submission update verification failed")
        return False
    
    print("✅ Manager can edit submissions from their location")
    
    # Create a submission for a different location if available
    if location_name_2:
        submission_id_2 = tester.test_create_submission(
            template_id,
            location_name_2,
            current_month,
            form_data
        )
        
        if not submission_id_2:
            print("❌ Failed to create submission for second location")
            return False
        
        # Test updating submission from different location as manager
        update_data = {
            "form_data": {
                "text_field": "Should not update",
                "number_field": 999,
                "date_field": "2025-02-28"
            },
            "status": "rejected"
        }
        
        success, _ = tester.test_update_submission(submission_id_2, update_data)
        if success:
            print("❌ Manager should not be able to update submission from different location")
            return False
        
        print("✅ Manager cannot edit submissions from other locations")
    
    # Create a data entry user
    data_entry_username = f"data_entry_{datetime.now().strftime('%H%M%S')}"
    data_entry_id = tester.test_create_user(data_entry_username, "Password123!", "data_entry", location_name)
    
    if not data_entry_id:
        print("❌ Failed to create data entry user")
        return False
    
    # Login as data entry
    if not tester.test_login(data_entry_username, "Password123!"):
        print("❌ Data entry login failed")
        return False
    
    # Test updating submission as data entry (should fail)
    update_data = {
        "form_data": {
            "text_field": "Should not update",
            "number_field": 999,
            "date_field": "2025-02-28"
        },
        "status": "rejected"
    }
    
    success, _ = tester.test_update_submission(submission_id, update_data)
    if success:
        print("❌ Data entry user should not be able to update submissions")
        return False
    
    print("✅ Data entry users cannot edit submissions")
    
    print("✅ Feature 2 tests passed: Submission editing permissions work correctly")
    return True

def test_feature_3_user_profile_editing():
    """Test Feature 3: User Profile Editing (Admin only)"""
    print("\n🔍 TESTING FEATURE 3: USER PROFILE EDITING")
    
    tester = ClientServicesAPITester()
    
    # Login as admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return False
    
    # Get locations
    success, locations = tester.test_get_locations()
    if not success or not locations:
        print("❌ Failed to get locations")
        return False
    
    location_name = locations[0]['name']
    location_name_2 = locations[1]['name'] if len(locations) > 1 else location_name
    
    # Create a test user
    test_username = f"test_user_{datetime.now().strftime('%H%M%S')}"
    user_id = tester.test_create_user(test_username, "Password123!", "data_entry", location_name)
    
    if not user_id:
        print("❌ Failed to create test user")
        return False
    
    # Test getting user details
    success, user = tester.test_get_user(user_id)
    if not success:
        print("❌ Failed to get user details")
        return False
    
    # Test updating user as admin
    update_data = {
        "username": f"{test_username}_updated",
        "role": "manager",
        "assigned_location": location_name_2
    }
    
    success, _ = tester.test_update_user(user_id, update_data)
    if not success:
        print("❌ Admin failed to update user")
        return False
    
    # Verify the update
    success, updated_user = tester.test_get_user(user_id)
    if not success:
        print("❌ Failed to get updated user")
        return False
    
    if updated_user['username'] != f"{test_username}_updated" or updated_user['role'] != "manager" or updated_user['assigned_location'] != location_name_2:
        print("❌ User update verification failed")
        return False
    
    print("✅ Admin can edit user profiles")
    
    # Test updating user with password
    update_data = {
        "username": f"{test_username}_updated",
        "password": "NewPassword456!",
        "role": "manager",
        "assigned_location": location_name_2
    }
    
    success, _ = tester.test_update_user(user_id, update_data)
    if not success:
        print("❌ Admin failed to update user with password")
        return False
    
    print("✅ Admin can update user password")
    
    # Create a manager user
    manager_username = f"manager_{datetime.now().strftime('%H%M%S')}"
    manager_id = tester.test_create_user(manager_username, "Password123!", "manager", location_name)
    
    if not manager_id:
        print("❌ Failed to create manager user")
        return False
    
    # Login as manager
    if not tester.test_login(manager_username, "Password123!"):
        print("❌ Manager login failed")
        return False
    
    # Test getting user details as manager (should fail)
    success, _ = tester.test_get_user(user_id)
    if success:
        print("❌ Manager should not be able to get user details")
        return False
    
    # Test updating user as manager (should fail)
    update_data = {
        "username": f"{test_username}_should_not_update",
        "role": "data_entry",
        "assigned_location": location_name
    }
    
    success, _ = tester.test_update_user(user_id, update_data)
    if success:
        print("❌ Manager should not be able to update users")
        return False
    
    print("✅ Managers cannot edit user profiles")
    
    # Create a data entry user
    data_entry_username = f"data_entry_{datetime.now().strftime('%H%M%S')}"
    data_entry_id = tester.test_create_user(data_entry_username, "Password123!", "data_entry", location_name)
    
    if not data_entry_id:
        print("❌ Failed to create data entry user")
        return False
    
    # Login as data entry
    if not tester.test_login(data_entry_username, "Password123!"):
        print("❌ Data entry login failed")
        return False
    
    # Test getting user details as data entry (should fail)
    success, _ = tester.test_get_user(user_id)
    if success:
        print("❌ Data entry user should not be able to get user details")
        return False
    
    # Test updating user as data entry (should fail)
    update_data = {
        "username": f"{test_username}_should_not_update",
        "role": "data_entry",
        "assigned_location": location_name
    }
    
    success, _ = tester.test_update_user(user_id, update_data)
    if success:
        print("❌ Data entry user should not be able to update users")
        return False
    
    print("✅ Data entry users cannot edit user profiles")
    
    print("✅ Feature 3 tests passed: User profile editing permissions work correctly")
    return True

def main():
    print("\n🔍 TESTING NEW FEATURES IN CLIENT SERVICES PLATFORM")
    
    # Test Feature 1: Detailed Submission View
    feature1_success = test_feature_1_detailed_submission_view()
    
    # Test Feature 2: Submission Editing
    feature2_success = test_feature_2_submission_editing()
    
    # Test Feature 3: User Profile Editing
    feature3_success = test_feature_3_user_profile_editing()
    
    # Print summary
    print("\n📊 FEATURE TESTING SUMMARY:")
    print(f"Feature 1 (Detailed Submission View): {'✅ PASSED' if feature1_success else '❌ FAILED'}")
    print(f"Feature 2 (Submission Editing): {'✅ PASSED' if feature2_success else '❌ FAILED'}")
    print(f"Feature 3 (User Profile Editing): {'✅ PASSED' if feature3_success else '❌ FAILED'}")
    
    if feature1_success and feature2_success and feature3_success:
        print("\n🎉 All features passed backend API testing!")
        return 0
    else:
        print("\n⚠️ Some features failed backend API testing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())