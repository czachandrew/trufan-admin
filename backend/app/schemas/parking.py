from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal


# Parking Lot Schemas

class ParkingLotPublic(BaseModel):
    """Public parking lot information (no auth required)."""
    id: UUID
    name: str
    description: Optional[str] = None
    total_spaces: int
    available_spaces: int
    location_lat: Optional[Decimal] = None
    location_lng: Optional[Decimal] = None
    is_active: bool

    # Pricing configuration
    base_rate: Decimal
    hourly_rate: Decimal
    max_daily_rate: Decimal
    min_duration_minutes: int = 15
    max_duration_hours: int = 24
    dynamic_multiplier: Decimal = Decimal("1.0")

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_pricing(cls, lot):
        """Create from ORM model with pricing config."""
        pricing = lot.pricing_config or {}
        return cls(
            id=lot.id,
            name=lot.name,
            description=lot.description,
            total_spaces=lot.total_spaces,
            available_spaces=lot.available_spaces,
            location_lat=lot.location_lat,
            location_lng=lot.location_lng,
            is_active=lot.is_active,
            base_rate=Decimal(str(pricing.get("base_rate", 10.00))),
            hourly_rate=Decimal(str(pricing.get("hourly_rate", 5.00))),
            max_daily_rate=Decimal(str(pricing.get("max_daily", 50.00))),
            min_duration_minutes=pricing.get("min_duration_minutes", 15),
            max_duration_hours=pricing.get("max_duration_hours", 24),
            dynamic_multiplier=Decimal(str(pricing.get("dynamic_multiplier", 1.0))),
        )


class ParkingLotCreate(BaseModel):
    """Create a new parking lot."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    location_address: Optional[str] = Field(None, max_length=500)
    total_spaces: int = Field(..., gt=0, description="Total number of parking spaces")
    location_lat: Optional[Decimal] = None
    location_lng: Optional[Decimal] = None

    # Pricing configuration
    base_rate: Decimal = Field(..., gt=0, description="Base parking rate")
    hourly_rate: Decimal = Field(..., gt=0, description="Hourly parking rate")
    max_daily_rate: Optional[Decimal] = Field(None, gt=0, description="Maximum daily rate")
    min_duration_minutes: int = Field(15, ge=1, le=60)
    max_duration_hours: int = Field(24, ge=1, le=168)


class ParkingLotUpdate(BaseModel):
    """Update an existing parking lot."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    location_address: Optional[str] = Field(None, max_length=500)
    total_spaces: Optional[int] = Field(None, gt=0)
    location_lat: Optional[Decimal] = None
    location_lng: Optional[Decimal] = None
    is_active: Optional[bool] = None

    # Pricing configuration
    base_rate: Optional[Decimal] = Field(None, gt=0)
    hourly_rate: Optional[Decimal] = Field(None, gt=0)
    max_daily_rate: Optional[Decimal] = Field(None, gt=0)
    min_duration_minutes: Optional[int] = Field(None, ge=1, le=60)
    max_duration_hours: Optional[int] = Field(None, ge=1, le=168)


class ParkingSpaceInfo(BaseModel):
    """Information about a specific parking space."""
    space_number: str
    lot_id: UUID
    lot_name: str
    is_occupied: bool


# Parking Session Schemas

class VehicleInfo(BaseModel):
    """Vehicle information for parking session."""
    plate: str = Field(..., min_length=1, max_length=20, description="License plate number")
    make: Optional[str] = Field(None, max_length=50, description="Vehicle make (e.g., Toyota)")
    model: Optional[str] = Field(None, max_length=50, description="Vehicle model (e.g., Camry)")
    color: Optional[str] = Field(None, max_length=30, description="Vehicle color")

    @field_validator("plate")
    @classmethod
    def validate_plate(cls, v):
        """Validate and normalize license plate."""
        # Remove spaces and convert to uppercase
        return v.strip().upper().replace(" ", "")


class ParkingSessionCreate(BaseModel):
    """Create a new parking session (public - no auth)."""
    lot_id: UUID
    space_number: Optional[str] = Field(None, description="Specific space number (optional)")

    # Vehicle information
    vehicle_plate: str = Field(..., min_length=1, max_length=20)
    vehicle_make: Optional[str] = Field(None, max_length=50)
    vehicle_model: Optional[str] = Field(None, max_length=50)
    vehicle_color: Optional[str] = Field(None, max_length=30)

    # Duration in hours
    duration_hours: float = Field(..., gt=0, description="Parking duration in hours")

    # Contact info for notifications (at least one required)
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

    @field_validator("vehicle_plate")
    @classmethod
    def validate_plate(cls, v):
        """Validate and normalize license plate."""
        return v.strip().upper().replace(" ", "")

    @field_validator("contact_phone")
    @classmethod
    def validate_phone(cls, v):
        """Basic phone validation."""
        if v:
            # Remove common formatting characters
            phone = v.replace("-", "").replace("(", "").replace(")", "").replace(" ", "")
            if not phone.startswith("+"):
                phone = "+1" + phone  # Default to US
            return phone
        return v


class ParkingSessionResponse(BaseModel):
    """Parking session response."""
    id: UUID
    lot_id: UUID
    lot_name: str
    space_number: Optional[str]

    # Vehicle info
    vehicle_plate: str
    vehicle_make: Optional[str]
    vehicle_model: Optional[str]
    vehicle_color: Optional[str]

    # Session timing
    start_time: datetime
    expires_at: datetime
    end_time: Optional[datetime]

    # Pricing
    base_price: Decimal
    actual_price: Optional[Decimal]

    # Status
    status: str

    # Access code (for looking up session without auth)
    access_code: str

    created_at: datetime

    class Config:
        from_attributes = True


class ParkingSessionExtend(BaseModel):
    """Extend parking session."""
    additional_hours: float = Field(..., gt=0, le=24, description="Additional hours to add")
    access_code: str = Field(..., description="Session access code")


class ParkingSessionEnd(BaseModel):
    """End parking session early."""
    access_code: str = Field(..., description="Session access code")


class ParkingSessionLookup(BaseModel):
    """Look up parking session."""
    session_id: Optional[UUID] = None
    vehicle_plate: Optional[str] = None
    access_code: Optional[str] = None


# Payment Simulation

class PaymentSimulation(BaseModel):
    """Simulate payment for parking session."""
    session_id: UUID
    amount: Decimal
    payment_method: str = "simulated"
    should_succeed: bool = True  # For testing failures


class PaymentResponse(BaseModel):
    """Payment response."""
    payment_id: UUID
    session_id: UUID
    amount: Decimal
    status: str
    message: str


# Notification Schemas

class ExpirationNotification(BaseModel):
    """Notification for expiring session."""
    session_id: UUID
    vehicle_plate: str
    lot_name: str
    expires_at: datetime
    minutes_until_expiry: int
    extend_url: str
