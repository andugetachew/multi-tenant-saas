import requests
import json

BASE_URL = "http://localhost:8000/api"
EMAIL = "admin@gmail.com"
PASSWORD = "admin123"

print("=" * 50)
print("TESTING MULTI-TENANT SAAS")
print("=" * 50)

# 1. Login
print("\n1. Logging in...")
try:
    response = requests.post(
        f"{BASE_URL}/auth/login/", json={"email": EMAIL, "password": PASSWORD}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")

    if response.status_code == 200:
        data = response.json()
        token = data.get("access")
        print(f"✅ Token obtained: {token[:50]}...")
    else:
        print(f"❌ Login failed: {response.text}")
        exit()
except Exception as e:
    print(f"❌ Error: {e}")
    exit()

headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# 2. Get organization
print("\n2. Getting organization...")
response = requests.get(f"{BASE_URL}/organizations/", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(f"✅ Organization: {response.json()}")
else:
    print(f"❌ Failed: {response.text}")

# 3. Create project
print("\n3. Creating project...")
response = requests.post(
    f"{BASE_URL}/projects/",
    headers=headers,
    json={"name": "Test Project", "description": "Testing all features"},
)
print(f"Status: {response.status_code}")
if response.status_code == 201:
    project = response.json()
    print(f"✅ Project created: {project}")
else:
    print(f"❌ Failed: {response.text}")

print("\n" + "=" * 50)
print("✅ TEST COMPLETE")
print("=" * 50)
