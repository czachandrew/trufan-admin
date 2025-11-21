import pytest
import asyncio
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from decimal import Decimal

from app.models.parking import ParkingLot, ParkingSpace


@pytest.fixture
def test_parking_lot(db):
    """Create a test parking lot with limited spaces."""
    lot = ParkingLot(
        id=uuid4(),
        name="Concurrency Test Lot",
        description="Test lot for concurrency",
        location_address="123 Concurrent St",
        location_lat=Decimal("40.7128"),
        location_lng=Decimal("-74.0060"),
        total_spaces=3,
        available_spaces=3,
        is_active=True,
        pricing_config={
            "base_rate": 10.00,
            "hourly_rate": 5.00,
            "max_daily": 50.00,
            "min_duration_minutes": 15,
            "max_duration_hours": 24,
            "dynamic_multiplier": 1.0,
        },
    )
    db.add(lot)
    db.commit()
    db.refresh(lot)
    return lot


@pytest.fixture
def test_parking_spaces(db, test_parking_lot):
    """Create test parking spaces."""
    spaces = []
    for i in range(1, 4):  # 3 spaces
        space = ParkingSpace(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            space_number=f"TEST-{i}",
            space_type="standard",
            is_occupied=False,
            is_active=True,
        )
        db.add(space)
        spaces.append(space)
    db.commit()
    for space in spaces:
        db.refresh(space)
    return spaces


class TestConcurrency:
    """Test concurrent parking operations."""

    def test_concurrent_space_booking_same_space(
        self, client, test_parking_lot, test_parking_spaces
    ):
        """Test that only one user can book a specific space when multiple try simultaneously."""
        target_space = test_parking_spaces[0]

        def create_session(index):
            """Create a parking session for a specific space."""
            session_data = {
                "lot_id": str(test_parking_lot.id),
                "space_number": target_space.space_number,
                "vehicle_plate": f"CONCURRENT{index}",
                "duration_hours": 1.0,
                "contact_email": f"user{index}@example.com",
            }
            return client.post("/api/v1/parking/sessions", json=session_data)

        # Try to book the same space 5 times concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_session, i) for i in range(5)]
            responses = [future.result() for future in futures]

        # Exactly one should succeed (201), others should fail (400 or 404)
        success_count = sum(1 for r in responses if r.status_code == 201)
        failure_count = sum(1 for r in responses if r.status_code in [400, 404])

        assert success_count == 1, f"Expected 1 success, got {success_count}"
        assert failure_count == 4, f"Expected 4 failures, got {failure_count}"

        # Check that the space is now occupied
        successful_response = [r for r in responses if r.status_code == 201][0]
        data = successful_response.json()
        assert data["space_number"] == target_space.space_number

    def test_concurrent_lot_booking_auto_assign(
        self, client, test_parking_lot, test_parking_spaces
    ):
        """Test concurrent bookings with auto-assignment to different spaces."""

        def create_session(index):
            """Create a parking session with auto-assignment."""
            session_data = {
                "lot_id": str(test_parking_lot.id),
                "vehicle_plate": f"AUTO{index}",
                "duration_hours": 1.0,
                "contact_email": f"auto{index}@example.com",
            }
            return client.post("/api/v1/parking/sessions", json=session_data)

        # Try to book 5 times concurrently (we have 3 spaces)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_session, i) for i in range(5)]
            responses = [future.result() for future in futures]

        # At least 3 should succeed (we have 3 spaces)
        success_count = sum(1 for r in responses if r.status_code == 201)
        assert success_count >= 3, f"Expected at least 3 successes, got {success_count}"

        # Verify all successful bookings have different spaces
        successful_responses = [r for r in responses if r.status_code == 201]
        space_numbers = [r.json()["space_number"] for r in successful_responses]

        # All assigned spaces should be unique
        assert len(space_numbers) == len(set(space_numbers)), "Duplicate space assignments detected"

    def test_concurrent_lot_level_parking(self, client, test_parking_lot):
        """Test concurrent lot-level parking (no specific spaces)."""

        def create_session(index):
            """Create a lot-level parking session."""
            session_data = {
                "lot_id": str(test_parking_lot.id),
                "vehicle_plate": f"LOT{index}",
                "duration_hours": 1.0,
                "contact_email": f"lot{index}@example.com",
            }
            return client.post("/api/v1/parking/sessions", json=session_data)

        # Try to book 5 times concurrently (lot has 3 spaces)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_session, i) for i in range(5)]
            responses = [future.result() for future in futures]

        # First 3 should succeed, rest should fail
        success_count = sum(1 for r in responses if r.status_code == 201)
        failure_count = sum(1 for r in responses if r.status_code == 400)

        assert success_count <= 3, f"Too many successes: {success_count}"
        assert failure_count >= 2, f"Expected at least 2 failures, got {failure_count}"

    def test_concurrent_session_extensions(
        self, client, test_parking_lot, test_parking_spaces
    ):
        """Test concurrent extensions of the same session."""
        # Create a session first
        session_data = {
            "lot_id": str(test_parking_lot.id),
            "vehicle_plate": "EXTEND123",
            "duration_hours": 1.0,
            "contact_email": "extend@example.com",
        }
        create_response = client.post("/api/v1/parking/sessions", json=session_data)
        assert create_response.status_code == 201

        access_code = create_response.json()["access_code"]
        session_id = create_response.json()["id"]

        # Pay for the session
        payment_data = {
            "session_id": session_id,
            "amount": create_response.json()["base_price"],
            "should_succeed": True,
        }
        client.post("/api/v1/parking/payments/simulate", json=payment_data)

        def extend_session(index):
            """Extend the parking session."""
            extend_data = {
                "additional_hours": 1.0,
                "access_code": access_code,
            }
            return client.post(
                f"/api/v1/parking/sessions/{access_code}/extend",
                json=extend_data,
            )

        # Try to extend the same session 5 times concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(extend_session, i) for i in range(5)]
            responses = [future.result() for future in futures]

        # All should succeed (extensions are additive)
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count == 5, f"Expected 5 successful extensions, got {success_count}"

    def test_concurrent_payment_processing(
        self, client, test_parking_lot, test_parking_spaces
    ):
        """Test concurrent payment attempts for the same session."""
        # Create a session first
        session_data = {
            "lot_id": str(test_parking_lot.id),
            "vehicle_plate": "PAY123",
            "duration_hours": 1.0,
            "contact_email": "pay@example.com",
        }
        create_response = client.post("/api/v1/parking/sessions", json=session_data)
        assert create_response.status_code == 201

        session_id = create_response.json()["id"]
        base_price = create_response.json()["base_price"]

        def process_payment(index):
            """Process payment for the session."""
            payment_data = {
                "session_id": session_id,
                "amount": base_price,
                "should_succeed": True,
            }
            return client.post("/api/v1/parking/payments/simulate", json=payment_data)

        # Try to pay for the same session 3 times concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(process_payment, i) for i in range(3)]
            responses = [future.result() for future in futures]

        # Only first should succeed, rest should fail (session already paid)
        success_count = sum(1 for r in responses if r.status_code == 200)
        failure_count = sum(1 for r in responses if r.status_code == 400)

        assert success_count == 1, f"Expected 1 successful payment, got {success_count}"
        assert failure_count == 2, f"Expected 2 failed payments, got {failure_count}"

    def test_concurrent_lot_availability_updates(
        self, client, test_parking_lot, test_parking_spaces
    ):
        """Test that lot availability is updated correctly under concurrent load."""
        initial_available = test_parking_lot.available_spaces

        def create_and_end_session(index):
            """Create a session and then end it."""
            # Create session
            session_data = {
                "lot_id": str(test_parking_lot.id),
                "vehicle_plate": f"AVAIL{index}",
                "duration_hours": 1.0,
                "contact_email": f"avail{index}@example.com",
            }
            create_response = client.post("/api/v1/parking/sessions", json=session_data)

            if create_response.status_code == 201:
                access_code = create_response.json()["access_code"]
                session_id = create_response.json()["id"]

                # Pay for session
                payment_data = {
                    "session_id": session_id,
                    "amount": create_response.json()["base_price"],
                    "should_succeed": True,
                }
                client.post("/api/v1/parking/payments/simulate", json=payment_data)

                # End session
                end_data = {"access_code": access_code}
                client.post(
                    f"/api/v1/parking/sessions/{access_code}/end",
                    json=end_data,
                )

            return create_response

        # Create and end 3 sessions concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(create_and_end_session, i) for i in range(3)]
            responses = [future.result() for future in futures]

        # Check final lot availability
        lot_response = client.get(f"/api/v1/parking/lots/{test_parking_lot.id}")
        assert lot_response.status_code == 200
        final_available = lot_response.json()["available_spaces"]

        # Should be back to initial availability (all sessions ended)
        assert final_available == initial_available, (
            f"Expected {initial_available} available spaces, got {final_available}"
        )

    def test_race_condition_space_occupation(
        self, client, test_parking_lot, test_parking_spaces
    ):
        """Test race condition when checking and marking space as occupied."""
        target_space = test_parking_spaces[0]

        def rapid_booking(index):
            """Attempt rapid booking of same space."""
            session_data = {
                "lot_id": str(test_parking_lot.id),
                "space_number": target_space.space_number,
                "vehicle_plate": f"RACE{index}",
                "duration_hours": 1.0,
                "contact_email": f"race{index}@example.com",
            }
            return client.post("/api/v1/parking/sessions", json=session_data)

        # Launch 10 concurrent requests to book the same space
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(rapid_booking, i) for i in range(10)]
            responses = [future.result() for future in futures]

        # Only one should succeed
        success_count = sum(1 for r in responses if r.status_code == 201)
        assert success_count == 1, (
            f"Race condition detected: {success_count} bookings succeeded for same space"
        )

        # Verify the space is marked as occupied
        space_check = client.get(f"/api/v1/parking/lots/{test_parking_lot.id}")
        lot_data = space_check.json()
        assert lot_data["available_spaces"] == 2  # Started with 3, one is now taken
