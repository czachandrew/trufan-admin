from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List
from uuid import uuid4
import secrets
import string
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.parking import ParkingLot, ParkingSpace, ParkingSession
from app.schemas.parking import (
    ParkingSessionCreate,
    ParkingSessionResponse,
    ParkingLotPublic,
    PaymentSimulation,
    PaymentResponse,
)
from fastapi import HTTPException, status


class ParkingService:
    """Service for managing parking sessions and spaces."""

    @staticmethod
    def _generate_access_code(length: int = 8) -> str:
        """Generate unique access code for parking session."""
        # Use uppercase letters and digits, exclude ambiguous characters (0, O, I, 1)
        alphabet = string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    def _calculate_parking_price(
        duration_hours: float,
        base_rate: Decimal,
        hourly_rate: Decimal,
        max_daily_rate: Decimal,
        dynamic_multiplier: Decimal = Decimal("1.0"),
    ) -> Decimal:
        """Calculate parking price based on duration and lot pricing config."""
        # Base calculation: base_rate + (hourly_rate * hours)
        hours_decimal = Decimal(str(duration_hours))
        calculated_price = base_rate + (hourly_rate * hours_decimal)

        # Apply dynamic pricing multiplier
        calculated_price *= dynamic_multiplier

        # Cap at max daily rate
        if calculated_price > max_daily_rate:
            calculated_price = max_daily_rate

        # Round to 2 decimal places
        return calculated_price.quantize(Decimal("0.01"))

    @staticmethod
    def get_available_parking_lots(db: Session) -> List[ParkingLotPublic]:
        """Get all active parking lots with available spaces."""
        lots = (
            db.query(ParkingLot)
            .filter(ParkingLot.is_active == True, ParkingLot.available_spaces > 0)
            .all()
        )

        return [ParkingLotPublic.from_orm_with_pricing(lot) for lot in lots]

    @staticmethod
    def get_parking_lot(db: Session, lot_id: str) -> Optional[ParkingLotPublic]:
        """Get specific parking lot by ID."""
        lot = db.query(ParkingLot).filter(ParkingLot.id == lot_id).first()
        if not lot:
            return None
        return ParkingLotPublic.from_orm_with_pricing(lot)

    @staticmethod
    def _find_available_space(db: Session, lot_id: str) -> Optional[ParkingSpace]:
        """Find an available parking space in the lot."""
        # Get an unoccupied space
        space = (
            db.query(ParkingSpace)
            .filter(
                and_(
                    ParkingSpace.lot_id == lot_id,
                    ParkingSpace.is_occupied == False,
                    ParkingSpace.is_active == True,
                )
            )
            .first()
        )
        return space

    @staticmethod
    def create_parking_session(
        db: Session, session_data: ParkingSessionCreate
    ) -> ParkingSessionResponse:
        """Create a new parking session."""
        # Validate parking lot exists and has space
        lot = db.query(ParkingLot).filter(ParkingLot.id == session_data.lot_id).first()
        if not lot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Parking lot not found"
            )

        if not lot.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parking lot is not active",
            )

        if lot.available_spaces <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No available spaces in this parking lot",
            )

        # Get pricing config
        pricing = lot.pricing_config or {}
        base_rate = Decimal(str(pricing.get("base_rate", 10.00)))
        hourly_rate = Decimal(str(pricing.get("hourly_rate", 5.00)))
        max_daily_rate = Decimal(str(pricing.get("max_daily", 50.00)))
        min_duration_minutes = pricing.get("min_duration_minutes", 15)
        max_duration_hours = pricing.get("max_duration_hours", 24)
        dynamic_multiplier = Decimal(str(pricing.get("dynamic_multiplier", 1.0)))

        # Validate duration
        if session_data.duration_hours * 60 < min_duration_minutes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Minimum parking duration is {min_duration_minutes} minutes",
            )

        if session_data.duration_hours > max_duration_hours:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum parking duration is {max_duration_hours} hours",
            )

        # Validate at least one contact method
        if not session_data.contact_email and not session_data.contact_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one contact method (email or phone) is required",
            )

        # Handle parking space assignment (optional)
        space = None
        if session_data.space_number:
            # Specific space requested - verify it exists and is available
            space = (
                db.query(ParkingSpace)
                .filter(
                    and_(
                        ParkingSpace.lot_id == session_data.lot_id,
                        ParkingSpace.space_number == session_data.space_number,
                    )
                )
                .first()
            )
            if not space:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parking space {session_data.space_number} not found",
                )
            if space.is_occupied:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parking space {session_data.space_number} is already occupied",
                )
        else:
            # Try to auto-assign a space (optional - lot-level parking is also supported)
            space = ParkingService._find_available_space(db, str(session_data.lot_id))

        # Calculate pricing
        base_price = ParkingService._calculate_parking_price(
            session_data.duration_hours,
            base_rate,
            hourly_rate,
            max_daily_rate,
            dynamic_multiplier,
        )

        # Calculate times
        start_time = datetime.utcnow()
        expires_at = start_time + timedelta(hours=session_data.duration_hours)

        # Generate unique access code
        access_code = ParkingService._generate_access_code()

        # Create parking session
        parking_session = ParkingSession(
            id=uuid4(),
            lot_id=session_data.lot_id,
            space_id=space.id if space else None,
            vehicle_plate=session_data.vehicle_plate,
            vehicle_make=session_data.vehicle_make,
            vehicle_model=session_data.vehicle_model,
            vehicle_color=session_data.vehicle_color,
            start_time=start_time,
            expires_at=expires_at,
            base_price=base_price,
            status="pending_payment",
            access_code=access_code,
            contact_email=session_data.contact_email,
            contact_phone=session_data.contact_phone,
        )

        db.add(parking_session)

        # Mark space as occupied
        if space:
            space.is_occupied = True

        # Decrement available spaces in lot
        lot.available_spaces -= 1

        db.commit()
        db.refresh(parking_session)

        # Build response
        return ParkingSessionResponse(
            id=parking_session.id,
            lot_id=parking_session.lot_id,
            lot_name=lot.name,
            space_number=space.space_number if space else None,
            vehicle_plate=parking_session.vehicle_plate,
            vehicle_make=parking_session.vehicle_make,
            vehicle_model=parking_session.vehicle_model,
            vehicle_color=parking_session.vehicle_color,
            start_time=parking_session.start_time,
            expires_at=parking_session.expires_at,
            end_time=parking_session.end_time,
            base_price=parking_session.base_price,
            actual_price=parking_session.actual_price,
            status=parking_session.status,
            access_code=parking_session.access_code,
            created_at=parking_session.created_at,
        )

    @staticmethod
    def simulate_payment(
        db: Session, payment_data: PaymentSimulation
    ) -> PaymentResponse:
        """Simulate payment processing for parking session."""
        # Get parking session
        session = (
            db.query(ParkingSession)
            .filter(ParkingSession.id == payment_data.session_id)
            .first()
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parking session not found",
            )

        if session.status != "pending_payment":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session is already {session.status}, cannot process payment",
            )

        # Simulate payment processing
        if payment_data.should_succeed:
            session.status = "active"
            session.actual_price = payment_data.amount
            payment_status = "completed"
            message = "Payment processed successfully (simulated)"
        else:
            session.status = "payment_failed"
            payment_status = "failed"
            message = "Payment failed (simulated)"

        db.commit()

        return PaymentResponse(
            payment_id=uuid4(),
            session_id=session.id,
            amount=payment_data.amount,
            status=payment_status,
            message=message,
        )

    @staticmethod
    def get_session_by_access_code(
        db: Session, access_code: str
    ) -> Optional[ParkingSessionResponse]:
        """Look up parking session by access code."""
        session = (
            db.query(ParkingSession)
            .filter(ParkingSession.access_code == access_code.upper())
            .first()
        )

        if not session:
            return None

        lot = db.query(ParkingLot).filter(ParkingLot.id == session.lot_id).first()
        space = (
            db.query(ParkingSpace).filter(ParkingSpace.id == session.space_id).first()
            if session.space_id
            else None
        )

        return ParkingSessionResponse(
            id=session.id,
            lot_id=session.lot_id,
            lot_name=lot.name if lot else "Unknown",
            space_number=space.space_number if space else None,
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

    @staticmethod
    def extend_parking_session(
        db: Session, access_code: str, additional_hours: float
    ) -> ParkingSessionResponse:
        """Extend parking session by additional hours."""
        session = (
            db.query(ParkingSession)
            .filter(ParkingSession.access_code == access_code.upper())
            .first()
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parking session not found",
            )

        if session.status not in ["active", "expiring_soon"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot extend session with status: {session.status}",
            )

        # Get lot pricing
        lot = db.query(ParkingLot).filter(ParkingLot.id == session.lot_id).first()
        pricing = lot.pricing_config or {}
        base_rate = Decimal(str(pricing.get("base_rate", 10.00)))
        hourly_rate = Decimal(str(pricing.get("hourly_rate", 5.00)))
        max_daily_rate = Decimal(str(pricing.get("max_daily", 50.00)))
        dynamic_multiplier = Decimal(str(pricing.get("dynamic_multiplier", 1.0)))

        # Calculate additional cost (no base rate, just hourly)
        additional_cost = ParkingService._calculate_parking_price(
            additional_hours,
            Decimal("0.00"),  # No base rate for extensions
            hourly_rate,
            max_daily_rate,
            dynamic_multiplier,
        )

        # Extend expiration time
        session.expires_at += timedelta(hours=additional_hours)

        # Update pricing
        current_price = session.actual_price or session.base_price
        session.actual_price = current_price + additional_cost

        # Update status if needed
        if session.status == "expiring_soon":
            session.status = "active"

        db.commit()
        db.refresh(session)

        space = (
            db.query(ParkingSpace).filter(ParkingSpace.id == session.space_id).first()
            if session.space_id
            else None
        )

        return ParkingSessionResponse(
            id=session.id,
            lot_id=session.lot_id,
            lot_name=lot.name,
            space_number=space.space_number if space else None,
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

    @staticmethod
    def end_parking_session(db: Session, access_code: str) -> ParkingSessionResponse:
        """End parking session early."""
        session = (
            db.query(ParkingSession)
            .filter(ParkingSession.access_code == access_code.upper())
            .first()
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parking session not found",
            )

        if session.status not in ["active", "expiring_soon", "pending_payment"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot end session with status: {session.status}",
            )

        # Update session
        session.end_time = datetime.utcnow()
        session.status = "completed"

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
        lot = db.query(ParkingLot).filter(ParkingLot.id == session.lot_id).first()
        if lot:
            lot.available_spaces += 1

        db.commit()
        db.refresh(session)

        space = (
            db.query(ParkingSpace).filter(ParkingSpace.id == session.space_id).first()
            if session.space_id
            else None
        )

        return ParkingSessionResponse(
            id=session.id,
            lot_id=session.lot_id,
            lot_name=lot.name if lot else "Unknown",
            space_number=space.space_number if space else None,
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

    @staticmethod
    def get_expiring_sessions(
        db: Session, minutes_threshold: int = 30
    ) -> List[ParkingSession]:
        """Get parking sessions that are expiring soon and need notification."""
        threshold_time = datetime.utcnow() + timedelta(minutes=minutes_threshold)

        sessions = (
            db.query(ParkingSession)
            .filter(
                and_(
                    ParkingSession.status == "active",
                    ParkingSession.expires_at <= threshold_time,
                    ParkingSession.expires_at > datetime.utcnow(),
                )
            )
            .all()
        )

        return sessions
