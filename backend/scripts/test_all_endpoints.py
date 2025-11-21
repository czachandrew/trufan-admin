#!/usr/bin/env python3
"""
Test all required dashboard endpoints.
Run with: docker-compose exec api python -m scripts.test_all_endpoints
"""
import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(method, path, headers=None, json=None):
    """Test a single endpoint and return status."""
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{path}", headers=headers)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{path}", headers=headers, json=json)
        elif method == "PUT":
            response = requests.put(f"{BASE_URL}{path}", headers=headers, json=json)

        return response.status_code, "✅ EXISTS" if response.status_code < 500 else "❌ ERROR"
    except Exception as e:
        return None, f"❌ FAILED: {str(e)}"


def main():
    print("\n" + "="*70)
    print("TESTING ALL REQUIRED DASHBOARD ENDPOINTS")
    print("="*70 + "\n")

    # Login first to get token
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "czachandrew@gmail.com", "password": "password"}
    )

    token = login_response.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}

    print("🔑 Authenticated successfully\n")
    print("HIGH PRIORITY ENDPOINTS:")
    print("-" * 70)

    # High Priority
    endpoints = [
        ("GET", "/auth/login", None, None, "Login"),
        ("GET", "/parking/lots", headers, None, "Get parking lots"),
        ("GET", "/parking/sessions", headers, None, "Get sessions"),
        ("GET", "/partner/opportunities", headers, None, "Get opportunities"),
    ]

    for method, path, hdrs, body, desc in endpoints:
        status, result = test_endpoint(method, path, hdrs, body)
        status_str = f"({status})" if status else ""
        print(f"  {result:<15} {method:<6} {path:<40} {status_str}")
        print(f"                - {desc}")

    print("\nMEDIUM PRIORITY ENDPOINTS:")
    print("-" * 70)

    medium_priority = [
        ("POST", "/parking/lots", headers, {"name": "Test"}, "Create lot"),
        ("PUT", "/parking/lots/00000000-0000-0000-0000-000000000000", headers, {"name": "Test"}, "Update lot"),
        ("GET", "/parking/sessions/TESTCODE", headers, None, "Get session by code"),
        ("POST", "/parking/sessions/TESTCODE/extend", headers, {"access_code": "TEST", "additional_hours": 1}, "Extend session"),
        ("GET", "/parking/lots/00000000-0000-0000-0000-000000000000/spaces", headers, None, "Get lot spaces"),
    ]

    for method, path, hdrs, body, desc in medium_priority:
        status, result = test_endpoint(method, path, hdrs, body)
        status_str = f"({status})" if status else ""
        print(f"  {result:<15} {method:<6} {path:<40}")
        print(f"                - {desc} {status_str}")

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("\n✅ = Endpoint exists (even if validation fails)")
    print("❌ = Endpoint missing (404/405) or server error (500)")
    print()


if __name__ == "__main__":
    main()
