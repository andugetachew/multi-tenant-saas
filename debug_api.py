import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_login():
    print("Testing login...")
    response = requests.post(
        f"{BASE_URL}/auth/login/",
        json={"email": "admin@gmail.com", "password": "admin123"},
    )
    print("Status Code:", response.status_code)

    if response.status_code == 200:
        data = response.json()
        print("✅ Login successful!")
        print(f"Access Token: {data['access'][:50]}...")
        print(f"User: {data['user']['email']}")
        print(f"Organization: {data['user']['organization']}")
        return data["access"]
    else:
        print(f"❌ Login failed: {response.text}")
        return None


def test_projects(token):
    print("\nTesting Projects API...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/projects/", headers=headers)
    print("Status Code:", response.status_code)

    if response.status_code == 200:
        projects = response.json()
        print(f"✅ Found {len(projects)} projects")
        for p in projects[:3]:
            print(f"  - {p['name']}")
    else:
        print(f"❌ Failed: {response.text}")


def test_dashboard(token):
    print("\nTesting Dashboard...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/projects/dashboard/stats/", headers=headers)
    print("Status Code:", response.status_code)

    if response.status_code == 200:
        stats = response.json()
        print(
            f"✅ Dashboard: {stats['total_projects']} projects, {stats['total_tasks']} tasks"
        )
    else:
        print(f"❌ Failed: {response.text}")


if __name__ == "__main__":
    token = test_login()
    if token:
        test_projects(token)
        test_dashboard(token)
        print("\n✅ All tests passed!")


def test_create_project(token):
    print("\nTesting Create Project...")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(
        f"{BASE_URL}/projects/",
        headers=headers,
        json={"name": "Debug Test Project", "description": "Created by debug script"},
    )
    print("Status Code:", response.status_code)
    if response.status_code == 201:
        print(f"✅ Project created: {response.json()['name']}")
        return response.json()["id"]
    else:
        print(f"❌ Failed: {response.text}")
        return None


def test_create_comment(token, project_id):
    print("\nTesting Create Comment...")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(
        f"{BASE_URL}/comments/",
        headers=headers,
        json={"project": project_id, "content": "Debug comment"},
    )
    print("Status Code:", response.status_code)
    if response.status_code == 201:
        print("✅ Comment created!")
    else:
        print(f"❌ Failed: {response.text}")
