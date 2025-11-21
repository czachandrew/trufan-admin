import asyncio
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.parking import ParkingSession, ParkingLot, ParkingSpace
from app.services.parking_service import ParkingService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class BackgroundTasks:
    """Background tasks for parking system."""

    _expiration_check_task: Optional[asyncio.Task] = None
    _is_running: bool = False

    @classmethod
    def start_expiration_checker(cls, check_interval_minutes: int = 5):
        """
        Start background task to check for expiring parking sessions.

        Args:
            check_interval_minutes: How often to check for expiring sessions (default: 5 minutes)
        """
        if cls._is_running:
            logger.warning("Expiration checker is already running")
            return

        cls._is_running = True
        cls._expiration_check_task = asyncio.create_task(
            cls._check_expiring_sessions_loop(check_interval_minutes)
        )
        logger.info(
            f"Started parking expiration checker (interval: {check_interval_minutes} minutes)"
        )

    @classmethod
    async def stop_expiration_checker(cls):
        """Stop background task for checking expiring sessions."""
        if not cls._is_running:
            logger.warning("Expiration checker is not running")
            return

        cls._is_running = False
        if cls._expiration_check_task:
            cls._expiration_check_task.cancel()
            try:
                await cls._expiration_check_task
            except asyncio.CancelledError:
                pass
            cls._expiration_check_task = None

        logger.info("Stopped parking expiration checker")

    @classmethod
    async def _check_expiring_sessions_loop(cls, check_interval_minutes: int):
        """
        Background loop that periodically checks for expiring sessions.

        Args:
            check_interval_minutes: How often to check
        """
        while cls._is_running:
            try:
                await cls._process_expiring_sessions()
            except Exception as e:
                logger.error(f"Error processing expiring sessions: {e}", exc_info=True)

            # Wait before next check
            await asyncio.sleep(check_interval_minutes * 60)

    @classmethod
    async def _process_expiring_sessions(cls):
        """Check for expiring sessions and send notifications."""
        db = SessionLocal()
        try:
            # Get sessions expiring in the next 30 minutes
            expiring_sessions = ParkingService.get_expiring_sessions(
                db, minutes_threshold=30
            )

            if not expiring_sessions:
                logger.debug("No expiring sessions found")
                return

            logger.info(f"Found {len(expiring_sessions)} expiring sessions")

            for session in expiring_sessions:
                try:
                    await cls._notify_expiring_session(db, session)
                except Exception as e:
                    logger.error(
                        f"Error notifying session {session.id}: {e}", exc_info=True
                    )

        finally:
            db.close()

    @classmethod
    async def _notify_expiring_session(cls, db: Session, session: ParkingSession):
        """
        Send notification for an expiring session.

        Args:
            db: Database session
            session: Parking session that is expiring
        """
        # Get lot and space information
        lot = db.query(ParkingLot).filter(ParkingLot.id == session.lot_id).first()
        space = None
        if session.space_id:
            space = (
                db.query(ParkingSpace)
                .filter(ParkingSpace.id == session.space_id)
                .first()
            )

        lot_name = lot.name if lot else "Unknown Lot"
        space_number = space.space_number if space else None

        # Send notifications
        results = await NotificationService.send_expiration_notification(
            session, lot_name, space_number
        )

        # Update session status to expiring_soon
        if results["email"] or results["sms"]:
            session.status = "expiring_soon"
            session.last_notification_sent = datetime.utcnow()
            db.commit()
            logger.info(f"Updated session {session.id} status to 'expiring_soon'")

    @classmethod
    async def _process_expired_sessions(cls):
        """Check for expired sessions and mark them as expired."""
        db = SessionLocal()
        try:
            # Get active sessions that have expired
            now = datetime.utcnow()
            expired_sessions = (
                db.query(ParkingSession)
                .filter(
                    ParkingSession.status.in_(["active", "expiring_soon"]),
                    ParkingSession.expires_at <= now,
                )
                .all()
            )

            if not expired_sessions:
                logger.debug("No expired sessions found")
                return

            logger.info(f"Found {len(expired_sessions)} expired sessions")

            for session in expired_sessions:
                try:
                    # Mark session as expired
                    session.status = "expired"
                    session.end_time = now

                    # Free up the parking space
                    if session.space_id:
                        space = (
                            db.query(ParkingSpace)
                            .filter(ParkingSpace.id == session.space_id)
                            .first()
                        )
                        if space:
                            space.is_occupied = False

                    # Increment available spaces in lot
                    lot = (
                        db.query(ParkingLot)
                        .filter(ParkingLot.id == session.lot_id)
                        .first()
                    )
                    if lot:
                        lot.available_spaces += 1

                    logger.info(
                        f"Marked session {session.id} as expired and freed space"
                    )

                except Exception as e:
                    logger.error(
                        f"Error expiring session {session.id}: {e}", exc_info=True
                    )

            db.commit()

        finally:
            db.close()

    @classmethod
    def start_expired_session_cleanup(cls, check_interval_minutes: int = 10):
        """
        Start background task to clean up expired parking sessions.

        Args:
            check_interval_minutes: How often to check for expired sessions (default: 10 minutes)
        """
        asyncio.create_task(cls._expired_session_cleanup_loop(check_interval_minutes))
        logger.info(
            f"Started expired session cleanup (interval: {check_interval_minutes} minutes)"
        )

    @classmethod
    async def _expired_session_cleanup_loop(cls, check_interval_minutes: int):
        """
        Background loop that periodically cleans up expired sessions.

        Args:
            check_interval_minutes: How often to check
        """
        while cls._is_running:
            try:
                await cls._process_expired_sessions()
            except Exception as e:
                logger.error(f"Error processing expired sessions: {e}", exc_info=True)

            # Wait before next check
            await asyncio.sleep(check_interval_minutes * 60)
