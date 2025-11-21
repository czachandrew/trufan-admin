import logging
from typing import Optional
from datetime import datetime

from app.models.parking import ParkingSession
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via email and SMS."""

    @staticmethod
    def _format_expiration_time(expires_at: datetime) -> tuple[int, str]:
        """Calculate minutes until expiration and format message."""
        now = datetime.utcnow()
        time_remaining = expires_at - now
        minutes_remaining = int(time_remaining.total_seconds() / 60)

        if minutes_remaining < 60:
            time_str = f"{minutes_remaining} minutes"
        else:
            hours = minutes_remaining // 60
            mins = minutes_remaining % 60
            if mins > 0:
                time_str = f"{hours} hour{'s' if hours != 1 else ''} and {mins} minutes"
            else:
                time_str = f"{hours} hour{'s' if hours != 1 else ''}"

        return minutes_remaining, time_str

    @staticmethod
    def _generate_extend_url(access_code: str) -> str:
        """Generate URL for extending parking session."""
        # TODO: Update with actual frontend URL once deployed
        base_url = settings.FRONTEND_URL if hasattr(settings, "FRONTEND_URL") else "http://localhost:3000"
        return f"{base_url}/parking/extend/{access_code}"

    @staticmethod
    async def send_expiration_email(
        session: ParkingSession,
        lot_name: str,
        space_number: Optional[str] = None,
    ) -> bool:
        """
        Send expiration warning email.

        Args:
            session: Parking session object
            lot_name: Name of the parking lot
            space_number: Optional parking space number

        Returns:
            True if email sent successfully, False otherwise
        """
        if not session.contact_email:
            logger.warning(f"No email address for session {session.id}")
            return False

        minutes_remaining, time_str = NotificationService._format_expiration_time(
            session.expires_at
        )
        extend_url = NotificationService._generate_extend_url(session.access_code)

        # Format space information
        space_info = f" (Space {space_number})" if space_number else ""

        # Email subject and body
        subject = f"⏰ Your parking session is expiring in {time_str}"
        body = f"""
Hello,

Your parking session at {lot_name}{space_info} is expiring soon!

Vehicle: {session.vehicle_plate}
Time Remaining: {time_str}
Expires At: {session.expires_at.strftime('%I:%M %p on %B %d, %Y')}

To extend your parking time, click here:
{extend_url}

Or use your access code: {session.access_code}

Thank you for using TruFan Parking!

---
This is an automated notification. Please do not reply to this email.
"""

        try:
            # TODO: Implement actual email sending with SendGrid/AWS SES
            # For now, just log the notification
            logger.info(f"EMAIL NOTIFICATION (simulated)")
            logger.info(f"To: {session.contact_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body preview: {body[:100]}...")

            # Simulate successful send
            return True

        except Exception as e:
            logger.error(f"Failed to send expiration email for session {session.id}: {e}")
            return False

    @staticmethod
    async def send_expiration_sms(
        session: ParkingSession,
        lot_name: str,
        space_number: Optional[str] = None,
    ) -> bool:
        """
        Send expiration warning SMS.

        Args:
            session: Parking session object
            lot_name: Name of the parking lot
            space_number: Optional parking space number

        Returns:
            True if SMS sent successfully, False otherwise
        """
        if not session.contact_phone:
            logger.warning(f"No phone number for session {session.id}")
            return False

        minutes_remaining, time_str = NotificationService._format_expiration_time(
            session.expires_at
        )
        extend_url = NotificationService._generate_extend_url(session.access_code)

        # Format space information
        space_info = f" (Space {space_number})" if space_number else ""

        # SMS message (keep it short)
        message = f"""TruFan Parking Alert:

Your parking at {lot_name}{space_info} expires in {time_str}.

Vehicle: {session.vehicle_plate}
Code: {session.access_code}

Extend now: {extend_url}
"""

        try:
            # TODO: Implement actual SMS sending with Twilio
            # For now, just log the notification
            logger.info(f"SMS NOTIFICATION (simulated)")
            logger.info(f"To: {session.contact_phone}")
            logger.info(f"Message: {message[:100]}...")

            # Simulate successful send
            return True

        except Exception as e:
            logger.error(f"Failed to send expiration SMS for session {session.id}: {e}")
            return False

    @staticmethod
    async def send_expiration_notification(
        session: ParkingSession,
        lot_name: str,
        space_number: Optional[str] = None,
    ) -> dict[str, bool]:
        """
        Send expiration notification via all available contact methods.

        Args:
            session: Parking session object
            lot_name: Name of the parking lot
            space_number: Optional parking space number

        Returns:
            Dictionary with results: {"email": bool, "sms": bool}
        """
        results = {"email": False, "sms": False}

        # Send email notification if contact email is available
        if session.contact_email:
            results["email"] = await NotificationService.send_expiration_email(
                session, lot_name, space_number
            )

        # Send SMS notification if contact phone is available
        if session.contact_phone:
            results["sms"] = await NotificationService.send_expiration_sms(
                session, lot_name, space_number
            )

        # Log notification results
        if results["email"] or results["sms"]:
            logger.info(
                f"Sent expiration notifications for session {session.id} "
                f"(email: {results['email']}, sms: {results['sms']})"
            )
        else:
            logger.warning(
                f"No notifications sent for session {session.id} - no contact methods available"
            )

        return results

    @staticmethod
    async def send_payment_confirmation(
        session: ParkingSession,
        lot_name: str,
        space_number: Optional[str] = None,
    ) -> bool:
        """
        Send payment confirmation notification.

        Args:
            session: Parking session object
            lot_name: Name of the parking lot
            space_number: Optional parking space number

        Returns:
            True if notification sent successfully
        """
        space_info = f" (Space {space_number})" if space_number else ""

        message = f"""TruFan Parking Confirmation:

Your parking session is confirmed!

Lot: {lot_name}{space_info}
Vehicle: {session.vehicle_plate}
Valid Until: {session.expires_at.strftime('%I:%M %p on %B %d, %Y')}
Amount Paid: ${session.actual_price}

Access Code: {session.access_code}

Save this code to extend or end your session early.
"""

        try:
            # Send to email if available
            if session.contact_email:
                logger.info(f"PAYMENT CONFIRMATION EMAIL (simulated)")
                logger.info(f"To: {session.contact_email}")
                logger.info(f"Message: {message[:100]}...")

            # Send to SMS if available
            if session.contact_phone:
                logger.info(f"PAYMENT CONFIRMATION SMS (simulated)")
                logger.info(f"To: {session.contact_phone}")
                logger.info(f"Message: {message[:100]}...")

            return True

        except Exception as e:
            logger.error(f"Failed to send payment confirmation for session {session.id}: {e}")
            return False
