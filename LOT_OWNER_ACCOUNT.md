# Lot Owner Account - Greenfield Plaza Parking

A single parking lot owner account has been created for testing the admin dashboard.

---

## Account Details

**Email:** owner@greenfieldparking.com
**Password:** password
**Role:** venue_admin (lot owner/operator)
**User ID:** 5d7be7d2-11c9-4110-b622-056e535ecdea

---

## Parking Lot Details

**Name:** Greenfield Plaza Parking
**Description:** Convenient parking for Greenfield Plaza shops and restaurants
**Address:** 5300 W Layton Ave, Greenfield, WI 53220
**Lot ID:** 3a51164e-49ed-46de-8986-537b0bc3ce39

**Capacity:**
- Total Spaces: 75
- Available Spaces: 75 (initially)

**Location:**
- Latitude: 42.9614
- Longitude: -88.0126
- City: Greenfield, WI

**Pricing:**
- Base Rate: $5.00
- Hourly Rate: $3.00
- Max Daily Rate: $25.00
- Min Duration: 15 minutes
- Max Duration: 24 hours

**Status:** Active ✅

---

## Testing the Account

### Login via API
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "owner@greenfieldparking.com",
    "password": "password"
  }'
```

### View Their Parking Lot
```bash
# After logging in, use the token to view all lots
curl http://localhost:8000/api/v1/parking/lots \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## What This Account Can Do

As a **venue_admin** role, this lot owner can:

✅ **View and manage their parking lot(s)**
- GET /parking/lots - See all lots
- POST /parking/lots - Create new lots
- PUT /parking/lots/{id} - Update lot details
- GET /parking/lots/{id}/spaces - View spaces

✅ **View and manage parking sessions**
- GET /parking/sessions - See all parking sessions
- View session details, vehicle info
- Extend parking time
- End sessions early

✅ **View opportunities**
- GET /partner/opportunities - See all partner opportunities
- Useful for understanding nearby offers for their customers

❌ **Cannot do (requires super_admin)**
- Create other admin users
- Manage other venues' lots
- System-wide configuration

---

## Use Case

This account represents a typical TruFan customer:
- **Small business owner** operating a single parking lot
- **Located in Greenfield, WI** (suburban Milwaukee area)
- **75 spaces** - medium-sized facility
- **Simple pricing** - $3/hour, max $25/day
- **Uses dashboard to:**
  - Monitor real-time parking occupancy
  - View active parking sessions
  - See vehicle/customer information
  - Manage pricing and availability
  - Track daily revenue

---

## All Test Accounts

You now have two accounts for testing:

### 1. Super Admin (Platform Owner)
- **Email:** czachandrew@gmail.com
- **Password:** password
- **Role:** super_admin
- **Purpose:** Full platform administration

### 2. Lot Owner (Customer)
- **Email:** owner@greenfieldparking.com
- **Password:** password
- **Role:** venue_admin
- **Purpose:** Single lot operator

---

**Created:** 2025-11-04
**Status:** ✅ Ready to use
