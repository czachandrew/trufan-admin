#!/usr/bin/env python3
"""
Create valet worker accounts for a lot owner.
Run with: docker-compose exec api python -m scripts.create_valet_workers
"""
import sys
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.venue import Venue, VenueStaff


def create_valet_workers():
    """Create valet worker accounts associated with Greenfield lot."""
    db: Session = SessionLocal()

    try:
        print("\n" + "="*70)
        print("CREATING VALET WORKER ACCOUNTS")
        print("="*70 + "\n")

        # Get the lot owner
        owner = db.query(User).filter(User.email == "owner@greenfieldparking.com").first()
        if not owner:
            print("❌ Lot owner not found!")
            print("   Run: docker-compose exec api python -m scripts.create_lot_owner")
            sys.exit(1)

        print(f"✓ Found lot owner: {owner.email}")
        print(f"  Owner ID: {owner.id}\n")

        # Create or get venue for Greenfield Plaza Parking
        # First check if we have a venue
        venue = db.query(Venue).filter(Venue.name.ilike("%Greenfield%")).first()

        if not venue:
            print("Creating venue for Greenfield Plaza Parking...")
            venue = Venue(
                name="Greenfield Plaza",
                slug="greenfield-plaza",
                email="contact@greenfieldplaza.com",
                phone="+14141234567",
                address_line1="5300 W Layton Ave",
                city="Greenfield",
                state="WI",
                zip_code="53220",
                country="USA",
                is_active=True,
                description="Shopping center with valet parking service"
            )
            db.add(venue)
            db.commit()
            db.refresh(venue)
            print(f"✓ Created venue: {venue.name} (ID: {venue.id})")
        else:
            print(f"✓ Found existing venue: {venue.name} (ID: {venue.id})")

        # Associate owner with venue as admin
        owner_staff = db.query(VenueStaff).filter(
            VenueStaff.user_id == owner.id,
            VenueStaff.venue_id == venue.id
        ).first()

        if not owner_staff:
            owner_staff = VenueStaff(
                user_id=owner.id,
                venue_id=venue.id,
                role="admin",
                is_active=True,
                permissions={"valet": True, "parking": True, "all_access": True}
            )
            db.add(owner_staff)
            db.commit()
            print(f"✓ Associated owner with venue as admin\n")
        else:
            print(f"✓ Owner already associated with venue\n")

        # Create valet workers
        print("Creating valet worker accounts...")

        workers = [
            {
                "email": "valet1@greenfieldparking.com",
                "first_name": "Mike",
                "last_name": "Johnson",
                "role": "valet_attendant"
            },
            {
                "email": "valet2@greenfieldparking.com",
                "first_name": "Sarah",
                "last_name": "Williams",
                "role": "valet_attendant"
            },
            {
                "email": "valet_supervisor@greenfieldparking.com",
                "first_name": "David",
                "last_name": "Martinez",
                "role": "supervisor"
            }
        ]

        created_workers = []

        for worker_data in workers:
            # Check if user already exists
            existing_user = db.query(User).filter(
                User.email == worker_data["email"]
            ).first()

            if existing_user:
                print(f"  ⚠️  User already exists: {worker_data['email']}")
                user = existing_user
            else:
                # Create user account with venue_staff role
                user = User(
                    email=worker_data["email"],
                    hashed_password=get_password_hash("password"),
                    first_name=worker_data["first_name"],
                    last_name=worker_data["last_name"],
                    role=UserRole.VENUE_STAFF,  # Staff role for valet workers
                    is_active=True,
                    email_verified=True,
                    created_at=datetime.utcnow(),
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"  ✓ Created user: {user.email} ({user.first_name} {user.last_name})")

            # Associate with venue through VenueStaff
            venue_staff = db.query(VenueStaff).filter(
                VenueStaff.user_id == user.id,
                VenueStaff.venue_id == venue.id
            ).first()

            if not venue_staff:
                venue_staff = VenueStaff(
                    user_id=user.id,
                    venue_id=venue.id,
                    role=worker_data["role"],
                    is_active=True,
                    permissions={
                        "valet": True,
                        "check_in": True,
                        "check_out": True,
                        "view_queue": True,
                        "update_status": True,
                        "file_incidents": worker_data["role"] == "supervisor"
                    }
                )
                db.add(venue_staff)
                db.commit()
                print(f"    → Associated with venue as {worker_data['role']}")

            created_workers.append({
                "user": user,
                "venue_staff": venue_staff
            })

        print("\n" + "="*70)
        print("VALET WORKER ACCOUNTS CREATED")
        print("="*70)
        print("\n✅ Created/verified 3 valet worker accounts:")
        print(f"\n📍 Venue: {venue.name}")
        print(f"   Venue ID: {venue.id}")
        print(f"\n👤 Lot Owner (Admin):")
        print(f"   Email: owner@greenfieldparking.com")
        print(f"   Password: password")
        print(f"   Role: venue_admin → admin at venue")
        print(f"\n👷 Valet Workers:")
        print(f"\n   1. Mike Johnson (Valet Attendant)")
        print(f"      Email: valet1@greenfieldparking.com")
        print(f"      Password: password")
        print(f"      Role: venue_staff → valet_attendant at venue")
        print(f"\n   2. Sarah Williams (Valet Attendant)")
        print(f"      Email: valet2@greenfieldparking.com")
        print(f"      Password: password")
        print(f"      Role: venue_staff → valet_attendant at venue")
        print(f"\n   3. David Martinez (Valet Supervisor)")
        print(f"      Email: valet_supervisor@greenfieldparking.com")
        print(f"      Password: password")
        print(f"      Role: venue_staff → supervisor at venue")
        print()

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    create_valet_workers()
