"""
Partner API endpoints for managing opportunities.
Partners use their API key for authentication.
Admins can use Bearer token authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from uuid import UUID
from datetime import date

from app.core.database import get_db
from app.core.dependencies import get_current_user_optional
from app.models.opportunity import Partner
from app.models.user import User
from app.schemas.opportunity import (
    OpportunityCreate,
    OpportunityUpdate,
    OpportunityResponse,
    ValidateClaimCode,
    ClaimCodeValidationResponse,
    PartnerAnalyticsRequest,
    OpportunityAnalyticsResponse,
)
from app.services.partner_service import PartnerOpportunityService


router = APIRouter()


def get_partner_from_api_key(
    x_api_key: str = Header(..., description="Partner API Key"),
    db: Session = Depends(get_db)
) -> Partner:
    """
    Authenticate partner by API key.
    """
    service = PartnerOpportunityService(db)
    partner = service.get_partner_by_api_key(x_api_key)

    if not partner:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    if not partner.is_active:
        raise HTTPException(
            status_code=403,
            detail="Partner account is inactive"
        )

    return partner


def get_partner_or_admin(
    x_api_key: Optional[str] = Header(None, description="Partner API Key (optional)"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Union[Partner, User]:
    """
    Authenticate via API key (partner) OR Bearer token (admin).

    Returns the authenticated partner if API key provided,
    or the authenticated admin user if Bearer token provided.
    """
    # Try API key first
    if x_api_key:
        service = PartnerOpportunityService(db)
        partner = service.get_partner_by_api_key(x_api_key)

        if not partner:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )

        if not partner.is_active:
            raise HTTPException(
                status_code=403,
                detail="Partner account is inactive"
            )

        return partner

    # Try Bearer token (admin)
    if current_user:
        if current_user.role not in ["super_admin", "venue_admin"]:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions. Admin role required."
            )
        return current_user

    # No authentication provided
    raise HTTPException(
        status_code=401,
        detail="Authentication required. Provide X-API-Key header or Bearer token."
    )


@router.post("/opportunities", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
def create_opportunity(
    opportunity_data: OpportunityCreate,
    partner: Partner = Depends(get_partner_from_api_key),
    db: Session = Depends(get_db),
):
    """
    Create a new opportunity.

    All opportunities must provide genuine user value:
    - 10%+ discount OR $5+ discount
    - 15+ minutes free parking
    - Valuable perks (skip line, free item, etc.)

    Opportunities not meeting value requirements will be rejected.
    """
    service = PartnerOpportunityService(db)

    opportunity = service.create_opportunity(
        str(partner.id),
        opportunity_data
    )

    return opportunity


@router.get("/opportunities", response_model=List[OpportunityResponse])
def get_partner_opportunities(
    status_filter: Optional[str] = Query(None, regex="^(active|expired|pending)$"),
    partner_id: Optional[str] = Query(None, description="Filter by partner ID (admin only)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    authenticated: Union[Partner, User] = Depends(get_partner_or_admin),
    db: Session = Depends(get_db),
):
    """
    List opportunities.

    Partners: See only their own opportunities
    Admins: See all opportunities (optionally filter by partner_id)

    Filter by status:
    - active: Currently running
    - expired: Past expiration date
    - pending: Awaiting admin approval
    """
    from app.models.opportunity import Opportunity
    from datetime import datetime

    # Build query
    query = db.query(Opportunity)

    # If authenticated as partner, only show their opportunities
    if isinstance(authenticated, Partner):
        query = query.filter(Opportunity.partner_id == authenticated.id)
    # If authenticated as admin and partner_id filter provided
    elif partner_id:
        query = query.filter(Opportunity.partner_id == partner_id)

    # Apply status filter
    if status_filter == "active":
        now = datetime.utcnow()
        query = query.filter(
            Opportunity.is_active == True,
            Opportunity.valid_until >= now
        )
    elif status_filter == "expired":
        now = datetime.utcnow()
        query = query.filter(Opportunity.valid_until < now)
    elif status_filter == "pending":
        query = query.filter(Opportunity.is_approved == False)

    # Order and paginate
    opportunities = query.order_by(Opportunity.created_at.desc()).offset(skip).limit(limit).all()

    return opportunities


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
def get_opportunity(
    opportunity_id: UUID,
    partner: Partner = Depends(get_partner_from_api_key),
    db: Session = Depends(get_db),
):
    """
    Get details of a specific opportunity.
    """
    from app.models.opportunity import Opportunity

    opportunity = db.query(Opportunity).filter(
        Opportunity.id == opportunity_id,
        Opportunity.partner_id == partner.id
    ).first()

    if not opportunity:
        raise HTTPException(
            status_code=404,
            detail="Opportunity not found"
        )

    return opportunity


@router.put("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
def update_opportunity(
    opportunity_id: UUID,
    update_data: OpportunityUpdate,
    partner: Partner = Depends(get_partner_from_api_key),
    db: Session = Depends(get_db),
):
    """
    Update an existing opportunity.

    Note: Changes to approved opportunities may require re-approval.
    """
    service = PartnerOpportunityService(db)

    opportunity = service.update_opportunity(
        str(partner.id),
        str(opportunity_id),
        update_data
    )

    return opportunity


@router.delete("/opportunities/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_opportunity(
    opportunity_id: UUID,
    partner: Partner = Depends(get_partner_from_api_key),
    db: Session = Depends(get_db),
):
    """
    Delete (deactivate) an opportunity.

    This soft-deletes the opportunity - it won't be shown to users
    but historical data is preserved for analytics.
    """
    service = PartnerOpportunityService(db)

    service.delete_opportunity(
        str(partner.id),
        str(opportunity_id)
    )

    return None


@router.post("/opportunities/{opportunity_id}/validate", response_model=ClaimCodeValidationResponse)
def validate_claim_code(
    opportunity_id: UUID,
    validation_data: ValidateClaimCode,
    partner: Partner = Depends(get_partner_from_api_key),
    db: Session = Depends(get_db),
):
    """
    Validate a user's claim code.

    Call this when a user arrives to redeem their opportunity.
    Returns user info and value details if valid.
    """
    service = PartnerOpportunityService(db)

    result = service.validate_claim_code(
        str(partner.id),
        validation_data.claim_code
    )

    return result


@router.post("/opportunities/{opportunity_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
def complete_opportunity(
    opportunity_id: UUID,
    claim_code: str = Query(..., description="Claim code to complete"),
    transaction_amount: Optional[float] = Query(None, description="Transaction amount if applicable"),
    partner: Partner = Depends(get_partner_from_api_key),
    db: Session = Depends(get_db),
):
    """
    Mark an opportunity as completed/redeemed.

    Call this after the user has successfully redeemed their opportunity.
    Include transaction_amount for revenue tracking.
    """
    from decimal import Decimal

    service = PartnerOpportunityService(db)

    service.mark_opportunity_completed(
        str(partner.id),
        claim_code,
        transaction_amount=Decimal(str(transaction_amount)) if transaction_amount else None
    )

    return None


@router.get("/analytics", response_model=OpportunityAnalyticsResponse)
def get_partner_analytics(
    date_start: date = Query(..., description="Start date (YYYY-MM-DD)"),
    date_end: date = Query(..., description="End date (YYYY-MM-DD)"),
    partner: Partner = Depends(get_partner_from_api_key),
    db: Session = Depends(get_db),
):
    """
    Get performance analytics for your opportunities.

    Returns value-focused metrics:
    - Unique users engaged
    - Claims and redemptions (not impressions!)
    - Redemption rate
    - Average transaction value
    - Total revenue and fees

    This is NOT traditional ad analytics - we focus on real business value.
    """
    service = PartnerOpportunityService(db)

    analytics = service.get_partner_analytics(
        str(partner.id),
        date_start=date_start,
        date_end=date_end
    )

    return analytics


@router.get("/analytics/opportunities/{opportunity_id}", response_model=OpportunityAnalyticsResponse)
def get_opportunity_analytics(
    opportunity_id: UUID,
    date_start: date = Query(..., description="Start date (YYYY-MM-DD)"),
    date_end: date = Query(..., description="End date (YYYY-MM-DD)"),
    partner: Partner = Depends(get_partner_from_api_key),
    db: Session = Depends(get_db),
):
    """
    Get analytics for a specific opportunity.
    """
    from app.models.opportunity import Opportunity

    # Verify opportunity belongs to partner
    opportunity = db.query(Opportunity).filter(
        Opportunity.id == opportunity_id,
        Opportunity.partner_id == partner.id
    ).first()

    if not opportunity:
        raise HTTPException(
            status_code=404,
            detail="Opportunity not found"
        )

    # Get analytics (same as partner-wide, but filtered to this opportunity)
    service = PartnerOpportunityService(db)

    # For now, use the same method - in production you'd filter by opportunity_id
    analytics = service.get_partner_analytics(
        str(partner.id),
        date_start=date_start,
        date_end=date_end
    )

    return analytics
