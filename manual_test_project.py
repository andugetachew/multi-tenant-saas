import requests
import json

# Login
login_url = "http://localhost:8000/api/auth/login/"
login_data = {"email": "admin@gmail.com", "password": "admin123"}

try:
    login_response = requests.post(login_url, json=login_data)
    login_response.raise_for_status()
    token = login_response.json()["access"]
    print(f"Got token: {token[:50]}...")
except Exception as e:
    print(f"Login failed: {e}")
    exit(1)

# Create project
project_url = "http://localhost:8000/api/projects/"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "X-Organization-ID": "1",
}
project_data = {"name": "My First Project", "description": "Test project"}

try:
    project_response = requests.post(project_url, json=project_data, headers=headers)
    print(f"Status: {project_response.status_code}")
    print(f"Response text: {project_response.text}")  # Print raw response
    if project_response.status_code == 500:
        print("Server error! Check Django terminal for details.")
    else:
        print(f"Response JSON: {project_response.json()}")
except Exception as e:
    print(f"Error: {e}")


# from django.test import TestCase
# from rest_framework.test import APIClient
# from django.contrib.auth import get_user_model
# from organizations.models import Organization

# User = get_user_model()


# class ProjectAPITest(TestCase):

#     def setUp(self):
#         self.client = APIClient()

#         # Create organization
#         self.organization = Organization.objects.create(name="Test Org")

#         # Create user
#         self.user = User.objects.create_user(
#             email="admin@gmail.com", password="admin123", organization=self.organization
#         )

#         # Authenticate user (NO JWT needed in tests)
#         self.client.force_authenticate(user=self.user)

#     def test_create_project(self):
#         url = "/api/projects/"

#         data = {"name": "My First Project", "description": "Test project"}

#         response = self.client.post(
#             url, data, format="json", HTTP_X_ORGANIZATION_ID=str(self.organization.id)
#         )

#         print("\nSTATUS:", response.status_code)
#         print("RESPONSE:", response.data)

#         self.assertEqual(response.status_code, 201)
