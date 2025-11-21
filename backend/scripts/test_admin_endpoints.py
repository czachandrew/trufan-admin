#!/usr/bin/env python3
"""
Test new admin endpoints.
Run with: docker-compose exec api python -m scripts.test_admin_endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"


def test_admin_endpoints():
    """Test admin endpoints with Bearer token."""
    print("\n" + "="*60)
    print("TESTING ADMIN ENDPOINTS")
    print("="*60 + "\n")

    # Step 1: Login
    print("Step 1: Logging in as admin...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "czachandrew@gmail.com",
            "password": "password"
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return

    token = login_response.json()['access_token']
    print(f"✓ Logged in successfully")
    print(f"  Token: {token[:50]}...\n")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Step 2: Test GET /parking/sessions
    print("Step 2: Testing GET /parking/sessions...")
    sessions_response = requests.get(
        f"{BASE_URL}/parking/sessions",
        headers=headers,
        params={"limit": 5}
    )

    print(f"  Status: {sessions_response.status_code}")
    if sessions_response.status_code == 200:
        sessions = sessions_response.json()
        print(f"  ✓ Retrieved {len(sessions)} sessions")
        if sessions:
            print(f"\n  Sample session:")
            print(f"    Vehicle: {sessions[0].get('vehicle_plate')}")
            print(f"    Lot: {sessions[0].get('lot_name')}")
            print(f"    Status: {sessions[0].get('status')}")
            print(f"    Started: {sessions[0].get('start_time')}")
    else:
        print(f"  ❌ Error: {sessions_response.text}")

    # Step 3: Test GET /partner/opportunities (with admin auth)
    print("\nStep 3: Testing GET /partner/opportunities with admin auth...")
    opps_response = requests.get(
        f"{BASE_URL}/partner/opportunities",
        headers=headers,
        params={"limit": 5}
    )

    print(f"  Status: {opps_response.status_code}")
    if opps_response.status_code == 200:
        opportunities = opps_response.json()
        print(f"  ✓ Retrieved {len(opportunities)} opportunities")
        if opportunities:
            print(f"\n  Sample opportunity:")
            print(f"    Title: {opportunities[0].get('title')}")
            print(f"    Type: {opportunities[0].get('opportunity_type')}")
            print(f"    Partner ID: {opportunities[0].get('partner_id')}")
            print(f"    Active: {opportunities[0].get('is_active')}")
    else:
        print(f"  ❌ Error: {opps_response.text}")

    print("\n" + "="*60)
    print("ADMIN ENDPOINTS TEST COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_admin_endpoints()
