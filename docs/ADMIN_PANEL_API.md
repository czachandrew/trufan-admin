# TruFan Parking - Admin Panel API Documentation

## Overview

This document provides comprehensive API documentation for building the admin panel (web-based) to manage the TruFan Parking system.

**Base URL:** `http://localhost:8000` (development)
**API Version:** v1
**API Prefix:** `/api/v1`
**Authentication:** Required (JWT Bearer tokens)

## Table of Contents

- [Authentication](#authentication)
- [Admin Workflow](#admin-workflow)
- [API Endpoints](#api-endpoints)
- [Data Models](#data-models)
- [Permissions & Roles](#permissions--roles)
- [Analytics & Reporting](#analytics--reporting)

---

## Authentication

### Admin Access

All admin endpoints require authentication with an **admin** or **staff** role.

### Login Flow

1. **Login:** `POST /api/v1/auth/login`
2. **Receive Tokens:** Access token (30min) + Refresh token (7 days)
3. **Include Token:** Add `Authorization: Bearer {access_token}` header to all requests
4. **Refresh Token:** Use `POST /api/v1/auth/refresh` when access token expires

### Example:

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "admin@trufan.com",
    "password": "AdminPass123"
  }'

# Response
{
  "user": {
    "id": "user-uuid",
    "email": "admin@trufan.com",
    "role": "admin",
    "first_name": "Admin",
    "last_name": "User"
  },
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}

# Use token in subsequent requests
curl -X GET http://localhost:8000/api/v1/admin/parking/lots \
  -H 'Authorization: Bearer eyJ...'
```

---

## Admin Workflow

### Typical Admin Tasks

1. **Lot Management** → Create/edit parking lots
2. **Space Management** → Add/configure parking spaces
3. **Session Monitoring** → View all active sessions
4. **Customer Support** → Look up sessions, extend time
5. **Pricing Management** → Adjust rates, dynamic pricing
6. **Analytics** → View revenue, occupancy, trends
7. **QR Code Generation** → Generate printable QR codes

---

## API Endpoints

### Authentication Endpoints (Already Implemented)

#### 1. Login

**Endpoint:** `POST /api/v1/auth/login`
**Auth:** None required

**Request:**
```json
{
  "email": "admin@trufan.com",
  "password": "AdminPass123"
}
```

**Response (200 OK):**
```json
{
  "user": {
    "id": "uuid",
    "email": "admin@trufan.com",
    "role": "admin",
    "first_name": "Admin",
    "last_name": "User",
    "is_active": true,
    "created_at": "2025-10-29T10:00:00Z"
  },
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

#### 2. Refresh Token

**Endpoint:** `POST /api/v1/auth/refresh`
**Auth:** Refresh token in body

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

#### 3. Get Current User

**Endpoint:** `GET /api/v1/users/me`
**Auth:** Bearer token required

---

### Admin Parking Lot Management (To Be Implemented)

#### 1. Get All Parking Lots (Admin View)

Get all parking lots with detailed information.

**Endpoint:** `GET /api/v1/admin/parking/lots`
**Auth:** Required (admin/staff)
**Rate Limit:** 60 requests/minute

**Query Parameters:**
- `is_active` (boolean, optional) - Filter by active status
- `venue_id` (UUID, optional) - Filter by venue
- `page` (int, default: 1) - Pagination
- `limit` (int, default: 20) - Items per page

**Response:**
```json
{
  "items": [
    {
      "id": "lot-uuid",
      "venue_id": "venue-uuid",
      "name": "Downtown Parking Garage",
      "description": "Multi-level parking near Main St",
      "location_address": "123 Main St",
      "location_lat": "40.7128",
      "location_lng": "-74.0060",
      "total_spaces": 100,
      "available_spaces": 45,
      "is_active": true,
      "pricing_config": {
        "base_rate": 10.00,
        "hourly_rate": 5.00,
        "max_daily": 50.00,
        "min_duration_minutes": 15,
        "max_duration_hours": 24,
        "dynamic_multiplier": 1.0
      },
      "created_at": "2025-10-29T10:00:00Z",
      "updated_at": "2025-10-29T10:00:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "pages": 2
}
```

#### 2. Create Parking Lot

**Endpoint:** `POST /api/v1/admin/parking/lots`
**Auth:** Required (admin only)

**Request:**
```json
{
  "name": "Downtown Parking Garage",
  "description": "Multi-level parking near Main St",
  "location_address": "123 Main St, New York, NY 10001",
  "location_lat": "40.7128",
  "location_lng": "-74.0060",
  "total_spaces": 100,
  "venue_id": "venue-uuid",  // Optional
  "pricing_config": {
    "base_rate": 10.00,
    "hourly_rate": 5.00,
    "max_daily": 50.00,
    "min_duration_minutes": 15,
    "max_duration_hours": 24,
    "dynamic_multiplier": 1.0
  }
}
```

**Response (201 Created):** Same as lot object above

#### 3. Update Parking Lot

**Endpoint:** `PUT /api/v1/admin/parking/lots/{lot_id}`
**Auth:** Required (admin/staff)

**Request:** Same fields as create (all optional for partial update)

#### 4. Delete Parking Lot

**Endpoint:** `DELETE /api/v1/admin/parking/lots/{lot_id}`
**Auth:** Required (admin only)

**Response (204 No Content)**

---

### Admin Space Management (To Be Implemented)

#### 1. Get Spaces for Lot

**Endpoint:** `GET /api/v1/admin/parking/lots/{lot_id}/spaces`
**Auth:** Required (admin/staff)

**Query Parameters:**
- `is_active` (boolean, optional)
- `is_occupied` (boolean, optional)
- `space_type` (string, optional) - Filter by type

**Response:**
```json
{
  "items": [
    {
      "id": "space-uuid",
      "lot_id": "lot-uuid",
      "space_number": "A-101",
      "space_type": "standard",
      "is_occupied": false,
      "is_active": true,
      "created_at": "2025-10-29T10:00:00Z",
      "updated_at": "2025-10-29T10:00:00Z"
    }
  ],
  "total": 100
}
```

**Space Types:**
- `standard` - Regular parking space
- `handicap` - ADA accessible
- `ev` - Electric vehicle charging
- `compact` - Compact car only
- `valet` - Valet parking

#### 2. Create Parking Space

**Endpoint:** `POST /api/v1/admin/parking/lots/{lot_id}/spaces`
**Auth:** Required (admin/staff)

**Request:**
```json
{
  "space_number": "A-101",
  "space_type": "standard"
}
```

#### 3. Bulk Create Spaces

**Endpoint:** `POST /api/v1/admin/parking/lots/{lot_id}/spaces/bulk`
**Auth:** Required (admin/staff)

**Request:**
```json
{
  "spaces": [
    { "space_number": "A-101", "space_type": "standard" },
    { "space_number": "A-102", "space_type": "standard" },
    { "space_number": "A-103", "space_type": "handicap" }
  ]
}
```

**Response:**
```json
{
  "created": 3,
  "failed": 0,
  "errors": []
}
```

#### 4. Update Space

**Endpoint:** `PUT /api/v1/admin/parking/spaces/{space_id}`
**Auth:** Required (admin/staff)

#### 5. Delete Space

**Endpoint:** `DELETE /api/v1/admin/parking/spaces/{space_id}`
**Auth:** Required (admin only)

---

### Admin Session Management (To Be Implemented)

#### 1. Get All Sessions

**Endpoint:** `GET /api/v1/admin/parking/sessions`
**Auth:** Required (admin/staff)

**Query Parameters:**
- `status` (string, optional) - Filter by status
- `lot_id` (UUID, optional) - Filter by lot
- `start_date` (ISO date, optional) - Filter from date
- `end_date` (ISO date, optional) - Filter to date
- `vehicle_plate` (string, optional) - Search by plate
- `page` (int, default: 1)
- `limit` (int, default: 50)

**Response:**
```json
{
  "items": [
    {
      "id": "session-uuid",
      "lot_id": "lot-uuid",
      "lot_name": "Downtown Garage",
      "space_id": "space-uuid",
      "space_number": "A-101",
      "vehicle_plate": "ABC123",
      "vehicle_make": "Toyota",
      "vehicle_model": "Camry",
      "vehicle_color": "Blue",
      "start_time": "2025-10-29T10:00:00Z",
      "expires_at": "2025-10-29T12:00:00Z",
      "end_time": null,
      "base_price": "20.00",
      "actual_price": "20.00",
      "status": "active",
      "access_code": "ABC12345",
      "contact_email": "user@example.com",
      "contact_phone": "+15551234567",
      "created_at": "2025-10-29T10:00:00Z"
    }
  ],
  "total": 250,
  "page": 1,
  "pages": 5
}
```

#### 2. Get Session by ID

**Endpoint:** `GET /api/v1/admin/parking/sessions/{session_id}`
**Auth:** Required (admin/staff)

#### 3. Search Session by Access Code

**Endpoint:** `GET /api/v1/admin/parking/sessions/search?access_code={code}`
**Auth:** Required (admin/staff)

#### 4. Search Session by License Plate

**Endpoint:** `GET /api/v1/admin/parking/sessions/search?vehicle_plate={plate}`
**Auth:** Required (admin/staff)

#### 5. Admin Extend Session

**Endpoint:** `POST /api/v1/admin/parking/sessions/{session_id}/extend`
**Auth:** Required (admin/staff)

**Request:**
```json
{
  "additional_hours": 1.0,
  "reason": "Customer request",
  "waive_fee": false  // Admin can extend for free
}
```

#### 6. Admin End Session

**Endpoint:** `POST /api/v1/admin/parking/sessions/{session_id}/end`
**Auth:** Required (admin/staff)

**Request:**
```json
{
  "reason": "Customer left early"
}
```

#### 7. Cancel Session

**Endpoint:** `POST /api/v1/admin/parking/sessions/{session_id}/cancel`
**Auth:** Required (admin only)

**Request:**
```json
{
  "reason": "Fraudulent session",
  "refund_amount": "20.00"  // Optional
}
```

---

### Analytics & Reporting (To Be Implemented)

#### 1. Dashboard Overview

**Endpoint:** `GET /api/v1/admin/analytics/dashboard`
**Auth:** Required (admin/staff)

**Query Parameters:**
- `start_date` (ISO date, optional) - Default: today
- `end_date` (ISO date, optional) - Default: today

**Response:**
```json
{
  "date_range": {
    "start": "2025-10-29T00:00:00Z",
    "end": "2025-10-29T23:59:59Z"
  },
  "summary": {
    "total_sessions": 150,
    "active_sessions": 45,
    "total_revenue": "3250.00",
    "average_duration": 2.5,
    "occupancy_rate": 0.75
  },
  "by_lot": [
    {
      "lot_id": "lot-uuid",
      "lot_name": "Downtown Garage",
      "sessions": 80,
      "revenue": "1800.00",
      "occupancy_rate": 0.80
    }
  ],
  "by_hour": [
    { "hour": 8, "sessions": 12, "revenue": "240.00" },
    { "hour": 9, "sessions": 18, "revenue": "360.00" }
  ]
}
```

#### 2. Revenue Report

**Endpoint:** `GET /api/v1/admin/analytics/revenue`
**Auth:** Required (admin)

**Query Parameters:**
- `start_date` (required)
- `end_date` (required)
- `lot_id` (optional)
- `group_by` (optional: day/week/month)

**Response:**
```json
{
  "total_revenue": "15000.00",
  "total_sessions": 750,
  "average_price": "20.00",
  "breakdown": [
    {
      "date": "2025-10-29",
      "revenue": "3250.00",
      "sessions": 150
    }
  ],
  "by_payment_status": {
    "completed": "14500.00",
    "pending": "500.00",
    "failed": "0.00"
  }
}
```

#### 3. Occupancy Report

**Endpoint:** `GET /api/v1/admin/analytics/occupancy`
**Auth:** Required (admin/staff)

**Response:**
```json
{
  "current_occupancy": {
    "total_spaces": 500,
    "occupied_spaces": 325,
    "available_spaces": 175,
    "occupancy_rate": 0.65
  },
  "by_lot": [
    {
      "lot_id": "lot-uuid",
      "lot_name": "Downtown Garage",
      "total_spaces": 100,
      "occupied": 75,
      "available": 25,
      "rate": 0.75
    }
  ],
  "peak_hours": [
    { "hour": 12, "average_occupancy": 0.85 },
    { "hour": 13, "average_occupancy": 0.90 }
  ]
}
```

#### 4. Session Duration Analysis

**Endpoint:** `GET /api/v1/admin/analytics/duration`
**Auth:** Required (admin)

**Response:**
```json
{
  "average_duration_hours": 2.5,
  "median_duration_hours": 2.0,
  "distribution": {
    "under_1h": 150,
    "1h_2h": 300,
    "2h_4h": 200,
    "over_4h": 50
  }
}
```

---

### QR Code Management (To Be Implemented)

#### 1. Generate Lot QR Code

**Endpoint:** `POST /api/v1/admin/parking/lots/{lot_id}/qr-code`
**Auth:** Required (admin/staff)

**Request:**
```json
{
  "size": 512,  // Pixels
  "format": "png"  // png, svg, pdf
}
```

**Response:**
```json
{
  "qr_code_data": "trufan://parking/lot/lot-uuid",
  "image_url": "/api/v1/qr-codes/lot-uuid.png",
  "download_url": "/api/v1/qr-codes/lot-uuid.pdf"
}
```

#### 2. Generate Space QR Code

**Endpoint:** `POST /api/v1/admin/parking/spaces/{space_id}/qr-code`
**Auth:** Required (admin/staff)

**Request:**
```json
{
  "size": 512,
  "format": "png",
  "include_space_number": true  // Include space # on QR
}
```

#### 3. Bulk Generate Space QR Codes

**Endpoint:** `POST /api/v1/admin/parking/lots/{lot_id}/qr-codes/bulk`
**Auth:** Required (admin/staff)

**Request:**
```json
{
  "format": "pdf",  // Generate printable PDF
  "layout": "4x4"  // 4 QR codes per page
}
```

**Response:**
```json
{
  "pdf_url": "/api/v1/downloads/qr-codes-lot-uuid.pdf",
  "total_codes": 100
}
```

---

### Pricing Management (To Be Implemented)

#### 1. Get Pricing Configuration

**Endpoint:** `GET /api/v1/admin/parking/lots/{lot_id}/pricing`
**Auth:** Required (admin/staff)

#### 2. Update Pricing

**Endpoint:** `PUT /api/v1/admin/parking/lots/{lot_id}/pricing`
**Auth:** Required (admin only)

**Request:**
```json
{
  "base_rate": 10.00,
  "hourly_rate": 5.00,
  "max_daily": 50.00,
  "min_duration_minutes": 15,
  "max_duration_hours": 24,
  "dynamic_multiplier": 1.2  // Increase during high demand
}
```

#### 3. Set Dynamic Pricing

**Endpoint:** `POST /api/v1/admin/parking/lots/{lot_id}/dynamic-pricing`
**Auth:** Required (admin only)

**Request:**
```json
{
  "rules": [
    {
      "condition": "occupancy_above",
      "threshold": 0.8,
      "multiplier": 1.5
    },
    {
      "condition": "time_range",
      "start_hour": 17,
      "end_hour": 20,
      "multiplier": 1.3
    }
  ]
}
```

---

### User Management (Already Implemented)

#### 1. Get All Users

**Endpoint:** `GET /api/v1/admin/users`
**Auth:** Required (admin only)

#### 2. Update User Role

**Endpoint:** `PUT /api/v1/admin/users/{user_id}/role`
**Auth:** Required (admin only)

**Request:**
```json
{
  "role": "staff"  // customer, staff, admin
}
```

#### 3. Deactivate User

**Endpoint:** `POST /api/v1/admin/users/{user_id}/deactivate`
**Auth:** Required (admin only)

---

## Data Models

### Parking Lot (Admin View)

```typescript
interface ParkingLot {
  id: string;
  venue_id?: string;
  name: string;
  description?: string;
  location_address?: string;
  location_lat?: string;
  location_lng?: string;
  total_spaces: number;
  available_spaces: number;
  is_active: boolean;
  pricing_config: PricingConfig;
  created_at: string;
  updated_at: string;
}

interface PricingConfig {
  base_rate: number;
  hourly_rate: number;
  max_daily: number;
  min_duration_minutes: number;
  max_duration_hours: number;
  dynamic_multiplier: number;
}
```

### Parking Space

```typescript
interface ParkingSpace {
  id: string;
  lot_id: string;
  space_number: string;
  space_type: 'standard' | 'handicap' | 'ev' | 'compact' | 'valet';
  is_occupied: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
```

### Session (Admin View)

```typescript
interface ParkingSessionAdmin {
  id: string;
  lot_id: string;
  lot_name: string;
  space_id?: string;
  space_number?: string;
  user_id?: string;
  vehicle_plate: string;
  vehicle_make?: string;
  vehicle_model?: string;
  vehicle_color?: string;
  start_time: string;
  expires_at: string;
  end_time?: string;
  base_price: string;
  actual_price?: string;
  status: SessionStatus;
  access_code: string;
  contact_email?: string;
  contact_phone?: string;
  last_notification_sent?: string;
  created_at: string;
  updated_at: string;
}
```

---

## Permissions & Roles

### Role Hierarchy

1. **admin** - Full access
2. **staff** - Limited admin access (can't delete, manage users)
3. **customer** - Public API only

### Endpoint Permissions

| Endpoint | Customer | Staff | Admin |
|----------|----------|-------|-------|
| Public parking APIs | ✓ | ✓ | ✓ |
| View lots/sessions | ✗ | ✓ | ✓ |
| Create/update lots | ✗ | ✓ | ✓ |
| Delete lots | ✗ | ✗ | ✓ |
| Create/update spaces | ✗ | ✓ | ✓ |
| Delete spaces | ✗ | ✗ | ✓ |
| Extend/end sessions | ✗ | ✓ | ✓ |
| Cancel sessions | ✗ | ✗ | ✓ |
| View analytics | ✗ | ✓ | ✓ |
| View revenue | ✗ | ✗ | ✓ |
| Manage pricing | ✗ | ✗ | ✓ |
| User management | ✗ | ✗ | ✓ |

---

## Error Handling

### Admin Error Responses

All errors include correlation ID for tracking:

```json
{
  "error": {
    "code": 403,
    "message": "Insufficient permissions",
    "correlation_id": "abc123..."
  }
}
```

### Common Admin Errors

| Code | Meaning | Action |
|------|---------|--------|
| 401 | Unauthorized | Token expired, refresh or re-login |
| 403 | Forbidden | Insufficient permissions for action |
| 409 | Conflict | Resource already exists (duplicate space number) |
| 422 | Validation Error | Invalid input data |

---

## Webhooks & Events (Future)

### Event Types

- `lot.created`
- `lot.updated`
- `lot.deleted`
- `session.created`
- `session.payment_completed`
- `session.extended`
- `session.expired`
- `session.cancelled`
- `alert.low_availability` (< 10% spaces)
- `alert.pricing_change`

---

## Rate Limiting

**Admin Limits:**
- Read endpoints: 120 requests/minute
- Write endpoints: 60 requests/minute
- Analytics endpoints: 30 requests/minute

**Higher limits available on request for integrations**

---

## Best Practices

### 1. Always Check Permissions

```typescript
const hasPermission = (user: User, action: string): boolean => {
  if (user.role === 'admin') return true;
  if (user.role === 'staff' && !['delete', 'manage_users'].includes(action)) return true;
  return false;
};
```

### 2. Handle Token Expiration

```typescript
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try to refresh token
      const newToken = await refreshAccessToken();
      if (newToken) {
        // Retry original request
        error.config.headers['Authorization'] = `Bearer ${newToken}`;
        return api.request(error.config);
      } else {
        // Redirect to login
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
```

### 3. Audit Logging

All admin actions should be logged:

```json
{
  "action": "lot.updated",
  "user_id": "admin-uuid",
  "lot_id": "lot-uuid",
  "changes": {
    "base_rate": { "from": "10.00", "to": "12.00" }
  },
  "timestamp": "2025-10-29T10:00:00Z"
}
```

---

## Testing Admin APIs

### Create Test Admin User

```bash
# Register admin user (requires manual role update in database)
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "admin@test.com",
    "password": "AdminTest123",
    "first_name": "Admin",
    "last_name": "Test"
  }'

# Update role in database
UPDATE users SET role = 'admin' WHERE email = 'admin@test.com';
```

---

## Support

**API Issues:** Report at https://github.com/trufan/api/issues
**Admin Documentation:** https://docs.trufan.com/admin
**API Status:** https://status.trufan.com
