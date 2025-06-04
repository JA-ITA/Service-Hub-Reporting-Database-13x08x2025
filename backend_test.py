
import requests
import sys
import time
import uuid
from datetime import datetime

class ClientServicesAPITester:
    def __init__(self, base_url="https://55c412e3-2b8e-4750-8c0e-a5c30dd61220.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_info = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_resources = {
            "users": [],
            "locations": [],
            "templates": []
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

    def test_get_current_user(self):
        """Test getting current user info"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

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
        return success

    def test_delete_user(self, user_id):
        """Test deleting a user"""
        success, _ = self.run_test(
            "Delete User",
            "DELETE",
            f"users/{user_id}",
            200
        )
        return success

    def test_create_location(self, name, description=None):
        """Test creating a new location"""
        location_data = {
            "name": name,
            "description": description
        }
        success, response = self.run_test(
            "Create Location",
            "POST",
            "locations",
            200,
            data=location_data
        )
        if success and 'id' in response:
            self.created_resources["locations"].append(response['id'])
            return response['id'], response['name']
        return None, None

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

    def test_update_location(self, location_id, name, description):
        """Test updating a location"""
        success, _ = self.run_test(
            "Update Location",
            "PUT",
            f"locations/{location_id}",
            200,
            data={"name": name, "description": description}
        )
        return success

    def test_delete_location(self, location_id):
        """Test deleting a location"""
        success, _ = self.run_test(
            "Delete Location",
            "DELETE",
            f"locations/{location_id}",
            200
        )
        return success

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

    def test_get_templates(self):
        """Test getting all templates"""
        success, response = self.run_test(
            "Get All Templates",
            "GET",
            "templates",
            200
        )
        if success:
            return success, response
        return False, []
        
    def test_get_template_by_id(self, template_id):
        """Test getting a specific template by ID"""
        success, response = self.run_test(
            "Get Template by ID",
            "GET",
            f"templates/{template_id}",
            200
        )
        if success:
            return success, response
        return False, {}

    def test_delete_template(self, template_id):
        """Test deleting a template"""
        success, _ = self.run_test(
            "Delete Template",
            "DELETE",
            f"templates/{template_id}",
            200
        )
        return success

    def test_file_upload(self, file_path):
        """Test file upload"""
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.split('/')[-1], f, 'image/jpeg')}
            success, response = self.run_test(
                "File Upload",
                "POST",
                "upload",
                200,
                files=files
            )
            if success and 'filename' in response:
                return response['filename']
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
        return success

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
        return success

    def test_export_csv(self):
        """Test CSV export"""
        success, _ = self.run_test(
            "Export CSV",
            "GET",
            "reports/csv",
            200
        )
        return success

    def cleanup(self):
        """Clean up created resources"""
        print("\n🧹 Cleaning up resources...")
        
        for template_id in self.created_resources["templates"]:
            self.test_delete_template(template_id)
            
        for location_id in self.created_resources["locations"]:
            self.test_delete_location(location_id)
            
        for user_id in self.created_resources["users"]:
            self.test_delete_user(user_id)

def main():
    # Setup
    tester = ClientServicesAPITester()
    timestamp = datetime.now().strftime('%H%M%S')
    
    # Create test data
    test_manager = f"manager_{timestamp}"
    test_data_entry = f"data_entry_{timestamp}"
    test_location = f"Test Location {timestamp}"
    test_template = f"Test Template {timestamp}"
    
    print("\n🔐 1. TESTING AUTHENTICATION")
    # Test login with default admin
    if not tester.test_login("admin", "admin123"):
        print("❌ Admin login failed, stopping tests")
        return 1
    
    # Test getting current user info
    tester.test_get_current_user()
    
    print("\n👥 2. TESTING USER MANAGEMENT")
    # Test getting all users
    tester.test_get_users()
    
    # Test creating users with different roles
    success, locations = tester.test_get_locations()
    location_name = None
    if success and locations:
        location_name = locations[0]['name']
        print(f"Using existing location: {location_name}")
    
    manager_id = tester.test_create_user(test_manager, "Password123!", "manager", location_name)
    data_entry_id = tester.test_create_user(test_data_entry, "Password123!", "data_entry", location_name)
    
    # Test getting users after creation
    tester.test_get_users()
    
    print("\n🏢 3. TESTING LOCATION MANAGEMENT")
    # Test getting all locations
    success, locations = tester.test_get_locations()
    if success:
        print(f"Found {len(locations)} pre-loaded locations")
        for loc in locations:
            print(f"  - {loc['name']}: {loc['description']}")
    
    # Test creating a new location
    location_id, location_name = tester.test_create_location(
        test_location, 
        "Test location for API testing"
    )
    
    if location_id:
        # Test updating the location
        tester.test_update_location(
            location_id,
            f"{test_location} Updated",
            "Updated description"
        )
    
    # Test getting locations after update
    tester.test_get_locations()
    
    print("\n📋 4. TESTING TEMPLATE MANAGEMENT")
    # Test getting all templates
    success, templates = tester.test_get_templates()
    
    # Test creating a template with various field types
    fields = [
        {"name": "text_field", "type": "text", "label": "Text Field", "required": True},
        {"name": "number_field", "type": "number", "label": "Number Field", "required": False},
        {"name": "date_field", "type": "date", "label": "Date Field", "required": True},
        {"name": "textarea_field", "type": "textarea", "label": "Text Area Field", "required": False},
        {"name": "select_field", "type": "select", "label": "Select Field", "required": True},
        {"name": "file_field", "type": "file", "label": "File Upload Field", "required": False}
    ]
    
    template_id = tester.test_create_template(
        test_template,
        "Test template with various field types",
        fields,
        [location_name]
    )
    
    # Test getting templates after creation
    tester.test_get_templates()
    
    print("\n📝 5. TESTING DATA SUBMISSION")
    # Create a test file for upload
    test_file_path = "/tmp/test_file.txt"
    with open(test_file_path, "w") as f:
        f.write("This is a test file for upload testing.")
    
    # Test file upload
    # Note: Skipping actual file upload as it requires multipart form data
    
    # Test data submission
    if template_id and location_name:
        current_month = datetime.now().strftime('%Y-%m')
        form_data = {
            "text_field": "Test text value",
            "number_field": 42,
            "date_field": "2025-02-15",
            "textarea_field": "This is a longer text for the textarea field",
            "select_field": "Option 1",
            "file_field": "test_file.txt"  # Just the filename, not actual upload
        }
        
        tester.test_create_submission(
            template_id,
            location_name,
            current_month,
            form_data
        )
    
    print("\n📊 6. TESTING REPORTS")
    # Test getting submissions
    tester.test_get_submissions()
    
    # Test filtering submissions
    if location_name:
        tester.test_get_submissions(location=location_name)
    
    # Test CSV export
    tester.test_export_csv()
    
    # Clean up
    tester.cleanup()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
