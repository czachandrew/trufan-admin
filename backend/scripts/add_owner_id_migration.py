#!/usr/bin/env python3
"""
Add owner_id column to parking_lots table.
Run with: docker-compose exec api python -m scripts.add_owner_id_migration
"""
import sys
from sqlalchemy import text

from app.core.database import engine, SessionLocal


def run_migration():
    """Add owner_id column to parking_lots."""
    print("\n" + "="*60)
    print("ADDING OWNER_ID TO PARKING_LOTS TABLE")
    print("="*60 + "\n")

    try:
        with engine.connect() as conn:
            # Check if column already exists
            check_query = text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='parking_lots'
                AND column_name='owner_id'
            """)
            result = conn.execute(check_query)
            if result.fetchone():
                print("✓ owner_id column already exists, skipping migration")
                return

            # Add owner_id column
            print("Adding owner_id column...")
            alter_query = text("""
                ALTER TABLE parking_lots
                ADD COLUMN owner_id UUID,
                ADD CONSTRAINT fk_parking_lots_owner_id
                    FOREIGN KEY (owner_id)
                    REFERENCES users(id)
                    ON DELETE SET NULL
            """)
            conn.execute(alter_query)
            conn.commit()

            print("✓ Added owner_id column to parking_lots")
            print("✓ Added foreign key constraint to users table")

            # Create index
            print("Creating index on owner_id...")
            index_query = text("""
                CREATE INDEX ix_parking_lots_owner_id
                ON parking_lots(owner_id)
            """)
            conn.execute(index_query)
            conn.commit()

            print("✓ Created index on owner_id")

        print("\n" + "="*60)
        print("MIGRATION COMPLETE")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    run_migration()
