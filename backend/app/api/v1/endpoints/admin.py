"""
Admin API Endpoints

This module provides general admin endpoints for venue management and administration.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.venue import Venue, VenueStaff
from pydantic import BaseModel
from datetime import datetime


router = APIRouter()


# Response Schemas

class VenueResponse(BaseModel):
    """Response schema for venue details."""
    id: UUID
    name: str
    slug: str
    address_line1: str
    address_line2: str | None
    city: str
    state: str
    zip_code: str
    country: str
    phone: str
    email: str
    website: str | None
    description: str | None
    is_active: bool
    stripe_account_id: str | None
    configuration: dict | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VenueListResponse(BaseModel):
    """Response schema for list of venues."""
    venues: List[VenueResponse]
    total: int


# Endpoints

@router.get("/venues", response_model=VenueListResponse)
def get_admin_venues(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get list of venues that the current admin user has access to.

    - **SUPER_ADMIN**: Returns all venues
    - **VENUE_ADMIN**: Returns venues where user is the owner
    - **VENUE_STAFF**: Returns venues where user is associated as staff
    - **CUSTOMER**: Not authorized

    Returns:
        List of venues with pagination info
    """

    # Check if user has admin/staff role
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access admin venues"
        )

    # Super admins get all venues
    if current_user.role == UserRole.SUPER_ADMIN:
        venues = db.query(Venue).filter(Venue.is_active == True).all()
        return VenueListResponse(
            venues=venues,
            total=len(venues)
        )

    # Venue admins get venues they're associated with as admin/owner
    if current_user.role == UserRole.VENUE_ADMIN:
        # Get venue IDs from VenueStaff association
        venue_ids = db.query(VenueStaff.venue_id).filter(
            VenueStaff.user_id == current_user.id
        ).all()
        venue_ids = [v[0] for v in venue_ids]

        venues = db.query(Venue).filter(
            Venue.id.in_(venue_ids),
            Venue.is_active == True
        ).all()

        return VenueListResponse(
            venues=venues,
            total=len(venues)
        )

    # Venue staff get venues they're associated with
    if current_user.role == UserRole.VENUE_STAFF:
        # Get venue IDs from VenueStaff association
        venue_ids = db.query(VenueStaff.venue_id).filter(
            VenueStaff.user_id == current_user.id
        ).all()
        venue_ids = [v[0] for v in venue_ids]

        venues = db.query(Venue).filter(
            Venue.id.in_(venue_ids),
            Venue.is_active == True
        ).all()

        return VenueListResponse(
            venues=venues,
            total=len(venues)
        )

    # Fallback - no venues
    return VenueListResponse(venues=[], total=0)


@router.get("/venues/{venue_id}", response_model=VenueResponse)
def get_admin_venue(
    venue_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get details for a specific venue.

    User must have access to the venue (owner, staff, or super admin).

    Args:
        venue_id: UUID of the venue

    Returns:
        Venue details
    """

    # Check if user has admin/staff role
    if current_user.role == UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access venue details"
        )

    # Get venue
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Venue not found with ID: {venue_id}"
        )

    # Check access permissions
    has_access = False

    # Super admins have access to all venues
    if current_user.role == UserRole.SUPER_ADMIN:
        has_access = True

    # Venue admins can access venues they're associated with
    elif current_user.role == UserRole.VENUE_ADMIN:
        venue_staff = db.query(VenueStaff).filter(
            VenueStaff.user_id == current_user.id,
            VenueStaff.venue_id == venue_id
        ).first()
        if venue_staff:
            has_access = True

    # Venue staff can access venues they're associated with
    elif current_user.role == UserRole.VENUE_STAFF:
        venue_staff = db.query(VenueStaff).filter(
            VenueStaff.user_id == current_user.id,
            VenueStaff.venue_id == venue_id
        ).first()
        if venue_staff:
            has_access = True

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this venue"
        )

    return venue
