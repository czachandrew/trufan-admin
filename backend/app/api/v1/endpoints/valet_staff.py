"""
Staff-facing Valet API Endpoints

This module provides staff and admin endpoints for managing valet parking operations,
including queue management, session status updates, incident reporting, capacity monitoring,
performance metrics, payment retries, refunds, and session search.

All endpoints require authentication and staff-level permissions (venue_staff, venue_admin).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from decimal import Decimal

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.valet import (
    ValetSession,
    ValetStatus,
    ValetIncident,
    ValetCapacity,
)
from app.models.venue import Venue, VenueStaff
from app.schemas.valet import (
    ValetQueueResponse,
    ValetSessionResponse,
    ValetStatusUpdate,
    ValetIncidentCreate,
    ValetIncidentResponse,
    ValetCapacityResponse,
    ValetMetricsResponse,
    ValetSearchResult,
    ValetSessionStatus,
    ParkingLocation,
    KeyAssignmentInput,
    KeyStorageConfigResponse,
    KeyStorageConfigUpdate,
    KeyManagement,
    KeyStorageLocation,
)
from app.services.valet_service import ValetService

router = APIRouter(tags=["valet-staff"])


def check_staff_permissions(current_user: User, venue_id: Optional[UUID] = None, db: Session = None) -> None:
    """
    Verify user has staff permissions for valet operations.

    Args:
        current_user: Current authenticated user
        venue_id: Optional venue ID for venue-specific checks
        db: Database session for venue staff lookup

    Raises:
        HTTPException: If user lacks required permissions
    """
    # Check if user has staff or admin role
    if current_user.role not in [UserRole.VENUE_STAFF, UserRole.VENUE_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff or admin role required for this operation"
        )

    # Super admins have access to all venues
    if current_user.role == UserRole.SUPER_ADMIN:
        return

    # For venue_staff and venue_admin, check venue association
    if venue_id and db:
        # Check if user is associated with this venue through VenueStaff
        venue_staff_record = db.query(VenueStaff).filter(
            and_(
                VenueStaff.user_id == current_user.id,
                VenueStaff.venue_id == venue_id,
                VenueStaff.is_active == True
            )
        ).first()

        if not venue_staff_record:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this venue"
            )


@router.get("/queue", response_model=ValetQueueResponse)
def get_active_valet_queue(
    venue_id: UUID = Query(..., description="Venue ID to get queue for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get active valet queue for staff dashboard.

    Returns categorized lists of sessions:
    - Pending check-ins (confirmed bookings)
    - Active parking (currently being parked)
    - Parked vehicles (awaiting retrieval)
    - Pending retrievals (retrieval requested)
    - Active retrievals (currently being retrieved)

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, venue_id, db)

    # Verify venue exists
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found"
        )

    # Get queue from service
    queue = ValetService.get_staff_queue(db, venue_id)

    return queue


@router.patch("/sessions/{session_id}/status", response_model=ValetSessionResponse)
def update_session_status(
    session_id: UUID,
    new_status: ValetSessionStatus = Query(..., description="New status to set"),
    parking_location: Optional[str] = Query(None, description="Parking location (e.g., 'Lot A - Row 3')"),
    notes: Optional[str] = Query(None, description="Status change notes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update valet session status (staff action).

    Validates status transitions according to the state machine:
    - PENDING -> CHECKED_IN, CANCELLED
    - CHECKED_IN -> PARKED, CANCELLED
    - PARKED -> RETRIEVAL_REQUESTED, CANCELLED
    - RETRIEVAL_REQUESTED -> RETRIEVING, PARKED, CANCELLED
    - RETRIEVING -> READY, RETRIEVAL_REQUESTED
    - READY -> COMPLETED, RETRIEVAL_REQUESTED

    Automatically updates timestamps and capacity counters based on status change.

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, db=db)

    # Get session to check venue access
    session = db.query(ValetSession).filter(ValetSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Valet session not found"
        )

    check_staff_permissions(current_user, session.venue_id, db)

    # Update status via service
    updated_session = ValetService.update_session_status(
        db=db,
        session_id=session_id,
        new_status=new_status.value,
        attendant_id=current_user.id,
        parking_location=parking_location,
        notes=notes
    )

    return updated_session


@router.post("/sessions/{session_id}/complete", response_model=ValetSessionResponse)
def force_complete_session(
    session_id: UUID,
    notes: Optional[str] = Query(None, description="Reason for manual completion"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Force complete a valet session (manual override).

    This endpoint allows staff to manually complete a session that may be stuck
    in an intermediate state or needs to be closed out for operational reasons.

    Use cases:
    - Customer left without proper check-out
    - System error requiring manual intervention
    - Emergency or special circumstances

    Creates an audit trail with the reason for manual completion.

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, db=db)

    # Get session
    session = db.query(ValetSession).filter(ValetSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Valet session not found"
        )

    check_staff_permissions(current_user, session.venue_id, db)

    # Check if already completed
    if session.status == ValetStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is already completed"
        )

    # Force transition to completed
    # Note: This bypasses normal state machine validation for emergency situations
    old_status = session.status
    session.status = ValetStatus.COMPLETED.value
    session.check_out_time = datetime.utcnow()
    session.attendant_id = current_user.id

    # Add note to internal notes
    completion_note = f"[MANUAL COMPLETION by {current_user.first_name} {current_user.last_name}] {notes or 'No reason provided'}"
    if session.internal_notes:
        session.internal_notes += f"\n{completion_note}"
    else:
        session.internal_notes = completion_note

    # Log status event
    ValetService._log_status_event(
        db=db,
        session_id=session_id,
        old_status=old_status,
        new_status=ValetStatus.COMPLETED.value,
        user_id=current_user.id,
        notes=completion_note,
        metadata={"manual_completion": True, "bypass_validation": True}
    )

    # Update capacity
    ValetService.update_capacity(
        db=db,
        venue_id=session.venue_id,
        increment=-1,
        pending_retrieval_delta=-1 if old_status in [
            ValetStatus.RETRIEVAL_REQUESTED.value,
            ValetStatus.RETRIEVING.value,
            ValetStatus.READY.value
        ] else 0
    )

    db.commit()
    db.refresh(session)

    return ValetService._build_session_response(db, session)


@router.patch("/sessions/{session_id}/location", response_model=ValetSessionResponse)
def update_parking_location(
    session_id: UUID,
    section: Optional[str] = Query(None, description="Parking section (e.g., 'A', 'B')"),
    level: Optional[str] = Query(None, description="Parking level (e.g., 'P1', 'Ground')"),
    spot_number: Optional[str] = Query(None, description="Spot number"),
    notes: Optional[str] = Query(None, description="Additional location notes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update parking location for a session (correction/fix).

    Allows staff to update or correct the parking location information
    for a vehicle. Useful when:
    - Initial location was recorded incorrectly
    - Vehicle was moved to a different spot
    - Additional location details need to be added

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, db=db)

    # Get session
    session = db.query(ValetSession).filter(ValetSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Valet session not found"
        )

    check_staff_permissions(current_user, session.venue_id, db)

    # Build location string
    location_parts = []
    if section:
        location_parts.append(f"Section {section}")
    if level:
        location_parts.append(f"Level {level}")
    if spot_number:
        location_parts.append(f"Spot {spot_number}")
    if notes:
        location_parts.append(f"({notes})")

    new_location = " - ".join(location_parts) if location_parts else notes

    if not new_location:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one location field must be provided"
        )

    # Update location
    old_location = session.parking_location
    session.parking_location = new_location
    session.updated_at = datetime.utcnow()

    # Add to internal notes
    location_note = f"[LOCATION UPDATE by {current_user.first_name} {current_user.last_name}] Changed from '{old_location}' to '{new_location}'"
    if session.internal_notes:
        session.internal_notes += f"\n{location_note}"
    else:
        session.internal_notes = location_note

    db.commit()
    db.refresh(session)

    return ValetService._build_session_response(db, session)


@router.post("/sessions/{session_id}/incident", response_model=ValetIncidentResponse)
def file_incident_report(
    session_id: UUID,
    incident_data: ValetIncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    File an incident report for a valet session.

    Creates a detailed incident report for:
    - Vehicle damage
    - Service delays
    - Customer complaints
    - Safety incidents
    - Other operational issues

    Incident reports are tracked separately and can be reviewed,
    resolved, and used for operational improvement and liability tracking.

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, db=db)

    # Get session
    session = db.query(ValetSession).filter(ValetSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Valet session not found"
        )

    check_staff_permissions(current_user, session.venue_id, db)

    # Create incident via service
    incident = ValetService.file_incident(
        db=db,
        session_id=session_id,
        incident_type=incident_data.incident_type.value,
        severity=incident_data.severity,
        title=f"{incident_data.incident_type.value.upper()}: {incident_data.description[:50]}...",
        description=incident_data.description,
        reporter_id=current_user.id,
        attachments=incident_data.photos
    )

    return incident


@router.get("/capacity", response_model=ValetCapacityResponse)
def get_real_time_capacity(
    venue_id: UUID = Query(..., description="Venue ID to get capacity for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get real-time capacity information for a venue.

    Returns:
    - Total capacity
    - Current occupancy
    - Available spaces
    - Utilization percentage
    - Active sessions count
    - Pending retrievals count
    - Staff availability

    Useful for operations dashboard and capacity planning.

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, venue_id, db)

    # Get venue
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found"
        )

    # Get capacity
    capacity = db.query(ValetCapacity).filter(
        ValetCapacity.venue_id == venue_id
    ).first()

    if not capacity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Capacity data not found for this venue"
        )

    # Count active sessions
    active_sessions = db.query(func.count(ValetSession.id)).filter(
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
    ).scalar() or 0

    # Calculate utilization
    utilization = (capacity.current_occupancy / capacity.total_capacity * 100) if capacity.total_capacity > 0 else 0

    return ValetCapacityResponse(
        venue_id=venue_id,
        venue_name=venue.name,
        total_capacity=capacity.total_capacity,
        current_occupancy=capacity.current_occupancy,
        available_spaces=capacity.available_capacity,
        utilization_percentage=round(utilization, 2),
        active_sessions=active_sessions,
        pending_retrievals=capacity.pending_retrievals,
        staff_available=capacity.attendants_on_duty,
        staff_busy=0  # TODO: Calculate from active attendant assignments
    )


@router.get("/metrics", response_model=ValetMetricsResponse)
def get_performance_metrics(
    venue_id: UUID = Query(..., description="Venue ID to get metrics for"),
    period_start: Optional[datetime] = Query(None, description="Start of reporting period"),
    period_end: Optional[datetime] = Query(None, description="End of reporting period"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get performance metrics for valet operations.

    Returns comprehensive metrics including:
    - Volume metrics (total, completed, cancelled sessions)
    - Time metrics (avg parking time, retrieval time, wait time)
    - Financial metrics (revenue, tips, avg session value)
    - Quality metrics (avg rating, incident count)
    - Capacity metrics (peak occupancy, utilization rate)

    Default period: Last 7 days if not specified

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, venue_id, db)

    # Get venue
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found"
        )

    # Default to last 7 days if not specified
    if not period_start:
        period_start = datetime.utcnow() - timedelta(days=7)
    if not period_end:
        period_end = datetime.utcnow()

    # Query sessions in period
    sessions_query = db.query(ValetSession).filter(
        and_(
            ValetSession.venue_id == venue_id,
            ValetSession.created_at >= period_start,
            ValetSession.created_at <= period_end
        )
    )

    # Volume metrics
    total_sessions = sessions_query.count()
    completed_sessions = sessions_query.filter(
        ValetSession.status == ValetStatus.COMPLETED.value
    ).count()
    cancelled_sessions = sessions_query.filter(
        ValetSession.status == ValetStatus.CANCELLED.value
    ).count()

    # Get completed sessions for detailed metrics
    completed = sessions_query.filter(
        ValetSession.status == ValetStatus.COMPLETED.value
    ).all()

    # Time metrics (in minutes)
    parking_times = []
    retrieval_times = []
    wait_times = []

    for session in completed:
        # Parking time: check-in to parked
        if session.check_in_time and session.parked_time:
            parking_delta = session.parked_time - session.check_in_time
            parking_times.append(parking_delta.total_seconds() / 60)

        # Retrieval time: retrieval requested to ready
        if session.retrieval_requested_time and session.ready_time:
            retrieval_delta = session.ready_time - session.retrieval_requested_time
            retrieval_times.append(retrieval_delta.total_seconds() / 60)

        # Wait time: check-in to check-out
        if session.check_in_time and session.check_out_time:
            wait_delta = session.check_out_time - session.check_in_time
            wait_times.append(wait_delta.total_seconds() / 60)

    avg_parking_time = sum(parking_times) / len(parking_times) if parking_times else None
    avg_retrieval_time = sum(retrieval_times) / len(retrieval_times) if retrieval_times else None
    avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else None

    # Financial metrics
    total_revenue = sum(s.total_price for s in completed if s.total_price)
    total_tips = sum(s.tip_amount for s in completed if s.tip_amount)
    avg_session_value = total_revenue / len(completed) if completed else None

    # Quality metrics
    rated_sessions = [s for s in completed if s.rating is not None]
    avg_rating = sum(s.rating for s in rated_sessions) / len(rated_sessions) if rated_sessions else None
    total_ratings = len(rated_sessions)

    # Incident count
    incident_count = db.query(func.count(ValetIncident.id)).filter(
        and_(
            ValetIncident.venue_id == venue_id,
            ValetIncident.created_at >= period_start,
            ValetIncident.created_at <= period_end
        )
    ).scalar() or 0

    # Capacity metrics (approximations based on sessions)
    peak_occupancy = max(
        (s.metadata.get("occupancy_snapshot", 0) for s in completed if s.metadata),
        default=0
    )

    # Get current capacity for avg calculation
    capacity = db.query(ValetCapacity).filter(
        ValetCapacity.venue_id == venue_id
    ).first()

    # Approximate average occupancy
    avg_occupancy = float(completed_sessions / 2) if completed_sessions > 0 else 0
    utilization_rate = (avg_occupancy / capacity.total_capacity) if capacity and capacity.total_capacity > 0 else 0

    return ValetMetricsResponse(
        venue_id=venue_id,
        period_start=period_start,
        period_end=period_end,
        total_sessions=total_sessions,
        completed_sessions=completed_sessions,
        cancelled_sessions=cancelled_sessions,
        no_shows=0,  # TODO: Track no-shows separately
        avg_parking_time_minutes=round(avg_parking_time, 2) if avg_parking_time else None,
        avg_retrieval_time_minutes=round(avg_retrieval_time, 2) if avg_retrieval_time else None,
        avg_wait_time_minutes=round(avg_wait_time, 2) if avg_wait_time else None,
        total_revenue=total_revenue,
        total_tips=total_tips,
        avg_session_value=avg_session_value,
        avg_rating=round(avg_rating, 2) if avg_rating else None,
        total_ratings=total_ratings,
        incident_count=incident_count,
        peak_occupancy=peak_occupancy,
        avg_occupancy=round(avg_occupancy, 2),
        utilization_rate=round(utilization_rate, 2)
    )


@router.post("/sessions/{session_id}/payment/retry", response_model=dict)
def retry_failed_payment(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retry failed payment for a session.

    Attempts to reprocess a payment that previously failed.
    Use cases:
    - Payment gateway timeout
    - Insufficient funds (after customer adds funds)
    - Network error during original transaction

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, db=db)

    # Get session
    session = db.query(ValetSession).filter(ValetSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Valet session not found"
        )

    check_staff_permissions(current_user, session.venue_id, db)

    # Check if payment is needed
    payment_status = session.additional_metadata.get("payment_status") if session.additional_metadata else None
    if payment_status == "succeeded":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment has already succeeded for this session"
        )

    # Attempt payment retry
    payment_result = ValetService.process_payment(
        db=db,
        session_id=session_id,
        amount=session.total_price,
        payment_method=session.additional_metadata.get("payment_method", "card") if session.additional_metadata else "card"
    )

    # Update session metadata
    if payment_result["success"]:
        session.additional_metadata = session.additional_metadata or {}
        session.additional_metadata["payment_status"] = "succeeded"
        session.additional_metadata["payment_transaction_id"] = payment_result["transaction_id"]
        session.additional_metadata["payment_processed_at"] = payment_result["processed_at"].isoformat()
        session.additional_metadata["payment_retry_by"] = str(current_user.id)
        db.commit()

    return {
        "success": payment_result["success"],
        "session_id": str(session_id),
        "amount": float(payment_result["amount"]),
        "transaction_id": payment_result["transaction_id"],
        "message": "Payment processed successfully" if payment_result["success"] else "Payment failed"
    }


@router.post("/sessions/{session_id}/refund", response_model=dict)
def process_refund(
    session_id: UUID,
    amount: Optional[Decimal] = Query(None, description="Refund amount (defaults to full amount)"),
    reason: str = Query(..., description="Reason for refund"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Process refund for a completed session.

    Issues a full or partial refund for a valet session.
    Common reasons:
    - Service quality issue
    - Customer complaint
    - Operational error
    - Goodwill gesture

    Requires admin approval for refunds over certain thresholds.

    Requires: venue_admin or super_admin role (elevated permissions)
    """
    # Check admin permissions for refunds
    if current_user.role not in [UserRole.VENUE_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required to process refunds"
        )

    # Get session
    session = db.query(ValetSession).filter(ValetSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Valet session not found"
        )

    check_staff_permissions(current_user, session.venue_id, db)

    # Validate session is completed
    if session.status != ValetStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only refund completed sessions"
        )

    # Check if payment exists
    payment_status = session.additional_metadata.get("payment_status") if session.additional_metadata else None
    if payment_status != "succeeded":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No successful payment found for this session"
        )

    # Check if already refunded
    if session.additional_metadata.get("refund_status") == "refunded":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session has already been refunded"
        )

    # Determine refund amount
    refund_amount = amount or session.total_price

    # Validate refund amount
    if refund_amount > session.total_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Refund amount cannot exceed total price of ${session.total_price}"
        )

    if refund_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refund amount must be greater than 0"
        )

    # TODO: Integrate with payment processor to issue actual refund
    # For now, simulate refund processing
    refund_id = f"refund_{session.id.hex[:16]}"

    # Update session metadata
    session.additional_metadata = session.additional_metadata or {}
    session.additional_metadata["refund_status"] = "refunded"
    session.additional_metadata["refund_amount"] = float(refund_amount)
    session.additional_metadata["refund_reason"] = reason
    session.additional_metadata["refund_id"] = refund_id
    session.additional_metadata["refund_processed_by"] = str(current_user.id)
    session.additional_metadata["refund_processed_at"] = datetime.utcnow().isoformat()

    # Add to internal notes
    refund_note = f"[REFUND PROCESSED by {current_user.first_name} {current_user.last_name}] Amount: ${refund_amount}, Reason: {reason}"
    if session.internal_notes:
        session.internal_notes += f"\n{refund_note}"
    else:
        session.internal_notes = refund_note

    db.commit()

    return {
        "success": True,
        "session_id": str(session_id),
        "refund_id": refund_id,
        "amount": float(refund_amount),
        "original_amount": float(session.total_price),
        "reason": reason,
        "processed_by": f"{current_user.first_name} {current_user.last_name}",
        "processed_at": datetime.utcnow().isoformat(),
        "message": f"Refund of ${refund_amount} processed successfully"
    }


@router.get("/sessions/search", response_model=List[ValetSearchResult])
def search_sessions(
    query: str = Query(..., min_length=2, description="Search query (plate, phone, name)"),
    venue_id: Optional[UUID] = Query(None, description="Filter by venue"),
    status_filter: Optional[ValetSessionStatus] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search valet sessions by plate, phone, or customer name.

    Search query matches against:
    - Vehicle license plate (partial match)
    - Customer phone number
    - Customer name (first or last)

    Useful for quickly finding sessions at check-out or when
    customers can't locate their ticket.

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, db=db)

    # Normalize search query
    search_query = query.strip().upper()

    # Build base query
    sessions_query = db.query(ValetSession)

    # Apply venue filter if provided
    if venue_id:
        check_staff_permissions(current_user, venue_id, db)
        sessions_query = sessions_query.filter(ValetSession.venue_id == venue_id)

    # Apply status filter
    if status_filter:
        sessions_query = sessions_query.filter(ValetSession.status == status_filter.value)
    else:
        # Default: exclude cancelled and completed from over 24 hours ago
        cutoff = datetime.utcnow() - timedelta(hours=24)
        sessions_query = sessions_query.filter(
            or_(
                ValetSession.status.notin_([ValetStatus.CANCELLED.value, ValetStatus.COMPLETED.value]),
                and_(
                    ValetSession.status.in_([ValetStatus.CANCELLED.value, ValetStatus.COMPLETED.value]),
                    ValetSession.updated_at >= cutoff
                )
            )
        )

    # Search by plate, phone, or join with user for name search
    search_conditions = [
        ValetSession.vehicle_plate.ilike(f"%{search_query}%"),
        ValetSession.contact_phone.ilike(f"%{search_query}%"),
    ]

    sessions_query = sessions_query.filter(or_(*search_conditions))

    # Order by most recent first
    sessions_query = sessions_query.order_by(desc(ValetSession.created_at))

    # Limit results
    sessions = sessions_query.limit(limit).all()

    # Build search results
    results = []
    for session in sessions:
        # Get customer name
        customer_name = None
        if session.user_id:
            user = db.query(User).filter(User.id == session.user_id).first()
            if user:
                customer_name = f"{user.first_name} {user.last_name}"

        # Build vehicle info
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

        # Parse parking location
        parking_loc = None
        if session.parking_location:
            parking_loc = ParkingLocation(notes=session.parking_location)

        results.append(ValetSearchResult(
            id=session.id,
            vehicle_plate=session.vehicle_plate,
            vehicle_info=vehicle_info,
            customer_name=customer_name,
            customer_phone=session.contact_phone,
            status=ValetSessionStatus(session.status),
            parking_location=parking_loc,
            checked_in_at=session.check_in_time
        ))

    return results


def _build_valet_session_response(session: ValetSession, db: Session) -> ValetSessionResponse:
    """Build ValetSessionResponse with key management info."""
    # Get lot name
    lot_name = session.parking_lot.name if session.parking_lot else "Unknown"

    # Build key management info if keys are assigned
    key_management = None
    if session.key_tag_number:
        storage_location = None
        if session.key_storage_zone:
            storage_location = KeyStorageLocation(
                zone=session.key_storage_zone,
                box=session.key_storage_box,
                position=session.key_storage_position
            )

        assigned_by_name = None
        if session.key_assigned_by:
            assigned_by_name = f"{session.key_assigned_by.first_name} {session.key_assigned_by.last_name}"

        grabbed_by_name = None
        if session.key_grabbed_by:
            grabbed_by_name = f"{session.key_grabbed_by.first_name} {session.key_grabbed_by.last_name}"

        key_management = KeyManagement(
            key_tag_number=session.key_tag_number,
            storage_location=storage_location,
            key_status=session.key_status,
            key_photo_url=session.key_photo_url,
            key_notes=session.key_notes,
            assigned_by=assigned_by_name,
            assigned_at=session.key_assigned_at,
            grabbed_by=grabbed_by_name,
            grabbed_at=session.key_grabbed_at
        )

    return ValetSessionResponse(
        id=session.id,
        ticket_number=session.ticket_number,
        venue_id=session.venue_id,
        status=session.status,
        service_type=session.service_type,
        vehicle_plate=session.vehicle_plate,
        vehicle_make=session.vehicle_make,
        vehicle_model=session.vehicle_model,
        vehicle_color=session.vehicle_color,
        vehicle_year=session.vehicle_year,
        check_in_time=session.check_in_time,
        parked_time=session.parked_time,
        retrieval_requested_time=session.retrieval_requested_time,
        ready_time=session.ready_time,
        check_out_time=session.check_out_time,
        base_price=session.base_price,
        tip=session.tip,
        total_price=session.total_price,
        contact_phone=session.contact_phone,
        contact_email=session.contact_email,
        pin=session.pin,
        parking_section=session.parking_section,
        parking_level=session.parking_level,
        parking_spot=session.parking_spot,
        created_at=session.created_at,
        updated_at=session.updated_at,
        key_management=key_management
    )


@router.post("/sessions/{session_id}/keys/assign", response_model=ValetSessionResponse)
def assign_keys_to_session(
    session_id: UUID,
    key_data: KeyAssignmentInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Assign keys to storage location for valet session.

    Records the key tag number and storage location (zone/box/position).
    Validates that the key tag is not already assigned to another active session.

    Key tag format: 3-digit numeric (001-999)

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, db=db)

    # Get session to verify venue access
    session = db.query(ValetSession).filter(ValetSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Valet session not found"
        )

    check_staff_permissions(current_user, session.venue_id, db)

    # Assign keys via service
    updated_session = ValetService.assign_keys(
        db=db,
        session_id=session_id,
        key_tag_number=key_data.key_tag_number,
        zone=key_data.zone,
        box=key_data.box,
        position=key_data.position,
        staff_user_id=current_user.id,
        key_photo_url=key_data.key_photo_url,
        key_notes=key_data.key_notes
    )

    # Build response with key management info
    return _build_valet_session_response(updated_session, db)


@router.post("/sessions/{session_id}/keys/grab", response_model=ValetSessionResponse)
def grab_keys_from_storage(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark keys as grabbed from storage for vehicle retrieval.

    Updates key status from 'in_storage' to 'grabbed' and records
    which staff member retrieved the keys and when.

    Used when valet attendant physically retrieves keys from the
    key storage location to go get the customer's vehicle.

    Requires: venue_staff, venue_admin, or super_admin role
    """
    check_staff_permissions(current_user, db=db)

    # Get session to verify venue access
    session = db.query(ValetSession).filter(ValetSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Valet session not found"
        )

    check_staff_permissions(current_user, session.venue_id, db)

    # Mark keys as grabbed
    updated_session = ValetService.mark_keys_grabbed(
        db=db,
        session_id=session_id,
        staff_user_id=current_user.id
    )

    # Build response with key management info
    return _build_valet_session_response(updated_session, db)


@router.get("/storage-config/{venue_identifier}", response_model=KeyStorageConfigResponse)
def get_key_storage_configuration(
    venue_identifier: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get key storage configuration for venue with real-time occupancy.

    Returns the configured storage layout (zones, boxes, positions)
    along with which positions are currently occupied by active
    valet sessions.

    Used by the admin panel to display the key storage grid with
    visual indicators of occupied positions.

    Requires: venue_staff, venue_admin, or super_admin role

    venue_identifier can be either a UUID or a venue slug
    """
    # Resolve venue_identifier to UUID
    try:
        venue_id = UUID(venue_identifier)
    except ValueError:
        # Try to find venue by slug
        from app.models.venue import Venue
        venue = db.query(Venue).filter(Venue.slug == venue_identifier).first()
        if not venue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Venue not found with identifier: {venue_identifier}"
            )
        venue_id = venue.id

    check_staff_permissions(current_user, venue_id, db)

    # Get configuration with occupancy
    config_data = ValetService.get_storage_config(db, venue_id)

    return config_data


@router.put("/storage-config/{venue_identifier}", response_model=KeyStorageConfigResponse)
def update_key_storage_configuration(
    venue_identifier: str,
    config_update: KeyStorageConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update key storage configuration for venue.

    Allows venue administrators to configure their key storage layout,
    including defining zones, boxes, and positions.

    This is typically done once during initial setup and adjusted
    as needed when physical storage changes.

    Requires: venue_admin or super_admin role only

    venue_identifier can be either a UUID or a venue slug
    """
    # Resolve venue_identifier to UUID
    try:
        venue_id = UUID(venue_identifier)
    except ValueError:
        # Try to find venue by slug
        from app.models.venue import Venue
        venue = db.query(Venue).filter(Venue.slug == venue_identifier).first()
        if not venue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Venue not found with identifier: {venue_identifier}"
            )
        venue_id = venue.id

    # Check for admin-level permissions (not just staff)
    if current_user.role not in [UserRole.VENUE_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required to update storage configuration"
        )

    check_staff_permissions(current_user, venue_id, db)

    # Update configuration
    updated_config = ValetService.update_storage_config(
        db=db,
        venue_id=venue_id,
        zones=[zone.dict() for zone in config_update.zones]
    )

    # Return with occupancy data
    config_data = ValetService.get_storage_config(db, venue_id)

    return config_data
