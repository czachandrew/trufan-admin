from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from enum import Enum


# Enums

class OpportunityTypeEnum(str, Enum):
    """Types of opportunities."""
    EXPERIENCE = "experience"
    CONVENIENCE = "convenience"
    DISCOVERY = "discovery"
    SERVICE = "service"
    BUNDLE = "bundle"


class InteractionTypeEnum(str, Enum):
    """Types of user interactions."""
    IMPRESSED = "impressed"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"
    COMPLETED = "completed"
    EXPIRED = "expired"


class FrequencyPreferenceEnum(str, Enum):
    """Frequency preferences."""
    ALL = "all"
    OCCASIONAL = "occasional"
    MINIMAL = "minimal"


# Partner Schemas

class PartnerBase(BaseModel):
    """Base partner schema."""
    business_name: str = Field(..., min_length=1, max_length=200)
    business_type: Optional[str] = Field(None, max_length=50)
    contact_email: str = Field(..., max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    location_lat: Optional[Decimal] = None
    location_lng: Optional[Decimal] = None


class PartnerCreate(PartnerBase):
    """Create a new partner."""
    webhook_url: Optional[str] = None
    billing_email: Optional[str] = None
    commission_rate: Decimal = Field(Decimal("0.15"), ge=0, le=1)
    max_active_opportunities: int = Field(10, ge=1, le=100)


class PartnerUpdate(BaseModel):
    """Update partner information."""
    business_name: Optional[str] = Field(None, min_length=1, max_length=200)
    business_type: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    location_lat: Optional[Decimal] = None
    location_lng: Optional[Decimal] = None
    webhook_url: Optional[str] = None
    billing_email: Optional[str] = None
    is_active: Optional[bool] = None


class PartnerResponse(PartnerBase):
    """Partner response schema."""
    id: UUID
    stripe_account_id: Optional[str] = None
    commission_rate: Decimal
    auto_approve_opportunities: bool
    max_active_opportunities: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Opportunity Schemas

class OpportunityBase(BaseModel):
    """Base opportunity schema."""
    title: str = Field(..., min_length=1, max_length=100)
    value_proposition: str = Field(..., min_length=1)
    opportunity_type: OpportunityTypeEnum
    trigger_rules: Dict[str, Any] = Field(default_factory=dict)
    valid_from: datetime
    valid_until: datetime
    availability_schedule: Optional[Dict[str, Any]] = None
    total_capacity: Optional[int] = Field(None, ge=1)
    value_details: Dict[str, Any]
    location_lat: Optional[Decimal] = None
    location_lng: Optional[Decimal] = None
    address: Optional[str] = None
    walking_distance_meters: Optional[int] = Field(None, ge=0)


class OpportunityCreate(OpportunityBase):
    """Create a new opportunity."""
    partner_id: UUID
    max_impressions_per_user: int = Field(3, ge=1, le=10)
    cooldown_hours: int = Field(24, ge=1, le=168)
    priority_score: int = Field(50, ge=1, le=100)

    @field_validator('valid_until')
    @classmethod
    def validate_dates(cls, v, info):
        if 'valid_from' in info.data and v <= info.data['valid_from']:
            raise ValueError('valid_until must be after valid_from')
        return v

    @field_validator('value_details')
    @classmethod
    def validate_value_details(cls, v):
        """Ensure opportunity provides real value."""
        has_discount = (
            v.get('discount_percentage', 0) >= 10 or
            v.get('discount_amount', 0) >= 5
        )
        has_parking = v.get('parking_extension_minutes', 0) >= 15
        has_perks = len(v.get('perks', [])) > 0

        if not (has_discount or has_parking or has_perks):
            raise ValueError(
                'Opportunity must provide meaningful value: '
                '10%+ discount, $5+ discount, 15+ min parking, or perks'
            )
        return v


class OpportunityUpdate(BaseModel):
    """Update an opportunity."""
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    value_proposition: Optional[str] = Field(None, min_length=1)
    opportunity_type: Optional[OpportunityTypeEnum] = None
    trigger_rules: Optional[Dict[str, Any]] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    availability_schedule: Optional[Dict[str, Any]] = None
    total_capacity: Optional[int] = Field(None, ge=1)
    value_details: Optional[Dict[str, Any]] = None
    location_lat: Optional[Decimal] = None
    location_lng: Optional[Decimal] = None
    address: Optional[str] = None
    walking_distance_meters: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    priority_score: Optional[int] = Field(None, ge=1, le=100)


class OpportunityResponse(OpportunityBase):
    """Opportunity response for users."""
    id: UUID
    partner_id: UUID
    used_capacity: int
    priority_score: int
    is_active: bool
    is_approved: bool
    created_at: datetime
    calculated_distance: Optional[int] = None  # Calculated based on user location

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_distance(cls, opportunity, user_lat: Optional[float] = None, user_lng: Optional[float] = None):
        """Create from ORM with calculated distance."""
        distance = None
        if user_lat and user_lng and opportunity.location_lat and opportunity.location_lng:
            # Simple distance calculation (Haversine would be more accurate)
            import math
            lat_diff = float(opportunity.location_lat) - user_lat
            lng_diff = float(opportunity.location_lng) - user_lng
            distance = int(math.sqrt(lat_diff**2 + lng_diff**2) * 111000)  # Rough meters

        return cls(
            id=opportunity.id,
            partner_id=opportunity.partner_id,
            title=opportunity.title,
            value_proposition=opportunity.value_proposition,
            opportunity_type=opportunity.opportunity_type,
            trigger_rules=opportunity.trigger_rules,
            valid_from=opportunity.valid_from,
            valid_until=opportunity.valid_until,
            availability_schedule=opportunity.availability_schedule,
            total_capacity=opportunity.total_capacity,
            used_capacity=opportunity.used_capacity,
            value_details=opportunity.value_details,
            location_lat=opportunity.location_lat,
            location_lng=opportunity.location_lng,
            address=opportunity.address,
            walking_distance_meters=opportunity.walking_distance_meters,
            priority_score=opportunity.priority_score,
            is_active=opportunity.is_active,
            is_approved=opportunity.is_approved,
            created_at=opportunity.created_at,
            calculated_distance=distance
        )


# Interaction Schemas

class OpportunityAccept(BaseModel):
    """Accept an opportunity."""
    parking_session_id: UUID


class OpportunityDismiss(BaseModel):
    """Dismiss an opportunity."""
    reason: str = Field(..., max_length=50)
    feedback: Optional[str] = Field(None, max_length=500)


class OpportunityComplete(BaseModel):
    """Complete/redeem an opportunity."""
    claim_code: str = Field(..., min_length=1, max_length=20)
    partner_confirmation: Optional[str] = None


class OpportunityAcceptResponse(BaseModel):
    """Response when user accepts an opportunity."""
    success: bool
    claim_code: str
    instructions: str
    valid_until: datetime
    parking_extended_by: Optional[int] = None  # Minutes if parking was extended


class InteractionContext(BaseModel):
    """Context of an interaction."""
    parking_time_remaining: Optional[int] = None  # Minutes
    user_location: Optional[Dict[str, float]] = None
    distance_from_opportunity: Optional[int] = None  # Meters
    time_of_day: Optional[str] = None
    weather: Optional[str] = None
    dismiss_reason: Optional[str] = None


class OpportunityInteractionResponse(BaseModel):
    """Interaction history response."""
    id: UUID
    opportunity_id: UUID
    interaction_type: InteractionTypeEnum
    interaction_context: Optional[Dict[str, Any]] = None
    value_claimed: Optional[Dict[str, Any]] = None
    value_redeemed: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Preferences Schemas

class OpportunityPreferencesUpdate(BaseModel):
    """Update user preferences."""
    opportunities_enabled: Optional[bool] = None
    frequency_preference: Optional[FrequencyPreferenceEnum] = None
    max_per_session: Optional[int] = Field(None, ge=0, le=10)
    quiet_hours: Optional[List[Dict[str, str]]] = None
    no_opportunity_days: Optional[List[str]] = None
    preferred_categories: Optional[List[str]] = None
    blocked_categories: Optional[List[str]] = None
    blocked_partner_ids: Optional[List[UUID]] = None
    max_walking_distance_meters: Optional[int] = Field(None, ge=0, le=5000)


class OpportunityPreferencesResponse(BaseModel):
    """User preferences response."""
    user_id: UUID
    opportunities_enabled: bool
    frequency_preference: str
    max_per_session: int
    quiet_hours: List[Dict[str, str]]
    no_opportunity_days: List[str]
    preferred_categories: List[str]
    blocked_categories: List[str]
    blocked_partner_ids: List[UUID]
    max_walking_distance_meters: int
    updated_at: datetime

    class Config:
        from_attributes = True


# Analytics Schemas

class OpportunityAnalyticsResponse(BaseModel):
    """Analytics response for partners."""
    period: Dict[str, date]
    engagement: Dict[str, Any]
    value: Dict[str, Decimal]


class PartnerAnalyticsRequest(BaseModel):
    """Request analytics for a date range."""
    date_start: date
    date_end: date
    granularity: str = Field("daily", pattern="^(hourly|daily)$")


# Partner API Validation

class ValidateClaimCode(BaseModel):
    """Validate a user's claim code."""
    claim_code: str = Field(..., min_length=1, max_length=20)


class ClaimCodeValidationResponse(BaseModel):
    """Claim code validation response."""
    valid: bool
    opportunity_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    value_details: Optional[Dict[str, Any]] = None
    claimed_at: Optional[datetime] = None
    message: str
