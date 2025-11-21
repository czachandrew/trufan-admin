"""
Database Migration Script: Add Convenience Store Tables

This script creates all necessary tables for the convenience store feature:
- convenience_items: Items available for purchase
- convenience_orders: Customer orders
- convenience_order_items: Line items in orders
- convenience_order_events: Order status history
- convenience_store_config: Venue-specific configuration

Run this script to add convenience store functionality to an existing database.
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_convenience_store_tables():
    """Create all convenience store tables."""

    # Create engine
    engine = create_engine(settings.DATABASE_URL)

    logger.info("Creating convenience store tables...")

    # SQL for creating tables
    sql_statements = [
        # 1. Create convenience_items table
        """
        CREATE TABLE IF NOT EXISTS convenience_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,

            -- Item details
            name VARCHAR(200) NOT NULL,
            description TEXT,
            image_url TEXT,
            category VARCHAR(50),

            -- Pricing
            base_price NUMERIC(10, 2) NOT NULL,
            markup_amount NUMERIC(10, 2) DEFAULT 0 NOT NULL,
            markup_percent NUMERIC(5, 2) DEFAULT 0 NOT NULL,
            final_price NUMERIC(10, 2) NOT NULL,

            -- Source
            source_store VARCHAR(200) NOT NULL,
            source_address TEXT,
            estimated_shopping_time_minutes INTEGER DEFAULT 15 NOT NULL,

            -- Availability
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            requires_age_verification BOOLEAN DEFAULT FALSE NOT NULL,
            max_quantity_per_order INTEGER DEFAULT 10 NOT NULL,

            -- Metadata
            tags TEXT[],
            sku VARCHAR(100),
            barcode VARCHAR(100),

            -- Time tracking
            created_at TIMESTAMP DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
            created_by_id UUID REFERENCES users(id) ON DELETE SET NULL
        );
        """,

        # Create indexes for convenience_items
        """
        CREATE INDEX IF NOT EXISTS ix_convenience_items_id ON convenience_items(id);
        CREATE INDEX IF NOT EXISTS ix_convenience_items_venue_id ON convenience_items(venue_id);
        CREATE INDEX IF NOT EXISTS ix_convenience_items_is_active ON convenience_items(is_active);
        CREATE INDEX IF NOT EXISTS ix_convenience_items_venue_active ON convenience_items(venue_id, is_active);
        CREATE INDEX IF NOT EXISTS ix_convenience_items_category ON convenience_items(category);
        CREATE INDEX IF NOT EXISTS ix_convenience_items_source_store ON convenience_items(source_store);
        """,

        # 2. Create convenience_orders table
        """
        CREATE TABLE IF NOT EXISTS convenience_orders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_number VARCHAR(20) UNIQUE NOT NULL,

            -- Relationships
            venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            parking_session_id UUID REFERENCES valet_sessions(id) ON DELETE SET NULL,

            -- Order details
            status VARCHAR(30) DEFAULT 'pending' NOT NULL,

            -- Pricing
            subtotal NUMERIC(10, 2) NOT NULL,
            service_fee NUMERIC(10, 2) NOT NULL,
            tax NUMERIC(10, 2) DEFAULT 0 NOT NULL,
            tip_amount NUMERIC(10, 2) DEFAULT 0 NOT NULL,
            total_amount NUMERIC(10, 2) NOT NULL,

            -- Payment
            payment_status VARCHAR(30) DEFAULT 'pending' NOT NULL,
            payment_intent_id VARCHAR(200),
            payment_method VARCHAR(50),

            -- Fulfillment
            assigned_staff_id UUID REFERENCES users(id) ON DELETE SET NULL,
            storage_location VARCHAR(100),
            delivery_instructions TEXT,
            special_instructions TEXT,

            -- Proof
            receipt_photo_url TEXT,
            delivery_photo_url TEXT,

            -- Timing
            estimated_ready_time TIMESTAMP,
            confirmed_at TIMESTAMP,
            shopping_started_at TIMESTAMP,
            purchased_at TIMESTAMP,
            stored_at TIMESTAMP,
            ready_at TIMESTAMP,
            delivered_at TIMESTAMP,
            completed_at TIMESTAMP,
            cancelled_at TIMESTAMP,

            -- Parking integration
            complimentary_time_added_minutes INTEGER DEFAULT 0 NOT NULL,

            -- Rating
            rating INTEGER CHECK (rating >= 1 AND rating <= 5),
            feedback TEXT,

            -- Metadata
            cancellation_reason TEXT,
            refund_amount NUMERIC(10, 2),
            refund_reason TEXT,

            created_at TIMESTAMP DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP DEFAULT NOW() NOT NULL
        );
        """,

        # Create indexes for convenience_orders
        """
        CREATE INDEX IF NOT EXISTS ix_convenience_orders_id ON convenience_orders(id);
        CREATE INDEX IF NOT EXISTS ix_convenience_orders_order_number ON convenience_orders(order_number);
        CREATE INDEX IF NOT EXISTS ix_convenience_orders_venue_id ON convenience_orders(venue_id);
        CREATE INDEX IF NOT EXISTS ix_convenience_orders_user_id ON convenience_orders(user_id);
        CREATE INDEX IF NOT EXISTS ix_convenience_orders_parking_session_id ON convenience_orders(parking_session_id);
        CREATE INDEX IF NOT EXISTS ix_convenience_orders_status ON convenience_orders(status);
        CREATE INDEX IF NOT EXISTS ix_convenience_orders_venue_status ON convenience_orders(venue_id, status);
        """,

        # 3. Create convenience_order_items table
        """
        CREATE TABLE IF NOT EXISTS convenience_order_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_id UUID NOT NULL REFERENCES convenience_orders(id) ON DELETE CASCADE,
            item_id UUID REFERENCES convenience_items(id) ON DELETE SET NULL,

            -- Snapshot of item at time of order
            item_name VARCHAR(200) NOT NULL,
            item_description TEXT,
            item_image_url TEXT,
            source_store VARCHAR(200),

            -- Pricing at time of order
            quantity INTEGER DEFAULT 1 NOT NULL,
            unit_price NUMERIC(10, 2) NOT NULL,
            line_total NUMERIC(10, 2) NOT NULL,

            -- Fulfillment
            status VARCHAR(30) DEFAULT 'pending' NOT NULL,
            substitution_notes TEXT,
            actual_price NUMERIC(10, 2),

            created_at TIMESTAMP DEFAULT NOW() NOT NULL
        );
        """,

        # Create indexes for convenience_order_items
        """
        CREATE INDEX IF NOT EXISTS ix_convenience_order_items_id ON convenience_order_items(id);
        CREATE INDEX IF NOT EXISTS ix_convenience_order_items_order_id ON convenience_order_items(order_id);
        """,

        # 4. Create convenience_order_events table
        """
        CREATE TABLE IF NOT EXISTS convenience_order_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_id UUID NOT NULL REFERENCES convenience_orders(id) ON DELETE CASCADE,

            status VARCHAR(30) NOT NULL,
            notes TEXT,
            photo_url TEXT,
            location VARCHAR(100),

            created_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT NOW() NOT NULL
        );
        """,

        # Create indexes for convenience_order_events
        """
        CREATE INDEX IF NOT EXISTS ix_convenience_order_events_id ON convenience_order_events(id);
        CREATE INDEX IF NOT EXISTS ix_convenience_order_events_order_id ON convenience_order_events(order_id);
        CREATE INDEX IF NOT EXISTS ix_convenience_order_events_created_at ON convenience_order_events(created_at);
        CREATE INDEX IF NOT EXISTS ix_convenience_order_events_order_created ON convenience_order_events(order_id, created_at);
        """,

        # 5. Create convenience_store_config table
        """
        CREATE TABLE IF NOT EXISTS convenience_store_config (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            venue_id UUID NOT NULL UNIQUE REFERENCES venues(id) ON DELETE CASCADE,

            -- Feature toggle
            is_enabled BOOLEAN DEFAULT TRUE NOT NULL,

            -- Pricing
            default_service_fee_percent NUMERIC(5, 2) DEFAULT 15.00 NOT NULL,
            minimum_order_amount NUMERIC(10, 2) DEFAULT 5.00 NOT NULL,
            maximum_order_amount NUMERIC(10, 2) DEFAULT 200.00 NOT NULL,

            -- Timing
            default_complimentary_parking_minutes INTEGER DEFAULT 15 NOT NULL,
            average_fulfillment_time_minutes INTEGER DEFAULT 30 NOT NULL,

            -- Availability
            operating_hours JSONB,

            -- Messaging
            welcome_message TEXT DEFAULT 'Want us to grab a few things for you while you park?',
            instructions_message TEXT,

            -- Storage locations available
            storage_locations TEXT[],

            created_at TIMESTAMP DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP DEFAULT NOW() NOT NULL
        );
        """,

        # Create indexes for convenience_store_config
        """
        CREATE INDEX IF NOT EXISTS ix_convenience_store_config_id ON convenience_store_config(id);
        CREATE INDEX IF NOT EXISTS ix_convenience_store_config_venue_id ON convenience_store_config(venue_id);
        """,
    ]

    # Execute each statement
    with engine.connect() as connection:
        for idx, sql in enumerate(sql_statements, 1):
            try:
                logger.info(f"Executing statement {idx}/{len(sql_statements)}...")
                connection.execute(text(sql))
                connection.commit()
                logger.info(f"Statement {idx} executed successfully")
            except Exception as e:
                logger.error(f"Error executing statement {idx}: {e}")
                raise

    logger.info("All convenience store tables created successfully!")


def verify_tables():
    """Verify that all tables were created."""

    engine = create_engine(settings.DATABASE_URL)

    tables = [
        "convenience_items",
        "convenience_orders",
        "convenience_order_items",
        "convenience_order_events",
        "convenience_store_config"
    ]

    logger.info("Verifying tables...")

    with engine.connect() as connection:
        for table in tables:
            result = connection.execute(text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
            ))
            exists = result.scalar()

            if exists:
                logger.info(f"✓ Table '{table}' exists")
            else:
                logger.error(f"✗ Table '{table}' does not exist")
                return False

    logger.info("All tables verified successfully!")
    return True


def main():
    """Main migration function."""

    try:
        logger.info("=" * 60)
        logger.info("Convenience Store Database Migration")
        logger.info("=" * 60)

        # Create tables
        create_convenience_store_tables()

        # Verify tables
        verify_tables()

        logger.info("=" * 60)
        logger.info("Migration completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
