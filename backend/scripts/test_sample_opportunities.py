#!/usr/bin/env python3
"""
Quick test to verify sample opportunities are visible.
Run with: docker-compose exec api python -m scripts.test_sample_opportunities
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"


def test_public_opportunities():
    """Test public opportunity viewing without authentication."""
    print("\n" + "="*60)
    print("TESTING PUBLIC OPPORTUNITY VIEWING")
    print("="*60 + "\n")

    # First, let's see if we have the Greenfield lot
    print("Step 1: Finding Greenfield parking lot...")
    lots_response = requests.get(f"{BASE_URL}/parking/lots")
    lots = lots_response.json()

    greenfield_lot = None
    for lot in lots:
        if "Greenfield" in lot.get('name', ''):
            greenfield_lot = lot
            print(f"✓ Found lot: {lot['name']} (ID: {lot['id']})")
            break

    if not greenfield_lot:
        print("❌ No Greenfield lot found. Using first available lot...")
        if lots:
            greenfield_lot = lots[0]
            print(f"   Using: {greenfield_lot['name']}")
        else:
            print("❌ No parking lots found at all!")
            return

    # Create a test parking session (public endpoint)
    print("\nStep 2: Creating test parking session...")
    session_response = requests.post(
        f"{BASE_URL}/parking/sessions",
        json={
            "lot_id": greenfield_lot['id'],
            "vehicle_plate": "TEST999",
            "vehicle_make": "Toyota",
            "vehicle_model": "Test",
            "vehicle_color": "Blue",
            "duration_hours": 2.0,
            "contact_email": "test@example.com"
        }
    )

    if session_response.status_code not in [200, 201]:
        print(f"❌ Failed to create session: {session_response.text}")
        return

    session = session_response.json()
    session_id = session.get('id')

    if not session_id:
        print(f"❌ No session ID in response: {session}")
        return

    print(f"✓ Created session: {session_id}")
    print(f"   Status: {session.get('status')}")

    # Now test PUBLIC opportunity viewing (no auth required!)
    print("\nStep 3: Fetching opportunities WITHOUT authentication...")
    print("   This should work now that opportunities are public!\n")

    opp_response = requests.get(
        f"{BASE_URL}/opportunities/active",
        params={"session_id": session_id}
        # NOTE: No Authorization header!
    )

    if opp_response.status_code != 200:
        print(f"❌ Failed to fetch opportunities: {opp_response.text}")
        return

    opportunities = opp_response.json()

    print("="*60)
    print(f"✅ SUCCESS! Found {len(opportunities)} public opportunities")
    print("="*60 + "\n")

    if len(opportunities) == 0:
        print("⚠️  No opportunities matched your context.")
        print("   This might be because:")
        print("   - Time of day doesn't match trigger rules")
        print("   - Day of week doesn't match")
        print("   - Parking time remaining doesn't match")
        print("\n   Try adjusting the trigger rules in the sample opportunities.")
    else:
        print("Sample Opportunities Available:\n")
        for idx, opp in enumerate(opportunities, 1):
            print(f"{idx}. {opp['title']}")
            print(f"   Value: {opp['value_proposition']}")
            print(f"   Type: {opp['opportunity_type']}")
            print(f"   Walking distance: {opp.get('walking_distance_meters', 'N/A')}m")
            if 'value_details' in opp:
                if 'discount_percentage' in opp['value_details']:
                    print(f"   Discount: {opp['value_details']['discount_percentage']}%")
                if 'parking_extension_minutes' in opp['value_details']:
                    print(f"   Parking extension: +{opp['value_details']['parking_extension_minutes']} min")
            print()

    # Try viewing one opportunity detail (also public now!)
    if opportunities:
        print("\nStep 4: Viewing opportunity details WITHOUT authentication...")
        detail_response = requests.get(
            f"{BASE_URL}/opportunities/{opportunities[0]['id']}"
            # NOTE: Still no Authorization header!
        )

        if detail_response.status_code == 200:
            print("✅ Successfully viewed opportunity details publicly!")
            detail = detail_response.json()
            print(f"   Title: {detail['title']}")
            print(f"   Partner ID: {detail['partner_id']}")
        else:
            print(f"❌ Failed to view details: {detail_response.text}")

    # Try accepting without auth (should fail)
    if opportunities:
        print("\nStep 5: Trying to ACCEPT without authentication...")
        accept_response = requests.post(
            f"{BASE_URL}/opportunities/{opportunities[0]['id']}/accept",
            json={"parking_session_id": session_id}
            # NOTE: No Authorization header - this should fail!
        )

        if accept_response.status_code == 401:
            print("✅ Correctly rejected! Got 401 Unauthorized")
            print("   This is expected - accepting requires authentication.")
        else:
            print(f"⚠️  Got status {accept_response.status_code} instead of 401")
            print(f"   Response: {accept_response.text}")

    print("\n" + "="*60)
    print("PUBLIC OPPORTUNITY VIEWING TEST COMPLETE!")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        test_public_opportunities()
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
