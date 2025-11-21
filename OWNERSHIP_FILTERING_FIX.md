# Ownership Filtering Fix ✅

Fixed the authorization issue where lot owners could see all parking lots instead of only their own.

---

## Problem

When logging in as `owner@greenfieldparking.com` (venue_admin role), the user could see all 229 parking lots in the system, not just their own Greenfield Plaza Parking lot.

This was a security/privacy issue - lot owners should only see and manage their own lots.

---

## Solution

Implemented a multi-level ownership and authorization system:

### 1. Added `owner_id` Field to ParkingLot Model

**File:** `/backend/app/models/parking.py`

```python
class ParkingLot(Base):
    __tablename__ = "parking_lots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # NEW

    # Relationships
    venue = relationship("Venue", back_populates="parking_lots")
    owner = relationship("User", foreign_keys=[owner_id])  # NEW
```

### 2. Database Migration

**Script:** `/backend/scripts/add_owner_id_migration.py`

```sql
ALTER TABLE parking_lots
ADD COLUMN owner_id UUID,
ADD CONSTRAINT fk_parking_lots_owner_id
    FOREIGN KEY (owner_id)
    REFERENCES users(id)
    ON DELETE SET NULL;

CREATE INDEX ix_parking_lots_owner_id ON parking_lots(owner_id);
```

### 3. Updated GET /parking/lots Endpoint

**File:** `/backend/app/api/v1/endpoints/parking.py`

```python
@router.get("/lots", response_model=List[ParkingLotPublic])
def get_available_parking_lots(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),  # NEW
):
    """
    Get available parking lots with role-based filtering:

    - venue_admin: Only their own lots
    - super_admin: All lots
    - Unauthenticated: All lots (for mobile app)
    """
    lots = ParkingService.get_available_parking_lots(db)

    # Filter by ownership for venue_admin users
    if current_user and current_user.role == "venue_admin":
        filtered_lots = []
        for lot in lots:
            full_lot = db.query(ParkingLot).filter(ParkingLot.id == lot.id).first()
            if full_lot and full_lot.owner_id == current_user.id:
                filtered_lots.append(lot)
        return filtered_lots

    # Super admin or unauthenticated - show all lots
    return lots
```

### 4. Updated POST /parking/lots Endpoint

Now automatically sets the `owner_id` when creating a lot:

```python
@router.post("/lots", response_model=ParkingLotPublic)
def create_parking_lot(
    lot_data: ParkingLotCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_lot = ParkingLot(
        name=lot_data.name,
        # ... other fields ...
        owner_id=current_user.id,  # NEW - automatically set owner
    )
```

### 5. Updated PUT /parking/lots/{id} Endpoint

Added ownership check - venue_admin can only update their own lots:

```python
@router.put("/lots/{lot_id}", response_model=ParkingLotPublic)
def update_parking_lot(
    lot_id: UUID,
    lot_data: ParkingLotUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # ... permission checks ...

    # venue_admin can only update their own lots
    if current_user.role == "venue_admin" and lot.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only update your own parking lots"
        )
```

### 6. Associated Existing Lot with Owner

**Script:** `/backend/scripts/associate_lot_with_owner.py`

Updated the existing "Greenfield Plaza Parking" lot to be owned by the `owner@greenfieldparking.com` user.

---

## Test Results

### Lot Owner (venue_admin)

```bash
docker-compose exec api python -m scripts.test_lot_owner
```

**Results:**
```
✓ Found 1 parking lot(s)
✅ Correctly filtered - owner only sees their own lot!

📍 Greenfield Plaza Parking
   Address: 5300 W Layton Ave, Greenfield, WI 53220
   Spaces: 75/75 available
```

### Super Admin

```bash
docker-compose exec api python -m scripts.test_super_admin_lots
```

**Results:**
```
✓ Found 229 parking lot(s)
✅ Correctly showing all lots (super_admin has full access)
```

---

## Authorization Matrix

| Role | GET /parking/lots | POST /parking/lots | PUT /parking/lots/{id} |
|------|------------------|-------------------|----------------------|
| **super_admin** | See ALL lots | Create owned by self | Update ANY lot |
| **venue_admin** | See ONLY own lots | Create owned by self | Update ONLY own lots |
| **venue_staff** | See ALL lots (public) | ❌ Forbidden | ❌ Forbidden |
| **customer** | See ALL lots (public) | ❌ Forbidden | ❌ Forbidden |
| **Unauthenticated** | See ALL lots (mobile) | ❌ Forbidden | ❌ Forbidden |

---

## Mobile App Compatibility

The public endpoint remains compatible with the mobile app:

- **Unauthenticated requests** (mobile app) still see all available lots
- **Authenticated requests** get role-based filtering automatically
- No breaking changes to existing mobile app code

---

## Database Schema Changes

### Before
```
parking_lots
  - id
  - venue_id (optional)
  - name
  - total_spaces
  - ...
```

### After
```
parking_lots
  - id
  - venue_id (optional)
  - owner_id (optional, FK to users)  ← NEW
  - name
  - total_spaces
  - ...
```

---

## Files Modified

1. `/backend/app/models/parking.py` - Added owner_id field and relationship
2. `/backend/app/api/v1/endpoints/parking.py` - Updated endpoints with filtering
3. `/backend/scripts/add_owner_id_migration.py` - Database migration (NEW)
4. `/backend/scripts/associate_lot_with_owner.py` - Associate existing lot (NEW)
5. `/backend/scripts/test_lot_owner.py` - Updated test to verify filtering
6. `/backend/scripts/test_super_admin_lots.py` - Test super_admin access (NEW)

---

## Security Benefits

✅ **Data Isolation** - Lot owners can't see other owners' data
✅ **Authorization Enforcement** - Can't update lots they don't own
✅ **Multi-tenant Support** - Multiple lot owners can use the same system
✅ **Backwards Compatible** - Mobile app still works without authentication
✅ **Role Hierarchy** - Super admins maintain full access for support/administration

---

## Next Steps (Optional)

Future enhancements could include:

1. **Venue-based Access** - Allow venue_staff to see lots within their venue
2. **Shared Ownership** - Support multiple owners for a single lot
3. **Access Delegation** - Allow owners to grant access to staff members
4. **Audit Logging** - Track who views/modifies which lots

---

**Status:** ✅ Fixed and tested

**Impact:** Lot owners now only see their own parking lots when logged into the admin dashboard

**Testing:** Both lot owner and super admin access verified working correctly
