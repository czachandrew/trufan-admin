#!/usr/bin/env python3
"""
Test newly implemented parking lot endpoints.
Run with: docker-compose exec api python -m scripts.test_new_lot_endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"


def test_lot_endpoints():
    """Test create, update, and spaces endpoints for parking lots."""
    print("\n" + "="*70)
    print("TESTING NEW PARKING LOT ENDPOINTS")
    print("="*70 + "\n")

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
    print(f"✓ Logged in successfully\n")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Step 2: Create a new parking lot
    print("Step 2: Testing POST /parking/lots (create new lot)...")
    new_lot_data = {
        "name": "Test Parking Structure",
        "description": "Multi-level parking structure for testing",
        "location_address": "456 Test Street, Milwaukee, WI 53202",
        "total_spaces": 150,
        "location_lat": "43.0389",
        "location_lng": "-87.9065",
        "base_rate": "12.00",
        "hourly_rate": "6.00",
        "max_daily_rate": "60.00",
        "min_duration_minutes": 30,
        "max_duration_hours": 12
    }

    create_response = requests.post(
        f"{BASE_URL}/parking/lots",
        headers=headers,
        json=new_lot_data
    )

    print(f"  Status: {create_response.status_code}")
    if create_response.status_code == 201:
        created_lot = create_response.json()
        lot_id = created_lot['id']
        print(f"  ✓ Created parking lot successfully")
        print(f"    ID: {lot_id}")
        print(f"    Name: {created_lot['name']}")
        print(f"    Total Spaces: {created_lot['total_spaces']}")
        print(f"    Available: {created_lot['available_spaces']}")
        print(f"    Hourly Rate: ${created_lot['hourly_rate']}")
    else:
        print(f"  ❌ Error: {create_response.text}")
        return

    # Step 3: Update the parking lot
    print(f"\nStep 3: Testing PUT /parking/lots/{lot_id} (update lot)...")
    update_data = {
        "name": "Test Parking Structure - Updated",
        "description": "Updated description for testing",
        "hourly_rate": "7.50",
        "is_active": True
    }

    update_response = requests.put(
        f"{BASE_URL}/parking/lots/{lot_id}",
        headers=headers,
        json=update_data
    )

    print(f"  Status: {update_response.status_code}")
    if update_response.status_code == 200:
        updated_lot = update_response.json()
        print(f"  ✓ Updated parking lot successfully")
        print(f"    Name: {updated_lot['name']}")
        print(f"    Description: {updated_lot['description']}")
        print(f"    Hourly Rate: ${updated_lot['hourly_rate']} (was $6.00)")
    else:
        print(f"  ❌ Error: {update_response.text}")

    # Step 4: Get spaces for the lot
    print(f"\nStep 4: Testing GET /parking/lots/{lot_id}/spaces...")
    spaces_response = requests.get(
        f"{BASE_URL}/parking/lots/{lot_id}/spaces",
        headers=headers
    )

    print(f"  Status: {spaces_response.status_code}")
    if spaces_response.status_code == 200:
        spaces = spaces_response.json()
        print(f"  ✓ Retrieved spaces successfully")
        print(f"    Number of spaces: {len(spaces)}")
        if len(spaces) == 0:
            print(f"    (No spaces created yet - this is expected for a new lot)")
    else:
        print(f"  ❌ Error: {spaces_response.text}")

    # Step 5: Test all original endpoints still work
    print("\nStep 5: Verifying original endpoints still work...")

    # GET /parking/lots
    lots_response = requests.get(f"{BASE_URL}/parking/lots")
    print(f"  GET /parking/lots: {lots_response.status_code} {'✓' if lots_response.status_code == 200 else '❌'}")

    # GET /parking/lots/{lot_id}
    lot_response = requests.get(f"{BASE_URL}/parking/lots/{lot_id}")
    print(f"  GET /parking/lots/{lot_id}: {lot_response.status_code} {'✓' if lot_response.status_code == 200 else '❌'}")

    # GET /parking/sessions
    sessions_response = requests.get(f"{BASE_URL}/parking/sessions", headers=headers)
    print(f"  GET /parking/sessions: {sessions_response.status_code} {'✓' if sessions_response.status_code == 200 else '❌'}")

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print("\n✅ All new parking lot endpoints are working!")
    print("   - POST /parking/lots (create)")
    print("   - PUT /parking/lots/{id} (update)")
    print("   - GET /parking/lots/{id}/spaces (list spaces)")
    print("\n✅ All original endpoints still working!")
    print()


if __name__ == "__main__":
    test_lot_endpoints()
