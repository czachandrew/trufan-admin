#!/usr/bin/env python3
"""
Test admin login.
Run with: docker-compose exec api python -m scripts.test_admin_login
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"


def test_login():
    """Test login with admin credentials."""
    print("\n" + "="*60)
    print("TESTING ADMIN LOGIN")
    print("="*60 + "\n")

    print("Attempting login...")
    print(f"  Email: czachandrew@gmail.com")
    print(f"  Password: password\n")

    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "czachandrew@gmail.com",
            "password": "password"
        }
    )

    print(f"Status Code: {response.status_code}\n")

    if response.status_code == 200:
        data = response.json()
        print("✅ LOGIN SUCCESSFUL!\n")
        print("Response:")
        print(json.dumps(data, indent=2))

        print("\n" + "="*60)
        print("ACCESS TOKEN (use this in your frontend)")
        print("="*60)
        print(data['access_token'])
        print("="*60 + "\n")

        print("User Info:")
        print(f"  ID: {data['user']['id']}")
        print(f"  Name: {data['user']['first_name']} {data['user']['last_name']}")
        print(f"  Email: {data['user']['email']}")
        print(f"  Role: {data['user']['role']}")
        print(f"  Email Verified: {data['user']['email_verified']}")
        print(f"  Active: {data['user']['is_active']}")
        print()
    else:
        print(f"❌ LOGIN FAILED!")
        print(f"Response: {response.text}")
        print()


if __name__ == "__main__":
    test_login()
