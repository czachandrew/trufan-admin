# TruFan API Documentation

## Overview

TruFan API provides comprehensive endpoints for venue and event management, including authentication, ticketing, parking, orders, and payments.

Base URL: `http://localhost:8000/api/v1`

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer {access_token}
```

### Token Lifecycle

- **Access Token**: Valid for 30 minutes
- **Refresh Token**: Valid for 7 days
- Use the refresh endpoint to get new access tokens without re-authenticating

## User Roles

The system supports multiple user roles with different permission levels:

1. **customer** - Basic user, can purchase tickets and make orders
2. **venue_staff** - Can scan tickets, manage parking
3. **venue_admin** - Can manage venue, events, and staff
4. **super_admin** - Full system access

## Endpoints

### Authentication

#### POST /auth/register
Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890"
}
```

**Response:** 201 Created
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "customer",
    "is_active": true,
    "is_verified": false,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

#### POST /auth/login
Login with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response:** 200 OK
```json
{
  "user": {...},
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

#### POST /auth/refresh
Refresh access token.

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response:** 200 OK
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

#### POST /auth/logout
Logout current user (requires authentication).

**Response:** 204 No Content

#### POST /auth/password-reset/request
Request password reset email.

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:** 200 OK
```json
{
  "message": "If the email exists, a reset link has been sent"
}
```

#### POST /auth/password-reset/confirm
Confirm password reset with token.

**Request:**
```json
{
  "token": "reset_token_from_email",
  "new_password": "NewSecurePass123"
}
```

**Response:** 200 OK
```json
{
  "message": "Password reset successful"
}
```

#### POST /auth/password/change
Change password for authenticated user.

**Request:**
```json
{
  "current_password": "OldPassword123",
  "new_password": "NewPassword123"
}
```

**Response:** 200 OK
```json
{
  "message": "Password changed successfully"
}
```

### Users

#### GET /users/me
Get current user profile (requires authentication).

**Response:** 200 OK
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "role": "customer",
  "is_active": true,
  "is_verified": false,
  "email_verified": false,
  "phone_verified": false,
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-15T14:30:00Z"
}
```

#### PATCH /users/me
Update current user profile (requires authentication).

**Request:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "phone": "+9876543210"
}
```

**Response:** 200 OK
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "phone": "+9876543210",
  ...
}
```

#### GET /users/{user_id}
Get user by ID (requires venue_staff role or higher).

**Response:** 200 OK
```json
{
  "id": "uuid",
  "email": "user@example.com",
  ...
}
```

#### GET /users
List all users (requires venue_admin role or higher).

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum number of records to return (default: 100)

**Response:** 200 OK
```json
[
  {
    "id": "uuid",
    "email": "user1@example.com",
    ...
  },
  {
    "id": "uuid",
    "email": "user2@example.com",
    ...
  }
]
```

## Error Handling

All error responses follow this format:

```json
{
  "error": {
    "code": 400,
    "message": "Error description",
    "details": [...],  // Optional, for validation errors
    "correlation_id": "uuid"
  }
}
```

### Common Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `204 No Content` - Request succeeded with no response body
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

## Rate Limiting

API requests are rate-limited to prevent abuse:
- **Limit**: 60 requests per minute per IP address
- **Burst**: 100 requests allowed in short bursts

Rate limit information is included in response headers:
- `X-RateLimit-Limit`: Maximum requests per minute
- `X-RateLimit-Remaining`: Remaining requests in current window

## Correlation IDs

Every request is assigned a correlation ID for tracing:
- If provided in request: Use `X-Correlation-ID` header
- If not provided: Generated automatically
- Included in all responses and logs

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

## Future Endpoints (To Be Implemented)

The following endpoint groups are defined in the database schema and ready for implementation:

- **Venues** - Venue management and configuration
- **Events** - Event creation and management
- **Tickets** - Ticket sales and validation
- **Parking** - Parking lot and session management
- **Orders** - Concessions and merchandise orders
- **Payments** - Payment processing and refunds

Refer to the database models in `backend/app/models/` for schema details.
