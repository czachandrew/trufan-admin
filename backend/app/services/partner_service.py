"""
Partner Opportunity Service - For partners to create and manage opportunities.

Ensures all opportunities provide genuine user value, not just advertising.
"""
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import uuid4
import secrets
import string
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from fastapi import HTTPException, status

from app.models.opportunity import (
    Partner,
    Opportunity,
    OpportunityInteraction,
    OpportunityAnalytics,
    InteractionType,
)
from app.schemas.opportunity import (
    PartnerCreate,
    PartnerUpdate,
    PartnerResponse,
    OpportunityCreate,
    OpportunityUpdate,
    OpportunityResponse,
    OpportunityAnalyticsResponse,
    ClaimCodeValidationResponse,
)


class PartnerOpportunityService:
    """
    Service for partners to create and manage opportunities.
    Ensures all opportunities provide genuine user value.
    """

    def __init__(self, db: Session):
        self.db = db

    # ==================== Partner Management ====================

    def create_partner(self, partner_data: PartnerCreate) -> Partner:
        """Create a new partner account."""

        # Check for duplicate email
        existing = self.db.query(Partner).filter(
            Partner.contact_email == partner_data.contact_email
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Partner with this email already exists"
            )

        # Generate API key
        api_key = self._generate_api_key()

        partner = Partner(
            business_name=partner_data.business_name,
            business_type=partner_data.business_type,
            contact_email=partner_data.contact_email,
            contact_phone=partner_data.contact_phone,
            address=partner_data.address,
            location_lat=partner_data.location_lat,
            location_lng=partner_data.location_lng,
            webhook_url=partner_data.webhook_url,
            api_key=api_key,
            billing_email=partner_data.billing_email,
            commission_rate=partner_data.commission_rate,
            max_active_opportunities=partner_data.max_active_opportunities,
            auto_approve_opportunities=False,  # Require manual approval initially
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(partner)
        self.db.commit()
        self.db.refresh(partner)

        return partner

    def get_partner_by_api_key(self, api_key: str) -> Optional[Partner]:
        """Get partner by API key for authentication."""
        return self.db.query(Partner).filter(
            Partner.api_key == api_key,
            Partner.is_active == True
        ).first()

    def update_partner(self, partner_id: str, update_data: PartnerUpdate) -> Partner:
        """Update partner information."""
        partner = self.db.query(Partner).filter(
            Partner.id == partner_id
        ).first()

        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")

        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(partner, field, value)

        partner.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(partner)

        return partner

    # ==================== Opportunity Management ====================

    def create_opportunity(
        self, partner_id: str, opportunity_data: OpportunityCreate
    ) -> Opportunity:
        """
        Create a new opportunity with validation.
        Ensures opportunity provides real value to users.
        """

        # Validate partner
        partner = self.db.query(Partner).filter(
            Partner.id == partner_id
        ).first()

        if not partner or not partner.is_active:
            raise HTTPException(
                status_code=403, detail="Partner account inactive"
            )

        # Check partner limits
        active_count = self._count_active_opportunities(partner_id)
        if active_count >= partner.max_active_opportunities:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {partner.max_active_opportunities} active opportunities allowed"
            )

        # Validate value proposition (already done by Pydantic, but double-check)
        if not self._validate_value_proposition(opportunity_data.value_details):
            raise HTTPException(
                status_code=400,
                detail="Opportunity must provide clear value to users"
            )

        # Create opportunity
        opportunity = Opportunity(
            partner_id=partner_id,
            title=opportunity_data.title,
            value_proposition=opportunity_data.value_proposition,
            opportunity_type=opportunity_data.opportunity_type.value,
            trigger_rules=opportunity_data.trigger_rules,
            valid_from=opportunity_data.valid_from,
            valid_until=opportunity_data.valid_until,
            availability_schedule=opportunity_data.availability_schedule,
            total_capacity=opportunity_data.total_capacity,
            used_capacity=0,
            value_details=opportunity_data.value_details,
            location_lat=opportunity_data.location_lat,
            location_lng=opportunity_data.location_lng,
            address=opportunity_data.address,
            walking_distance_meters=opportunity_data.walking_distance_meters,
            max_impressions_per_user=opportunity_data.max_impressions_per_user,
            cooldown_hours=opportunity_data.cooldown_hours,
            priority_score=opportunity_data.priority_score,
            is_active=True,
            is_approved=partner.auto_approve_opportunities,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(opportunity)
        self.db.commit()
        self.db.refresh(opportunity)

        # If not auto-approved, queue for review
        if not partner.auto_approve_opportunities:
            # TODO: Integrate with admin notification system
            pass

        return opportunity

    def _count_active_opportunities(self, partner_id: str) -> int:
        """Count partner's currently active opportunities."""
        return self.db.query(func.count(Opportunity.id)).filter(
            Opportunity.partner_id == partner_id,
            Opportunity.is_active == True,
            Opportunity.valid_until >= datetime.utcnow()
        ).scalar()

    def _validate_value_proposition(self, value_details: Dict[str, Any]) -> bool:
        """
        Ensure opportunity provides real value, not just advertising.
        """
        # Must have at least one tangible benefit
        has_discount = (
            value_details.get('discount_percentage', 0) >= 10 or
            value_details.get('discount_amount', 0) >= 5
        )
        has_parking_benefit = value_details.get('parking_extension_minutes', 0) >= 15
        has_perks = len(value_details.get('perks', [])) > 0

        return has_discount or has_parking_benefit or has_perks

    def get_partner_opportunities(
        self,
        partner_id: str,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Opportunity]:
        """Get partner's opportunities with optional filtering."""

        query = self.db.query(Opportunity).filter(
            Opportunity.partner_id == partner_id
        )

        if status_filter == "active":
            query = query.filter(
                Opportunity.is_active == True,
                Opportunity.valid_until >= datetime.utcnow()
            )
        elif status_filter == "expired":
            query = query.filter(
                Opportunity.valid_until < datetime.utcnow()
            )
        elif status_filter == "pending":
            query = query.filter(
                Opportunity.is_approved == False
            )

        return query.order_by(
            Opportunity.created_at.desc()
        ).offset(skip).limit(limit).all()

    def update_opportunity(
        self, partner_id: str, opportunity_id: str, update_data: OpportunityUpdate
    ) -> Opportunity:
        """Update an opportunity."""

        opportunity = self.db.query(Opportunity).filter(
            Opportunity.id == opportunity_id,
            Opportunity.partner_id == partner_id
        ).first()

        if not opportunity:
            raise HTTPException(
                status_code=404, detail="Opportunity not found"
            )

        # Update fields
        update_dict = update_data.dict(exclude_unset=True)

        # Validate value_details if being updated
        if 'value_details' in update_dict:
            if not self._validate_value_proposition(update_dict['value_details']):
                raise HTTPException(
                    status_code=400,
                    detail="Updated opportunity must provide clear value to users"
                )

        for field, value in update_dict.items():
            if field == 'opportunity_type' and value:
                setattr(opportunity, field, value.value)
            else:
                setattr(opportunity, field, value)

        opportunity.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(opportunity)

        return opportunity

    def delete_opportunity(self, partner_id: str, opportunity_id: str):
        """Delete/deactivate an opportunity."""

        opportunity = self.db.query(Opportunity).filter(
            Opportunity.id == opportunity_id,
            Opportunity.partner_id == partner_id
        ).first()

        if not opportunity:
            raise HTTPException(
                status_code=404, detail="Opportunity not found"
            )

        # Soft delete - just deactivate
        opportunity.is_active = False
        opportunity.updated_at = datetime.utcnow()
        self.db.commit()

    # ==================== Claim Code Validation ====================

    def validate_claim_code(
        self, partner_id: str, claim_code: str
    ) -> ClaimCodeValidationResponse:
        """
        Validate a user's claim code.
        Partners call this when user redeems an opportunity.
        """

        # Find the interaction with this claim code
        # Note: We store claim codes in interaction_context for now
        # In production, you might want a separate claim_codes table
        interaction = self.db.query(OpportunityInteraction).join(
            Opportunity
        ).filter(
            Opportunity.partner_id == partner_id,
            OpportunityInteraction.interaction_type == InteractionType.ACCEPTED.value,
            OpportunityInteraction.interaction_context.contains({"claim_code": claim_code})
        ).first()

        if not interaction:
            return ClaimCodeValidationResponse(
                valid=False,
                message="Invalid claim code"
            )

        # Check if already redeemed
        if interaction.interaction_type == InteractionType.COMPLETED.value:
            return ClaimCodeValidationResponse(
                valid=False,
                message="Claim code already redeemed"
            )

        # Check expiration (24 hours from acceptance)
        expires_at = interaction.created_at + timedelta(hours=24)
        if datetime.utcnow() > expires_at:
            return ClaimCodeValidationResponse(
                valid=False,
                message="Claim code expired"
            )

        return ClaimCodeValidationResponse(
            valid=True,
            opportunity_id=interaction.opportunity_id,
            user_id=interaction.user_id,
            value_details=interaction.value_claimed,
            claimed_at=interaction.created_at,
            message="Valid claim code"
        )

    def mark_opportunity_completed(
        self,
        partner_id: str,
        claim_code: str,
        transaction_amount: Optional[Decimal] = None
    ):
        """
        Mark an opportunity as completed/redeemed.
        Records revenue for analytics.
        """

        # Find interaction
        interaction = self.db.query(OpportunityInteraction).join(
            Opportunity
        ).filter(
            Opportunity.partner_id == partner_id,
            OpportunityInteraction.interaction_context.contains({"claim_code": claim_code})
        ).first()

        if not interaction:
            raise HTTPException(
                status_code=404, detail="Claim code not found"
            )

        # Get partner commission rate
        partner = self.db.query(Partner).filter(
            Partner.id == partner_id
        ).first()

        # Update interaction
        interaction.interaction_type = InteractionType.COMPLETED.value
        interaction.completed_at = datetime.utcnow()

        if transaction_amount:
            interaction.partner_revenue = transaction_amount
            interaction.platform_commission = transaction_amount * partner.commission_rate

        self.db.commit()

    # ==================== Analytics ====================

    def get_partner_analytics(
        self,
        partner_id: str,
        date_start: date,
        date_end: date
    ) -> OpportunityAnalyticsResponse:
        """
        Return value-focused analytics for partners.
        NOT traditional ad metrics - focus on engagement and value.
        """

        # Get all interactions in date range
        interactions = self.db.query(OpportunityInteraction).join(
            Opportunity
        ).filter(
            Opportunity.partner_id == partner_id,
            func.date(OpportunityInteraction.created_at).between(date_start, date_end)
        ).all()

        # Calculate metrics
        unique_users = len(set(str(i.user_id) for i in interactions))

        impressions = sum(
            1 for i in interactions
            if i.interaction_type == InteractionType.IMPRESSED.value
        )

        views = sum(
            1 for i in interactions
            if i.interaction_type == InteractionType.VIEWED.value
        )

        acceptances = sum(
            1 for i in interactions
            if i.interaction_type == InteractionType.ACCEPTED.value
        )

        completions = sum(
            1 for i in interactions
            if i.interaction_type == InteractionType.COMPLETED.value
        )

        total_revenue = sum(
            i.partner_revenue for i in interactions
            if i.partner_revenue
        ) or Decimal("0.00")

        total_commission = sum(
            i.platform_commission for i in interactions
            if i.platform_commission
        ) or Decimal("0.00")

        avg_transaction = (
            total_revenue / acceptances
            if acceptances > 0 else Decimal("0.00")
        )

        redemption_rate = (
            completions / acceptances
            if acceptances > 0 else 0.0
        )

        return OpportunityAnalyticsResponse(
            period={
                "start": date_start,
                "end": date_end
            },
            engagement={
                "unique_users": unique_users,
                "impressions": impressions,
                "views": views,
                "claims": acceptances,
                "redemptions": completions,
                "redemption_rate": round(redemption_rate, 3)
            },
            value={
                "avg_transaction": avg_transaction,
                "total_revenue": total_revenue,
                "platform_fees": total_commission,
                "net_revenue": total_revenue - total_commission
            }
        )

    # ==================== Helper Methods ====================

    def _generate_api_key(self, length: int = 32) -> str:
        """Generate unique API key for partner."""
        alphabet = string.ascii_letters + string.digits
        while True:
            api_key = "pk_" + "".join(secrets.choice(alphabet) for _ in range(length))
            # Check uniqueness
            existing = self.db.query(Partner).filter(
                Partner.api_key == api_key
            ).first()
            if not existing:
                return api_key
