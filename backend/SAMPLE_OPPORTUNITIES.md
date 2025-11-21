# Sample Opportunities for iOS Testing

## Overview

Sample opportunities have been created for testing the iOS Opportunity Discovery feature. These opportunities are **publicly viewable** (no authentication required) and can be used to test the complete user flow.

---

## Test Partner

**Name:** Main Street Coffee Co.
**Type:** Cafe
**Location:** Greenfield, WI (42.9614, -88.0126)
**API Key:** `pk_sample_test_key_999`
**Address:** 123 Main Street, Greenfield, WI 53220

---

## Sample Opportunities

### 1. ☕ Free Pastry with Any Coffee

**Type:** Discovery
**Value Proposition:** Buy any coffee, get a fresh pastry free! Perfect way to start your day.

**Trigger Rules:**
- Time remaining: 20-90 minutes
- Days: Monday-Friday
- Time of day: 6:00 AM - 11:00 AM

**Value Details:**
- Fixed value: $4.50
- Perks: Fresh baked, artisan coffee
- Parking extension: +15 minutes

**Capacity:** 23/200 claimed

**Priority Score:** 75

---

### 2. 🍔 $8 Lunch Special

**Type:** Bundle
**Value Proposition:** Gourmet burger, fries, and a drink for just $8. Usually $14!

**Trigger Rules:**
- Time remaining: 30-120 minutes
- Time of day: 11:00 AM - 2:30 PM

**Value Details:**
- Fixed discount: $6.00 off
- Original price: $14.00
- Perks: Includes drink, fast service
- Parking extension: +30 minutes

**Capacity:** 12/100 claimed

**Priority Score:** 85

---

### 3. ☀️ 25% Off Afternoon Treats

**Type:** Convenience
**Value Proposition:** Get 25% off any specialty drink or dessert between 2-5pm

**Trigger Rules:**
- Time remaining: 25-180 minutes
- Time of day: 2:00 PM - 5:00 PM

**Value Details:**
- Discount: 25%
- Perks: Happy hour special, outdoor seating
- Parking extension: +20 minutes

**Capacity:** Unlimited

**Priority Score:** 70

---

## Testing Instructions

### 1. View Opportunities (Public - No Auth Required)

```bash
# Get Greenfield parking lot ID first
curl http://localhost:8000/api/v1/parking/lots | jq '.[] | select(.name | contains("Greenfield")) | {id, name}'

# Create a parking session
curl -X POST http://localhost:8000/api/v1/parking/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "lot_id": "YOUR_LOT_ID",
    "vehicle_plate": "TEST999",
    "vehicle_make": "Toyota",
    "vehicle_model": "Test",
    "vehicle_color": "Blue",
    "duration_hours": 2.0,
    "contact_email": "test@example.com"
  }'

# View opportunities WITHOUT authentication (public!)
curl "http://localhost:8000/api/v1/opportunities/active?session_id=YOUR_SESSION_ID"
```

### 2. View Opportunity Details (Public - No Auth Required)

```bash
# View details of a specific opportunity
curl http://localhost:8000/api/v1/opportunities/OPPORTUNITY_ID
```

### 3. Accept Opportunity (Requires Authentication)

```bash
# This will fail with 403/401 without authentication
curl -X POST http://localhost:8000/api/v1/opportunities/OPPORTUNITY_ID/accept \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "parking_session_id": "YOUR_SESSION_ID"
  }'
```

---

## iOS Testing Flow

### Guest User Flow (No Account)

1. **Create parking session** - User parks, session created
2. **View opportunities** - App calls `/opportunities/active?session_id={id}` WITHOUT auth token
3. **See 3 sample opportunities** - Should display all 3 opportunities above
4. **Tap opportunity** - Navigate to detail view, call `/opportunities/{id}` WITHOUT auth token
5. **Tap "Sign In to Accept"** - Show authentication prompt
6. **Sign up/Login** - User creates account or logs in
7. **Accept opportunity** - Now call `/opportunities/{id}/accept` WITH auth token
8. **Receive claim code** - Get 8-character code like "2X4H4XDB"
9. **Show code to partner** - Partner validates using their API key

### Authenticated User Flow

1. **Create parking session** - User parks, session created
2. **View opportunities** - App calls `/opportunities/active?session_id={id}` WITH auth token
3. **Get personalized results** - Based on user preferences and history
4. **Tap opportunity** - Backend tracks "viewed" interaction
5. **Tap "Accept"** - Directly accepts, no auth prompt
6. **Receive claim code** - Get code instantly
7. **Show code to partner** - Partner validates

---

## Expected Behavior Based on Time of Day

**6:00 AM - 11:00 AM:**
- ☕ Free Pastry with Any Coffee will show up

**11:00 AM - 2:30 PM:**
- 🍔 $8 Lunch Special will show up
- Other lunch opportunities may appear

**2:00 PM - 5:00 PM:**
- ☀️ 25% Off Afternoon Treats will show up
- 🍔 $8 Lunch Special will show up (until 2:30 PM)

**Other times:**
- Opportunities with no time restrictions may still appear
- Relevance scoring will prioritize best matches

---

## Running Test Scripts

### Add Sample Opportunities (Already Done)

```bash
docker-compose exec api python -m scripts.add_sample_opportunities
```

### Test Public Opportunity Viewing

```bash
docker-compose exec api python -m scripts.test_sample_opportunities
```

### Run Full Workflow Test

```bash
docker-compose exec api python -m scripts.test_opportunity_workflow
```

---

## API Response Example

When calling `/opportunities/active?session_id={id}` without authentication, you'll get:

```json
[
  {
    "id": "a4b835a7-7880-4fe1-8590-05f6416d2285",
    "partner_id": "7ef41b65-ecf5-48c7-8b55-8acef01bf41d",
    "title": "☕ Free Pastry with Any Coffee",
    "value_proposition": "Buy any coffee, get a fresh pastry free! Perfect way to start your day.",
    "opportunity_type": "discovery",
    "value_details": {
      "fixed_value_usd": 4.5,
      "perks": ["fresh_baked", "artisan_coffee"],
      "parking_extension_minutes": 15
    },
    "location_lat": "42.96140000",
    "location_lng": "-88.01260000",
    "address": "123 Main Street, Greenfield, WI 53220",
    "walking_distance_meters": 120,
    "calculated_distance": 0,
    "priority_score": 75,
    "trigger_rules": {
      "time_remaining_min": 20,
      "time_remaining_max": 90,
      "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "time_of_day_start": "06:00",
      "time_of_day_end": "11:00"
    },
    "valid_from": "2025-10-31T15:53:00.123456",
    "valid_until": "2025-12-30T15:53:00.123456",
    "total_capacity": 200,
    "used_capacity": 23,
    "is_active": true,
    "is_approved": true,
    "created_at": "2025-10-31T15:53:00.123456"
  }
]
```

---

## Key Testing Points

### ✅ What Should Work Without Auth:
- Viewing opportunity list (`GET /opportunities/active`)
- Viewing opportunity details (`GET /opportunities/{id}`)
- Browsing all public opportunities

### ❌ What Should Fail Without Auth:
- Accepting opportunities (`POST /opportunities/{id}/accept`) → Returns 403
- Dismissing opportunities (`POST /opportunities/{id}/dismiss`) → Returns 403
- Viewing preferences (`GET /opportunities/preferences`) → Returns 403
- Updating preferences (`PUT /opportunities/preferences`) → Returns 403
- Viewing history (`GET /opportunities/history`) → Returns 403

### 🎯 Conversion Points:
- User taps "Accept" on opportunity detail → Show "Sign In to Accept"
- User taps "Dismiss" on opportunity → Show "Sign in to customize"
- User tries to access Preferences → Redirect to sign in
- User tries to access History → Redirect to sign in

---

## Notes for iOS Developers

1. **No Impression Tracking for Guests** - Backend only tracks impressions for authenticated users. Don't worry about manual tracking.

2. **Field Mapping** - Use JSONDecoder with `.convertFromSnakeCase` to automatically convert `parking_extension_minutes` to `parkingExtensionMinutes`.

3. **Partner Names** - Backend returns `partner_id` but not partner name. Display "Local Partner" or "Main Street Coffee Co." based on partner_id lookup.

4. **Error Handling** - When accept/dismiss/etc. return 403, show authentication prompt with clear benefits.

5. **Deep Linking** - After user signs up from opportunity flow, deep link back to opportunity detail so they can immediately accept.

6. **Capacity Display** - Show remaining capacity when `total_capacity` is not null. Example: "Only 177 left!" or "12 already claimed".

7. **Emoji Support** - Titles include emoji (☕, 🍔, ☀️) - ensure proper rendering in UI.

---

## Cleanup

To remove sample opportunities and partner:

```bash
docker-compose exec db psql -U trufan -d trufan -c "DELETE FROM partners WHERE api_key = 'pk_sample_test_key_999';"
```

This will cascade delete all associated opportunities.
