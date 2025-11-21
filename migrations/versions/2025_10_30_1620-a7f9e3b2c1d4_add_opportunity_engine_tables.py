"""add opportunity engine tables

Revision ID: a7f9e3b2c1d4
Revises: e136fd07c90a
Create Date: 2025-10-30 16:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = 'a7f9e3b2c1d4'
down_revision: Union[str, None] = 'e136fd07c90a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create partners table
    op.create_table(
        'partners',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('business_name', sa.String(200), nullable=False),
        sa.Column('business_type', sa.String(50), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=False),
        sa.Column('contact_phone', sa.String(20), nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('location_lat', sa.Numeric(10, 8), nullable=True),
        sa.Column('location_lng', sa.Numeric(11, 8), nullable=True),

        # Integration details
        sa.Column('webhook_url', sa.Text, nullable=True),
        sa.Column('api_key', sa.String(255), unique=True, nullable=True),

        # Settlement/billing
        sa.Column('stripe_account_id', sa.String(255), nullable=True),
        sa.Column('commission_rate', sa.Numeric(3, 2), nullable=False, server_default='0.15'),
        sa.Column('billing_email', sa.String(255), nullable=True),

        # Settings
        sa.Column('auto_approve_opportunities', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('max_active_opportunities', sa.Integer, nullable=False, server_default='10'),

        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index(op.f('ix_partners_id'), 'partners', ['id'], unique=False)
    op.create_index(op.f('ix_partners_api_key'), 'partners', ['api_key'], unique=True)
    op.create_index('ix_partners_location', 'partners', ['location_lat', 'location_lng'], unique=False)

    # Create opportunities table
    op.create_table(
        'opportunities',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('partner_id', UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(100), nullable=False),
        sa.Column('value_proposition', sa.Text, nullable=False),
        sa.Column('opportunity_type', sa.String(20), nullable=False),

        # Trigger conditions
        sa.Column('trigger_rules', JSONB, nullable=False, server_default='{}'),

        # Availability window
        sa.Column('valid_from', sa.DateTime, nullable=False),
        sa.Column('valid_until', sa.DateTime, nullable=False),
        sa.Column('availability_schedule', JSONB, nullable=True),

        # Capacity management
        sa.Column('total_capacity', sa.Integer, nullable=True),
        sa.Column('used_capacity', sa.Integer, nullable=False, server_default='0'),

        # Value details
        sa.Column('value_details', JSONB, nullable=False),

        # Location data
        sa.Column('location_lat', sa.Numeric(10, 8), nullable=True),
        sa.Column('location_lng', sa.Numeric(11, 8), nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('walking_distance_meters', sa.Integer, nullable=True),

        # Configuration
        sa.Column('max_impressions_per_user', sa.Integer, nullable=False, server_default='3'),
        sa.Column('cooldown_hours', sa.Integer, nullable=False, server_default='24'),
        sa.Column('priority_score', sa.Integer, nullable=False, server_default='50'),

        # State
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_approved', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.ForeignKeyConstraint(['partner_id'], ['partners.id'], ondelete='CASCADE'),
        sa.CheckConstraint('valid_until > valid_from', name='valid_date_range'),
        sa.CheckConstraint('used_capacity <= total_capacity OR total_capacity IS NULL', name='valid_capacity'),
        sa.CheckConstraint("opportunity_type IN ('experience', 'convenience', 'discovery', 'service', 'bundle')", name='valid_opportunity_type'),
    )
    op.create_index(op.f('ix_opportunities_id'), 'opportunities', ['id'], unique=False)
    op.create_index(op.f('ix_opportunities_partner_id'), 'opportunities', ['partner_id'], unique=False)
    op.create_index('ix_opportunities_active', 'opportunities', ['is_active', 'is_approved'], unique=False)
    op.create_index('ix_opportunities_location', 'opportunities', ['location_lat', 'location_lng'], unique=False)
    op.create_index('ix_opportunities_valid_dates', 'opportunities', ['valid_from', 'valid_until'], unique=False)

    # Create opportunity_interactions table
    op.create_table(
        'opportunity_interactions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('opportunity_id', UUID(as_uuid=True), nullable=False),
        sa.Column('parking_session_id', UUID(as_uuid=True), nullable=True),

        sa.Column('interaction_type', sa.String(20), nullable=False),

        # Context when interaction happened
        sa.Column('interaction_context', JSONB, nullable=True),

        # Value tracking
        sa.Column('value_claimed', JSONB, nullable=True),
        sa.Column('value_redeemed', JSONB, nullable=True),
        sa.Column('partner_revenue', sa.Numeric(10, 2), nullable=True),
        sa.Column('platform_commission', sa.Numeric(10, 2), nullable=True),

        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime, nullable=True),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parking_session_id'], ['parking_sessions.id'], ondelete='SET NULL'),
        sa.CheckConstraint("interaction_type IN ('impressed', 'viewed', 'accepted', 'dismissed', 'completed', 'expired')", name='valid_interaction_type'),
        sa.UniqueConstraint('user_id', 'opportunity_id', 'parking_session_id', name='unique_user_opportunity_session'),
    )
    op.create_index(op.f('ix_opportunity_interactions_id'), 'opportunity_interactions', ['id'], unique=False)
    op.create_index('ix_interactions_user', 'opportunity_interactions', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_interactions_session', 'opportunity_interactions', ['parking_session_id'], unique=False)

    # Create opportunity_preferences table
    op.create_table(
        'opportunity_preferences',
        sa.Column('user_id', UUID(as_uuid=True), primary_key=True),

        # Master control
        sa.Column('opportunities_enabled', sa.Boolean, nullable=False, server_default='true'),

        # Frequency control
        sa.Column('frequency_preference', sa.String(20), nullable=False, server_default="'occasional'"),
        sa.Column('max_per_session', sa.Integer, nullable=False, server_default='3'),

        # Timing preferences
        sa.Column('quiet_hours', JSONB, nullable=False, server_default='[]'),
        sa.Column('no_opportunity_days', sa.ARRAY(sa.String(10)), nullable=False, server_default='{}'),

        # Category preferences
        sa.Column('preferred_categories', sa.ARRAY(sa.String(20)), nullable=False, server_default='{}'),
        sa.Column('blocked_categories', sa.ARRAY(sa.String(20)), nullable=False, server_default='{}'),
        sa.Column('blocked_partner_ids', sa.ARRAY(UUID(as_uuid=True)), nullable=False, server_default='{}'),

        # Location preferences
        sa.Column('max_walking_distance_meters', sa.Integer, nullable=False, server_default='500'),

        # Learning data
        sa.Column('acceptance_patterns', JSONB, nullable=False, server_default='{}'),

        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint("frequency_preference IN ('all', 'occasional', 'minimal')", name='valid_frequency_preference'),
    )
    op.create_index(op.f('ix_opportunity_preferences_user_id'), 'opportunity_preferences', ['user_id'], unique=False)

    # Create opportunity_analytics table
    op.create_table(
        'opportunity_analytics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('opportunity_id', UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('hour', sa.Integer, nullable=True),

        # Exposure metrics
        sa.Column('unique_impressions', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_impressions', sa.Integer, nullable=False, server_default='0'),

        # Engagement metrics
        sa.Column('views', sa.Integer, nullable=False, server_default='0'),
        sa.Column('acceptances', sa.Integer, nullable=False, server_default='0'),
        sa.Column('completions', sa.Integer, nullable=False, server_default='0'),

        # Value metrics
        sa.Column('total_user_value', sa.Numeric(10, 2), nullable=False, server_default='0.00'),
        sa.Column('total_partner_revenue', sa.Numeric(10, 2), nullable=False, server_default='0.00'),
        sa.Column('total_platform_commission', sa.Numeric(10, 2), nullable=False, server_default='0.00'),

        # Performance metrics
        sa.Column('avg_time_to_accept', sa.Integer, nullable=True),
        sa.Column('avg_distance_meters', sa.Integer, nullable=True),

        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('opportunity_id', 'date', 'hour', name='unique_opportunity_date_hour'),
    )
    op.create_index(op.f('ix_opportunity_analytics_id'), 'opportunity_analytics', ['id'], unique=False)
    op.create_index('ix_analytics_date', 'opportunity_analytics', ['opportunity_id', 'date'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_analytics_date', table_name='opportunity_analytics')
    op.drop_index(op.f('ix_opportunity_analytics_id'), table_name='opportunity_analytics')
    op.drop_table('opportunity_analytics')

    op.drop_index(op.f('ix_opportunity_preferences_user_id'), table_name='opportunity_preferences')
    op.drop_table('opportunity_preferences')

    op.drop_index('ix_interactions_session', table_name='opportunity_interactions')
    op.drop_index('ix_interactions_user', table_name='opportunity_interactions')
    op.drop_index(op.f('ix_opportunity_interactions_id'), table_name='opportunity_interactions')
    op.drop_table('opportunity_interactions')

    op.drop_index('ix_opportunities_valid_dates', table_name='opportunities')
    op.drop_index('ix_opportunities_location', table_name='opportunities')
    op.drop_index('ix_opportunities_active', table_name='opportunities')
    op.drop_index(op.f('ix_opportunities_partner_id'), table_name='opportunities')
    op.drop_index(op.f('ix_opportunities_id'), table_name='opportunities')
    op.drop_table('opportunities')

    op.drop_index('ix_partners_location', table_name='partners')
    op.drop_index(op.f('ix_partners_api_key'), table_name='partners')
    op.drop_index(op.f('ix_partners_id'), table_name='partners')
    op.drop_table('partners')
