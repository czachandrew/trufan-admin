#!/usr/bin/env python3
"""
Create valet service database tables.
Run with: docker-compose exec api python -m scripts.create_valet_tables
"""
import sys
from sqlalchemy import text

from app.core.database import engine


def create_valet_tables():
    """Create all valet service tables."""
    print("\n" + "="*70)
    print("CREATING VALET SERVICE TABLES")
    print("="*70 + "\n")

    try:
        with engine.connect() as conn:
            # 1. Create saved_vehicles table first (referenced by valet_sessions)
            print("Creating saved_vehicles table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS saved_vehicles (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

                    vehicle_plate VARCHAR(20) NOT NULL,
                    vehicle_make VARCHAR(100) NOT NULL,
                    vehicle_model VARCHAR(100) NOT NULL,
                    vehicle_color VARCHAR(50),
                    vehicle_year INTEGER,
                    vehicle_photo_url TEXT,

                    nickname VARCHAR(100),

                    is_default BOOLEAN DEFAULT false,

                    last_used_at TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,

                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),

                    UNIQUE(user_id, vehicle_plate)
                );

                CREATE INDEX IF NOT EXISTS idx_saved_vehicles_user ON saved_vehicles(user_id);
                CREATE INDEX IF NOT EXISTS idx_saved_vehicles_default ON saved_vehicles(user_id, is_default) WHERE is_default = true;
            """))
            conn.commit()
            print("✓ Created saved_vehicles table")

            # 2. Create valet_sessions table
            print("Creating valet_sessions table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS valet_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    ticket_number VARCHAR(20) UNIQUE NOT NULL,

                    -- References
                    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
                    attendant_id UUID REFERENCES users(id) ON DELETE SET NULL,
                    saved_vehicle_id UUID REFERENCES saved_vehicles(id) ON DELETE SET NULL,
                    parking_space_id UUID REFERENCES parking_spaces(id) ON DELETE SET NULL,

                    -- Vehicle information
                    vehicle_plate VARCHAR(20) NOT NULL,
                    vehicle_make VARCHAR(100) NOT NULL,
                    vehicle_model VARCHAR(100) NOT NULL,
                    vehicle_color VARCHAR(50),
                    vehicle_year INTEGER,
                    vehicle_notes TEXT,

                    -- Service details
                    service_type VARCHAR(20) NOT NULL DEFAULT 'standard',
                    status VARCHAR(50) NOT NULL DEFAULT 'requested',
                    priority VARCHAR(20) DEFAULT 'normal',

                    -- Timing
                    check_in_time TIMESTAMP,
                    parked_time TIMESTAMP,
                    retrieval_requested_time TIMESTAMP,
                    ready_time TIMESTAMP,
                    check_out_time TIMESTAMP,
                    estimated_retrieval_minutes INTEGER,
                    actual_retrieval_minutes INTEGER,

                    -- Pricing
                    base_price NUMERIC(10, 2) NOT NULL,
                    service_fee NUMERIC(10, 2) DEFAULT 0,
                    tip NUMERIC(10, 2) DEFAULT 0,
                    total_price NUMERIC(10, 2) NOT NULL,

                    -- Contact
                    contact_phone VARCHAR(20),
                    contact_email VARCHAR(255),
                    notification_preferences JSONB DEFAULT '{}',

                    -- Security
                    pin VARCHAR(4) NOT NULL,
                    qr_code_data TEXT,
                    access_code VARCHAR(50),

                    -- Parking location
                    parking_section VARCHAR(50),
                    parking_level VARCHAR(20),
                    parking_spot VARCHAR(20),
                    parking_notes TEXT,

                    -- Rating
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                    feedback TEXT,

                    -- Payment
                    payment_method_id VARCHAR(255),
                    payment_transaction_id VARCHAR(255),
                    payment_status VARCHAR(20) DEFAULT 'pending',

                    -- Metadata
                    special_requests TEXT,
                    internal_notes TEXT,
                    metadata JSONB DEFAULT '{}',

                    -- Timestamps
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_valet_sessions_ticket ON valet_sessions(ticket_number);
                CREATE INDEX IF NOT EXISTS idx_valet_sessions_status ON valet_sessions(status);
                CREATE INDEX IF NOT EXISTS idx_valet_sessions_venue ON valet_sessions(venue_id);
                CREATE INDEX IF NOT EXISTS idx_valet_sessions_user ON valet_sessions(user_id);
                CREATE INDEX IF NOT EXISTS idx_valet_sessions_plate ON valet_sessions(vehicle_plate);
                CREATE INDEX IF NOT EXISTS idx_valet_sessions_phone ON valet_sessions(contact_phone);
                CREATE INDEX IF NOT EXISTS idx_valet_sessions_created ON valet_sessions(created_at);
            """))
            conn.commit()
            print("✓ Created valet_sessions table")

            # 3. Create valet_status_events table
            print("Creating valet_status_events table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS valet_status_events (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id UUID NOT NULL REFERENCES valet_sessions(id) ON DELETE CASCADE,

                    old_status VARCHAR(50),
                    new_status VARCHAR(50) NOT NULL,

                    changed_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                    changed_by_name VARCHAR(255),

                    location_lat NUMERIC(10, 8),
                    location_lng NUMERIC(11, 8),

                    notes TEXT,

                    created_at TIMESTAMP DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_valet_status_events_session ON valet_status_events(session_id);
                CREATE INDEX IF NOT EXISTS idx_valet_status_events_created ON valet_status_events(created_at);
            """))
            conn.commit()
            print("✓ Created valet_status_events table")

            # 4. Create valet_communications table
            print("Creating valet_communications table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS valet_communications (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id UUID NOT NULL REFERENCES valet_sessions(id) ON DELETE CASCADE,

                    type VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,

                    recipient_phone VARCHAR(20),
                    recipient_email VARCHAR(255),

                    provider_id VARCHAR(255),
                    provider_status VARCHAR(50),

                    sent_at TIMESTAMP DEFAULT NOW(),
                    delivered_at TIMESTAMP,
                    read_at TIMESTAMP,

                    error_message TEXT,

                    metadata JSONB DEFAULT '{}'
                );

                CREATE INDEX IF NOT EXISTS idx_valet_communications_session ON valet_communications(session_id);
                CREATE INDEX IF NOT EXISTS idx_valet_communications_sent ON valet_communications(sent_at);
            """))
            conn.commit()
            print("✓ Created valet_communications table")

            # 5. Create valet_incidents table
            print("Creating valet_incidents table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS valet_incidents (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id UUID NOT NULL REFERENCES valet_sessions(id) ON DELETE CASCADE,

                    incident_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL DEFAULT 'low',
                    description TEXT NOT NULL,

                    reported_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                    reported_by_name VARCHAR(255),

                    assigned_to_user_id UUID REFERENCES users(id) ON DELETE SET NULL,

                    photo_urls TEXT[],

                    resolution_status VARCHAR(20) DEFAULT 'open',
                    resolution_notes TEXT,
                    resolved_at TIMESTAMP,

                    estimated_cost NUMERIC(10, 2),
                    actual_cost NUMERIC(10, 2),

                    requires_followup BOOLEAN DEFAULT false,

                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_valet_incidents_session ON valet_incidents(session_id);
                CREATE INDEX IF NOT EXISTS idx_valet_incidents_status ON valet_incidents(resolution_status);
                CREATE INDEX IF NOT EXISTS idx_valet_incidents_severity ON valet_incidents(severity);
            """))
            conn.commit()
            print("✓ Created valet_incidents table")

            # 6. Create valet_capacity table
            print("Creating valet_capacity table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS valet_capacity (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,

                    total_capacity INTEGER NOT NULL,
                    current_occupancy INTEGER DEFAULT 0,
                    available_spaces INTEGER DEFAULT 0,

                    attendants_on_duty INTEGER DEFAULT 0,
                    attendants_required INTEGER DEFAULT 1,

                    average_retrieval_time NUMERIC(5, 2) DEFAULT 0,
                    average_wait_time NUMERIC(5, 2) DEFAULT 0,

                    pending_checkins INTEGER DEFAULT 0,
                    pending_retrievals INTEGER DEFAULT 0,

                    is_accepting_vehicles BOOLEAN DEFAULT true,

                    updated_at TIMESTAMP DEFAULT NOW(),

                    UNIQUE(venue_id)
                );

                CREATE INDEX IF NOT EXISTS idx_valet_capacity_venue ON valet_capacity(venue_id);
            """))
            conn.commit()
            print("✓ Created valet_capacity table")

            # 7. Create valet_pricing table
            print("Creating valet_pricing table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS valet_pricing (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,

                    base_price NUMERIC(10, 2) NOT NULL,
                    service_fee NUMERIC(10, 2) DEFAULT 0,

                    standard_price NUMERIC(10, 2),
                    vip_price NUMERIC(10, 2),
                    event_price NUMERIC(10, 2),
                    premium_price NUMERIC(10, 2),

                    hourly_rate NUMERIC(10, 2),
                    daily_max NUMERIC(10, 2),

                    surge_multiplier NUMERIC(3, 2) DEFAULT 1.0,
                    peak_hours JSONB DEFAULT '{}',

                    is_active BOOLEAN DEFAULT true,

                    valid_from TIMESTAMP,
                    valid_until TIMESTAMP,

                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_valet_pricing_venue ON valet_pricing(venue_id);
                CREATE INDEX IF NOT EXISTS idx_valet_pricing_active ON valet_pricing(venue_id, is_active) WHERE is_active = true;
            """))
            conn.commit()
            print("✓ Created valet_pricing table")

            # 8. Create valet_metrics_daily table
            print("Creating valet_metrics_daily table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS valet_metrics_daily (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
                    metric_date DATE NOT NULL,

                    total_sessions INTEGER DEFAULT 0,
                    completed_sessions INTEGER DEFAULT 0,
                    cancelled_sessions INTEGER DEFAULT 0,
                    no_show_sessions INTEGER DEFAULT 0,

                    average_service_duration NUMERIC(5, 2),
                    average_retrieval_time NUMERIC(5, 2),
                    average_wait_time NUMERIC(5, 2),

                    peak_occupancy INTEGER DEFAULT 0,
                    average_occupancy NUMERIC(5, 2),

                    total_revenue NUMERIC(10, 2) DEFAULT 0,
                    total_tips NUMERIC(10, 2) DEFAULT 0,
                    average_tip_percentage NUMERIC(5, 2),

                    average_rating NUMERIC(3, 2),
                    total_ratings INTEGER DEFAULT 0,

                    total_incidents INTEGER DEFAULT 0,

                    attendant_hours NUMERIC(10, 2),
                    revenue_per_attendant_hour NUMERIC(10, 2),

                    created_at TIMESTAMP DEFAULT NOW(),

                    UNIQUE(venue_id, metric_date)
                );

                CREATE INDEX IF NOT EXISTS idx_valet_metrics_venue ON valet_metrics_daily(venue_id);
                CREATE INDEX IF NOT EXISTS idx_valet_metrics_date ON valet_metrics_daily(metric_date);
            """))
            conn.commit()
            print("✓ Created valet_metrics_daily table")

            # Add foreign key constraint for saved_vehicle_id (circular dependency)
            print("Adding saved_vehicle_id foreign key...")
            conn.execute(text("""
                ALTER TABLE valet_sessions
                DROP CONSTRAINT IF EXISTS fk_valet_sessions_saved_vehicle;

                ALTER TABLE valet_sessions
                ADD CONSTRAINT fk_valet_sessions_saved_vehicle
                FOREIGN KEY (saved_vehicle_id)
                REFERENCES saved_vehicles(id)
                ON DELETE SET NULL;
            """))
            conn.commit()
            print("✓ Added saved_vehicle_id foreign key")

        print("\n" + "="*70)
        print("VALET TABLES CREATED SUCCESSFULLY")
        print("="*70)
        print("\n✅ Created 8 valet service tables:")
        print("   1. saved_vehicles")
        print("   2. valet_sessions")
        print("   3. valet_status_events")
        print("   4. valet_communications")
        print("   5. valet_incidents")
        print("   6. valet_capacity")
        print("   7. valet_pricing")
        print("   8. valet_metrics_daily")
        print()

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    create_valet_tables()
