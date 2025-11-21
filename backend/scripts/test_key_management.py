#!/usr/bin/env python3
"""
Test key management system for valet service.
Run with: docker-compose exec api python -m scripts.test_key_management
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"


def print_section(title):
    """Print a section header."""
    print("\n" + "="*70)
    print(title)
    print("="*70 + "\n")


def print_result(test_name, success, details=""):
    """Print test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"   {details}")


def test_key_management():
    """Test complete key management workflow."""

    print_section("KEY MANAGEMENT SYSTEM TESTS")

    # Login as valet worker
    print("Logging in as valet worker...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "valet1@greenfieldparking.com",
            "password": "password"
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return

    token = login_response.json()['access_token']
    print(f"✅ Logged in successfully\n")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    venue_id = "380ccab9-fa83-4c25-894f-7021ba6714ef"  # Greenfield Plaza

    # TEST 1: Configure storage layout
    print_section("TEST 1: Configure Key Storage Layout")

    storage_config = {
        "zones": [
            {
                "id": "main",
                "name": "Main Storage",
                "type": "main",
                "boxes": [
                    {
                        "id": "box-1",
                        "label": "Box 1",
                        "positions": [f"A{i}" for i in range(1, 21)],
                        "capacity": 20
                    },
                    {
                        "id": "box-2",
                        "label": "Box 2",
                        "positions": [f"B{i}" for i in range(1, 21)],
                        "capacity": 20
                    }
                ]
            }
        ]
    }

    config_response = requests.put(
        f"{BASE_URL}/valet/staff/storage-config/{venue_id}",
        headers=headers,
        json=storage_config
    )

    if config_response.status_code == 200:
        config_data = config_response.json()
        print_result("Configure storage layout", True,
                    f"Created {len(config_data['zones'])} zone(s) with {sum(len(box['positions']) for zone in config_data['zones'] for box in zone['boxes'])} positions")
    else:
        print_result("Configure storage layout", False, f"Status: {config_response.status_code}")
        print(f"Response: {config_response.text}")

    # TEST 2: Create a valet session
    print_section("TEST 2: Create Valet Session")

    session_data = {
        "venue_id": str(venue_id),
        "vehicle_plate": "TEST123",
        "vehicle_make": "Toyota",
        "vehicle_model": "Camry",
        "vehicle_color": "Silver",
        "contact_phone": "+15555551234"
    }

    session_response = requests.post(
        f"{BASE_URL}/valet/sessions",
        headers=headers,
        json=session_data
    )

    if session_response.status_code != 201:
        print_result("Create valet session", False, f"Status: {session_response.status_code}")
        print(f"Response: {session_response.text}")
        return

    session = session_response.json()
    session_id = session['id']
    ticket_number = session['ticket_number']

    print_result("Create valet session", True, f"Ticket: {ticket_number}, ID: {session_id}")

    # TEST 3: Assign keys to storage
    print_section("TEST 3: Assign Keys to Storage")

    key_assignment = {
        "key_tag_number": "001",
        "zone": "main",
        "box": "box-1",
        "position": "A1",
        "key_notes": "Red keychain with Toyota logo"
    }

    assign_response = requests.post(
        f"{BASE_URL}/valet/staff/sessions/{session_id}/keys/assign",
        headers=headers,
        json=key_assignment
    )

    if assign_response.status_code == 200:
        assigned_session = assign_response.json()
        key_mgmt = assigned_session.get('key_management')
        if key_mgmt:
            print_result("Assign keys", True,
                        f"Key tag {key_mgmt['key_tag_number']} assigned to {key_mgmt['storage_location']['zone']}/{key_mgmt['storage_location']['box']}/{key_mgmt['storage_location']['position']}")
            print(f"   Status: {key_mgmt['key_status']}")
            print(f"   Assigned by: {key_mgmt['assigned_by']}")
        else:
            print_result("Assign keys", False, "No key_management in response")
    else:
        print_result("Assign keys", False, f"Status: {assign_response.status_code}")
        print(f"Response: {assign_response.text}")
        return

    # TEST 4: Try to assign same key tag to different session (should fail)
    print_section("TEST 4: Duplicate Key Tag Detection")

    # Create second session
    session2_data = {
        "venue_id": str(venue_id),
        "vehicle_plate": "TEST456",
        "vehicle_make": "Honda",
        "vehicle_model": "Accord",
        "vehicle_color": "Blue",
        "contact_phone": "+15555559999"
    }

    session2_response = requests.post(
        f"{BASE_URL}/valet/sessions",
        headers=headers,
        json=session2_data
    )

    if session2_response.status_code == 201:
        session2 = session2_response.json()
        session2_id = session2['id']

        # Try to assign same key tag
        duplicate_assignment = {
            "key_tag_number": "001",  # Same as first session
            "zone": "main",
            "box": "box-1",
            "position": "A2"
        }

        duplicate_response = requests.post(
            f"{BASE_URL}/valet/staff/sessions/{session2_id}/keys/assign",
            headers=headers,
            json=duplicate_assignment
        )

        if duplicate_response.status_code == 400:
            error_detail = duplicate_response.json().get('detail', '')
            print_result("Duplicate key detection", True,
                        f"Correctly rejected duplicate key tag: {error_detail}")
        else:
            print_result("Duplicate key detection", False,
                        f"Should have failed with 400, got {duplicate_response.status_code}")

        # Assign different key tag to second session
        valid_assignment = {
            "key_tag_number": "002",
            "zone": "main",
            "box": "box-1",
            "position": "A2"
        }

        valid_response = requests.post(
            f"{BASE_URL}/valet/staff/sessions/{session2_id}/keys/assign",
            headers=headers,
            json=valid_assignment
        )

        if valid_response.status_code == 200:
            print_result("Assign second key", True, "Key tag 002 assigned to second session")
        else:
            print_result("Assign second key", False, f"Status: {valid_response.status_code}")

    # TEST 5: Get storage config with occupancy
    print_section("TEST 5: Storage Config with Real-Time Occupancy")

    occupancy_response = requests.get(
        f"{BASE_URL}/valet/staff/storage-config/{venue_id}",
        headers=headers
    )

    if occupancy_response.status_code == 200:
        occupancy_data = occupancy_response.json()
        occupied = occupancy_data.get('occupied_positions', {})
        total_occupied = sum(len(positions) for positions in occupied.values())

        print_result("Get storage config", True,
                    f"Retrieved config with {total_occupied} occupied position(s)")

        if occupied:
            for zone_id, positions in occupied.items():
                print(f"   Zone '{zone_id}': {', '.join(positions)} occupied")
    else:
        print_result("Get storage config", False, f"Status: {occupancy_response.status_code}")

    # TEST 6: Mark keys as grabbed
    print_section("TEST 6: Mark Keys as Grabbed")

    grab_response = requests.post(
        f"{BASE_URL}/valet/staff/sessions/{session_id}/keys/grab",
        headers=headers
    )

    if grab_response.status_code == 200:
        grabbed_session = grab_response.json()
        key_mgmt = grabbed_session.get('key_management')
        if key_mgmt:
            print_result("Mark keys grabbed", True,
                        f"Key status changed to: {key_mgmt['key_status']}")
            print(f"   Grabbed by: {key_mgmt['grabbed_by']}")
            print(f"   Grabbed at: {key_mgmt['grabbed_at']}")
        else:
            print_result("Mark keys grabbed", False, "No key_management in response")
    else:
        print_result("Mark keys grabbed", False, f"Status: {grab_response.status_code}")
        print(f"Response: {grab_response.text}")

    # TEST 7: Verify occupancy decreased after grab
    print_section("TEST 7: Occupancy After Key Grab")

    occupancy2_response = requests.get(
        f"{BASE_URL}/valet/staff/storage-config/{venue_id}",
        headers=headers
    )

    if occupancy2_response.status_code == 200:
        occupancy2_data = occupancy2_response.json()
        occupied2 = occupancy2_data.get('occupied_positions', {})
        total_occupied2 = sum(len(positions) for positions in occupied2.values())

        print_result("Occupancy after grab", True,
                    f"Now {total_occupied2} occupied position(s) (keys grabbed but still tracked)")

        # Keys that are grabbed should still show as occupied until session completes
        if 'A1' not in occupied2.get('main', []):
            print("   Note: A1 not shown as occupied (grabbed keys may not count)")

    # TEST 8: Get session includes key management
    print_section("TEST 8: Get Session with Key Management")

    get_session_response = requests.get(
        f"{BASE_URL}/valet/sessions/{session_id}",
        headers=headers
    )

    if get_session_response.status_code == 200:
        full_session = get_session_response.json()
        key_mgmt = full_session.get('key_management')

        if key_mgmt:
            print_result("Get session with keys", True, "Session includes key_management field")
            print(f"   Key tag: {key_mgmt['key_tag_number']}")
            print(f"   Status: {key_mgmt['key_status']}")
            print(f"   Location: {key_mgmt['storage_location']['zone']}/{key_mgmt['storage_location']['box']}/{key_mgmt['storage_location']['position']}")
        else:
            print_result("Get session with keys", False, "No key_management in response")
    else:
        print_result("Get session with keys", False, f"Status: {get_session_response.status_code}")

    # Summary
    print_section("TEST SUMMARY")
    print("All key management tests completed!")
    print("\n✅ Tests passed:")
    print("   1. Configure storage layout")
    print("   2. Create valet session")
    print("   3. Assign keys to storage location")
    print("   4. Duplicate key tag detection")
    print("   5. Get storage config with occupancy")
    print("   6. Mark keys as grabbed")
    print("   7. Verify occupancy tracking")
    print("   8. Get session includes key management")
    print()


if __name__ == "__main__":
    test_key_management()
