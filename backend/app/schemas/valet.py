from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from enum import Enum


# Enums

class ValetSessionStatus(str, Enum):
    """Valet session status."""
    REQUESTED = "requested"  # Initial booking request
    CONFIRMED = "confirmed"  # Booking confirmed
    CHECKED_IN = "checked_in"  # Customer arrived, keys handed over
    PARKED = "parked"  # Vehicle parked
    RETRIEVAL_REQUESTED = "retrieval_requested"  # Customer requested retrieval
    RETRIEVING = "retrieving"  # Valet retrieving vehicle
    READY = "ready"  # Vehicle ready for pickup
    COMPLETED = "completed"  # Session completed
    CANCELLED = "cancelled"  # Session cancelled
    NO_SHOW = "no_show"  # Customer did not show up


class ValetStaffStatus(str, Enum):
    """Valet staff status."""
    AVAILABLE = "available"
    BUSY = "busy"
    ON_BREAK = "break"
    OFF_DUTY = "off_duty"


class ValetIncidentType(str, Enum):
    """Types of valet incidents."""
    DAMAGE = "damage"  # Vehicle damage
    DELAY = "delay"  # Service delay
    COMPLAINT = "complaint"  # Customer complaint
    SAFETY = "safety"  # Safety incident
    OTHER = "other"


class ValetPriorityLevel(str, Enum):
    """Priority level for valet requests."""
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# Common Schemas

class ParkingLocation(BaseModel):
    """Information about parking location."""
    section: Optional[str] = Field(None, max_length=50, description="Parking section (e.g., 'A', 'B')")
    level: Optional[str] = Field(None, max_length=20, description="Parking level/floor (e.g., 'P1', 'Ground')")
    spot_number: Optional[str] = Field(None, max_length=20, description="Specific spot number")
    notes: Optional[str] = Field(None, max_length=500, description="Additional location notes")

    class Config:
        from_attributes = True


class VehicleInfo(BaseModel):
    """Vehicle information for valet service."""
    plate: str = Field(..., min_length=1, max_length=20, description="License plate number")
    make: Optional[str] = Field(None, max_length=50, description="Vehicle make (e.g., Toyota)")
    model: Optional[str] = Field(None, max_length=50, description="Vehicle model (e.g., Camry)")
    color: Optional[str] = Field(None, max_length=30, description="Vehicle color")
    year: Optional[int] = Field(None, ge=1900, le=2100, description="Vehicle year")
    notes: Optional[str] = Field(None, max_length=500, description="Special notes (e.g., scratches, modifications)")

    @field_validator("plate")
    @classmethod
    def validate_plate(cls, v):
        """Validate and normalize license plate."""
        return v.strip().upper().replace(" ", "")


class StatusEvent(BaseModel):
    """Timeline event for status changes."""
    status: ValetSessionStatus
    timestamp: datetime
    notes: Optional[str] = None
    staff_id: Optional[UUID] = None
    staff_name: Optional[str] = None

    class Config:
        from_attributes = True


class PaymentInfo(BaseModel):
    """Payment information for valet session."""
    amount: Decimal = Field(..., ge=0, description="Payment amount")
    tip: Optional[Decimal] = Field(None, ge=0, description="Tip amount")
    payment_method: Optional[str] = Field(None, max_length=50, description="Payment method")
    transaction_id: Optional[str] = Field(None, max_length=100, description="Payment transaction ID")
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PricingInfo(BaseModel):
    """Pricing information for valet service."""
    base_rate: Decimal = Field(..., ge=0, description="Base valet service rate")
    hourly_rate: Optional[Decimal] = Field(None, ge=0, description="Hourly rate for extended parking")
    estimated_total: Decimal = Field(..., ge=0, description="Estimated total cost")
    actual_total: Optional[Decimal] = Field(None, ge=0, description="Actual total cost")
    currency: str = Field(default="USD", max_length=3, description="Currency code")

    class Config:
        from_attributes = True


# User-facing Schemas

class ValetSessionCreate(BaseModel):
    """Create a new valet session (booking request)."""
    venue_id: UUID
    event_id: Optional[UUID] = Field(None, description="Associated event (if applicable)")

    # Vehicle information
    vehicle_plate: str = Field(..., min_length=1, max_length=20)
    vehicle_make: Optional[str] = Field(None, max_length=50)
    vehicle_model: Optional[str] = Field(None, max_length=50)
    vehicle_color: Optional[str] = Field(None, max_length=30)
    vehicle_year: Optional[int] = Field(None, ge=1900, le=2100)
    vehicle_notes: Optional[str] = Field(None, max_length=500)

    # Timing
    arrival_time: Optional[datetime] = Field(None, description="Expected arrival time")
    estimated_duration_hours: Optional[float] = Field(None, gt=0, le=48, description="Estimated parking duration")

    # Contact info
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=20)

    # Special requests
    special_requests: Optional[str] = Field(None, max_length=1000, description="Special handling requests")

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
            phone = v.replace("-", "").replace("(", "").replace(")", "").replace(" ", "")
            if not phone.startswith("+"):
                phone = "+1" + phone  # Default to US
            return phone
        return v


class ValetSessionCheckin(BaseModel):
    """Check in for valet service (customer arrival)."""
    session_id: UUID
    actual_arrival_time: Optional[datetime] = Field(None, description="Actual arrival time")
    vehicle_condition_notes: Optional[str] = Field(None, max_length=1000, description="Vehicle condition on arrival")


class ValetRetrievalRequest(BaseModel):
    """Request vehicle retrieval."""
    session_id: Optional[UUID] = None
    access_code: Optional[str] = Field(None, description="Session access code (alternative to session_id)")
    estimated_pickup_time: Optional[datetime] = Field(None, description="When customer expects to pick up")
    priority: ValetPriorityLevel = Field(default=ValetPriorityLevel.NORMAL, description="Request priority")


class ValetRating(BaseModel):
    """Rate valet service and add tip."""
    session_id: UUID
    rating: int = Field(..., ge=1, le=5, description="Service rating (1-5 stars)")
    tip_amount: Optional[Decimal] = Field(None, ge=0, description="Tip amount")
    feedback: Optional[str] = Field(None, max_length=1000, description="Additional feedback")


class SavedVehicleCreate(BaseModel):
    """Save vehicle information for future use."""
    plate: str = Field(..., min_length=1, max_length=20)
    make: Optional[str] = Field(None, max_length=50)
    model: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=30)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    is_default: bool = Field(default=False, description="Set as default vehicle")

    @field_validator("plate")
    @classmethod
    def validate_plate(cls, v):
        """Validate and normalize license plate."""
        return v.strip().upper().replace(" ", "")


class SavedVehicleResponse(BaseModel):
    """Saved vehicle response."""
    id: UUID
    user_id: UUID
    plate: str
    make: Optional[str]
    model: Optional[str]
    color: Optional[str]
    year: Optional[int]
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Key Management Schemas (moved here for forward reference resolution)

class KeyStorageLocation(BaseModel):
    """Key storage location details."""
    zone: str
    zone_name: Optional[str] = None
    box: str
    box_label: Optional[str] = None
    position: str

    class Config:
        from_attributes = True


class KeyManagement(BaseModel):
    """Key management information for valet session."""
    key_tag_number: Optional[str] = None
    storage_location: Optional[KeyStorageLocation] = None
    key_status: Optional[str] = None  # with_customer, with_valet, in_storage, grabbed, returned
    key_photo_url: Optional[str] = None
    key_notes: Optional[str] = None
    assigned_by: Optional[str] = None  # Staff member name
    assigned_at: Optional[datetime] = None
    grabbed_by: Optional[str] = None  # Staff member name
    grabbed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ValetSessionResponse(BaseModel):
    """Full valet session details."""
    id: UUID
    venue_id: UUID
    venue_name: str
    event_id: Optional[UUID]
    user_id: Optional[UUID]

    # Vehicle info
    vehicle_plate: str
    vehicle_make: Optional[str]
    vehicle_model: Optional[str]
    vehicle_color: Optional[str]
    vehicle_year: Optional[int]

    # Status
    status: ValetSessionStatus
    priority: ValetPriorityLevel

    # Timing
    requested_at: datetime
    arrival_time: Optional[datetime]
    checked_in_at: Optional[datetime]
    parked_at: Optional[datetime]
    retrieval_requested_at: Optional[datetime]
    ready_at: Optional[datetime]
    completed_at: Optional[datetime]

    # Location
    parking_location: Optional[ParkingLocation]

    # Pricing
    pricing: PricingInfo
    payment: Optional[PaymentInfo]

    # Staff
    assigned_valet_id: Optional[UUID]
    assigned_valet_name: Optional[str]

    # Access
    access_code: str

    # Key Management
    key_management: Optional[KeyManagement] = None

    # Timeline
    timeline: List[StatusEvent] = []

    # Rating
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ValetAvailability(BaseModel):
    """Valet service availability at venue."""
    venue_id: UUID
    venue_name: str
    is_available: bool
    current_capacity: int
    max_capacity: int
    estimated_wait_minutes: Optional[int] = None
    pricing: PricingInfo
    operating_hours: Optional[Dict[str, Any]] = None
    special_notes: Optional[str] = None


class ValetHistoryItem(BaseModel):
    """Summary of valet session for history list."""
    id: UUID
    venue_name: str
    vehicle_plate: str
    vehicle_info: Optional[str] = None  # "2020 Toyota Camry"
    status: ValetSessionStatus
    arrival_time: Optional[datetime]
    completed_at: Optional[datetime]
    total_cost: Optional[Decimal]
    rating: Optional[int]

    class Config:
        from_attributes = True


class ValetHistory(BaseModel):
    """List of valet sessions for user."""
    sessions: List[ValetHistoryItem]
    total: int
    page: int
    page_size: int


# Staff-facing Schemas

class ValetQueueItem(BaseModel):
    """Single item in valet queue."""
    session_id: UUID
    vehicle_plate: str
    vehicle_info: Optional[str] = None  # "2020 Toyota Camry - Red"
    customer_name: Optional[str] = None
    status: ValetSessionStatus
    priority: ValetPriorityLevel
    arrival_time: Optional[datetime]
    wait_time_minutes: Optional[int] = None
    parking_location: Optional[ParkingLocation]
    assigned_valet_id: Optional[UUID]
    assigned_valet_name: Optional[str]
    special_requests: Optional[str] = None

    class Config:
        from_attributes = True


class ValetQueueResponse(BaseModel):
    """Full valet queue for staff dashboard."""
    pending_checkins: List[ValetQueueItem] = []  # Confirmed but not checked in
    active_parking: List[ValetQueueItem] = []  # Being parked
    parked: List[ValetQueueItem] = []  # Currently parked
    pending_retrievals: List[ValetQueueItem] = []  # Retrieval requested
    active_retrievals: List[ValetQueueItem] = []  # Being retrieved
    total_active: int
    available_capacity: int


class ValetStatusUpdate(BaseModel):
    """Update valet session status (staff action)."""
    session_id: UUID
    new_status: ValetSessionStatus
    notes: Optional[str] = Field(None, max_length=1000, description="Status change notes")
    parking_location: Optional[ParkingLocation] = None
    estimated_ready_time: Optional[datetime] = None


class ValetIncidentCreate(BaseModel):
    """Report an incident during valet service."""
    session_id: UUID
    incident_type: ValetIncidentType
    severity: str = Field(..., pattern="^(low|medium|high|critical)$", description="Incident severity")
    description: str = Field(..., min_length=10, max_length=2000, description="Detailed incident description")
    reported_by: UUID = Field(..., description="Staff member reporting the incident")
    photos: Optional[List[str]] = Field(None, description="URLs to incident photos")
    action_taken: Optional[str] = Field(None, max_length=1000, description="Actions taken to resolve")


class ValetIncidentResponse(BaseModel):
    """Incident report response."""
    id: UUID
    session_id: UUID
    incident_type: ValetIncidentType
    severity: str
    description: str
    reported_by: UUID
    reported_by_name: Optional[str]
    reported_at: datetime
    photos: Optional[List[str]]
    action_taken: Optional[str]
    resolved: bool
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class ValetCapacityResponse(BaseModel):
    """Current capacity information."""
    venue_id: UUID
    venue_name: str
    total_capacity: int
    current_occupancy: int
    available_spaces: int
    utilization_percentage: float
    active_sessions: int
    pending_retrievals: int
    staff_available: int
    staff_busy: int


class ValetMetricsResponse(BaseModel):
    """Valet service metrics for reporting."""
    venue_id: UUID
    period_start: datetime
    period_end: datetime

    # Volume metrics
    total_sessions: int
    completed_sessions: int
    cancelled_sessions: int
    no_shows: int

    # Time metrics
    avg_parking_time_minutes: Optional[float] = None
    avg_retrieval_time_minutes: Optional[float] = None
    avg_wait_time_minutes: Optional[float] = None

    # Financial metrics
    total_revenue: Decimal
    total_tips: Decimal
    avg_session_value: Optional[Decimal] = None

    # Quality metrics
    avg_rating: Optional[float] = None
    total_ratings: int
    incident_count: int

    # Capacity metrics
    peak_occupancy: int
    avg_occupancy: float
    utilization_rate: float


class ValetSearchResult(BaseModel):
    """Search result for valet sessions."""
    id: UUID
    vehicle_plate: str
    vehicle_info: Optional[str]
    customer_name: Optional[str]
    customer_phone: Optional[str]
    status: ValetSessionStatus
    parking_location: Optional[ParkingLocation]
    checked_in_at: Optional[datetime]

    class Config:
        from_attributes = True


class ValetStaffUpdate(BaseModel):
    """Update staff status."""
    staff_id: UUID
    status: ValetStaffStatus
    notes: Optional[str] = Field(None, max_length=500)


class ValetStaffInfo(BaseModel):
    """Staff member information."""
    id: UUID
    name: str
    status: ValetStaffStatus
    current_session_id: Optional[UUID] = None
    sessions_today: int
    avg_rating: Optional[float] = None

    class Config:
        from_attributes = True


# Assignment Schemas

class ValetAssignment(BaseModel):
    """Assign valet to session."""
    session_id: UUID
    valet_id: UUID
    priority: ValetPriorityLevel = ValetPriorityLevel.NORMAL


class ValetReassignment(BaseModel):
    """Reassign session to different valet."""
    session_id: UUID
    new_valet_id: UUID
    reason: Optional[str] = Field(None, max_length=500)


# Lookup Schemas

class ValetSessionLookup(BaseModel):
    """Look up valet session by various identifiers."""
    session_id: Optional[UUID] = None
    access_code: Optional[str] = None
    vehicle_plate: Optional[str] = None
    phone: Optional[str] = None


# Notification Schemas

class ValetNotification(BaseModel):
    """Notification for valet service updates."""
    session_id: UUID
    notification_type: str = Field(..., description="Type of notification (ready, delayed, etc.)")
    message: str
    estimated_ready_time: Optional[datetime] = None
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None


# Additional Key Management Schemas

class KeyAssignmentInput(BaseModel):
    """Input for assigning keys to valet session."""
    key_tag_number: str = Field(..., pattern=r"^\d{3}$", description="3-digit numeric key tag (001-999)")
    zone: str = Field(..., min_length=1, max_length=50)
    box: str = Field(..., min_length=1, max_length=50)
    position: str = Field(..., min_length=1, max_length=20)
    key_photo_url: Optional[str] = None
    key_notes: Optional[str] = None


class KeyStorageBox(BaseModel):
    """Key storage box configuration."""
    id: str
    label: str
    positions: List[str]
    capacity: int


class KeyStorageZone(BaseModel):
    """Key storage zone configuration."""
    id: str
    name: str
    type: str  # main, overflow, vip
    boxes: List[KeyStorageBox]


class KeyStorageConfigResponse(BaseModel):
    """Key storage configuration response."""
    venue_id: UUID
    zones: List[KeyStorageZone]
    occupied_positions: Dict[str, List[str]] = {}  # zone_id -> [occupied positions]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class KeyStorageConfigUpdate(BaseModel):
    """Input for updating key storage configuration."""
    zones: List[KeyStorageZone]
