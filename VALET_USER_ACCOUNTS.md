# Valet User Accounts & Permissions

Complete guide to user roles, venue associations, and permissions for valet service testing.

---

## Overview

The valet service uses a **hierarchical permission system** with venue-based access control:

1. **User Roles** - Global role assigned to each user
2. **Venue Association** - Links staff to specific venues via `VenueStaff` table
3. **Venue Permissions** - Fine-grained permissions per venue

---

## User Roles

### Available Roles

Defined in `app/models/user.py`:

```python
class UserRole(str, enum.Enum):
    CUSTOMER = "customer"           # Regular customers
    VENUE_STAFF = "venue_staff"     # Valet workers, attendants
    VENUE_ADMIN = "venue_admin"     # Lot owners, managers
    SUPER_ADMIN = "super_admin"     # Platform administrators
```

### Role Capabilities

| Role | Description | Valet Access |
|------|-------------|--------------|
| **CUSTOMER** | Regular users | Can book valet, view own sessions |
| **VENUE_STAFF** | Valet workers | Staff endpoints for assigned venue only |
| **VENUE_ADMIN** | Lot owners | Staff endpoints + lot management for assigned venues |
| **SUPER_ADMIN** | Platform admins | Full access to all venues and features |

---

## Venue Association (VenueStaff Table)

Staff users (venue_staff and venue_admin) must be associated with venues through the `VenueStaff` table:

```sql
CREATE TABLE venue_staff (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    venue_id UUID REFERENCES venues(id),
    role VARCHAR(50),              -- e.g., "admin", "supervisor", "valet_attendant"
    permissions JSONB,              -- Fine-grained permissions
    is_active BOOLEAN,
    UNIQUE(user_id, venue_id)
);
```

### How It Works

1. User has global `role` (e.g., VENUE_STAFF)
2. VenueStaff record links user to specific venue(s)
3. `role` field in VenueStaff defines their function at that venue
4. `permissions` JSONB stores specific capabilities

### Permission Checking

When a valet worker accesses staff endpoints:

```python
def check_staff_permissions(current_user, venue_id, db):
    # 1. Check global role
    if current_user.role not in [VENUE_STAFF, VENUE_ADMIN, SUPER_ADMIN]:
        raise 403 "Staff role required"

    # 2. Super admins bypass venue check
    if current_user.role == SUPER_ADMIN:
        return

    # 3. Check venue association
    venue_staff = db.query(VenueStaff).filter(
        VenueStaff.user_id == current_user.id,
        VenueStaff.venue_id == venue_id,
        VenueStaff.is_active == True
    ).first()

    if not venue_staff:
        raise 403 "You do not have access to this venue"
```

---

## Test Accounts Created

### 1. Lot Owner (Admin)

**Login:**
- **Email:** owner@greenfieldparking.com
- **Password:** password

**Permissions:**
- User.role = `VENUE_ADMIN`
- Associated with Greenfield Plaza venue as `admin`
- VenueStaff.permissions = `{"valet": true, "parking": true, "all_access": true}`

**Can Do:**
- Manage parking lots (owns Greenfield Plaza Parking)
- Access all valet staff endpoints for their venue
- View all sessions at their venue
- Process refunds, manage incidents
- View metrics and analytics

### 2. Valet Attendant #1 (Mike)

**Login:**
- **Email:** valet1@greenfieldparking.com
- **Password:** password

**Permissions:**
- User.role = `VENUE_STAFF`
- Associated with Greenfield Plaza venue as `valet_attendant`
- VenueStaff.permissions = `{"valet": true, "check_in": true, "check_out": true, "view_queue": true, "update_status": true}`

**Can Do:**
- Check in vehicles (scan ticket/PIN)
- Park vehicles and record location
- View active queue for Greenfield Plaza
- Update session status (parked → retrieving → ready)
- Complete check-outs
- View capacity metrics

**Cannot Do:**
- Access other venues
- Process refunds (requires admin)
- Manage lots or pricing

### 3. Valet Attendant #2 (Sarah)

**Login:**
- **Email:** valet2@greenfieldparking.com
- **Password:** password

**Permissions:**
- Same as Mike (valet_attendant)

### 4. Valet Supervisor (David)

**Login:**
- **Email:** valet_supervisor@greenfieldparking.com
- **Password:** password

**Permissions:**
- User.role = `VENUE_STAFF`
- Associated with Greenfield Plaza venue as `supervisor`
- VenueStaff.permissions = `{"valet": true, "check_in": true, "check_out": true, "view_queue": true, "update_status": true, "file_incidents": true}`

**Can Do:**
- Everything valet attendants can do
- File incident reports
- View detailed metrics
- Manage queue priorities

**Cannot Do:**
- Process refunds (still requires venue_admin or super_admin)

### 5. Platform Admin (You)

**Login:**
- **Email:** czachandrew@gmail.com
- **Password:** password

**Permissions:**
- User.role = `SUPER_ADMIN`
- No venue association required (access all venues)

**Can Do:**
- Everything, everywhere
- Access all venues without VenueStaff records
- System administration

---

## Venue Information

**Created Venue:**
- **Name:** Greenfield Plaza
- **ID:** 380ccab9-fa83-4c25-894f-7021ba6714ef
- **Address:** 5300 W Layton Ave, Greenfield, WI 53220

**Associated Parking Lot:**
- **Name:** Greenfield Plaza Parking
- **Owner:** owner@greenfieldparking.com
- **Capacity:** 75 spaces

All valet workers are associated with this venue through the VenueStaff table.

---

## Testing Workflow

### 1. Customer Books Valet (Mobile App)

**As a customer:**
```bash
curl -X POST http://localhost:8000/api/v1/valet/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "venueId": "380ccab9-fa83-4c25-894f-7021ba6714ef",
    "vehicle": {
      "licensePlate": "ABC123",
      "make": "Toyota",
      "model": "Camry",
      "color": "Silver"
    },
    "serviceType": "standard",
    "contactPhone": "+15555551234"
  }'
```

Response includes:
- `ticketNumber` (e.g., "V-2847")
- `pin` (e.g., "4729")
- `qrCodeData` for scanning

### 2. Valet Worker Checks In (Staff App)

**Login as:** valet1@greenfieldparking.com

**Check in with ticket/PIN:**
```bash
curl -X PATCH http://localhost:8000/api/v1/valet/staff/sessions/{id}/status \
  -H "Authorization: Bearer VALET1_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "newStatus": "checked_in"
  }'
```

**Permission Check:**
- ✅ User has VENUE_STAFF role
- ✅ User associated with Greenfield Plaza venue
- ✅ Session belongs to Greenfield Plaza venue
- ✅ Request allowed

### 3. Valet Parks Vehicle

**Update status to parked:**
```bash
curl -X PATCH http://localhost:8000/api/v1/valet/staff/sessions/{id}/status \
  -H "Authorization: Bearer VALET1_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "newStatus": "parked",
    "parkingLocation": {
      "section": "B",
      "level": "2",
      "spot": "14"
    }
  }'
```

### 4. Customer Requests Retrieval

**Customer uses mobile app or SMS:**
```bash
curl -X POST http://localhost:8000/api/v1/valet/sessions/{id}/request-retrieval \
  -H "Authorization: Bearer CUSTOMER_TOKEN"
```

### 5. Valet Worker Retrieves & Delivers

**View queue:**
```bash
curl http://localhost:8000/api/v1/valet/staff/queue?venueId=380ccab9-fa83-4c25-894f-7021ba6714ef \
  -H "Authorization: Bearer VALET2_TOKEN"
```

**Update to retrieving:**
```bash
curl -X PATCH http://localhost:8000/api/v1/valet/staff/sessions/{id}/status \
  -H "Authorization: Bearer VALET2_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"newStatus": "retrieving"}'
```

**Mark ready:**
```bash
curl -X PATCH http://localhost:8000/api/v1/valet/staff/sessions/{id}/status \
  -H "Authorization: Bearer VALET2_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"newStatus": "ready"}'
```

---

## Permission Scenarios

### ✅ Allowed Access

**Scenario:** Valet1 accessing queue for Greenfield Plaza
- User: valet1@greenfieldparking.com (VENUE_STAFF)
- Venue: 380ccab9-fa83-4c25-894f-7021ba6714ef (Greenfield Plaza)
- VenueStaff record exists linking them
- **Result:** ✅ Access granted

### ❌ Denied Access

**Scenario:** Valet1 trying to access different venue
- User: valet1@greenfieldparking.com (VENUE_STAFF)
- Venue: {different-venue-id}
- No VenueStaff record for that venue
- **Result:** ❌ 403 "You do not have access to this venue"

### ✅ Super Admin Bypass

**Scenario:** Platform admin accessing any venue
- User: czachandrew@gmail.com (SUPER_ADMIN)
- Venue: any venue ID
- No VenueStaff record needed
- **Result:** ✅ Access granted (super admin bypass)

---

## Adding More Workers

To add additional valet workers for a venue:

```python
# 1. Create user account
user = User(
    email="newvalet@greenfieldparking.com",
    hashed_password=get_password_hash("password"),
    first_name="John",
    last_name="Smith",
    role=UserRole.VENUE_STAFF,
    is_active=True
)
db.add(user)
db.commit()

# 2. Associate with venue
venue_staff = VenueStaff(
    user_id=user.id,
    venue_id="380ccab9-fa83-4c25-894f-7021ba6714ef",
    role="valet_attendant",
    is_active=True,
    permissions={
        "valet": True,
        "check_in": True,
        "check_out": True,
        "view_queue": True,
        "update_status": True
    }
)
db.add(venue_staff)
db.commit()
```

Or use the management dashboard (future feature) to invite staff members.

---

## Summary

✅ **User Roles** - Global roles define base permissions (CUSTOMER, VENUE_STAFF, VENUE_ADMIN, SUPER_ADMIN)

✅ **Venue Association** - VenueStaff table links staff to specific venues

✅ **Permission Checks** - All staff endpoints verify both role AND venue association

✅ **Test Accounts** - 4 accounts created (1 owner + 3 workers) all associated with Greenfield Plaza

✅ **Security** - Staff can only access venues they're associated with (except super_admin)

✅ **Ready for Testing** - All accounts can be used to test valet workflows

---

**Next Steps:**
1. Use API docs to test endpoints: http://localhost:8000/api/v1/docs
2. Test authentication with each account
3. Verify venue isolation (valet1 can't access other venues)
4. Test complete valet workflow from booking to check-out
