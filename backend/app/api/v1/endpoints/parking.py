from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_optional
from app.models.user import User
from app.models.parking import ParkingLot, ParkingSpace
from app.schemas.parking import (
    ParkingLotPublic,
    ParkingLotCreate,
    ParkingLotUpdate,
    ParkingSessionCreate,
    ParkingSessionResponse,
    ParkingSessionExtend,
    ParkingSessionEnd,
    PaymentSimulation,
    PaymentResponse,
)
from app.services.parking_service import ParkingService

router = APIRouter()


@router.get("/lots", response_model=List[ParkingLotPublic])
def get_available_parking_lots(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Get available parking lots.

    Public endpoint - no authentication required for mobile app.

    When authenticated:
    - venue_admin: Returns only their own lots
    - super_admin: Returns all lots
    - Not authenticated: Returns all lots (for public mobile app)
    """
    # Get all lots
    lots = ParkingService.get_available_parking_lots(db)

    # Filter by ownership for venue_admin users
    if current_user and current_user.role == "venue_admin":
        # Only show lots owned by this user
        filtered_lots = []
        for lot in lots:
            # Get the full lot from database to check owner_id
            full_lot = db.query(ParkingLot).filter(ParkingLot.id == lot.id).first()
            if full_lot and full_lot.owner_id == current_user.id:
                filtered_lots.append(lot)
        return filtered_lots

    # Super admin or unauthenticated - show all lots
    return lots


@router.get("/lots/{lot_id}", response_model=ParkingLotPublic)
def get_parking_lot(lot_id: str, db: Session = Depends(get_db)):
    """
    Get details for a specific parking lot.

    Public endpoint - no authentication required.
    Used when scanning a QR code for a specific lot.
    """
    lot = ParkingService.get_parking_lot(db, lot_id)
    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parking lot not found",
        )
    return lot


@router.post("/lots", response_model=ParkingLotPublic, status_code=status.HTTP_201_CREATED)
def create_parking_lot(
    lot_data: ParkingLotCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new parking lot.

    Requires authentication (admin only).
    """
    # Check user has permission (admin only)
    if current_user.role not in ["super_admin", "venue_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create parking lots"
        )

    # Build pricing configuration
    pricing_config = {
        "base_rate": float(lot_data.base_rate),
        "hourly_rate": float(lot_data.hourly_rate),
        "max_daily": float(lot_data.max_daily_rate) if lot_data.max_daily_rate else None,
        "min_duration_minutes": lot_data.min_duration_minutes,
        "max_duration_hours": lot_data.max_duration_hours,
        "dynamic_multiplier": 1.0,
    }

    # Create parking lot
    new_lot = ParkingLot(
        name=lot_data.name,
        description=lot_data.description,
        location_address=lot_data.location_address,
        total_spaces=lot_data.total_spaces,
        available_spaces=lot_data.total_spaces,  # Initially all spaces available
        location_lat=lot_data.location_lat,
        location_lng=lot_data.location_lng,
        pricing_config=pricing_config,
        is_active=True,
        owner_id=current_user.id,  # Set the owner to the creating user
    )

    db.add(new_lot)
    db.commit()
    db.refresh(new_lot)

    # Return using the from_orm_with_pricing method
    return ParkingLotPublic.from_orm_with_pricing(new_lot)


@router.put("/lots/{lot_id}", response_model=ParkingLotPublic)
def update_parking_lot(
    lot_id: UUID,
    lot_data: ParkingLotUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing parking lot.

    Requires authentication (admin only).
    Supports partial updates - only provided fields will be updated.

    venue_admin can only update their own lots.
    super_admin can update any lot.
    """
    # Check user has permission (admin only)
    if current_user.role not in ["super_admin", "venue_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update parking lots"
        )

    # Get existing lot
    lot = db.query(ParkingLot).filter(ParkingLot.id == lot_id).first()
    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parking lot not found"
        )

    # venue_admin can only update their own lots
    if current_user.role == "venue_admin" and lot.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own parking lots"
        )

    # Update basic fields if provided
    update_data = lot_data.dict(exclude_unset=True)

    # Extract pricing fields
    pricing_fields = ["base_rate", "hourly_rate", "max_daily_rate", "min_duration_minutes", "max_duration_hours"]
    pricing_updates = {}

    for field in pricing_fields:
        if field in update_data:
            value = update_data.pop(field)
            # Map to pricing_config keys
            if field == "max_daily_rate":
                pricing_updates["max_daily"] = float(value) if value else None
            else:
                pricing_updates[field] = float(value) if isinstance(value, Decimal) else value

    # Update pricing_config if any pricing fields were provided
    if pricing_updates:
        current_pricing = lot.pricing_config or {}
        current_pricing.update(pricing_updates)
        lot.pricing_config = current_pricing
        # Mark JSONB field as modified for SQLAlchemy
        flag_modified(lot, "pricing_config")

    # Update remaining basic fields
    for key, value in update_data.items():
        setattr(lot, key, value)

    db.commit()
    db.refresh(lot)

    return ParkingLotPublic.from_orm_with_pricing(lot)


@router.get("/lots/{lot_id}/spaces", response_model=List[dict])
def get_lot_spaces(
    lot_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all parking spaces for a specific lot.

    Requires authentication (admin/operator only).
    Returns space details with current occupancy status.
    """
    # Check user has permission
    if current_user.role not in ["super_admin", "venue_admin", "venue_staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view spaces"
        )

    # Verify lot exists
    lot = db.query(ParkingLot).filter(ParkingLot.id == lot_id).first()
    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parking lot not found"
        )

    # Get all spaces for this lot
    spaces = db.query(ParkingSpace).filter(ParkingSpace.lot_id == lot_id).all()

    # Build response with occupancy info
    response = []
    for space in spaces:
        response.append({
            "id": str(space.id),
            "space_number": space.space_number,
            "space_type": space.space_type,
            "is_occupied": space.is_occupied,
            "is_active": space.is_active,
            "created_at": space.created_at.isoformat(),
        })

    return response


@router.get("/sessions", response_model=List[ParkingSessionResponse])
def list_parking_sessions(
    lot_id: Optional[str] = Query(None, description="Filter by parking lot ID"),
    status_filter: Optional[str] = Query(None, description="Filter by status (active, completed, expired, cancelled)"),
    start_date: Optional[datetime] = Query(None, description="Filter sessions starting after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter sessions starting before this date"),
    vehicle_plate: Optional[str] = Query(None, description="Filter by vehicle plate (partial match)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List parking sessions with filtering and pagination.

    Requires authentication (admin/operator only).

    Filters:
    - lot_id: Filter by specific parking lot
    - status: Filter by session status (active, completed, expired, cancelled)
    - start_date/end_date: Filter by date range
    - vehicle_plate: Search by license plate (partial match)
    - limit/offset: Pagination
    """
    from app.models.parking import ParkingSession

    # Check user has permission (admin or operator)
    if current_user.role not in ["super_admin", "venue_admin", "venue_staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view sessions"
        )

    # Build query
    query = db.query(ParkingSession)

    # Apply filters
    if lot_id:
        query = query.filter(ParkingSession.lot_id == lot_id)

    if status_filter:
        query = query.filter(ParkingSession.status == status_filter)

    if start_date:
        query = query.filter(ParkingSession.start_time >= start_date)

    if end_date:
        query = query.filter(ParkingSession.start_time <= end_date)

    if vehicle_plate:
        # Normalize and search
        normalized_plate = vehicle_plate.strip().upper().replace(" ", "")
        query = query.filter(ParkingSession.vehicle_plate.ilike(f"%{normalized_plate}%"))

    # Order by most recent first
    query = query.order_by(ParkingSession.created_at.desc())

    # Paginate
    sessions = query.offset(offset).limit(limit).all()

    # Convert to response models with lot names
    response_sessions = []
    for session in sessions:
        # Get lot name
        lot_name = session.parking_lot.name if session.parking_lot else "Unknown"

        # Create response
        session_response = ParkingSessionResponse(
            id=session.id,
            lot_id=session.lot_id,
            lot_name=lot_name,
            space_number=session.space.space_number if session.space else None,
            vehicle_plate=session.vehicle_plate,
            vehicle_make=session.vehicle_make,
            vehicle_model=session.vehicle_model,
            vehicle_color=session.vehicle_color,
            start_time=session.start_time,
            expires_at=session.expires_at,
            end_time=session.end_time,
            base_price=session.base_price,
            actual_price=session.actual_price,
            status=session.status,
            access_code=session.access_code,
            created_at=session.created_at,
        )
        response_sessions.append(session_response)

    return response_sessions


@router.post("/sessions", response_model=ParkingSessionResponse, status_code=status.HTTP_201_CREATED)
def create_parking_session(
    session_data: ParkingSessionCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new parking session.

    Public endpoint - no authentication required.

    Requirements:
    - Vehicle plate number (required)
    - Duration in hours (required)
    - At least one contact method (email or phone)
    - Optional: specific space number

    Returns an access code that can be used to look up and manage the session.
    """
    return ParkingService.create_parking_session(db, session_data)


@router.get("/sessions/{access_code}", response_model=ParkingSessionResponse)
def get_parking_session(access_code: str, db: Session = Depends(get_db)):
    """
    Look up parking session by access code.

    Public endpoint - no authentication required.

    The access code is provided when creating the session and can be used
    to look up session details, extend parking time, or end the session early.
    """
    session = ParkingService.get_session_by_access_code(db, access_code)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parking session not found",
        )
    return session


@router.post("/sessions/{access_code}/extend", response_model=ParkingSessionResponse)
def extend_parking_session(
    access_code: str,
    extend_data: ParkingSessionExtend,
    db: Session = Depends(get_db),
):
    """
    Extend parking session by additional hours.

    Public endpoint - no authentication required.
    Requires the access code from the original session.

    Additional charges will be calculated based on the lot's hourly rate.
    """
    # Verify access code matches
    if extend_data.access_code.upper() != access_code.upper():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access code mismatch",
        )

    return ParkingService.extend_parking_session(
        db, access_code, extend_data.additional_hours
    )


@router.post("/sessions/{access_code}/end", response_model=ParkingSessionResponse)
def end_parking_session(
    access_code: str,
    end_data: ParkingSessionEnd,
    db: Session = Depends(get_db),
):
    """
    End parking session early.

    Public endpoint - no authentication required.
    Requires the access code from the original session.

    Frees up the parking space immediately.
    """
    # Verify access code matches
    if end_data.access_code.upper() != access_code.upper():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access code mismatch",
        )

    return ParkingService.end_parking_session(db, access_code)


@router.post("/payments/simulate", response_model=PaymentResponse)
def simulate_payment(
    payment_data: PaymentSimulation,
    db: Session = Depends(get_db),
):
    """
    Simulate payment processing for a parking session.

    Public endpoint - no authentication required.

    This is a temporary endpoint for testing payment flows without Stripe.
    Set `should_succeed: false` to test payment failure scenarios.

    Once payment succeeds, the session status changes from 'pending_payment' to 'active'.
    """
    return ParkingService.simulate_payment(db, payment_data)


@router.post("/testing/create-nearby-lot", response_model=ParkingLotPublic, status_code=status.HTTP_201_CREATED)
def create_test_lot_nearby(
    latitude: float = Query(..., description="User's current latitude"),
    longitude: float = Query(..., description="User's current longitude"),
    db: Session = Depends(get_db),
):
    """
    Create a test parking lot near the provided coordinates.

    TESTING ENDPOINT - For internal testing only.

    This endpoint allows testers to create a parking lot within ~0.5 miles
    of their current location for proximity testing.

    The lot will be created with:
    - Random offset from provided location (0.002-0.005 degrees, ~200-500m)
    - Realistic pricing
    - 100 total spaces
    - Active status
    """
    import random
    import uuid

    # Create random offset (0.002-0.005 degrees = ~200-500 meters)
    lat_offset = random.uniform(0.002, 0.005) * random.choice([-1, 1])
    lng_offset = random.uniform(0.002, 0.005) * random.choice([-1, 1])

    test_lot_lat = latitude + lat_offset
    test_lot_lng = longitude + lng_offset

    # Generate random test lot name
    lot_number = random.randint(1, 999)
    test_lot_name = f"Test Parking Lot #{lot_number}"

    # Get or create a test venue
    from app.models.venue import Venue
    test_venue = db.query(Venue).filter(Venue.name == "Test Venue").first()

    if not test_venue:
        test_venue = Venue(
            id=str(uuid.uuid4()),
            name="Test Venue",
            address={
                "street": "123 Test Street",
                "city": "Test City",
                "state": "TS",
                "zipCode": "00000",
                "country": "USA"
            },
            settings={
                "parkingEnabled": True,
                "valetEnabled": True,
                "convenienceStoreEnabled": True
            }
        )
        db.add(test_venue)
        db.flush()

    # Create pricing configuration
    pricing_config = {
        "hourlyRate": f"{random.uniform(3.0, 8.0):.2f}",
        "dailyMax": f"{random.uniform(25.0, 50.0):.2f}",
        "eventRate": f"{random.uniform(15.0, 35.0):.2f}"
    }

    # Create the test parking lot
    new_lot = ParkingLot(
        id=str(uuid.uuid4()),
        name=test_lot_name,
        venue_id=test_venue.id,
        capacity=100,
        available_spaces=100,
        location={
            "latitude": test_lot_lat,
            "longitude": test_lot_lng
        },
        pricing=pricing_config,
        is_public=True,
        is_active=True,
        address={
            "street": f"{random.randint(100, 999)} Test Ave",
            "city": "Test City",
            "state": "TS",
            "zipCode": "00000"
        }
    )

    db.add(new_lot)
    db.commit()
    db.refresh(new_lot)

    return new_lot
