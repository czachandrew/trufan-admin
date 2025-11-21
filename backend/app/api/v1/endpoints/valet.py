from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.valet import SavedVehicle
from app.schemas.valet import (
    ValetSessionCreate,
    ValetSessionResponse,
    ValetSessionCheckin,
    ValetRetrievalRequest,
    ValetRating,
    ValetAvailability,
    ValetHistory,
    SavedVehicleCreate,
    SavedVehicleResponse,
)
from app.services.valet_service import ValetService

router = APIRouter()


@router.post("/sessions", response_model=ValetSessionResponse, status_code=status.HTTP_201_CREATED)
def create_valet_session(
    session_data: ValetSessionCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Create a new valet booking.

    Creates a valet session with vehicle information and generates a unique ticket number
    and PIN for verification. The session starts in PENDING status until customer checks in.

    Requirements:
    - Vehicle plate number (required)
    - At least one contact method (email or phone)
    - Venue must have available capacity

    Returns:
    - Complete session details with ticket number and access code
    - Ticket number and PIN for customer verification
    - Estimated pricing information

    Authentication:
    - Optional - if authenticated, session will be linked to user account
    - If not authenticated, contact information must be provided
    """
    user_id = current_user.id if current_user else None
    return ValetService.create_valet_session(db, session_data, user_id)


@router.post("/sessions/{session_id}/checkin", response_model=ValetSessionResponse)
def checkin_valet_session(
    session_id: UUID,
    checkin_data: ValetSessionCheckin,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    User check-in on arrival at venue.

    This endpoint allows customers to check in when they arrive at the venue.
    The valet attendant will verify the vehicle and ticket information during this process.

    Requirements:
    - Valid session ID
    - Session must be in PENDING status
    - User must be authenticated and own the session

    Process:
    1. Customer arrives at venue
    2. Provides ticket number and PIN to valet attendant
    3. Valet verifies information and checks in customer
    4. Keys are handed over to valet
    5. Session status changes to CHECKED_IN

    Authentication:
    - Required - user must own the session or be venue staff
    """
    # Verify user owns the session or is staff
    session = ValetService.get_session(db, session_id=session_id)

    if current_user.role not in ["super_admin", "venue_admin", "venue_staff"]:
        if not session or session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only check in your own valet sessions"
            )

    # For customer self-check-in, we need to get the PIN from metadata
    # In practice, this would be done by the valet attendant with the ticket and PIN
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Check-in must be performed by valet attendant with ticket number and PIN"
    )


@router.post("/sessions/{session_id}/request-retrieval", response_model=dict)
def request_vehicle_retrieval(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Request car retrieval.

    Notifies valet staff that the customer is ready to leave and needs their vehicle retrieved.
    Calculates estimated time for vehicle retrieval based on service type and queue length.

    Requirements:
    - Session must be in PARKED status
    - User must own the session

    Process:
    1. Customer requests retrieval (typically 10-15 minutes before leaving)
    2. System calculates ETA based on:
       - Service type (standard, VIP, premium)
       - Current retrieval queue length
       - Parking location distance
    3. Valet staff receives notification
    4. Customer receives ETA
    5. Session status changes to RETRIEVAL_REQUESTED

    Returns:
    - Updated session details
    - Estimated retrieval time in minutes
    - Estimated ready time (datetime)

    Authentication:
    - Required - user must own the session
    """
    # Verify user owns the session
    session = ValetService.get_session(db, session_id=session_id)

    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only request retrieval for your own valet sessions"
        )

    return ValetService.request_retrieval(
        db,
        session_id=session_id,
        user_id=current_user.id
    )


@router.post("/sessions/{session_id}/cancel-request", response_model=ValetSessionResponse)
def cancel_retrieval_request(
    session_id: UUID,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cancel vehicle retrieval request.

    Allows customer to cancel their retrieval request if their plans change.
    Vehicle remains parked and can be requested again later.

    Requirements:
    - Session must be in RETRIEVAL_REQUESTED or RETRIEVING status
    - User must own the session

    Use cases:
    - Customer decides to stay longer
    - Plans changed, not leaving yet
    - Requested too early by mistake

    Process:
    1. Customer cancels retrieval request
    2. Valet staff notified to stop retrieval
    3. Session status returns to PARKED
    4. Customer can request retrieval again when ready

    Authentication:
    - Required - user must own the session
    """
    # Verify user owns the session
    session = ValetService.get_session(db, session_id=session_id)

    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel retrieval for your own valet sessions"
        )

    return ValetService.cancel_retrieval_request(
        db,
        session_id=session_id,
        user_id=current_user.id,
        reason=reason
    )


@router.get("/sessions/{session_id}", response_model=ValetSessionResponse)
def get_valet_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get valet session details.

    Retrieves complete information about a valet session including:
    - Current status and location
    - Vehicle information
    - Timeline of status changes
    - Pricing and payment details
    - Assigned valet staff
    - ETA information (if retrieval requested)

    The timeline shows the complete history of the session with timestamps
    for each status change and which staff member performed the action.

    Authentication:
    - Required - user must own the session or be venue staff
    """
    session = ValetService.get_session(db, session_id=session_id, include_timeline=True)

    # Verify user owns the session or is staff
    if current_user.role not in ["super_admin", "venue_admin", "venue_staff"]:
        if not session or session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own valet sessions"
            )

    return session


@router.post("/sessions/{session_id}/rate", response_model=ValetSessionResponse)
def rate_valet_session(
    session_id: UUID,
    rating_data: ValetRating,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit rating and tip for valet service.

    Allows customers to rate their valet experience and add a tip after service completion.
    Ratings help maintain service quality and provide feedback to valet staff.

    Requirements:
    - Session must be in COMPLETED or READY status
    - User must own the session
    - Rating must be between 1-5 stars

    Rating Guidelines:
    - 5 stars: Excellent service, quick and professional
    - 4 stars: Good service, met expectations
    - 3 stars: Average service, acceptable
    - 2 stars: Below average, some issues
    - 1 star: Poor service, significant problems

    The feedback field is optional but encouraged for:
    - Exceptional service (5 stars) - what made it great?
    - Poor service (1-2 stars) - what went wrong?

    Tips are optional and go directly to the valet staff who served you.

    Authentication:
    - Required - user must own the session
    """
    # Verify user owns the session
    session = ValetService.get_session(db, session_id=session_id)

    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only rate your own valet sessions"
        )

    # Verify session_id matches
    if rating_data.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session ID mismatch"
        )

    return ValetService.rate_and_tip(
        db,
        session_id=session_id,
        rating=rating_data.rating,
        tip_amount=rating_data.tip_amount,
        feedback=rating_data.feedback,
        user_id=current_user.id
    )


@router.get("/sessions/history", response_model=ValetHistory)
def get_valet_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get user's valet history.

    Retrieves a paginated list of all valet sessions for the authenticated user.
    Shows both active and completed sessions with summary information.

    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page, max 100 (default: 20)
    - status_filter: Filter by status (optional)
      - "pending": Bookings not yet checked in
      - "checked_in": Currently being parked
      - "parked": Vehicle parked, can request retrieval
      - "retrieval_requested": Retrieval in progress
      - "completed": Service completed
      - "cancelled": Cancelled bookings

    Each history item includes:
    - Venue name and location
    - Vehicle information
    - Service dates and times
    - Total cost
    - Rating (if provided)

    Use cases:
    - View past valet services
    - Track active sessions
    - Review service history for receipts
    - Find previous vehicles used

    Authentication:
    - Required - returns only user's own sessions
    """
    return ValetService.get_user_history(
        db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status_filter=status_filter
    )


@router.get("/venues/{venue_id}/availability", response_model=ValetAvailability)
def check_valet_availability(
    venue_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Check valet availability at venue.

    Public endpoint that provides real-time valet service availability information
    for a specific venue. No authentication required.

    Returns:
    - Whether valet service is currently accepting new customers
    - Current capacity and utilization
    - Estimated wait time for parking
    - Pricing information
    - Operating hours
    - Special notices or restrictions

    This endpoint is typically called:
    - When user scans venue QR code
    - Before creating a valet booking
    - To check if valet service is available
    - To see current wait times

    Capacity Information:
    - current_capacity: Number of vehicles currently parked
    - max_capacity: Total parking capacity
    - is_available: Whether accepting new bookings
    - estimated_wait_minutes: How long until vehicle is parked

    Pricing shows the base rate and estimated total for standard service.
    Actual pricing may vary based on:
    - Service type selected (standard, VIP, premium)
    - Duration of parking
    - Special event pricing
    - Tips (optional)

    Authentication:
    - Not required - public endpoint for mobile app
    """
    return ValetService.get_venue_availability(db, venue_id)


@router.post("/vehicles/save", response_model=SavedVehicleResponse, status_code=status.HTTP_201_CREATED)
def save_vehicle(
    vehicle_data: SavedVehicleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save vehicle to user profile.

    Allows users to save their vehicle information for faster future bookings.
    Saved vehicles auto-populate booking forms, reducing time and errors.

    Features:
    - Save multiple vehicles
    - Set one as default (auto-selected for bookings)
    - Update vehicle information
    - Reuse for future valet sessions

    Fields:
    - plate: License plate (required, normalized to uppercase)
    - make: Vehicle make (optional, e.g., "Toyota")
    - model: Vehicle model (optional, e.g., "Camry")
    - color: Vehicle color (optional, helps valet identify)
    - year: Vehicle year (optional)
    - is_default: Set as default vehicle (optional)

    If is_default is true, any existing default vehicle will be unmarked.

    Benefits:
    - Faster booking process
    - Consistent vehicle information
    - Helpful for users with multiple vehicles
    - Reduces input errors

    Authentication:
    - Required - vehicle saved to user's profile
    """
    # Check if vehicle with this plate already exists for user
    existing = db.query(SavedVehicle).filter(
        SavedVehicle.user_id == current_user.id,
        SavedVehicle.vehicle_plate == vehicle_data.plate
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehicle with this plate number already saved"
        )

    # If setting as default, unmark other defaults
    if vehicle_data.is_default:
        db.query(SavedVehicle).filter(
            SavedVehicle.user_id == current_user.id,
            SavedVehicle.is_default == True
        ).update({"is_default": False})

    # Create saved vehicle
    saved_vehicle = SavedVehicle(
        user_id=current_user.id,
        vehicle_plate=vehicle_data.plate,
        vehicle_make=vehicle_data.make or "",
        vehicle_model=vehicle_data.model or "",
        vehicle_color=vehicle_data.color or "",
        vehicle_year=vehicle_data.year,
        is_default=vehicle_data.is_default
    )

    db.add(saved_vehicle)
    db.commit()
    db.refresh(saved_vehicle)

    return saved_vehicle


@router.get("/vehicles", response_model=List[SavedVehicleResponse])
def get_saved_vehicles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get user's saved vehicles.

    Retrieves all vehicles saved to the user's profile, ordered with
    default vehicle first.

    Returns:
    - List of saved vehicles
    - Default vehicle marked with is_default=true
    - Vehicle details (plate, make, model, color, year)
    - Created date for each vehicle

    The default vehicle is automatically selected when creating new bookings.

    Use cases:
    - Display vehicle list in booking form
    - Allow user to select from saved vehicles
    - Manage saved vehicles (view, edit, delete)
    - Pre-populate booking forms

    Authentication:
    - Required - returns only user's saved vehicles
    """
    vehicles = db.query(SavedVehicle).filter(
        SavedVehicle.user_id == current_user.id
    ).order_by(
        SavedVehicle.is_default.desc(),
        SavedVehicle.created_at.desc()
    ).all()

    return vehicles
