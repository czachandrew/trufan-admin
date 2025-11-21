import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.models.parking import ParkingLot, ParkingSpace, ParkingSession
from app.services.parking_service import ParkingService
from app.services.background_tasks import BackgroundTasks


@pytest.fixture
def test_parking_lot(db):
    """Create a test parking lot."""
    lot = ParkingLot(
        id=uuid4(),
        name="Background Task Test Lot",
        description="Test lot for background tasks",
        location_address="789 Background Ave",
        location_lat=Decimal("40.7128"),
        location_lng=Decimal("-74.0060"),
        total_spaces=5,
        available_spaces=5,
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
        space_number="BG-101",
        space_type="standard",
        is_occupied=True,
        is_active=True,
    )
    db.add(space)
    db.commit()
    db.refresh(space)
    return space


class TestExpiringSessionDetection:
    """Test detection of expiring parking sessions."""

    def test_get_expiring_sessions_30_minutes(self, db, test_parking_lot, test_parking_space):
        """Test finding sessions expiring within 30 minutes."""
        # Create sessions at different expiration times
        sessions = []

        # Session expiring in 15 minutes (should be detected)
        session1 = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            space_id=test_parking_space.id,
            vehicle_plate="EXPIRE15",
            start_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=15),
            base_price=Decimal("15.00"),
            status="active",
            access_code="CODE15",
            contact_email="15min@example.com",
        )
        sessions.append(session1)

        # Session expiring in 29 minutes (should be detected)
        session2 = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            vehicle_plate="EXPIRE29",
            start_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=29),
            base_price=Decimal("15.00"),
            status="active",
            access_code="CODE29",
            contact_email="29min@example.com",
        )
        sessions.append(session2)

        # Session expiring in 45 minutes (should NOT be detected)
        session3 = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            vehicle_plate="EXPIRE45",
            start_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=45),
            base_price=Decimal("15.00"),
            status="active",
            access_code="CODE45",
            contact_email="45min@example.com",
        )
        sessions.append(session3)

        # Already expired (should NOT be detected - different status needed)
        session4 = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            vehicle_plate="EXPIRED",
            start_time=datetime.utcnow() - timedelta(hours=2),
            expires_at=datetime.utcnow() - timedelta(minutes=5),
            base_price=Decimal("15.00"),
            status="active",
            access_code="CODEEXP",
            contact_email="expired@example.com",
        )
        sessions.append(session4)

        for session in sessions:
            db.add(session)
        db.commit()

        # Get expiring sessions
        expiring = ParkingService.get_expiring_sessions(db, minutes_threshold=30)

        # Should find sessions 1 and 2 only
        expiring_plates = [s.vehicle_plate for s in expiring]
        assert "EXPIRE15" in expiring_plates
        assert "EXPIRE29" in expiring_plates
        assert "EXPIRE45" not in expiring_plates
        # EXPIRED might be included since it's still "active" status
        # In production, expired sessions would have different status

    def test_get_expiring_sessions_60_minutes(self, db, test_parking_lot):
        """Test finding sessions expiring within 60 minutes."""
        # Create session expiring in 50 minutes
        session = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            vehicle_plate="EXPIRE50",
            start_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=50),
            base_price=Decimal("15.00"),
            status="active",
            access_code="CODE50",
            contact_email="50min@example.com",
        )
        db.add(session)
        db.commit()

        # Should find with 60-minute threshold
        expiring = ParkingService.get_expiring_sessions(db, minutes_threshold=60)
        assert len(expiring) >= 1
        assert any(s.vehicle_plate == "EXPIRE50" for s in expiring)

        # Should NOT find with 30-minute threshold
        expiring_30 = ParkingService.get_expiring_sessions(db, minutes_threshold=30)
        assert not any(s.vehicle_plate == "EXPIRE50" for s in expiring_30)

    def test_get_expiring_sessions_excludes_other_statuses(self, db, test_parking_lot):
        """Test that only active sessions are considered for expiration."""
        statuses_to_test = ["completed", "cancelled", "expired", "pending_payment"]

        for i, status in enumerate(statuses_to_test):
            # Use shorter plate to fit VARCHAR(20) constraint
            session = ParkingSession(
                id=uuid4(),
                lot_id=test_parking_lot.id,
                vehicle_plate=f"STS{i}",  # Short plate
                start_time=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(minutes=15),
                base_price=Decimal("15.00"),
                status=status,
                access_code=f"CODE{i}",
                contact_email=f"{status}@example.com",
            )
            db.add(session)
        db.commit()

        # None of these should be detected (all non-active)
        expiring = ParkingService.get_expiring_sessions(db, minutes_threshold=30)
        expiring_plates = [s.vehicle_plate for s in expiring]

        # None of the test plates should be in results
        for i in range(len(statuses_to_test)):
            assert f"STS{i}" not in expiring_plates

    def test_get_expiring_sessions_empty_result(self, db, test_parking_lot):
        """Test when no sessions are expiring soon."""
        # Create session expiring in 2 hours
        session = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            vehicle_plate="FARFUTURE",
            start_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=2),
            base_price=Decimal("15.00"),
            status="active",
            access_code="CODEFAR",
            contact_email="far@example.com",
        )
        db.add(session)
        db.commit()

        # Should not find this specific session with 30-minute threshold
        expiring = ParkingService.get_expiring_sessions(db, minutes_threshold=30)
        expiring_plates = [s.vehicle_plate for s in expiring]
        assert "FARFUTURE" not in expiring_plates


class TestExpiredSessionCleanup:
    """Test cleanup of expired parking sessions."""

    @pytest.mark.asyncio
    async def test_expired_session_status_update(self, db, test_parking_lot, test_parking_space):
        """Test that expired sessions get their status updated."""
        # Create expired session
        expired_session = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            space_id=test_parking_space.id,
            vehicle_plate="CLEANUP1",
            start_time=datetime.utcnow() - timedelta(hours=3),
            expires_at=datetime.utcnow() - timedelta(minutes=30),
            base_price=Decimal("15.00"),
            status="active",
            access_code="CLEANUP1",
            contact_email="cleanup@example.com",
        )
        db.add(expired_session)
        db.commit()

        # Run cleanup
        await BackgroundTasks._process_expired_sessions()

        # Refresh and check status
        db.refresh(expired_session)
        assert expired_session.status == "expired"
        assert expired_session.end_time is not None

    @pytest.mark.asyncio
    async def test_expired_session_frees_space(self, db, test_parking_lot, test_parking_space):
        """Test that expired sessions free up parking spaces."""
        # Mark space as occupied
        test_parking_space.is_occupied = True
        db.commit()

        # Create expired session
        expired_session = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            space_id=test_parking_space.id,
            vehicle_plate="FREESPACE",
            start_time=datetime.utcnow() - timedelta(hours=2),
            expires_at=datetime.utcnow() - timedelta(minutes=15),
            base_price=Decimal("15.00"),
            status="active",
            access_code="FREESPACE",
            contact_email="free@example.com",
        )
        db.add(expired_session)
        db.commit()

        # Run cleanup
        await BackgroundTasks._process_expired_sessions()

        # Space should be freed
        db.refresh(test_parking_space)
        assert test_parking_space.is_occupied is False

    @pytest.mark.asyncio
    async def test_expired_session_updates_lot_availability(
        self, db, test_parking_lot, test_parking_space
    ):
        """Test that expired sessions update lot availability count."""
        # Set initial availability
        initial_available = test_parking_lot.available_spaces
        test_parking_lot.available_spaces = initial_available - 1
        db.commit()

        # Create expired session
        expired_session = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            space_id=test_parking_space.id,
            vehicle_plate="LOTCOUNT",
            start_time=datetime.utcnow() - timedelta(hours=2),
            expires_at=datetime.utcnow() - timedelta(minutes=10),
            base_price=Decimal("15.00"),
            status="active",
            access_code="LOTCOUNT",
            contact_email="count@example.com",
        )
        db.add(expired_session)
        db.commit()

        # Run cleanup
        await BackgroundTasks._process_expired_sessions()

        # Lot availability should increase
        db.refresh(test_parking_lot)
        assert test_parking_lot.available_spaces == initial_available

    @pytest.mark.asyncio
    async def test_cleanup_multiple_expired_sessions(self, db, test_parking_lot):
        """Test cleanup of multiple expired sessions at once."""
        # Create 5 expired sessions
        for i in range(5):
            session = ParkingSession(
                id=uuid4(),
                lot_id=test_parking_lot.id,
                vehicle_plate=f"MULTI{i}",
                start_time=datetime.utcnow() - timedelta(hours=2),
                expires_at=datetime.utcnow() - timedelta(minutes=i * 5 + 5),
                base_price=Decimal("15.00"),
                status="active",
                access_code=f"MULTI{i}",
                contact_email=f"multi{i}@example.com",
            )
            db.add(session)
        db.commit()

        # Run cleanup
        await BackgroundTasks._process_expired_sessions()

        # All should be marked as expired
        expired_sessions = (
            db.query(ParkingSession)
            .filter(ParkingSession.vehicle_plate.like("MULTI%"))
            .all()
        )
        for session in expired_sessions:
            assert session.status == "expired"

    @pytest.mark.asyncio
    async def test_cleanup_ignores_active_sessions(self, db, test_parking_lot):
        """Test that cleanup doesn't affect non-expired sessions."""
        # Create active session (not expired)
        active_session = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            vehicle_plate="STILLACTIVE",
            start_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=2),
            base_price=Decimal("15.00"),
            status="active",
            access_code="STILLACTIVE",
            contact_email="active@example.com",
        )
        db.add(active_session)
        db.commit()

        # Run cleanup
        await BackgroundTasks._process_expired_sessions()

        # Session should still be active
        db.refresh(active_session)
        assert active_session.status == "active"
        assert active_session.end_time is None


class TestBackgroundTaskNotifications:
    """Test notification sending in background tasks."""

    @pytest.mark.asyncio
    async def test_notify_expiring_session(self, db, test_parking_lot, test_parking_space):
        """Test that expiring sessions get notifications sent."""
        # Create expiring session
        expiring_session = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            space_id=test_parking_space.id,
            vehicle_plate="NOTIFY1",
            start_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=20),
            base_price=Decimal("15.00"),
            status="active",
            access_code="NOTIFY1",
            contact_email="notify@example.com",
        )
        db.add(expiring_session)
        db.commit()

        # Process the session
        await BackgroundTasks._notify_expiring_session(db, expiring_session)

        # Session status should be updated
        db.refresh(expiring_session)
        assert expiring_session.status == "expiring_soon"
        assert expiring_session.last_notification_sent is not None

    @pytest.mark.asyncio
    async def test_process_expiring_sessions_full_flow(self, db, test_parking_lot):
        """Test the complete expiring sessions processing flow."""
        # Create expiring session
        session = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            vehicle_plate="FULLFLOW",
            start_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=25),
            base_price=Decimal("15.00"),
            status="active",
            access_code="FULLFLOW",
            contact_email="flow@example.com",
            contact_phone="+15551234567",
        )
        db.add(session)
        db.commit()

        # Run the full process
        await BackgroundTasks._process_expiring_sessions()

        # Session should be updated
        db.refresh(session)
        assert session.status == "expiring_soon"
        assert session.last_notification_sent is not None

    @pytest.mark.asyncio
    async def test_notification_timestamp_update(self, db, test_parking_lot):
        """Test that last_notification_sent timestamp is updated."""
        session = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            vehicle_plate="TIMESTAMP",
            start_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=20),
            base_price=Decimal("15.00"),
            status="active",
            access_code="TIMESTAMP",
            contact_email="timestamp@example.com",
            last_notification_sent=None,
        )
        db.add(session)
        db.commit()

        # Process notification
        await BackgroundTasks._notify_expiring_session(db, session)

        # Check timestamp was set
        db.refresh(session)
        assert session.last_notification_sent is not None
        assert isinstance(session.last_notification_sent, datetime)


class TestBackgroundTaskEdgeCases:
    """Test edge cases in background task processing."""

    @pytest.mark.asyncio
    async def test_cleanup_with_no_expired_sessions(self, db):
        """Test cleanup when there are no expired sessions."""
        # Should not raise any errors
        await BackgroundTasks._process_expired_sessions()

    @pytest.mark.asyncio
    async def test_notification_with_no_expiring_sessions(self, db):
        """Test notification processing when no sessions are expiring."""
        # Should not raise any errors
        await BackgroundTasks._process_expiring_sessions()

    @pytest.mark.asyncio
    async def test_cleanup_session_without_space(self, db, test_parking_lot):
        """Test cleanup of lot-level session (no specific space)."""
        session = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            space_id=None,  # No specific space
            vehicle_plate="NOSPACE",
            start_time=datetime.utcnow() - timedelta(hours=2),
            expires_at=datetime.utcnow() - timedelta(minutes=10),
            base_price=Decimal("15.00"),
            status="active",
            access_code="NOSPACE",
            contact_email="nospace@example.com",
        )
        db.add(session)
        db.commit()

        # Should handle gracefully
        await BackgroundTasks._process_expired_sessions()

        db.refresh(session)
        assert session.status == "expired"

    @pytest.mark.asyncio
    async def test_notification_without_contact_info(self, db, test_parking_lot):
        """Test notification for session without contact info."""
        session = ParkingSession(
            id=uuid4(),
            lot_id=test_parking_lot.id,
            vehicle_plate="NOCONTACT",
            start_time=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=20),
            base_price=Decimal("15.00"),
            status="active",
            access_code="NOCONTACT",
            # No contact email or phone
        )
        db.add(session)
        db.commit()

        # Should handle gracefully (no notification sent, but status not updated)
        await BackgroundTasks._notify_expiring_session(db, session)

        db.refresh(session)
        # Status should remain active since no notification was sent
        assert session.status == "active"

    @pytest.mark.asyncio
    async def test_multiple_lots_concurrent_cleanup(self, db):
        """Test cleanup across multiple parking lots."""
        # Create multiple lots with expired sessions
        for lot_num in range(3):
            lot = ParkingLot(
                id=uuid4(),
                name=f"Multi Lot {lot_num}",
                location_address=f"{lot_num} Multi St",
                total_spaces=10,
                available_spaces=9,
                is_active=True,
                pricing_config={},
            )
            db.add(lot)
            db.commit()

            # Add expired session to each lot
            session = ParkingSession(
                id=uuid4(),
                lot_id=lot.id,
                vehicle_plate=f"LOT{lot_num}",
                start_time=datetime.utcnow() - timedelta(hours=2),
                expires_at=datetime.utcnow() - timedelta(minutes=10),
                base_price=Decimal("15.00"),
                status="active",
                access_code=f"LOT{lot_num}",
                contact_email=f"lot{lot_num}@example.com",
            )
            db.add(session)
        db.commit()

        # Run cleanup
        await BackgroundTasks._process_expired_sessions()

        # All sessions should be expired
        all_sessions = db.query(ParkingSession).filter(
            ParkingSession.vehicle_plate.like("LOT%")
        ).all()
        for session in all_sessions:
            assert session.status == "expired"
