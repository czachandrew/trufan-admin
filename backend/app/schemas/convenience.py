"""
Convenience Store Schemas

This module defines Pydantic schemas for the convenience store feature,
including request/response models for items, orders, and configuration.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from enum import Enum


# Enums

class ConvenienceItemCategory(str, Enum):
    """Product category for convenience items."""
    GROCERY = "grocery"
    FOOD = "food"
    BEVERAGE = "beverage"
    PERSONAL_CARE = "personal_care"
    ELECTRONICS = "electronics"
    OTHER = "other"


class ConvenienceOrderStatus(str, Enum):
    """Order status for convenience orders."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHOPPING = "shopping"
    PURCHASED = "purchased"
    STORED = "stored"
    READY = "ready"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Payment status for orders."""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    REFUNDED = "refunded"
    FAILED = "failed"


class OrderItemStatus(str, Enum):
    """Status for individual order items."""
    PENDING = "pending"
    FOUND = "found"
    NOT_FOUND = "not_found"
    SUBSTITUTED = "substituted"
    DELIVERED = "delivered"


# Item Schemas

class ConvenienceItemBase(BaseModel):
    """Base schema for convenience items."""
    name: str = Field(..., min_length=1, max_length=200, description="Item name")
    description: Optional[str] = Field(None, description="Item description")
    image_url: Optional[str] = Field(None, description="URL to item image")
    category: Optional[ConvenienceItemCategory] = Field(None, description="Item category")
    base_price: Decimal = Field(..., ge=0, description="Base price at store")
    markup_amount: Decimal = Field(default=Decimal("0"), ge=0, description="Fixed markup amount")
    markup_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100, description="Percentage markup")
    source_store: str = Field(..., min_length=1, max_length=200, description="Source store name")
    source_address: Optional[str] = Field(None, description="Store address")
    estimated_shopping_time_minutes: int = Field(default=15, ge=1, description="Estimated shopping time")
    requires_age_verification: bool = Field(default=False, description="Requires age verification")
    max_quantity_per_order: int = Field(default=10, ge=1, le=100, description="Max quantity per order")
    tags: Optional[List[str]] = Field(default=None, description="Item tags")
    sku: Optional[str] = Field(None, max_length=100, description="SKU")
    barcode: Optional[str] = Field(None, max_length=100, description="Barcode")


class ConvenienceItemCreate(ConvenienceItemBase):
    """Create a new convenience item."""
    venue_id: UUID


class ConvenienceItemUpdate(BaseModel):
    """Update an existing convenience item."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[ConvenienceItemCategory] = None
    base_price: Optional[Decimal] = Field(None, ge=0)
    markup_amount: Optional[Decimal] = Field(None, ge=0)
    markup_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    source_store: Optional[str] = Field(None, min_length=1, max_length=200)
    source_address: Optional[str] = None
    estimated_shopping_time_minutes: Optional[int] = Field(None, ge=1)
    requires_age_verification: Optional[bool] = None
    max_quantity_per_order: Optional[int] = Field(None, ge=1, le=100)
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)


class ConvenienceItemResponse(ConvenienceItemBase):
    """Response schema for convenience item."""
    id: UUID
    venue_id: UUID
    final_price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[UUID]

    class Config:
        from_attributes = True


class ConvenienceItemList(BaseModel):
    """List of convenience items with pagination."""
    items: List[ConvenienceItemResponse]
    total: int
    page: int
    page_size: int


# Order Item Schemas

class OrderItemCreate(BaseModel):
    """Create an order item."""
    item_id: UUID
    quantity: int = Field(..., ge=1, le=100, description="Quantity to order")


class OrderItemResponse(BaseModel):
    """Response schema for order item."""
    id: UUID
    order_id: UUID
    item_id: Optional[UUID]
    item_name: str
    item_description: Optional[str]
    item_image_url: Optional[str]
    source_store: Optional[str]
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    status: OrderItemStatus
    substitution_notes: Optional[str]
    actual_price: Optional[Decimal]
    created_at: datetime

    class Config:
        from_attributes = True


class OrderItemUpdateStatus(BaseModel):
    """Update order item status (staff)."""
    status: OrderItemStatus
    substitution_notes: Optional[str] = Field(None, description="Notes about substitution")
    actual_price: Optional[Decimal] = Field(None, ge=0, description="Actual price paid at store")


# Order Schemas

class ConvenienceOrderCreate(BaseModel):
    """Create a new convenience order."""
    venue_id: UUID
    items: List[OrderItemCreate] = Field(..., min_items=1, description="Items to order")
    parking_session_id: Optional[UUID] = Field(None, description="Associated parking session")
    delivery_instructions: Optional[str] = Field(None, max_length=1000, description="Delivery instructions")
    special_instructions: Optional[str] = Field(None, max_length=1000, description="Special instructions")

    @field_validator("items")
    @classmethod
    def validate_items(cls, v):
        """Ensure at least one item."""
        if not v or len(v) == 0:
            raise ValueError("At least one item is required")
        return v


# Order Event Schema (moved here for forward reference)
class OrderEventResponse(BaseModel):
    """Response schema for order event."""
    id: UUID
    order_id: UUID
    status: str
    notes: Optional[str]
    photo_url: Optional[str]
    location: Optional[str]
    created_by_id: Optional[UUID]
    created_by_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ConvenienceOrderResponse(BaseModel):
    """Response schema for convenience order."""
    id: UUID
    order_number: str
    venue_id: UUID
    venue_name: Optional[str] = None
    user_id: UUID
    parking_session_id: Optional[UUID]
    status: ConvenienceOrderStatus
    subtotal: Decimal
    service_fee: Decimal
    tax: Decimal
    tip_amount: Decimal
    total_amount: Decimal
    payment_status: PaymentStatus
    payment_method: Optional[str]
    assigned_staff_id: Optional[UUID]
    assigned_staff_name: Optional[str]
    storage_location: Optional[str]
    delivery_instructions: Optional[str]
    special_instructions: Optional[str]
    receipt_photo_url: Optional[str]
    delivery_photo_url: Optional[str]
    estimated_ready_time: Optional[datetime]
    confirmed_at: Optional[datetime]
    shopping_started_at: Optional[datetime]
    purchased_at: Optional[datetime]
    stored_at: Optional[datetime]
    ready_at: Optional[datetime]
    delivered_at: Optional[datetime]
    completed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    complimentary_time_added_minutes: int
    rating: Optional[int]
    feedback: Optional[str]
    cancellation_reason: Optional[str]
    refund_amount: Optional[Decimal]
    refund_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []
    events: List[OrderEventResponse] = []

    class Config:
        from_attributes = True


class ConvenienceOrderSummary(BaseModel):
    """Summary of convenience order for list views."""
    id: UUID
    order_number: str
    venue_name: Optional[str]
    status: ConvenienceOrderStatus
    total_amount: Decimal
    item_count: int
    estimated_ready_time: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ConvenienceOrderList(BaseModel):
    """List of convenience orders with pagination."""
    orders: List[ConvenienceOrderSummary]
    total: int
    page: int
    page_size: int


class OrderCancelRequest(BaseModel):
    """Request to cancel an order."""
    cancellation_reason: str = Field(..., min_length=1, max_length=500, description="Reason for cancellation")


class OrderRatingCreate(BaseModel):
    """Submit rating for completed order."""
    rating: int = Field(..., ge=1, le=5, description="Rating (1-5 stars)")
    feedback: Optional[str] = Field(None, max_length=1000, description="Optional feedback")
    tip_amount: Optional[Decimal] = Field(None, ge=0, description="Optional tip amount")


# Staff Fulfillment Schemas

class OrderAcceptRequest(BaseModel):
    """Accept an order for fulfillment."""
    estimated_ready_time: Optional[datetime] = Field(None, description="Estimated ready time")


class OrderStartShoppingRequest(BaseModel):
    """Start shopping for an order."""
    notes: Optional[str] = Field(None, max_length=500, description="Shopping notes")


class OrderCompleteShoppingRequest(BaseModel):
    """Complete shopping for an order."""
    receipt_photo_url: Optional[str] = Field(None, description="URL to receipt photo")
    notes: Optional[str] = Field(None, max_length=500, description="Shopping completion notes")


class OrderStoreRequest(BaseModel):
    """Store items at location."""
    storage_location: str = Field(..., min_length=1, max_length=100, description="Storage location")
    notes: Optional[str] = Field(None, max_length=500, description="Storage notes")


class OrderDeliverRequest(BaseModel):
    """Deliver order to customer."""
    delivery_photo_url: Optional[str] = Field(None, description="URL to delivery photo")
    notes: Optional[str] = Field(None, max_length=500, description="Delivery notes")


class OrderRefundRequest(BaseModel):
    """Request a refund for an order."""
    refund_amount: Decimal = Field(..., ge=0, description="Refund amount")
    refund_reason: str = Field(..., min_length=1, max_length=500, description="Refund reason")


# Configuration Schemas

class ConvenienceStoreConfigBase(BaseModel):
    """Base schema for convenience store configuration."""
    is_enabled: bool = Field(default=True, description="Feature enabled")
    default_service_fee_percent: Decimal = Field(default=Decimal("15.00"), ge=0, le=100, description="Default service fee %")
    minimum_order_amount: Decimal = Field(default=Decimal("5.00"), ge=0, description="Minimum order amount")
    maximum_order_amount: Decimal = Field(default=Decimal("200.00"), ge=0, description="Maximum order amount")
    default_complimentary_parking_minutes: int = Field(default=15, ge=0, description="Default complimentary parking minutes")
    average_fulfillment_time_minutes: int = Field(default=30, ge=1, description="Average fulfillment time")
    operating_hours: Optional[Dict[str, Any]] = Field(None, description="Operating hours by day")
    welcome_message: Optional[str] = Field(None, max_length=500, description="Welcome message")
    instructions_message: Optional[str] = Field(None, max_length=1000, description="Instructions message")
    storage_locations: Optional[List[str]] = Field(None, description="Available storage locations")


class ConvenienceStoreConfigCreate(ConvenienceStoreConfigBase):
    """Create convenience store configuration."""
    venue_id: UUID


class ConvenienceStoreConfigUpdate(BaseModel):
    """Update convenience store configuration."""
    is_enabled: Optional[bool] = None
    default_service_fee_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    minimum_order_amount: Optional[Decimal] = Field(None, ge=0)
    maximum_order_amount: Optional[Decimal] = Field(None, ge=0)
    default_complimentary_parking_minutes: Optional[int] = Field(None, ge=0)
    average_fulfillment_time_minutes: Optional[int] = Field(None, ge=1)
    operating_hours: Optional[Dict[str, Any]] = None
    welcome_message: Optional[str] = Field(None, max_length=500)
    instructions_message: Optional[str] = Field(None, max_length=1000)
    storage_locations: Optional[List[str]] = None


class ConvenienceStoreConfigResponse(ConvenienceStoreConfigBase):
    """Response schema for convenience store configuration."""
    id: UUID
    venue_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Bulk Import Schema

class ItemImportRow(BaseModel):
    """Single row for bulk item import."""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    base_price: Decimal
    markup_percent: Decimal = Decimal("0")
    source_store: str
    source_address: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None


class ItemBulkImportRequest(BaseModel):
    """Bulk import items."""
    items: List[ItemImportRow] = Field(..., min_items=1, description="Items to import")

    @field_validator("items")
    @classmethod
    def validate_items(cls, v):
        """Ensure at least one item."""
        if not v or len(v) == 0:
            raise ValueError("At least one item is required")
        return v


class ItemBulkImportResponse(BaseModel):
    """Response for bulk import."""
    success_count: int
    error_count: int
    errors: List[Dict[str, Any]] = []
    imported_items: List[ConvenienceItemResponse] = []


# Categories Response

class CategoriesResponse(BaseModel):
    """Available categories."""
    categories: List[str]


# Pricing Calculation

class PricingBreakdown(BaseModel):
    """Pricing breakdown for order."""
    subtotal: Decimal
    service_fee: Decimal
    tax: Decimal
    total: Decimal
