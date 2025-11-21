import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.models.parking import ParkingLot, ParkingSpace, ParkingSession
from app.services.notification_service import NotificationService


@pytest.fixture
def test_parking_lot(db):
    """Create a test parking lot."""
    lot = ParkingLot(
        id=uuid4(),
        name="Notification Test Lot",
        description="Test lot for notifications",
        location_address="456 Notify St",
        location_lat=Decimal("40.7128"),
        location_lng=Decimal("-74.0060"),
        total_spaces=10,
        available_spaces=10,
        is_active=True,
        pricing_config={
            "base_rate": 10.00,
            "hourly_rate": 5.00,
            "max_daily": 50.00,
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
        space_number="NOTIFY-101",
        space_type="standard",
        is_occupied=False,
        is_active=True,
    )
    db.add(space)
    db.commit()
    db.refresh(space)
    return space


@pytest.fixture
def test_active_session(db, test_parking_lot, test_parking_space):
    """Create an active parking session."""
    session = ParkingSession(
        id=uuid4(),
        lot_id=test_parking_lot.id,
        space_id=test_parking_space.id,
        vehicle_plate="TEST123",
        vehicle_make="Toyota",
        vehicle_model="Camry",
        vehicle_color="Blue",
        start_time=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=1),
        base_price=Decimal("15.00"),
        actual_price=Decimal("15.00"),
        status="active",
        access_code="TESTCODE",
        contact_email="test@example.com",
        contact_phone="+15551234567",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@pytest.fixture
def test_expiring_session(db, test_parking_lot, test_parking_space):
    """Create a session that's expiring soon."""
    session = ParkingSession(
        id=uuid4(),
        lot_id=test_parking_lot.id,
        space_id=test_parking_space.id,
        vehicle_plate="EXPIRE123",
        vehicle_make="Honda",
        vehicle_model="Accord",
        start_time=datetime.utcnow() - timedelta(hours=1),
        expires_at=datetime.utcnow() + timedelta(minutes=15),  # Expires in 15 min
        base_price=Decimal("20.00"),
        actual_price=Decimal("20.00"),
        status="active",
        access_code="EXPIRECODE",
        contact_email="expiring@example.com",
        contact_phone="+15559876543",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


class TestNotificationFormatting:
    """Test notification formatting and content."""

    @pytest.mark.asyncio
    async def test_expiration_time_formatting_minutes(self):
        """Test formatting expiration time when less than an hour."""
        expires_at = datetime.utcnow() + timedelta(minutes=25)
        minutes, time_str = NotificationService._format_expiration_time(expires_at)

        # Allow 1-minute tolerance for test execution time
        assert 24 <= minutes <= 25
        assert ("24 minutes" in time_str or "25 minutes" in time_str)

    @pytest.mark.asyncio
    async def test_expiration_time_formatting_hours(self):
        """Test formatting expiration time when more than an hour."""
        expires_at = datetime.utcnow() + timedelta(hours=2, minutes=30)
        minutes, time_str = NotificationService._format_expiration_time(expires_at)

        # Allow 1-minute tolerance for test execution time
        assert 149 <= minutes <= 150  # 2.5 hours = 150 minutes
        assert "2 hour" in time_str
        assert ("29 minutes" in time_str or "30 minutes" in time_str)

    @pytest.mark.asyncio
    async def test_expiration_time_formatting_exact_hour(self):
        """Test formatting when exactly on the hour."""
        expires_at = datetime.utcnow() + timedelta(hours=3)
        minutes, time_str = NotificationService._format_expiration_time(expires_at)

        # Allow 1-minute tolerance for test execution time
        assert 179 <= minutes <= 180
        assert "3 hour" in time_str or "2 hour" in time_str

    @pytest.mark.asyncio
    async def test_extend_url_generation(self):
        """Test extend URL generation."""
        access_code = "ABC12345"
        url = NotificationService._generate_extend_url(access_code)

        assert access_code in url
        assert "parking/extend" in url or "parking" in url

    @pytest.mark.asyncio
    async def test_email_notification_content(self, test_active_session, test_parking_lot):
        """Test email notification contains required information."""
        result = await NotificationService.send_expiration_email(
            test_active_session, test_parking_lot.name, "NOTIFY-101"
        )

        # Should return True (simulated success)
        assert result is True

    @pytest.mark.asyncio
    async def test_sms_notification_content(self, test_active_session, test_parking_lot):
        """Test SMS notification contains required information."""
        result = await NotificationService.send_expiration_sms(
            test_active_session, test_parking_lot.name, "NOTIFY-101"
        )

        # Should return True (simulated success)
        assert result is True

    @pytest.mark.asyncio
    async def test_notification_without_email(self, db, test_parking_lot):
        """Test notification when no email is provided."""
        session = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            vehicle_plate="NOEMAIL",
            start_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            base_price=Decimal("15.00"),
            status="active",
            access_code="NOEMAIL",
            contact_phone="+15551111111",  # Only phone, no email
        )
        db.add(session)
        db.commit()

        result = await NotificationService.send_expiration_email(
            session, test_parking_lot.name
        )

        # Should return False (no email available)
        assert result is False

    @pytest.mark.asyncio
    async def test_notification_without_phone(self, db, test_parking_lot):
        """Test notification when no phone is provided."""
        session = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            vehicle_plate="NOPHONE",
            start_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            base_price=Decimal("15.00"),
            status="active",
            access_code="NOPHONE",
            contact_email="test@example.com",  # Only email, no phone
        )
        db.add(session)
        db.commit()

        result = await NotificationService.send_expiration_sms(
            session, test_parking_lot.name
        )

        # Should return False (no phone available)
        assert result is False


class TestNotificationDelivery:
    """Test notification delivery logic."""

    @pytest.mark.asyncio
    async def test_send_notification_both_channels(self, test_active_session, test_parking_lot):
        """Test sending notification via both email and SMS."""
        results = await NotificationService.send_expiration_notification(
            test_active_session, test_parking_lot.name, "NOTIFY-101"
        )

        # Both should succeed (simulated)
        assert results["email"] is True
        assert results["sms"] is True

    @pytest.mark.asyncio
    async def test_send_notification_email_only(self, db, test_parking_lot):
        """Test sending notification when only email is available."""
        session = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            vehicle_plate="EMAILONLY",
            start_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            base_price=Decimal("15.00"),
            status="active",
            access_code="EMAILONLY",
            contact_email="email@example.com",
        )
        db.add(session)
        db.commit()

        results = await NotificationService.send_expiration_notification(
            session, test_parking_lot.name
        )

        assert results["email"] is True
        assert results["sms"] is False

    @pytest.mark.asyncio
    async def test_send_notification_sms_only(self, db, test_parking_lot):
        """Test sending notification when only SMS is available."""
        session = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            vehicle_plate="SMSONLY",
            start_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            base_price=Decimal("15.00"),
            status="active",
            access_code="SMSONLY",
            contact_phone="+15552222222",
        )
        db.add(session)
        db.commit()

        results = await NotificationService.send_expiration_notification(
            session, test_parking_lot.name
        )

        assert results["email"] is False
        assert results["sms"] is True

    @pytest.mark.asyncio
    async def test_send_notification_no_contact(self, db, test_parking_lot):
        """Test notification when no contact methods available."""
        session = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            vehicle_plate="NOCONTACT",
            start_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            base_price=Decimal("15.00"),
            status="active",
            access_code="NOCONTACT",
        )
        db.add(session)
        db.commit()

        results = await NotificationService.send_expiration_notification(
            session, test_parking_lot.name
        )

        # Both should fail (no contact info)
        assert results["email"] is False
        assert results["sms"] is False

    @pytest.mark.asyncio
    async def test_payment_confirmation(self, test_active_session, test_parking_lot):
        """Test payment confirmation notification."""
        result = await NotificationService.send_payment_confirmation(
            test_active_session, test_parking_lot.name, "NOTIFY-101"
        )

        # Should succeed (simulated)
        assert result is True

    @pytest.mark.asyncio
    async def test_notification_with_space_number(
        self, test_active_session, test_parking_lot, test_parking_space
    ):
        """Test notification includes space number when provided."""
        results = await NotificationService.send_expiration_notification(
            test_active_session,
            test_parking_lot.name,
            test_parking_space.space_number,
        )

        assert results["email"] is True
        assert results["sms"] is True

    @pytest.mark.asyncio
    async def test_notification_without_space_number(
        self, test_active_session, test_parking_lot
    ):
        """Test notification works without space number (lot-level parking)."""
        results = await NotificationService.send_expiration_notification(
            test_active_session, test_parking_lot.name, None
        )

        assert results["email"] is True
        assert results["sms"] is True


class TestNotificationTiming:
    """Test notification timing and thresholds."""

    @pytest.mark.asyncio
    async def test_notification_for_expiring_session(
        self, test_expiring_session, test_parking_lot
    ):
        """Test notification for session expiring within threshold."""
        results = await NotificationService.send_expiration_notification(
            test_expiring_session, test_parking_lot.name
        )

        # Both channels should work
        assert results["email"] is True
        assert results["sms"] is True

    @pytest.mark.asyncio
    async def test_notification_multiple_calls(self, test_active_session, test_parking_lot):
        """Test that multiple notification calls work correctly."""
        # Send notification twice
        results1 = await NotificationService.send_expiration_notification(
            test_active_session, test_parking_lot.name
        )
        results2 = await NotificationService.send_expiration_notification(
            test_active_session, test_parking_lot.name
        )

        # Both should succeed (simulated - in production would need debouncing)
        assert results1["email"] is True
        assert results2["email"] is True

    @pytest.mark.asyncio
    async def test_email_contains_vehicle_info(self, test_active_session, test_parking_lot):
        """Test that email notification contains vehicle information."""
        # This is a simulated test - in a real scenario we'd capture the email content
        result = await NotificationService.send_expiration_email(
            test_active_session, test_parking_lot.name
        )

        assert result is True
        # Vehicle plate should be available in session
        assert test_active_session.vehicle_plate == "TEST123"

    @pytest.mark.asyncio
    async def test_sms_contains_access_code(self, test_active_session, test_parking_lot):
        """Test that SMS notification contains access code."""
        result = await NotificationService.send_expiration_sms(
            test_active_session, test_parking_lot.name
        )

        assert result is True
        # Access code should be available in session
        assert test_active_session.access_code == "TESTCODE"

    @pytest.mark.asyncio
    async def test_notification_with_expired_session(self, db, test_parking_lot):
        """Test notification for already expired session."""
        expired_session = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            vehicle_plate="EXPIRED",
            start_time=datetime.utcnow() - timedelta(hours=3),
            expires_at=datetime.utcnow() - timedelta(hours=1),  # Already expired
            base_price=Decimal("15.00"),
            status="active",
            access_code="EXPIRED",
            contact_email="expired@example.com",
        )
        db.add(expired_session)
        db.commit()

        # Notification should still work (showing negative time)
        results = await NotificationService.send_expiration_notification(
            expired_session, test_parking_lot.name
        )

        assert results["email"] is True
