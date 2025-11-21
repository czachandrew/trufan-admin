#!/usr/bin/env python3
"""Inspect database schema to see what columns actually exist"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from sqlalchemy import text

def inspect_schema():
    db = SessionLocal()
    try:
        # Check parking_lots table structure
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'parking_lots'
            ORDER BY ordinal_position;
        """))

        print("📋 parking_lots table columns:")
        print("-" * 60)
        for row in result:
            print(f"  {row.column_name:30} {row.data_type:20} {'NULL' if row.is_nullable == 'YES' else 'NOT NULL'}")

        print("\n" + "="*60 + "\n")

        # Check venues table structure
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'venues'
            ORDER BY ordinal_position;
        """))

        print("📋 venues table columns:")
        print("-" * 60)
        for row in result:
            print(f"  {row.column_name:30} {row.data_type:20} {'NULL' if row.is_nullable == 'YES' else 'NOT NULL'}")

    finally:
        db.close()

if __name__ == "__main__":
    inspect_schema()
