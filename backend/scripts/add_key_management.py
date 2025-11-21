#!/usr/bin/env python3
"""
Add key management fields to valet_sessions and create key_storage_configs table.
Run with: docker-compose exec api python -m scripts.add_key_management
"""
import sys
from sqlalchemy import text

from app.core.database import engine


def add_key_management():
    """Add key management to valet service."""
    print("\n" + "="*70)
    print("ADDING KEY MANAGEMENT TO VALET SERVICE")
    print("="*70 + "\n")

    try:
        with engine.connect() as conn:
            # 1. Add key management columns to valet_sessions table
            print("Adding key management columns to valet_sessions...")
            conn.execute(text("""
                -- Add key management fields
                ALTER TABLE valet_sessions
                ADD COLUMN IF NOT EXISTS key_tag_number VARCHAR(10),
                ADD COLUMN IF NOT EXISTS key_storage_zone VARCHAR(50),
                ADD COLUMN IF NOT EXISTS key_storage_box VARCHAR(50),
                ADD COLUMN IF NOT EXISTS key_storage_position VARCHAR(20),
                ADD COLUMN IF NOT EXISTS key_status VARCHAR(20),
                ADD COLUMN IF NOT EXISTS key_photo_url TEXT,
                ADD COLUMN IF NOT EXISTS key_notes TEXT,

                -- Add key tracking fields
                ADD COLUMN IF NOT EXISTS key_assigned_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
                ADD COLUMN IF NOT EXISTS key_assigned_at TIMESTAMP,
                ADD COLUMN IF NOT EXISTS key_grabbed_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
                ADD COLUMN IF NOT EXISTS key_grabbed_at TIMESTAMP;
            """))
            conn.commit()
            print("✓ Added key management columns to valet_sessions")

            # 2. Create index on key_tag_number
            print("Creating index on key_tag_number...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_valet_sessions_key_tag_number
                ON valet_sessions(key_tag_number);
            """))
            conn.commit()
            print("✓ Created index on key_tag_number")

            # 3. Create key_storage_configs table
            print("Creating key_storage_configs table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS key_storage_configs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE UNIQUE,

                    zones JSONB NOT NULL DEFAULT '[]'::jsonb,

                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS ix_key_storage_configs_venue
                ON key_storage_configs(venue_id);
            """))
            conn.commit()
            print("✓ Created key_storage_configs table")

        print("\n" + "="*70)
        print("KEY MANAGEMENT MIGRATION COMPLETE")
        print("="*70)
        print("\n✅ Changes applied:")
        print("   1. Added 11 key management columns to valet_sessions")
        print("   2. Created index on key_tag_number")
        print("   3. Created key_storage_configs table")
        print()

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    add_key_management()
