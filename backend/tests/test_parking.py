import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.models.parking import ParkingLot, ParkingSpace, ParkingSession


@pytest.fixture
def test_parking_lot(db):
    """Create a test parking lot."""
    lot = ParkingLot(
        id=uuid4(),
        name="Test Parking Lot",
        description="A test parking lot",
        location_address="123 Test St",
        location_lat=Decimal("40.7128"),
        location_lng=Decimal("-74.0060"),
        total_spaces=100,
        available_spaces=100,
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
def test_parking_space(db, test_parking_lot):
    """Create a test parking space."""
    space = ParkingSpace(
        id=uuid4(),
        lot_id=test_parking_lot.id,
        space_number="A-101",
        space_type="standard",
        is_occupied=False,
        is_active=True,
    )
    db.add(space)
    db.commit()
    db.refresh(space)
    return space


class TestParkingLots:
    """Test parking lot endpoints."""

    def test_get_available_parking_lots(self, client, test_parking_lot):
        """Test getting all available parking lots."""
        response = client.get("/api/v1/parking/lots")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Verify lot data structure
        lot = data[0]
        assert "id" in lot
        assert "name" in lot
        assert "total_spaces" in lot
        assert "available_spaces" in lot
        assert "base_rate" in lot
        assert "hourly_rate" in lot

    def test_get_specific_parking_lot(self, client, test_parking_lot):
        """Test getting a specific parking lot by ID."""
        response = client.get(f"/api/v1/parking/lots/{test_parking_lot.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == str(test_parking_lot.id)
        assert data["name"] == test_parking_lot.name
        assert data["total_spaces"] == test_parking_lot.total_spaces

    def test_get_nonexistent_parking_lot(self, client):
        """Test getting a nonexistent parking lot returns 404."""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/parking/lots/{fake_id}")
        assert response.status_code == 404


class TestParkingSessions:
    """Test parking session endpoints."""

    def test_create_parking_session_with_email(self, client, test_parking_lot):
        """Test creating a parking session with email contact."""
        session_data = {
            "lot_id": str(test_parking_lot.id),
            "vehicle_plate": "ABC123",
            "vehicle_make": "Toyota",
            "vehicle_model": "Camry",
            "vehicle_color": "Blue",
            "duration_hours": 2.0,
            "contact_email": "test@example.com",
        }

        response = client.post("/api/v1/parking/sessions", json=session_data)
        assert response.status_code == 201

        data = response.json()
        assert data["vehicle_plate"] == "ABC123"
        assert data["lot_id"] == str(test_parking_lot.id)
        assert data["status"] == "pending_payment"
        assert "access_code" in data
        assert len(data["access_code"]) == 8
        assert "base_price" in data
        assert float(data["base_price"]) > 0

    def test_create_parking_session_with_phone(self, client, test_parking_lot):
        """Test creating a parking session with phone contact."""
        session_data = {
            "lot_id": str(test_parking_lot.id),
            "vehicle_plate": "XYZ789",
            "duration_hours": 1.0,
            "contact_phone": "5551234567",
        }

        response = client.post("/api/v1/parking/sessions", json=session_data)
        assert response.status_code == 201

        data = response.json()
        assert data["vehicle_plate"] == "XYZ789"
        assert data["status"] == "pending_payment"

    def test_create_parking_session_with_specific_space(
        self, client, test_parking_lot, test_parking_space
    ):
        """Test creating a parking session with specific space."""
        session_data = {
            "lot_id": str(test_parking_lot.id),
            "space_number": test_parking_space.space_number,
            "vehicle_plate": "DEF456",
            "duration_hours": 3.0,
            "contact_email": "space@example.com",
        }

        response = client.post("/api/v1/parking/sessions", json=session_data)
        assert response.status_code == 201

        data = response.json()
        assert data["space_number"] == test_parking_space.space_number

    def test_create_session_without_contact_fails(self, client, test_parking_lot):
        """Test that creating session without contact info fails."""
        session_data = {
            "lot_id": str(test_parking_lot.id),
            "vehicle_plate": "NOCONTACT",
            "duration_hours": 1.0,
        }

        response = client.post("/api/v1/parking/sessions", json=session_data)
        assert response.status_code == 400
        response_data = response.json()
        # Error handler wraps errors in "error" object
        error_message = response_data.get("error", {}).get("message", "")
        assert "contact method" in error_message.lower()

    def test_create_session_with_invalid_duration(self, client, test_parking_lot):
        """Test creating session with duration below minimum fails."""
        session_data = {
            "lot_id": str(test_parking_lot.id),
            "vehicle_plate": "SHORT",
            "duration_hours": 0.1,  # 6 minutes - below 15 minute minimum
            "contact_email": "test@example.com",
        }

        response = client.post("/api/v1/parking/sessions", json=session_data)
        assert response.status_code == 400

    def test_create_session_nonexistent_lot(self, client):
        """Test creating session for nonexistent lot fails."""
        session_data = {
            "lot_id": str(uuid4()),
            "vehicle_plate": "NOLOT",
            "duration_hours": 1.0,
            "contact_email": "test@example.com",
        }

        response = client.post("/api/v1/parking/sessions", json=session_data)
        assert response.status_code == 404

    def test_license_plate_normalization(self, client, test_parking_lot):
        """Test that license plates are normalized (uppercase, no spaces)."""
        session_data = {
            "lot_id": str(test_parking_lot.id),
            "vehicle_plate": "abc 123",  # lowercase with space
            "duration_hours": 1.0,
            "contact_email": "test@example.com",
        }

        response = client.post("/api/v1/parking/sessions", json=session_data)
        assert response.status_code == 201

        data = response.json()
        assert data["vehicle_plate"] == "ABC123"  # Should be normalized


class TestSessionLookup:
    """Test parking session lookup."""

    def test_get_session_by_access_code(self, client, test_parking_lot):
        """Test looking up a session by access code."""
        # Create a session first
        session_data = {
            "lot_id": str(test_parking_lot.id),
            "vehicle_plate": "LOOKUP123",
            "duration_hours": 2.0,
            "contact_email": "lookup@example.com",
        }

        create_response = client.post("/api/v1/parking/sessions", json=session_data)
        assert create_response.status_code == 201
        access_code = create_response.json()["access_code"]

        # Look up the session
        lookup_response = client.get(f"/api/v1/parking/sessions/{access_code}")
        assert lookup_response.status_code == 200

        data = lookup_response.json()
        assert data["access_code"] == access_code
        assert data["vehicle_plate"] == "LOOKUP123"

    def test_get_session_with_invalid_code(self, client):
        """Test looking up session with invalid access code."""
        response = client.get("/api/v1/parking/sessions/INVALID")
        assert response.status_code == 404


class TestPaymentSimulation:
    """Test payment simulation."""

    def test_simulate_successful_payment(self, client, test_parking_lot):
        """Test successful payment simulation."""
        # Create a session
        session_data = {
            "lot_id": str(test_parking_lot.id),
            "vehicle_plate": "PAY123",
            "duration_hours": 2.0,
            "contact_email": "pay@example.com",
        }

        create_response = client.post("/api/v1/parking/sessions", json=session_data)
        assert create_response.status_code == 201

        session_id = create_response.json()["id"]
        base_price = create_response.json()["base_price"]

        # Simulate payment
        payment_data = {
            "session_id": session_id,
            "amount": base_price,
            "should_succeed": True,
        }

        payment_response = client.post(
            "/api/v1/parking/payments/simulate", json=payment_data
        )
        assert payment_response.status_code == 200

        payment = payment_response.json()
        assert payment["status"] == "completed"
        assert payment["session_id"] == session_id

        # Verify session status changed to active
        access_code = create_response.json()["access_code"]
        session_response = client.get(f"/api/v1/parking/sessions/{access_code}")
        assert session_response.json()["status"] == "active"

    def test_simulate_failed_payment(self, client, test_parking_lot):
        """Test failed payment simulation."""
        # Create a session
        session_data = {
            "lot_id": str(test_parking_lot.id),
            "vehicle_plate": "PAYFAIL",
            "duration_hours": 1.0,
            "contact_email": "fail@example.com",
        }

        create_response = client.post("/api/v1/parking/sessions", json=session_data)
        session_id = create_response.json()["id"]

        # Simulate failed payment
        payment_data = {
            "session_id": session_id,
            "amount": "10.00",
            "should_succeed": False,
        }

        payment_response = client.post(
            "/api/v1/parking/payments/simulate", json=payment_data
        )
        assert payment_response.status_code == 200

        payment = payment_response.json()
        assert payment["status"] == "failed"

    def test_payment_for_nonexistent_session(self, client):
        """Test payment for nonexistent session fails."""
        payment_data = {
            "session_id": str(uuid4()),
            "amount": "10.00",
            "should_succeed": True,
        }

        response = client.post("/api/v1/parking/payments/simulate", json=payment_data)
        assert response.status_code == 404


class TestSessionExtension:
    """Test parking session extension."""

    def test_extend_parking_session(self, client, test_parking_lot):
        """Test extending a parking session."""
        # Create and pay for a session
        session_data = {
            "lot_id": str(test_parking_lot.id),
            "vehicle_plate": "EXTEND123",
            "duration_hours": 1.0,
            "contact_email": "extend@example.com",
        }

        create_response = client.post("/api/v1/parking/sessions", json=session_data)
        access_code = create_response.json()["access_code"]
        session_id = create_response.json()["id"]
        original_expires = create_response.json()["expires_at"]

        # Pay for session
        payment_data = {
            "session_id": session_id,
            "amount": create_response.json()["base_price"],
            "should_succeed": True,
        }
        client.post("/api/v1/parking/payments/simulate", json=payment_data)

        # Extend the session
        extend_data = {"additional_hours": 2.0, "access_code": access_code}

        extend_response = client.post(
            f"/api/v1/parking/sessions/{access_code}/extend", json=extend_data
        )
        assert extend_response.status_code == 200

        data = extend_response.json()
        assert data["expires_at"] != original_expires  # Expiration should be extended

    def test_extend_unpaid_session_fails(self, client, test_parking_lot):
        """Test extending unpaid session fails."""
        # Create session (pending payment)
        session_data = {
            "lot_id": str(test_parking_lot.id),
            "vehicle_plate": "UNPAID",
            "duration_hours": 1.0,
            "contact_email": "unpaid@example.com",
        }

        create_response = client.post("/api/v1/parking/sessions", json=session_data)
        access_code = create_response.json()["access_code"]

        # Try to extend before payment
        extend_data = {"additional_hours": 1.0, "access_code": access_code}

        extend_response = client.post(
            f"/api/v1/parking/sessions/{access_code}/extend", json=extend_data
        )
        assert extend_response.status_code == 400


class TestSessionEnding:
    """Test ending parking sessions early."""

    def test_end_parking_session(self, client, test_parking_lot):
        """Test ending a parking session early."""
        # Create and pay for a session
        session_data = {
            "lot_id": str(test_parking_lot.id),
            "vehicle_plate": "END123",
            "duration_hours": 3.0,
            "contact_email": "end@example.com",
        }

        create_response = client.post("/api/v1/parking/sessions", json=session_data)
        access_code = create_response.json()["access_code"]
        session_id = create_response.json()["id"]

        # Pay for session
        payment_data = {
            "session_id": session_id,
            "amount": create_response.json()["base_price"],
            "should_succeed": True,
        }
        client.post("/api/v1/parking/payments/simulate", json=payment_data)

        # End the session
        end_data = {"access_code": access_code}

        end_response = client.post(
            f"/api/v1/parking/sessions/{access_code}/end", json=end_data
        )
        assert end_response.status_code == 200

        data = end_response.json()
        assert data["status"] == "completed"
        assert data["end_time"] is not None


class TestPricingCalculation:
    """Test parking pricing calculation."""

    def test_basic_pricing(self, client, test_parking_lot):
        """Test basic pricing calculation."""
        # 2 hours: base_rate (10) + hourly_rate (5) * 2 = 20
        session_data = {
            "lot_id": str(test_parking_lot.id),
            "vehicle_plate": "PRICE1",
            "duration_hours": 2.0,
            "contact_email": "price@example.com",
        }

        response = client.post("/api/v1/parking/sessions", json=session_data)
        data = response.json()

        # base_rate (10) + hourly_rate (5) * 2 hours = 20
        assert float(data["base_price"]) == 20.0

    def test_max_daily_rate_cap(self, client, test_parking_lot):
        """Test that pricing is capped at max daily rate."""
        # 24 hours would be 10 + (5 * 24) = 130, but max is 50
        session_data = {
            "lot_id": str(test_parking_lot.id),
            "vehicle_plate": "MAXPRICE",
            "duration_hours": 24.0,
            "contact_email": "max@example.com",
        }

        response = client.post("/api/v1/parking/sessions", json=session_data)
        data = response.json()

        # Should be capped at max_daily_rate (50)
        assert float(data["base_price"]) == 50.0
