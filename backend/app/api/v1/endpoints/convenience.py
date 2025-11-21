"""
Customer API Endpoints for Convenience Store

This module provides customer-facing endpoints for browsing items,
placing orders, and managing their convenience store orders.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.convenience import (
    ConvenienceItemResponse,
    ConvenienceItemList,
    ConvenienceOrderCreate,
    ConvenienceOrderResponse,
    ConvenienceOrderList,
    ConvenienceOrderSummary,
    OrderCancelRequest,
    OrderRatingCreate,
    CategoriesResponse,
    ConvenienceStoreConfigResponse,
    ConvenienceItemCategory,
)
from app.services.convenience_service import (
    ConvenienceItemService,
    ConvenienceOrderService,
    ConvenienceConfigService,
)

router = APIRouter(tags=["convenience"])


# Browse Items Endpoints

@router.get("/venues/{venue_id}/items", response_model=ConvenienceItemList)
def browse_items(
    venue_id: UUID,
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Browse available convenience items at a venue.

    Returns only active items. Customers can filter by category and search by name/description.
    Public endpoint - no authentication required.
    """
    items, total = ConvenienceItemService.list_items(
        db=db,
        venue_id=venue_id,
        category=category,
        is_active=True,  # Only show active items to customers
        search=search,
        page=page,
        page_size=page_size
    )

    return ConvenienceItemList(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/venues/{venue_id}/items/{item_id}", response_model=ConvenienceItemResponse)
def get_item_details(
    venue_id: UUID,
    item_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific item.

    Public endpoint - no authentication required.
    """
    item = ConvenienceItemService.get_item(db=db, item_id=item_id)

    # Verify item belongs to venue
    if item.venue_id != venue_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    # Verify item is active
    if not item.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not available"
        )

    return item


@router.get("/venues/{venue_id}/categories", response_model=CategoriesResponse)
def get_venue_categories(
    venue_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get list of categories that have active items at this venue.

    Returns only categories with at least one active item.
    Public endpoint - no authentication required.
    """
    from sqlalchemy import func, distinct
    from app.models.convenience import ConvenienceItem

    # Get distinct categories with active items
    categories = db.query(distinct(ConvenienceItem.category)).filter(
        ConvenienceItem.venue_id == venue_id,
        ConvenienceItem.is_active == True,
        ConvenienceItem.category.isnot(None)
    ).all()

    category_list = [cat[0] for cat in categories if cat[0]]

    return CategoriesResponse(categories=category_list)


@router.get("/venues/{venue_id}/config", response_model=ConvenienceStoreConfigResponse)
def get_venue_info(
    venue_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get convenience store information for a venue.

    Returns configuration including operating hours, welcome message, etc.
    Useful for displaying store information to customers.

    Public endpoint - no authentication required.
    """
    config = ConvenienceConfigService.get_or_create_config(db=db, venue_id=venue_id)

    if not config.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Convenience store not available at this venue"
        )

    return config


# Order Management Endpoints

@router.post("/orders", response_model=ConvenienceOrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: ConvenienceOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new convenience order.

    Customers can order items from a venue. The order includes:
    - Line items with quantities
    - Calculated pricing (subtotal + service fee + tax)
    - Optional parking session association for time extension
    - Delivery and special instructions

    Validates:
    - All items exist and are active
    - Quantities don't exceed item limits
    - Order total meets minimum/maximum requirements

    Requires: Authenticated user
    """
    return ConvenienceOrderService.create_order(
        db=db,
        order_data=order_data,
        user_id=current_user.id
    )


@router.get("/orders/{order_id}", response_model=ConvenienceOrderResponse)
def get_order_details(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed information about a specific order.

    Includes full order details, line items, status timeline, and fulfillment information.
    Users can only view their own orders.

    Requires: Authenticated user
    """
    order = ConvenienceOrderService.get_order(db=db, order_id=order_id)

    # Verify order belongs to user
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own orders"
        )

    return order


@router.get("/my-orders", response_model=ConvenienceOrderList)
def get_my_orders(
    status: Optional[str] = Query(None, description="Filter by order status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Orders per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get list of current user's orders.

    Returns paginated list of orders with optional status filter.
    Ordered by creation date (newest first).

    Requires: Authenticated user
    """
    orders, total = ConvenienceOrderService.list_user_orders(
        db=db,
        user_id=current_user.id,
        status=status,
        page=page,
        page_size=page_size
    )

    # Convert to summary format
    summaries = []
    for order in orders:
        summaries.append(ConvenienceOrderSummary(
            id=order.id,
            order_number=order.order_number,
            venue_name=order.venue_name,
            status=order.status,
            total_amount=order.total_amount,
            item_count=len(order.items),
            estimated_ready_time=order.estimated_ready_time,
            created_at=order.created_at
        ))

    return ConvenienceOrderList(
        orders=summaries,
        total=total,
        page=page,
        page_size=page_size
    )


@router.patch("/orders/{order_id}/cancel", response_model=ConvenienceOrderResponse)
def cancel_order(
    order_id: UUID,
    cancel_data: OrderCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cancel an order.

    Customers can cancel orders that are pending, confirmed, or being shopped.
    Once items are purchased or stored, orders cannot be cancelled.

    A cancellation reason must be provided for tracking purposes.

    Requires: Authenticated user (order owner)
    """
    order = ConvenienceOrderService.get_order(db=db, order_id=order_id)

    # Verify order belongs to user
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own orders"
        )

    return ConvenienceOrderService.cancel_order(
        db=db,
        order_id=order_id,
        user_id=current_user.id,
        cancellation_reason=cancel_data.cancellation_reason
    )


@router.post("/orders/{order_id}/rate", response_model=ConvenienceOrderResponse)
def rate_order(
    order_id: UUID,
    rating_data: OrderRatingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Rate a completed order.

    Customers can rate delivered or completed orders on a scale of 1-5 stars.
    Optional feedback and tip can be provided.

    Tips are added to the order total and go to the fulfillment staff.

    Requires: Authenticated user (order owner)
    """
    order = ConvenienceOrderService.get_order(db=db, order_id=order_id)

    # Verify order belongs to user
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only rate your own orders"
        )

    return ConvenienceOrderService.rate_order(
        db=db,
        order_id=order_id,
        user_id=current_user.id,
        rating=rating_data.rating,
        feedback=rating_data.feedback,
        tip_amount=rating_data.tip_amount
    )
