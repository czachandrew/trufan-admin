# TruFan Parking - Mobile Client API Documentation

## Overview

This document provides comprehensive API documentation for building mobile clients (iOS/Android/React Native) that consume the TruFan Parking API.

**Base URL:** `http://localhost:8000` (development)
**API Version:** v1
**API Prefix:** `/api/v1`

## Table of Contents

- [Authentication](#authentication)
- [Parking Workflow](#parking-workflow)
- [API Endpoints](#api-endpoints)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [QR Code Integration](#qr-code-integration)
- [Example Flows](#example-flows)

---

## Authentication

### Public Access (No Authentication Required)

All parking endpoints are **public** and do not require authentication. Users can:
- View available parking lots
- Create parking sessions
- Manage sessions using access codes

### Future: Optional User Accounts

User authentication may be added later for:
- Saving payment methods
- Viewing parking history
- Managing multiple vehicles

---

## Parking Workflow

### User Journey

1. **Scan QR Code** → Get lot ID or space number
2. **View Lot Details** → See pricing, availability
3. **Enter Vehicle Info** → License plate, make/model (optional)
4. **Select Duration** → Choose parking time
5. **Provide Contact** → Email or phone for notifications
6. **Simulate Payment** → Process payment (Stripe integration later)
7. **Receive Access Code** → Save for session management
8. **Get Notifications** → Email/SMS when parking expires
9. **Extend or End** → Modify session using access code

---

## API Endpoints

### 1. Get Available Parking Lots

Get all active parking lots with available spaces.

**Endpoint:** `GET /api/v1/parking/lots`
**Auth:** None required
**Rate Limit:** 60 requests/minute

**Response:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Downtown Parking Garage",
    "description": "Multi-level parking near Main St",
    "total_spaces": 100,
    "available_spaces": 45,
    "location_lat": "40.7128",
    "location_lng": "-74.0060",
    "is_active": true,
    "base_rate": "10.00",
    "hourly_rate": "5.00",
    "max_daily_rate": "50.00",
    "min_duration_minutes": 15,
    "max_duration_hours": 24,
    "dynamic_multiplier": "1.0"
  }
]
```

**Use Case:** Display list of nearby parking lots on map

---

### 2. Get Specific Parking Lot

Get details for a specific lot (typically after QR code scan).

**Endpoint:** `GET /api/v1/parking/lots/{lot_id}`
**Auth:** None required
**Rate Limit:** 60 requests/minute

**Path Parameters:**
- `lot_id` (UUID, required) - Parking lot ID from QR code

**Response:** Same as above, single object

**Use Case:** Show lot details after scanning QR code

---

### 3. Create Parking Session

Create a new parking session.

**Endpoint:** `POST /api/v1/parking/sessions`
**Auth:** None required
**Rate Limit:** 30 requests/minute

**Request Body:**
```json
{
  "lot_id": "123e4567-e89b-12d3-a456-426614174000",
  "space_number": "A-101",  // Optional - for specific space QR codes
  "vehicle_plate": "ABC123",  // Required
  "vehicle_make": "Toyota",  // Optional
  "vehicle_model": "Camry",  // Optional
  "vehicle_color": "Blue",  // Optional
  "duration_hours": 2.0,  // Required, must be > 0
  "contact_email": "user@example.com",  // One required
  "contact_phone": "+15551234567"  // One required
}
```

**Validation:**
- `vehicle_plate`: 1-20 characters, auto-uppercase, spaces removed
- `duration_hours`: Between min_duration_minutes and max_duration_hours
- At least one contact method (email or phone) required
- `contact_phone`: Auto-formatted to E.164 (+1XXXXXXXXXX)

**Response (201 Created):**
```json
{
  "id": "session-uuid",
  "lot_id": "lot-uuid",
  "lot_name": "Downtown Parking Garage",
  "space_number": "A-101",
  "vehicle_plate": "ABC123",
  "vehicle_make": "Toyota",
  "vehicle_model": "Camry",
  "vehicle_color": "Blue",
  "start_time": "2025-10-29T10:00:00Z",
  "expires_at": "2025-10-29T12:00:00Z",
  "end_time": null,
  "base_price": "20.00",
  "actual_price": null,
  "status": "pending_payment",
  "access_code": "ABC12345",  // SAVE THIS!
  "created_at": "2025-10-29T10:00:00Z"
}
```

**Important:**
- Store `access_code` locally - user needs this to manage session
- Status starts as `pending_payment` until payment is processed
- `base_price` is calculated: base_rate + (hourly_rate × duration_hours)
- Price is capped at `max_daily_rate`

**Use Case:** User fills out parking form and submits

---

### 4. Simulate Payment

Process payment for parking session (temporary - Stripe integration later).

**Endpoint:** `POST /api/v1/parking/payments/simulate`
**Auth:** None required
**Rate Limit:** 30 requests/minute

**Request Body:**
```json
{
  "session_id": "session-uuid",
  "amount": "20.00",
  "should_succeed": true  // Set false to test failure
}
```

**Response (200 OK):**
```json
{
  "payment_id": "payment-uuid",
  "session_id": "session-uuid",
  "amount": "20.00",
  "status": "completed",
  "message": "Payment processed successfully (simulated)"
}
```

**After Success:**
- Session status changes from `pending_payment` → `active`
- Space is marked as occupied
- Lot available_spaces decrements
- Notification sent to user

**Use Case:** Process payment after session creation

---

### 5. Look Up Session by Access Code

Retrieve session details using access code.

**Endpoint:** `GET /api/v1/parking/sessions/{access_code}`
**Auth:** None required (access code acts as auth)
**Rate Limit:** 60 requests/minute

**Path Parameters:**
- `access_code` (string, required) - 8-character code from session creation

**Response (200 OK):** Same as Create Session response

**Use Case:**
- User returns to app and enters access code
- Check current session status
- Show time remaining

---

### 6. Extend Parking Session

Add more time to an active session.

**Endpoint:** `POST /api/v1/parking/sessions/{access_code}/extend`
**Auth:** None required (access code acts as auth)
**Rate Limit:** 30 requests/minute

**Path Parameters:**
- `access_code` (string, required)

**Request Body:**
```json
{
  "additional_hours": 1.0,  // Must be > 0, ≤ 24
  "access_code": "ABC12345"  // Must match URL parameter
}
```

**Response (200 OK):**
```json
{
  "id": "session-uuid",
  "lot_id": "lot-uuid",
  "lot_name": "Downtown Parking Garage",
  "space_number": "A-101",
  "vehicle_plate": "ABC123",
  "start_time": "2025-10-29T10:00:00Z",
  "expires_at": "2025-10-29T13:00:00Z",  // Extended by 1 hour
  "base_price": "20.00",
  "actual_price": "25.00",  // Additional charge added
  "status": "active",
  "access_code": "ABC12345",
  "created_at": "2025-10-29T10:00:00Z"
}
```

**Pricing:**
- No base rate for extensions
- Only hourly rate applied: hourly_rate × additional_hours × dynamic_multiplier
- Total capped at max_daily_rate

**Use Case:**
- User receives expiration notification
- Clicks extend link in email/SMS
- Adds more time

---

### 7. End Parking Session

End session early and free up space.

**Endpoint:** `POST /api/v1/parking/sessions/{access_code}/end`
**Auth:** None required (access code acts as auth)
**Rate Limit:** 30 requests/minute

**Path Parameters:**
- `access_code` (string, required)

**Request Body:**
```json
{
  "access_code": "ABC12345"  // Must match URL parameter
}
```

**Response (200 OK):**
```json
{
  "id": "session-uuid",
  "lot_id": "lot-uuid",
  "lot_name": "Downtown Parking Garage",
  "space_number": "A-101",
  "vehicle_plate": "ABC123",
  "start_time": "2025-10-29T10:00:00Z",
  "expires_at": "2025-10-29T12:00:00Z",
  "end_time": "2025-10-29T11:30:00Z",  // Session ended
  "base_price": "20.00",
  "actual_price": "20.00",
  "status": "completed",
  "access_code": "ABC12345",
  "created_at": "2025-10-29T10:00:00Z"
}
```

**After End:**
- Session status → `completed`
- Space marked as available
- Lot available_spaces increments

**Use Case:** User leaves early and wants to free up space

---

## Data Models

### Session Statuses

| Status | Description |
|--------|-------------|
| `pending_payment` | Session created, awaiting payment |
| `active` | Payment complete, space occupied |
| `expiring_soon` | Expires within 30 minutes, notification sent |
| `expired` | Session expired, space freed |
| `completed` | User ended early |
| `cancelled` | Session cancelled (future feature) |
| `payment_failed` | Payment processing failed |

### Status Transitions

```
pending_payment → active (after payment)
active → expiring_soon (30 min before expiry)
active → completed (user ends early)
active → expired (time runs out)
expiring_soon → active (user extends)
expiring_soon → expired (time runs out)
```

---

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "error": {
    "code": 400,
    "message": "Parking lot not found",
    "correlation_id": "abc123..."
  }
}
```

### Common Error Codes

| Code | Meaning | Example |
|------|---------|---------|
| 400 | Bad Request | Invalid duration, missing contact info |
| 404 | Not Found | Lot/session not found |
| 422 | Validation Error | Invalid email format, plate too long |
| 429 | Rate Limit | Too many requests |
| 500 | Server Error | Internal error (retry with backoff) |

### Specific Error Scenarios

#### 1. No Available Spaces
```json
{
  "error": {
    "code": 400,
    "message": "No available spaces in this parking lot"
  }
}
```
**Action:** Show "Lot Full" message, suggest nearby lots

#### 2. Invalid Duration
```json
{
  "error": {
    "code": 400,
    "message": "Minimum parking duration is 15 minutes"
  }
}
```
**Action:** Show duration requirements, update UI

#### 3. Session Not Found
```json
{
  "error": {
    "code": 404,
    "message": "Parking session not found"
  }
}
```
**Action:** Access code invalid, ask user to re-enter

#### 4. Cannot Extend Unpaid Session
```json
{
  "error": {
    "code": 400,
    "message": "Cannot extend session with status: pending_payment"
  }
}
```
**Action:** Prompt user to complete payment first

---

## QR Code Integration

### QR Code Formats

TruFan uses two types of QR codes:

#### 1. Lot-Level QR Code
Points to entire parking lot, any available space assigned.

**QR Data:**
```
trufan://parking/lot/{lot_id}
```

**Example:**
```
trufan://parking/lot/123e4567-e89b-12d3-a456-426614174000
```

**Mobile Handling:**
1. Parse QR code
2. Extract `lot_id`
3. Call `GET /api/v1/parking/lots/{lot_id}`
4. Show lot details screen
5. User fills form (leave `space_number` empty)
6. Create session with auto-assignment

#### 2. Space-Specific QR Code
Points to specific parking space.

**QR Data:**
```
trufan://parking/lot/{lot_id}/space/{space_number}
```

**Example:**
```
trufan://parking/lot/123e4567-e89b-12d3-a456-426614174000/space/A-101
```

**Mobile Handling:**
1. Parse QR code
2. Extract `lot_id` and `space_number`
3. Call `GET /api/v1/parking/lots/{lot_id}`
4. Show lot details with pre-filled space
5. User fills form (include `space_number` in request)
6. Create session with specific space

### QR Code Scanner Implementation

**React Native Example:**
```javascript
import { Camera } from 'expo-camera';

const handleQRScan = ({ data }) => {
  // Parse trufan:// URL
  const url = new URL(data);

  if (url.protocol !== 'trufan:') {
    return alert('Invalid QR code');
  }

  const pathParts = url.pathname.split('/');
  // pathParts: ['', 'parking', 'lot', '{lot_id}', 'space', '{space_number}']

  const lotId = pathParts[3];
  const spaceNumber = pathParts[5] || null;

  // Navigate to parking form
  navigation.navigate('ParkingForm', { lotId, spaceNumber });
};
```

---

## Example Flows

### Flow 1: Complete Parking Session (Lot-Level)

```javascript
// 1. User scans QR code at lot entrance
const lotId = parseLotIdFromQR(qrData);

// 2. Fetch lot details
const lot = await fetch(`/api/v1/parking/lots/${lotId}`).then(r => r.json());

// Display: name, pricing, available_spaces

// 3. User fills form and submits
const sessionRequest = {
  lot_id: lotId,
  // No space_number - auto-assign
  vehicle_plate: "ABC123",
  duration_hours: 2.0,
  contact_email: "user@example.com"
};

const session = await fetch('/api/v1/parking/sessions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(sessionRequest)
}).then(r => r.json());

// Save access code to AsyncStorage/SecureStore
await saveAccessCode(session.access_code);

// Display: "Session created! Access code: ABC12345"
// Show: space_number (if assigned), expires_at, base_price

// 4. Process payment
const payment = await fetch('/api/v1/parking/payments/simulate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: session.id,
    amount: session.base_price,
    should_succeed: true
  })
}).then(r => r.json());

if (payment.status === 'completed') {
  // Display: "Payment successful! Parking active until {expires_at}"
  // Show: QR code or access code for easy retrieval
}
```

### Flow 2: Extend Parking from Notification

```javascript
// User clicks "Extend Parking" link in email/SMS
// Link format: https://app.trufan.com/extend/{access_code}

// 1. Parse access code from deep link
const accessCode = parseDeepLink(url);

// 2. Fetch current session
const session = await fetch(`/api/v1/parking/sessions/${accessCode}`)
  .then(r => r.json());

// Display: current expiration time, vehicle info

// 3. User selects additional hours
const additionalHours = 1.0; // From UI picker

// 4. Extend session
const extended = await fetch(`/api/v1/parking/sessions/${accessCode}/extend`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    additional_hours: additionalHours,
    access_code: accessCode
  })
}).then(r => r.json());

// Display: new expires_at, additional_cost
// Show: payment screen for additional charge
```

### Flow 3: Look Up Existing Session

```javascript
// User opens app without QR scan
// Wants to check current parking status

// 1. Load saved access codes
const savedCodes = await loadAccessCodes();

// 2. Fetch sessions for each code
const sessions = await Promise.all(
  savedCodes.map(code =>
    fetch(`/api/v1/parking/sessions/${code}`)
      .then(r => r.ok ? r.json() : null)
  )
);

// Filter active sessions
const activeSessions = sessions
  .filter(s => s && ['active', 'expiring_soon'].includes(s.status));

// Display: list of active parking sessions
// For each: lot_name, space_number, expires_at, time_remaining
```

---

## Rate Limiting

**Limits:**
- Read endpoints (GET): 60 requests/minute
- Write endpoints (POST): 30 requests/minute

**Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
```

**When Exceeded:**
```json
{
  "error": {
    "code": 429,
    "message": "Rate limit exceeded. Please try again later."
  }
}
```

**Best Practices:**
- Cache lot data locally (refresh every 5 minutes)
- Implement exponential backoff for retries
- Show user-friendly "Too many requests" message

---

## Testing

### Test Server
- Base URL: `http://localhost:8000`
- Always returns success for payments when `should_succeed: true`
- Notifications are logged but not sent

### Test Data

**Create Test Lot:**
```bash
# Contact admin to create test lot
# Or use existing lot IDs from API
```

**Test Cards (future Stripe integration):**
- Success: 4242 4242 4242 4242
- Decline: 4000 0000 0000 0002

---

## Best Practices

### 1. Store Access Codes Securely
```javascript
import * as SecureStore from 'expo-secure-store';

await SecureStore.setItemAsync('access_codes', JSON.stringify(codes));
```

### 2. Handle Network Errors
```javascript
try {
  const response = await fetch(url);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error.message);
  }
  return response.json();
} catch (err) {
  if (err.message === 'Network request failed') {
    alert('No internet connection');
  } else {
    alert(err.message);
  }
}
```

### 3. Show Time Remaining
```javascript
const getTimeRemaining = (expiresAt) => {
  const now = new Date();
  const expires = new Date(expiresAt);
  const diff = expires - now;

  if (diff <= 0) return 'Expired';

  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
};
```

### 4. Validate Before Submit
```javascript
const validateParkingForm = (data) => {
  const errors = {};

  if (!data.vehicle_plate) {
    errors.vehicle_plate = 'License plate required';
  }

  if (data.duration_hours < 0.25) {
    errors.duration_hours = 'Minimum 15 minutes';
  }

  if (!data.contact_email && !data.contact_phone) {
    errors.contact = 'Email or phone required';
  }

  return errors;
};
```

### 5. Handle Deep Links
```javascript
// app.json
{
  "expo": {
    "scheme": "trufan"
  }
}

// App.js
Linking.addEventListener('url', ({ url }) => {
  if (url.startsWith('trufan://parking/')) {
    handleParkingDeepLink(url);
  }
});
```

---

## Support

**API Issues:** Report at https://github.com/trufan/api/issues
**Documentation:** https://docs.trufan.com
**API Status:** https://status.trufan.com
