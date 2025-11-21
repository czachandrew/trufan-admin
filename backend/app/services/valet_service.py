"""
Valet Service Module

This module provides comprehensive business logic for managing valet parking sessions,
including session creation, check-in/check-out, retrieval requests, status updates,
capacity management, and payment processing.
"""

import logging
import secrets
import string
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.valet import (
    ValetSession,
    ValetStatus,
    ValetStatusEvent,
    ValetCommunication,
    ValetIncident,
    ValetCapacity,
    SavedVehicle,
    ValetPricing,
    KeyStorageConfig,
    ServiceType,
    IncidentType,
    IncidentSeverity,
    CommunicationType,
    CommunicationStatus,
)
from app.models.venue import Venue
from app.models.user import User
from app.schemas.valet import (
    ValetSessionCreate,
    ValetSessionResponse,
    ValetSessionCheckin,
    ValetRetrievalRequest,
    ValetRating,
    ValetAvailability,
    ValetHistoryItem,
    ValetHistory,
    ValetQueueResponse,
    ValetQueueItem,
    ValetStatusUpdate,
    ValetIncidentCreate,
    ValetIncidentResponse,
    ValetCapacityResponse,
    ValetPriorityLevel,
    ValetSessionStatus,
    StatusEvent,
    PricingInfo,
    PaymentInfo,
    ParkingLocation,
)

logger = logging.getLogger(__name__)


class ValetService:
    """
    Service class for managing valet parking operations.

    This service handles the complete lifecycle of valet sessions including:
    - Session creation and booking
    - Check-in and vehicle handover
    - Parking location tracking
    - Retrieval requests with ETA calculation
    - Status management with state machine validation
    - Rating and tipping
    - Capacity management
    - Incident reporting
    - Communication/notification logging
    """

    # Status transition rules - defines valid state machine transitions
    VALID_TRANSITIONS: Dict[str, List[str]] = {
        ValetStatus.PENDING.value: [ValetStatus.CHECKED_IN.value, ValetStatus.CANCELLED.value],
        ValetStatus.CHECKED_IN.value: [ValetStatus.PARKED.value, ValetStatus.CANCELLED.value],
        ValetStatus.PARKED.value: [ValetStatus.RETRIEVAL_REQUESTED.value, ValetStatus.CANCELLED.value],
        ValetStatus.RETRIEVAL_REQUESTED.value: [ValetStatus.RETRIEVING.value, ValetStatus.PARKED.value, ValetStatus.CANCELLED.value],
        ValetStatus.RETRIEVING.value: [ValetStatus.READY.value, ValetStatus.RETRIEVAL_REQUESTED.value],
        ValetStatus.READY.value: [ValetStatus.COMPLETED.value, ValetStatus.RETRIEVAL_REQUESTED.value],
        ValetStatus.COMPLETED.value: [],  # Terminal state
        ValetStatus.CANCELLED.value: [],  # Terminal state
    }

    # ETA configuration (in minutes)
    ETA_CONFIG = {
        ServiceType.STANDARD.value: {"parking": 5, "retrieval_base": 8, "retrieval_per_car": 2},
        ServiceType.VIP.value: {"parking": 3, "retrieval_base": 5, "retrieval_per_car": 1},
        ServiceType.PREMIUM.value: {"parking": 2, "retrieval_base": 3, "retrieval_per_car": 0.5},
        ServiceType.EVENT.value: {"parking": 7, "retrieval_base": 10, "retrieval_per_car": 3},
    }

    @staticmethod
    def generate_ticket_number(db: Session) -> str:
        """
        Generate unique valet ticket number in V-XXXX format.

        Args:
            db: Database session

        Returns:
            Unique ticket number (e.g., "V-1234")
        """
        max_attempts = 100
        for _ in range(max_attempts):
            # Generate 4-digit number
            number = secrets.randbelow(10000)
            ticket_number = f"V-{number:04d}"

            # Check if unique
            exists = db.query(ValetSession).filter(
                ValetSession.ticket_number == ticket_number
            ).first()

            if not exists:
                return ticket_number

        # Fallback to UUID-based generation if all attempts exhausted
        return f"V-{uuid4().hex[:4].upper()}"

    @staticmethod
    def generate_pin() -> str:
        """
        Generate 4-digit PIN for session verification.

        Returns:
            4-digit PIN as string
        """
        return f"{secrets.randbelow(10000):04d}"

    @staticmethod
    def calculate_eta(
        db: Session,
        venue_id: UUID,
        service_type: str,
        operation: str = "retrieval"
    ) -> Tuple[int, datetime]:
        """
        Calculate estimated time of arrival/completion based on service type and queue.

        Args:
            db: Database session
            venue_id: Venue ID
            service_type: Type of service (standard, vip, premium, event)
            operation: Type of operation ("parking" or "retrieval")

        Returns:
            Tuple of (minutes_eta, estimated_datetime)
        """
        eta_config = ValetService.ETA_CONFIG.get(
            service_type,
            ValetService.ETA_CONFIG[ServiceType.STANDARD.value]
        )

        if operation == "parking":
            base_eta = eta_config["parking"]
        else:
            base_eta = eta_config["retrieval_base"]

            # Add time based on queue length
            queue_count = db.query(func.count(ValetSession.id)).filter(
                and_(
                    ValetSession.venue_id == venue_id,
                    ValetSession.status.in_([
                        ValetStatus.RETRIEVAL_REQUESTED.value,
                        ValetStatus.RETRIEVING.value
                    ])
                )
            ).scalar() or 0

            additional_time = queue_count * eta_config["retrieval_per_car"]
            base_eta += additional_time

        # Add some buffer time
        eta_minutes = int(base_eta * 1.2)
        estimated_time = datetime.utcnow() + timedelta(minutes=eta_minutes)

        return eta_minutes, estimated_time

    @staticmethod
    def validate_status_transition(current_status: str, new_status: str) -> bool:
        """
        Validate if status transition is allowed by state machine.

        Args:
            current_status: Current session status
            new_status: Desired new status

        Returns:
            True if transition is valid, False otherwise
        """
        allowed_transitions = ValetService.VALID_TRANSITIONS.get(current_status, [])
        return new_status in allowed_transitions

    @staticmethod
    def check_capacity(db: Session, venue_id: UUID) -> Tuple[bool, Optional[str]]:
        """
        Check if venue has available valet capacity.

        Args:
            db: Database session
            venue_id: Venue ID

        Returns:
            Tuple of (has_capacity, message)
        """
        capacity = db.query(ValetCapacity).filter(
            ValetCapacity.venue_id == venue_id
        ).first()

        if not capacity:
            logger.warning(f"No capacity record found for venue {venue_id}")
            return True, None  # Allow if no capacity tracking

        if not capacity.is_accepting_vehicles:
            return False, capacity.status_message or "Valet service temporarily unavailable"

        if capacity.available_capacity <= 0:
            return False, "Valet service at full capacity"

        return True, None

    @staticmethod
    def update_capacity(
        db: Session,
        venue_id: UUID,
        increment: int = 0,
        pending_checkin_delta: int = 0,
        pending_retrieval_delta: int = 0
    ) -> Optional[ValetCapacity]:
        """
        Update venue capacity counters.

        Args:
            db: Database session
            venue_id: Venue ID
            increment: Change in current occupancy (+1 for check-in, -1 for check-out)
            pending_checkin_delta: Change in pending check-ins counter
            pending_retrieval_delta: Change in pending retrievals counter

        Returns:
            Updated capacity object or None
        """
        capacity = db.query(ValetCapacity).filter(
            ValetCapacity.venue_id == venue_id
        ).first()

        if not capacity:
            logger.warning(f"No capacity record found for venue {venue_id}")
            return None

        # Update occupancy
        if increment != 0:
            capacity.current_occupancy = max(0, capacity.current_occupancy + increment)
            capacity.available_capacity = capacity.total_capacity - capacity.current_occupancy

        # Update queue counters
        if pending_checkin_delta != 0:
            capacity.pending_check_ins = max(0, capacity.pending_check_ins + pending_checkin_delta)

        if pending_retrieval_delta != 0:
            capacity.pending_retrievals = max(0, capacity.pending_retrievals + pending_retrieval_delta)

        capacity.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(capacity)

        return capacity

    @staticmethod
    def _log_status_event(
        db: Session,
        session_id: UUID,
        old_status: Optional[str],
        new_status: str,
        user_id: Optional[UUID] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ValetStatusEvent:
        """
        Log status change event to timeline.

        Args:
            db: Database session
            session_id: Valet session ID
            old_status: Previous status
            new_status: New status
            user_id: User who made the change
            notes: Optional notes about the change
            metadata: Additional metadata

        Returns:
            Created status event
        """
        event = ValetStatusEvent(
            id=uuid4(),
            session_id=session_id,
            user_id=user_id,
            old_status=old_status,
            new_status=new_status,
            notes=notes,
            metadata=metadata or {}
        )
        db.add(event)
        return event

    @staticmethod
    def _get_pricing(db: Session, venue_id: UUID, service_type: str) -> Dict[str, Decimal]:
        """
        Get pricing configuration for venue and service type.

        Args:
            db: Database session
            venue_id: Venue ID
            service_type: Service type

        Returns:
            Dictionary with pricing details
        """
        pricing = db.query(ValetPricing).filter(
            and_(
                ValetPricing.venue_id == venue_id,
                ValetPricing.pricing_tier == service_type,
                ValetPricing.is_active == True
            )
        ).first()

        if pricing:
            return {
                "base_price": pricing.base_price,
                "service_fee": pricing.service_fee,
                "hourly_rate": pricing.hourly_rate or Decimal("0.00"),
                "daily_max": pricing.daily_max or Decimal("0.00")
            }

        # Default pricing if not configured
        defaults = {
            ServiceType.STANDARD.value: Decimal("25.00"),
            ServiceType.VIP.value: Decimal("50.00"),
            ServiceType.PREMIUM.value: Decimal("75.00"),
            ServiceType.EVENT.value: Decimal("35.00"),
        }

        base = defaults.get(service_type, Decimal("25.00"))
        return {
            "base_price": base,
            "service_fee": Decimal("5.00"),
            "hourly_rate": Decimal("0.00"),
            "daily_max": Decimal("0.00")
        }

    @staticmethod
    def create_valet_session(
        db: Session,
        session_data: ValetSessionCreate,
        user_id: Optional[UUID] = None
    ) -> ValetSessionResponse:
        """
        Create new valet booking with ticket generation, PIN, and QR code data.

        Args:
            db: Database session
            session_data: Session creation data
            user_id: Optional authenticated user ID

        Returns:
            Complete valet session response with ticket details

        Raises:
            HTTPException: If venue not found, at capacity, or validation fails
        """
        # Validate venue exists
        venue = db.query(Venue).filter(Venue.id == session_data.venue_id).first()
        if not venue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venue not found"
            )

        if not venue.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Venue is not active"
            )

        # Check capacity
        has_capacity, capacity_message = ValetService.check_capacity(db, session_data.venue_id)
        if not has_capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=capacity_message
            )

        # Validate at least one contact method
        if not session_data.contact_email and not session_data.contact_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one contact method (email or phone) is required"
            )

        # Determine service type (default to standard)
        service_type = ServiceType.STANDARD.value

        # Get pricing
        pricing = ValetService._get_pricing(db, session_data.venue_id, service_type)
        base_price = pricing["base_price"]
        service_fee = pricing["service_fee"]
        total_price = base_price + service_fee

        # Generate unique identifiers
        ticket_number = ValetService.generate_ticket_number(db)
        pin = ValetService.generate_pin()

        # Create session
        valet_session = ValetSession(
            id=uuid4(),
            venue_id=session_data.venue_id,
            user_id=user_id,
            vehicle_plate=session_data.vehicle_plate,
            vehicle_make=session_data.vehicle_make,
            vehicle_model=session_data.vehicle_model,
            vehicle_color=session_data.vehicle_color,
            vehicle_year=session_data.vehicle_year,
            vehicle_notes=session_data.vehicle_notes,
            service_type=service_type,
            ticket_number=ticket_number,
            base_price=base_price,
            service_fee=service_fee,
            total_price=total_price,
            contact_phone=session_data.contact_phone,
            contact_email=session_data.contact_email,
            special_instructions=session_data.special_requests,
            status=ValetStatus.PENDING.value,
            additional_metadata={
                "pin": pin,
                "qr_code_data": f"{ticket_number}:{pin}",
                "arrival_time": session_data.arrival_time.isoformat() if session_data.arrival_time else None
            }
        )

        db.add(valet_session)

        # Log initial status
        ValetService._log_status_event(
            db,
            valet_session.id,
            None,
            ValetStatus.PENDING.value,
            user_id,
            "Session created"
        )

        # Update capacity counters
        ValetService.update_capacity(db, session_data.venue_id, pending_checkin_delta=1)

        db.commit()
        db.refresh(valet_session)

        logger.info(f"Created valet session {valet_session.id} - Ticket: {ticket_number}")

        # Build response
        return ValetService._build_session_response(db, valet_session)

    @staticmethod
    def checkin_session(
        db: Session,
        ticket_number: str,
        pin: str,
        attendant_id: Optional[UUID] = None,
        parking_location: Optional[str] = None
    ) -> ValetSessionResponse:
        """
        Check in customer on arrival - verify ticket and PIN, hand over keys.

        Args:
            db: Database session
            ticket_number: Valet ticket number
            pin: 4-digit PIN for verification
            attendant_id: ID of valet attendant performing check-in
            parking_location: Optional initial parking location

        Returns:
            Updated session response

        Raises:
            HTTPException: If session not found, PIN invalid, or wrong status
        """
        # Find session
        session = db.query(ValetSession).filter(
            ValetSession.ticket_number == ticket_number
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Valet session not found"
            )

        # Verify PIN
        stored_pin = session.additional_metadata.get("pin") if session.additional_metadata else None
        if stored_pin != pin:
            logger.warning(f"Invalid PIN attempt for session {session.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid PIN"
            )

        # Validate status transition
        if session.status != ValetStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot check in session with status: {session.status}"
            )

        # Update session
        session.status = ValetStatus.CHECKED_IN.value
        session.check_in_time = datetime.utcnow()
        session.attendant_id = attendant_id
        if parking_location:
            session.parking_location = parking_location

        # Log status change
        ValetService._log_status_event(
            db,
            session.id,
            ValetStatus.PENDING.value,
            ValetStatus.CHECKED_IN.value,
            attendant_id,
            "Customer checked in, keys received"
        )

        # Update capacity
        ValetService.update_capacity(
            db,
            session.venue_id,
            increment=1,
            pending_checkin_delta=-1
        )

        db.commit()
        db.refresh(session)

        logger.info(f"Checked in valet session {session.id}")

        return ValetService._build_session_response(db, session)

    @staticmethod
    def request_retrieval(
        db: Session,
        ticket_number: Optional[str] = None,
        pin: Optional[str] = None,
        session_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        priority: str = ValetPriorityLevel.NORMAL.value
    ) -> Dict[str, Any]:
        """
        Request car retrieval with ETA calculation.

        Args:
            db: Database session
            ticket_number: Valet ticket number (if using ticket/PIN)
            pin: 4-digit PIN (if using ticket/PIN)
            session_id: Session ID (if authenticated)
            user_id: User ID making request
            priority: Request priority level

        Returns:
            Dictionary with session details and ETA

        Raises:
            HTTPException: If session not found, invalid credentials, or wrong status
        """
        # Find session by ticket or ID
        if ticket_number and pin:
            session = db.query(ValetSession).filter(
                ValetSession.ticket_number == ticket_number
            ).first()

            if session:
                stored_pin = session.additional_metadata.get("pin") if session.additional_metadata else None
                if stored_pin != pin:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid PIN"
                    )
        elif session_id:
            session = db.query(ValetSession).filter(
                ValetSession.id == session_id
            ).first()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either ticket_number/pin or session_id required"
            )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Valet session not found"
            )

        # Validate status
        if session.status not in [ValetStatus.PARKED.value, ValetStatus.READY.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot request retrieval for session with status: {session.status}"
            )

        # Calculate ETA
        eta_minutes, estimated_time = ValetService.calculate_eta(
            db,
            session.venue_id,
            session.service_type,
            "retrieval"
        )

        # Update session
        old_status = session.status
        session.status = ValetStatus.RETRIEVAL_REQUESTED.value
        session.retrieval_requested_time = datetime.utcnow()
        session.estimated_ready_time = estimated_time

        # Log status change
        ValetService._log_status_event(
            db,
            session.id,
            old_status,
            ValetStatus.RETRIEVAL_REQUESTED.value,
            user_id,
            f"Retrieval requested - ETA: {eta_minutes} minutes"
        )

        # Update capacity
        ValetService.update_capacity(
            db,
            session.venue_id,
            pending_retrieval_delta=1
        )

        db.commit()
        db.refresh(session)

        logger.info(f"Retrieval requested for session {session.id} - ETA: {eta_minutes} min")

        return {
            "session": ValetService._build_session_response(db, session),
            "eta_minutes": eta_minutes,
            "estimated_ready_time": estimated_time
        }

    @staticmethod
    def cancel_retrieval_request(
        db: Session,
        session_id: UUID,
        user_id: Optional[UUID] = None,
        reason: Optional[str] = None
    ) -> ValetSessionResponse:
        """
        Cancel retrieval request and return to parked status.

        Args:
            db: Database session
            session_id: Valet session ID
            user_id: User cancelling request
            reason: Optional cancellation reason

        Returns:
            Updated session response

        Raises:
            HTTPException: If session not found or wrong status
        """
        session = db.query(ValetSession).filter(
            ValetSession.id == session_id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Valet session not found"
            )

        if session.status not in [ValetStatus.RETRIEVAL_REQUESTED.value, ValetStatus.RETRIEVING.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel retrieval for session with status: {session.status}"
            )

        # Update session
        old_status = session.status
        session.status = ValetStatus.PARKED.value
        session.retrieval_requested_time = None
        session.estimated_ready_time = None

        # Log status change
        ValetService._log_status_event(
            db,
            session.id,
            old_status,
            ValetStatus.PARKED.value,
            user_id,
            f"Retrieval cancelled: {reason}" if reason else "Retrieval cancelled"
        )

        # Update capacity
        ValetService.update_capacity(
            db,
            session.venue_id,
            pending_retrieval_delta=-1
        )

        db.commit()
        db.refresh(session)

        logger.info(f"Retrieval cancelled for session {session.id}")

        return ValetService._build_session_response(db, session)

    @staticmethod
    def get_session(
        db: Session,
        session_id: Optional[UUID] = None,
        ticket_number: Optional[str] = None,
        include_timeline: bool = True
    ) -> ValetSessionResponse:
        """
        Get session details with timeline.

        Args:
            db: Database session
            session_id: Session ID
            ticket_number: Ticket number (alternative lookup)
            include_timeline: Whether to include status timeline

        Returns:
            Session response with details

        Raises:
            HTTPException: If session not found
        """
        query = db.query(ValetSession)

        if session_id:
            query = query.filter(ValetSession.id == session_id)
        elif ticket_number:
            query = query.filter(ValetSession.ticket_number == ticket_number)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either session_id or ticket_number required"
            )

        session = query.first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Valet session not found"
            )

        return ValetService._build_session_response(db, session, include_timeline)

    @staticmethod
    def update_session_status(
        db: Session,
        session_id: UUID,
        new_status: str,
        attendant_id: Optional[UUID] = None,
        parking_location: Optional[str] = None,
        notes: Optional[str] = None
    ) -> ValetSessionResponse:
        """
        Update session status (staff action).

        Args:
            db: Database session
            session_id: Session ID
            new_status: New status to set
            attendant_id: Staff member making change
            parking_location: Optional parking location update
            notes: Optional notes about status change

        Returns:
            Updated session response

        Raises:
            HTTPException: If session not found or invalid transition
        """
        session = db.query(ValetSession).filter(
            ValetSession.id == session_id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Valet session not found"
            )

        # Validate transition
        if not ValetService.validate_status_transition(session.status, new_status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition: {session.status} -> {new_status}"
            )

        old_status = session.status
        session.status = new_status

        # Update timestamps based on status
        now = datetime.utcnow()
        if new_status == ValetStatus.PARKED.value:
            session.parked_time = now
        elif new_status == ValetStatus.RETRIEVING.value:
            # Don't update retrieval_requested_time if already set
            pass
        elif new_status == ValetStatus.READY.value:
            session.ready_time = now
        elif new_status == ValetStatus.COMPLETED.value:
            session.check_out_time = now

        # Update parking location
        if parking_location:
            session.parking_location = parking_location

        # Update attendant
        if attendant_id:
            session.attendant_id = attendant_id

        # Log status change
        ValetService._log_status_event(
            db,
            session.id,
            old_status,
            new_status,
            attendant_id,
            notes
        )

        # Update capacity counters based on status change
        capacity_updates = {}
        if new_status == ValetStatus.COMPLETED.value:
            capacity_updates["increment"] = -1
            if old_status in [ValetStatus.RETRIEVAL_REQUESTED.value, ValetStatus.RETRIEVING.value, ValetStatus.READY.value]:
                capacity_updates["pending_retrieval_delta"] = -1
        elif new_status == ValetStatus.RETRIEVING.value and old_status == ValetStatus.RETRIEVAL_REQUESTED.value:
            # No capacity change, just queue movement
            pass
        elif new_status == ValetStatus.READY.value:
            if old_status in [ValetStatus.RETRIEVAL_REQUESTED.value, ValetStatus.RETRIEVING.value]:
                capacity_updates["pending_retrieval_delta"] = -1

        if capacity_updates:
            ValetService.update_capacity(db, session.venue_id, **capacity_updates)

        db.commit()
        db.refresh(session)

        logger.info(f"Updated session {session.id} status: {old_status} -> {new_status}")

        return ValetService._build_session_response(db, session)

    @staticmethod
    def rate_and_tip(
        db: Session,
        session_id: UUID,
        rating: int,
        tip_amount: Optional[Decimal] = None,
        feedback: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> ValetSessionResponse:
        """
        Submit rating and tip for completed session.

        Args:
            db: Database session
            session_id: Session ID
            rating: Rating (1-5)
            tip_amount: Optional tip amount
            feedback: Optional feedback text
            user_id: User submitting rating

        Returns:
            Updated session response

        Raises:
            HTTPException: If session not found or not completed
        """
        session = db.query(ValetSession).filter(
            ValetSession.id == session_id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Valet session not found"
            )

        if session.status not in [ValetStatus.COMPLETED.value, ValetStatus.READY.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only rate completed or ready sessions"
            )

        # Validate rating
        if rating < 1 or rating > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rating must be between 1 and 5"
            )

        # Update session
        session.rating = rating
        session.feedback = feedback

        if tip_amount and tip_amount > 0:
            session.tip_amount = tip_amount
            session.total_price += tip_amount

        db.commit()
        db.refresh(session)

        logger.info(f"Session {session.id} rated: {rating} stars, tip: ${tip_amount or 0}")

        return ValetService._build_session_response(db, session)

    @staticmethod
    def get_user_history(
        db: Session,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None
    ) -> ValetHistory:
        """
        Get user's valet history with pagination.

        Args:
            db: Database session
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Items per page
            status_filter: Optional status filter

        Returns:
            Paginated history response
        """
        query = db.query(ValetSession).filter(
            ValetSession.user_id == user_id
        )

        if status_filter:
            query = query.filter(ValetSession.status == status_filter)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        sessions = query.order_by(desc(ValetSession.check_in_time)).offset(offset).limit(page_size).all()

        # Build history items
        items = []
        for session in sessions:
            venue = db.query(Venue).filter(Venue.id == session.venue_id).first()
            vehicle_info = None
            if session.vehicle_make or session.vehicle_model:
                parts = []
                if session.vehicle_year:
                    parts.append(str(session.vehicle_year))
                if session.vehicle_make:
                    parts.append(session.vehicle_make)
                if session.vehicle_model:
                    parts.append(session.vehicle_model)
                vehicle_info = " ".join(parts)

            items.append(ValetHistoryItem(
                id=session.id,
                venue_name=venue.name if venue else "Unknown",
                vehicle_plate=session.vehicle_plate,
                vehicle_info=vehicle_info,
                status=ValetSessionStatus(session.status),
                arrival_time=session.check_in_time,
                completed_at=session.check_out_time,
                total_cost=session.total_price,
                rating=session.rating
            ))

        return ValetHistory(
            sessions=items,
            total=total,
            page=page,
            page_size=page_size
        )

    @staticmethod
    def get_venue_availability(db: Session, venue_id: UUID) -> ValetAvailability:
        """
        Check valet availability at venue.

        Args:
            db: Database session
            venue_id: Venue ID

        Returns:
            Availability information

        Raises:
            HTTPException: If venue not found
        """
        venue = db.query(Venue).filter(Venue.id == venue_id).first()
        if not venue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venue not found"
            )

        capacity = db.query(ValetCapacity).filter(
            ValetCapacity.venue_id == venue_id
        ).first()

        if not capacity:
            # No capacity tracking, assume available
            pricing = ValetService._get_pricing(db, venue_id, ServiceType.STANDARD.value)
            return ValetAvailability(
                venue_id=venue_id,
                venue_name=venue.name,
                is_available=True,
                current_capacity=0,
                max_capacity=0,
                pricing=PricingInfo(
                    base_rate=pricing["base_price"],
                    estimated_total=pricing["base_price"] + pricing["service_fee"]
                )
            )

        # Calculate wait time based on queue
        eta_minutes, _ = ValetService.calculate_eta(
            db,
            venue_id,
            ServiceType.STANDARD.value,
            "parking"
        )

        pricing = ValetService._get_pricing(db, venue_id, ServiceType.STANDARD.value)

        return ValetAvailability(
            venue_id=venue_id,
            venue_name=venue.name,
            is_available=capacity.is_accepting_vehicles and capacity.available_capacity > 0,
            current_capacity=capacity.current_occupancy,
            max_capacity=capacity.total_capacity,
            estimated_wait_minutes=eta_minutes,
            pricing=PricingInfo(
                base_rate=pricing["base_price"],
                estimated_total=pricing["base_price"] + pricing["service_fee"]
            ),
            special_notes=capacity.status_message
        )

    @staticmethod
    def get_staff_queue(db: Session, venue_id: UUID) -> ValetQueueResponse:
        """
        Get active queue for staff dashboard.

        Args:
            db: Database session
            venue_id: Venue ID

        Returns:
            Queue response with categorized sessions
        """
        # Get all active sessions
        sessions = db.query(ValetSession).filter(
            and_(
                ValetSession.venue_id == venue_id,
                ValetSession.status.in_([
                    ValetStatus.PENDING.value,
                    ValetStatus.CHECKED_IN.value,
                    ValetStatus.PARKED.value,
                    ValetStatus.RETRIEVAL_REQUESTED.value,
                    ValetStatus.RETRIEVING.value,
                    ValetStatus.READY.value
                ])
            )
        ).order_by(ValetSession.check_in_time).all()

        # Categorize sessions
        pending_checkins = []
        active_parking = []
        parked = []
        pending_retrievals = []
        active_retrievals = []

        for session in sessions:
            item = ValetService._build_queue_item(db, session)

            if session.status == ValetStatus.PENDING.value:
                pending_checkins.append(item)
            elif session.status == ValetStatus.CHECKED_IN.value:
                active_parking.append(item)
            elif session.status == ValetStatus.PARKED.value:
                parked.append(item)
            elif session.status == ValetStatus.RETRIEVAL_REQUESTED.value:
                pending_retrievals.append(item)
            elif session.status == ValetStatus.RETRIEVING.value:
                active_retrievals.append(item)
            elif session.status == ValetStatus.READY.value:
                # Ready vehicles could go in multiple categories, adding to retrievals
                active_retrievals.append(item)

        # Get capacity
        capacity = db.query(ValetCapacity).filter(
            ValetCapacity.venue_id == venue_id
        ).first()

        return ValetQueueResponse(
            pending_checkins=pending_checkins,
            active_parking=active_parking,
            parked=parked,
            pending_retrievals=pending_retrievals,
            active_retrievals=active_retrievals,
            total_active=len(sessions),
            available_capacity=capacity.available_capacity if capacity else 0
        )

    @staticmethod
    def file_incident(
        db: Session,
        session_id: UUID,
        incident_type: str,
        severity: str,
        title: str,
        description: str,
        reporter_id: UUID,
        attachments: Optional[List[str]] = None
    ) -> ValetIncidentResponse:
        """
        Create incident report.

        Args:
            db: Database session
            session_id: Valet session ID
            incident_type: Type of incident
            severity: Severity level
            title: Incident title
            description: Detailed description
            reporter_id: User reporting incident
            attachments: Optional attachment URLs

        Returns:
            Created incident response

        Raises:
            HTTPException: If session not found
        """
        session = db.query(ValetSession).filter(
            ValetSession.id == session_id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Valet session not found"
            )

        # Create incident
        incident = ValetIncident(
            id=uuid4(),
            session_id=session_id,
            venue_id=session.venue_id,
            reporter_id=reporter_id,
            incident_type=incident_type,
            severity=severity,
            title=title,
            description=description,
            attachments=attachments or []
        )

        db.add(incident)
        db.commit()
        db.refresh(incident)

        logger.warning(f"Incident filed for session {session_id}: {title} ({severity})")

        # Get reporter name
        reporter = db.query(User).filter(User.id == reporter_id).first()
        reporter_name = f"{reporter.first_name} {reporter.last_name}" if reporter else None

        return ValetIncidentResponse(
            id=incident.id,
            session_id=incident.session_id,
            incident_type=ValetIncidentType(incident.incident_type),
            severity=incident.severity,
            description=incident.description,
            reported_by=incident.reporter_id,
            reported_by_name=reporter_name,
            reported_at=incident.created_at,
            photos=incident.attachments,
            action_taken=incident.resolution,
            resolved=incident.is_resolved,
            resolved_at=incident.resolved_at
        )

    @staticmethod
    def process_payment(
        db: Session,
        session_id: UUID,
        amount: Decimal,
        payment_method: str,
        transaction_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle payment processing (placeholder for payment integration).

        Args:
            db: Database session
            session_id: Valet session ID
            amount: Payment amount
            payment_method: Payment method
            transaction_id: Transaction ID from payment processor

        Returns:
            Payment result

        Raises:
            HTTPException: If session not found or payment fails
        """
        session = db.query(ValetSession).filter(
            ValetSession.id == session_id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Valet session not found"
            )

        # TODO: Integrate with actual payment processor (Stripe, etc.)
        # For now, simulate successful payment

        logger.info(f"Processing payment for session {session_id}: ${amount} via {payment_method}")

        return {
            "success": True,
            "amount": amount,
            "transaction_id": transaction_id or f"sim_{uuid4().hex[:16]}",
            "payment_method": payment_method,
            "processed_at": datetime.utcnow()
        }

    @staticmethod
    def send_notification(
        db: Session,
        session_id: UUID,
        notification_type: str,
        message: str,
        recipient: Optional[str] = None,
        communication_type: str = CommunicationType.SMS.value
    ) -> bool:
        """
        Send push/SMS notification and log it.

        Args:
            db: Database session
            session_id: Valet session ID
            notification_type: Type of notification
            message: Message content
            recipient: Recipient (phone/email), uses session contact if not provided
            communication_type: Type (sms, push, email)

        Returns:
            True if sent successfully
        """
        session = db.query(ValetSession).filter(
            ValetSession.id == session_id
        ).first()

        if not session:
            logger.error(f"Cannot send notification - session {session_id} not found")
            return False

        # Determine recipient
        if not recipient:
            if communication_type == CommunicationType.SMS.value:
                recipient = session.contact_phone
            elif communication_type == CommunicationType.EMAIL.value:
                recipient = session.contact_email

        if not recipient:
            logger.warning(f"No recipient found for {communication_type} notification")
            return False

        # Log communication
        comm = ValetCommunication(
            id=uuid4(),
            session_id=session_id,
            user_id=session.user_id,
            communication_type=communication_type,
            recipient=recipient,
            message=message,
            status=CommunicationStatus.SENT.value,
            sent_at=datetime.utcnow()
        )

        db.add(comm)
        session.last_notification_sent = datetime.utcnow()
        db.commit()

        # TODO: Integrate with actual notification service (Twilio, FCM, etc.)
        logger.info(f"NOTIFICATION ({communication_type.upper()}): To {recipient} - {message[:50]}...")

        return True

    @staticmethod
    def assign_keys(
        db: Session,
        session_id: UUID,
        key_tag_number: str,
        zone: str,
        box: str,
        position: str,
        staff_user_id: UUID,
        key_photo_url: Optional[str] = None,
        key_notes: Optional[str] = None
    ) -> ValetSession:
        """
        Assign keys to storage location.

        Args:
            db: Database session
            session_id: Valet session ID
            key_tag_number: 3-digit numeric key tag (001-999)
            zone: Storage zone ID
            box: Storage box ID
            position: Storage position (e.g., A1)
            staff_user_id: ID of staff member assigning keys
            key_photo_url: Optional photo of keys
            key_notes: Optional notes about keys

        Returns:
            Updated valet session

        Raises:
            HTTPException: If session not found or key tag already in use
        """
        from fastapi import HTTPException, status
        from app.models.valet import ValetSession, ValetStatusEvent
        from datetime import datetime

        # Get session
        session = db.query(ValetSession).filter(ValetSession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Valet session not found"
            )

        # Check for duplicate key tag in active sessions (not completed/cancelled)
        duplicate = db.query(ValetSession).filter(
            ValetSession.key_tag_number == key_tag_number,
            ValetSession.id != session_id,
            ValetSession.status.notin_(['completed', 'cancelled', 'no_show'])
        ).first()

        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Key tag {key_tag_number} is already assigned to another active session (Ticket: {duplicate.ticket_number})"
            )

        # Update session with key information
        session.key_tag_number = key_tag_number
        session.key_storage_zone = zone
        session.key_storage_box = box
        session.key_storage_position = position
        session.key_status = "in_storage"
        session.key_photo_url = key_photo_url
        session.key_notes = key_notes
        session.key_assigned_by_id = staff_user_id
        session.key_assigned_at = datetime.utcnow()

        # Log status event
        event = ValetStatusEvent(
            session_id=session.id,
            old_status=session.status,
            new_status=session.status,  # Status doesn't change, but we log the key assignment
            changed_by_user_id=staff_user_id,
            notes=f"Keys assigned to storage: {zone}/{box}/{position} (Tag: {key_tag_number})"
        )
        db.add(event)

        db.commit()
        db.refresh(session)

        return session

    @staticmethod
    def mark_keys_grabbed(
        db: Session,
        session_id: UUID,
        staff_user_id: UUID
    ) -> ValetSession:
        """
        Mark keys as grabbed from storage for retrieval.

        Args:
            db: Database session
            session_id: Valet session ID
            staff_user_id: ID of staff member grabbing keys

        Returns:
            Updated valet session

        Raises:
            HTTPException: If session not found or keys not in storage
        """
        from fastapi import HTTPException, status
        from app.models.valet import ValetSession, ValetStatusEvent
        from datetime import datetime

        # Get session
        session = db.query(ValetSession).filter(ValetSession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Valet session not found"
            )

        # Verify keys are in storage
        if session.key_status != "in_storage":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Keys are not in storage (current status: {session.key_status})"
            )

        # Update key status
        session.key_status = "grabbed"
        session.key_grabbed_by_id = staff_user_id
        session.key_grabbed_at = datetime.utcnow()

        # Log status event
        event = ValetStatusEvent(
            session_id=session.id,
            old_status=session.status,
            new_status=session.status,
            changed_by_user_id=staff_user_id,
            notes=f"Keys grabbed from storage: {session.key_storage_zone}/{session.key_storage_box}/{session.key_storage_position}"
        )
        db.add(event)

        db.commit()
        db.refresh(session)

        return session

    @staticmethod
    def get_storage_config(db: Session, venue_id: UUID):
        """
        Get key storage configuration for venue with real-time occupancy.

        Args:
            db: Database session
            venue_id: Venue ID

        Returns:
            Dictionary with zones and occupied_positions
        """
        from app.models.valet import KeyStorageConfig, ValetSession

        # Get storage config
        config = db.query(KeyStorageConfig).filter(
            KeyStorageConfig.venue_id == venue_id
        ).first()

        if not config:
            # Return empty configuration if none exists
            return {
                "venue_id": venue_id,
                "zones": [],
                "occupied_positions": {},
                "created_at": None,
                "updated_at": None
            }

        # Get occupied positions from active sessions
        active_sessions = db.query(ValetSession).filter(
            ValetSession.venue_id == venue_id,
            ValetSession.key_status.in_(['in_storage', 'grabbed']),
            ValetSession.status.notin_(['completed', 'cancelled', 'no_show'])
        ).all()

        # Build occupied positions map: zone_id -> [positions]
        occupied_positions = {}
        for session in active_sessions:
            if session.key_storage_zone and session.key_storage_position:
                zone_id = session.key_storage_zone
                if zone_id not in occupied_positions:
                    occupied_positions[zone_id] = []
                occupied_positions[zone_id].append(session.key_storage_position)

        return {
            "venue_id": config.venue_id,
            "zones": config.zones,
            "occupied_positions": occupied_positions,
            "created_at": config.created_at,
            "updated_at": config.updated_at
        }

    @staticmethod
    def update_storage_config(
        db: Session,
        venue_id: UUID,
        zones: list
    ):
        """
        Update or create storage configuration.

        Args:
            db: Database session
            venue_id: Venue ID
            zones: List of zone configurations

        Returns:
            Updated/created configuration
        """
        from app.models.valet import KeyStorageConfig
        from datetime import datetime

        # Get or create config
        config = db.query(KeyStorageConfig).filter(
            KeyStorageConfig.venue_id == venue_id
        ).first()

        if config:
            # Update existing
            config.zones = zones
            config.updated_at = datetime.utcnow()
        else:
            # Create new
            config = KeyStorageConfig(
                venue_id=venue_id,
                zones=zones
            )
            db.add(config)

        db.commit()
        db.refresh(config)

        return config

    # Helper methods

    @staticmethod
    def _build_session_response(
        db: Session,
        session: ValetSession,
        include_timeline: bool = True
    ) -> ValetSessionResponse:
        """Build complete session response from model."""
        venue = db.query(Venue).filter(Venue.id == session.venue_id).first()

        # Build timeline
        timeline = []
        if include_timeline:
            events = db.query(ValetStatusEvent).filter(
                ValetStatusEvent.session_id == session.id
            ).order_by(ValetStatusEvent.created_at).all()

            for event in events:
                staff_name = None
                if event.user_id:
                    user = db.query(User).filter(User.id == event.user_id).first()
                    if user:
                        staff_name = f"{user.first_name} {user.last_name}"

                timeline.append(StatusEvent(
                    status=ValetSessionStatus(event.new_status),
                    timestamp=event.created_at,
                    notes=event.notes,
                    staff_id=event.user_id,
                    staff_name=staff_name
                ))

        # Get attendant name
        attendant_name = None
        if session.attendant_id:
            attendant = db.query(User).filter(User.id == session.attendant_id).first()
            if attendant:
                attendant_name = f"{attendant.first_name} {attendant.last_name}"

        # Build parking location
        parking_loc = None
        if session.parking_location:
            # Parse location string (e.g., "Lot A - Row 3")
            parking_loc = ParkingLocation(notes=session.parking_location)

        # Build key management info
        key_mgmt = None
        if hasattr(session, 'key_tag_number') and session.key_tag_number:
            from app.schemas.valet import KeyManagement, KeyStorageLocation

            # Build storage location if available
            storage_loc = None
            if session.key_storage_zone and session.key_storage_box and session.key_storage_position:
                storage_loc = KeyStorageLocation(
                    zone=session.key_storage_zone,
                    box=session.key_storage_box,
                    position=session.key_storage_position
                )

            # Get assigned by staff name
            assigned_by_name = None
            if hasattr(session, 'key_assigned_by_id') and session.key_assigned_by_id:
                assigned_by = db.query(User).filter(User.id == session.key_assigned_by_id).first()
                if assigned_by:
                    assigned_by_name = f"{assigned_by.first_name} {assigned_by.last_name}"

            # Get grabbed by staff name
            grabbed_by_name = None
            if hasattr(session, 'key_grabbed_by_id') and session.key_grabbed_by_id:
                grabbed_by = db.query(User).filter(User.id == session.key_grabbed_by_id).first()
                if grabbed_by:
                    grabbed_by_name = f"{grabbed_by.first_name} {grabbed_by.last_name}"

            key_mgmt = KeyManagement(
                key_tag_number=session.key_tag_number,
                storage_location=storage_loc,
                key_status=session.key_status if hasattr(session, 'key_status') else None,
                key_photo_url=session.key_photo_url if hasattr(session, 'key_photo_url') else None,
                key_notes=session.key_notes if hasattr(session, 'key_notes') else None,
                assigned_by=assigned_by_name,
                assigned_at=session.key_assigned_at if hasattr(session, 'key_assigned_at') else None,
                grabbed_by=grabbed_by_name,
                grabbed_at=session.key_grabbed_at if hasattr(session, 'key_grabbed_at') else None
            )

        return ValetSessionResponse(
            id=session.id,
            venue_id=session.venue_id,
            venue_name=venue.name if venue else "Unknown",
            event_id=None,
            user_id=session.user_id,
            vehicle_plate=session.vehicle_plate,
            vehicle_make=session.vehicle_make,
            vehicle_model=session.vehicle_model,
            vehicle_color=session.vehicle_color,
            vehicle_year=session.vehicle_year,
            status=ValetSessionStatus(session.status),
            priority=ValetPriorityLevel.NORMAL,  # TODO: Store priority in session
            requested_at=session.created_at,
            arrival_time=session.check_in_time,
            checked_in_at=session.check_in_time,
            parked_at=session.parked_time,
            retrieval_requested_at=session.retrieval_requested_time,
            ready_at=session.ready_time,
            completed_at=session.check_out_time,
            parking_location=parking_loc,
            pricing=PricingInfo(
                base_rate=session.base_price,
                estimated_total=session.total_price
            ),
            payment=PaymentInfo(
                amount=session.total_price,
                tip=session.tip_amount
            ) if session.check_out_time else None,
            assigned_valet_id=session.attendant_id,
            assigned_valet_name=attendant_name,
            access_code=session.ticket_number,
            key_management=key_mgmt,
            timeline=timeline,
            rating=session.rating,
            feedback=session.feedback,
            created_at=session.created_at,
            updated_at=session.updated_at
        )

    @staticmethod
    def _build_queue_item(db: Session, session: ValetSession) -> ValetQueueItem:
        """Build queue item from session."""
        vehicle_info = None
        if session.vehicle_make or session.vehicle_model:
            parts = []
            if session.vehicle_year:
                parts.append(str(session.vehicle_year))
            if session.vehicle_make:
                parts.append(session.vehicle_make)
            if session.vehicle_model:
                parts.append(session.vehicle_model)
            if session.vehicle_color:
                parts.append(f"- {session.vehicle_color}")
            vehicle_info = " ".join(parts)

        # Get customer name
        customer_name = None
        if session.user_id:
            user = db.query(User).filter(User.id == session.user_id).first()
            if user:
                customer_name = f"{user.first_name} {user.last_name}"

        # Get attendant name
        attendant_name = None
        if session.attendant_id:
            attendant = db.query(User).filter(User.id == session.attendant_id).first()
            if attendant:
                attendant_name = f"{attendant.first_name} {attendant.last_name}"

        # Calculate wait time
        wait_time = None
        if session.check_in_time:
            delta = datetime.utcnow() - session.check_in_time
            wait_time = int(delta.total_seconds() / 60)

        # Parse parking location
        parking_loc = None
        if session.parking_location:
            parking_loc = ParkingLocation(notes=session.parking_location)

        return ValetQueueItem(
            session_id=session.id,
            vehicle_plate=session.vehicle_plate,
            vehicle_info=vehicle_info,
            customer_name=customer_name,
            status=ValetSessionStatus(session.status),
            priority=ValetPriorityLevel.NORMAL,
            arrival_time=session.check_in_time,
            wait_time_minutes=wait_time,
            parking_location=parking_loc,
            assigned_valet_id=session.attendant_id,
            assigned_valet_name=attendant_name,
            special_requests=session.special_instructions
        )
