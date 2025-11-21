# New Admin Endpoints - Ready to Use!

## Overview

I've implemented the missing admin endpoints that your frontend dashboard needs. Both are now working and tested!

---

## 1. GET /parking/sessions

List all parking sessions with filtering and pagination.

### Endpoint
```
GET /api/v1/parking/sessions
```

### Authentication
**Required:** Bearer token (admin or operator role)

```
Authorization: Bearer {your_access_token}
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lot_id` | UUID | No | Filter by parking lot ID |
| `status_filter` | string | No | Filter by status: `active`, `completed`, `expired`, `cancelled` |
| `start_date` | datetime | No | Filter sessions starting after this date (ISO 8601) |
| `end_date` | datetime | No | Filter sessions starting before this date (ISO 8601) |
| `vehicle_plate` | string | No | Search by license plate (partial match, case-insensitive) |
| `limit` | int | No | Max results (1-500, default: 100) |
| `offset` | int | No | Pagination offset (default: 0) |

### Example Request

```bash
curl "http://localhost:8000/api/v1/parking/sessions?status_filter=active&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Response

```json
[
  {
    "id": "uuid",
    "lot_id": "uuid",
    "lot_name": "Greenfield Plaza Parking",
    "space_number": "A-002",
    "vehicle_plate": "ABC123",
    "vehicle_make": "Toyota",
    "vehicle_model": "Camry",
    "vehicle_color": "Silver",
    "start_time": "2025-11-03T15:30:00",
    "expires_at": "2025-11-03T17:30:00",
    "end_time": null,
    "base_price": "15.00",
    "actual_price": null,
    "status": "active",
    "access_code": "ABC12XYZ",
    "created_at": "2025-11-03T15:30:00"
  }
]
```

### Frontend Usage

```typescript
// src/api/parking.ts
export async function getSessions(filters?: {
  lotId?: string;
  status?: 'active' | 'completed' | 'expired' | 'cancelled';
  startDate?: string;
  endDate?: string;
  vehiclePlate?: string;
  limit?: number;
  offset?: number;
}) {
  const params = new URLSearchParams();

  if (filters?.lotId) params.append('lot_id', filters.lotId);
  if (filters?.status) params.append('status_filter', filters.status);
  if (filters?.startDate) params.append('start_date', filters.startDate);
  if (filters?.endDate) params.append('end_date', filters.endDate);
  if (filters?.vehiclePlate) params.append('vehicle_plate', filters.vehiclePlate);
  if (filters?.limit) params.append('limit', filters.limit.toString());
  if (filters?.offset) params.append('offset', filters.offset.toString());

  const response = await client.get(`/parking/sessions?${params}`);
  return response.data;
}
```

---

## 2. GET /partner/opportunities (Now Supports Admin Auth!)

List opportunities - now works with Bearer token authentication for admins!

### Endpoint
```
GET /api/v1/partner/opportunities
```

### Authentication Options

**Option 1: Partner API Key** (for partners)
```
X-API-Key: pk_partner_api_key_here
```

**Option 2: Bearer Token** (for admins) ⭐ NEW!
```
Authorization: Bearer {your_access_token}
```

### What Changed?

- **Partners:** See only their own opportunities (same as before)
- **Admins:** See ALL opportunities from all partners! 🎉

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status_filter` | string | No | Filter: `active`, `expired`, `pending` |
| `partner_id` | UUID | No | Filter by partner (admin only) |
| `skip` | int | No | Pagination offset (default: 0) |
| `limit` | int | No | Max results (1-100, default: 50) |

### Example Request (Admin)

```bash
curl "http://localhost:8000/api/v1/partner/opportunities?status_filter=active&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Response

```json
[
  {
    "id": "uuid",
    "partner_id": "uuid",
    "title": "☕ Free Pastry with Any Coffee",
    "value_proposition": "Buy any coffee, get a fresh pastry free!",
    "opportunity_type": "discovery",
    "trigger_rules": {
      "time_remaining_min": 20,
      "time_remaining_max": 90,
      "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "time_of_day_start": "06:00",
      "time_of_day_end": "11:00"
    },
    "value_details": {
      "fixed_value_usd": 4.5,
      "perks": ["fresh_baked", "artisan_coffee"],
      "parking_extension_minutes": 15
    },
    "valid_from": "2025-10-31T15:53:00",
    "valid_until": "2025-12-30T15:53:00",
    "total_capacity": 200,
    "used_capacity": 23,
    "priority_score": 75,
    "location_lat": "42.96140000",
    "location_lng": "-88.01260000",
    "address": "123 Main Street, Greenfield, WI 53220",
    "walking_distance_meters": 120,
    "is_active": true,
    "is_approved": true,
    "created_at": "2025-10-31T15:53:00"
  }
]
```

### Frontend Usage

```typescript
// src/api/opportunities.ts
export async function getPartnerOpportunities(filters?: {
  status?: 'active' | 'expired' | 'pending';
  partnerId?: string;
  skip?: number;
  limit?: number;
}) {
  const params = new URLSearchParams();

  if (filters?.status) params.append('status_filter', filters.status);
  if (filters?.partnerId) params.append('partner_id', filters.partnerId);
  if (filters?.skip) params.append('skip', filters.skip.toString());
  if (filters?.limit) params.append('limit', filters.limit.toString());

  const response = await client.get(`/partner/opportunities?${params}`);
  return response.data;
}
```

---

## Testing

Both endpoints have been tested and are working:

```bash
docker-compose exec api python -m scripts.test_admin_endpoints
```

**Test Results:**
```
✓ GET /parking/sessions: 200 OK - Retrieved 5 sessions
✓ GET /partner/opportunities: 200 OK - Retrieved 5 opportunities
```

---

## Permissions

### Required Roles

**Sessions Endpoint:**
- `super_admin` ✅
- `venue_admin` ✅
- `venue_staff` ✅
- `customer` ❌ (403 Forbidden)

**Opportunities Endpoint:**
- `super_admin` ✅ (sees all opportunities)
- `venue_admin` ✅ (sees all opportunities)
- `venue_staff` ❌ (403 Forbidden)
- `customer` ❌ (403 Forbidden)

### Your Account

Your account (`czachandrew@gmail.com`) has role `super_admin`, so you have access to both endpoints!

---

## Error Responses

### 401 Unauthorized
```json
{
  "error": {
    "code": 401,
    "message": "Not authenticated"
  }
}
```
**Solution:** Include `Authorization: Bearer {token}` header

### 403 Forbidden
```json
{
  "error": {
    "code": 403,
    "message": "Insufficient permissions to view sessions"
  }
}
```
**Solution:** User needs admin or operator role

### 422 Unprocessable Entity
```json
{
  "error": {
    "code": 422,
    "message": "Validation error"
  }
}
```
**Solution:** Check query parameters are correct type/format

---

## Updated Admin Dashboard Implementation

Your dashboard should now work! Make sure your API calls look like this:

```typescript
// Dashboard.vue or Dashboard.tsx
onMounted(async () => {
  try {
    // Fetch sessions
    const sessions = await getSessions({
      status: 'active',
      limit: 100
    });

    // Fetch opportunities
    const opportunities = await getPartnerOpportunities({
      status: 'active',
      limit: 100
    });

    // Update state
    parkingStore.sessions = sessions;
    opportunitiesStore.opportunities = opportunities;
  } catch (error) {
    console.error('Error loading dashboard:', error);
  }
});
```

---

## What's Next?

Other admin endpoints from the prompt that are still missing (but not critical for MVP):

- `POST /parking/sessions/{sessionId}/refund` - Process refunds
- `POST /parking/sessions/{sessionId}/notes` - Add admin notes
- `GET /parking/sessions/{sessionId}/history` - Event history
- `GET /parking/lots/{lotId}/spaces` - List spaces
- `POST /parking/lots/{lotId}/spaces` - Add spaces
- `GET /admin/analytics/parking` - Parking analytics
- `GET /admin/users` - User management

These can be added later as needed!

---

**Status:** ✅ Ready to use!
**Tested:** ✅ Both endpoints working
**Deployed:** ✅ Live on localhost:8000

Your frontend dashboard should now load successfully! 🎉
