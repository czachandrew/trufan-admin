# TruFan Mobile App - Backend Integration Guide

## API Endpoint

**Production API Base URL:**
```
https://trufan-admin-production.railway.app/api/v1
```

Replace `trufan-admin-production` with the actual Railway domain.

---

## Authentication Flow

### 1. User Registration

**Endpoint:** `POST /api/v1/auth/register`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "firstName": "John",
  "lastName": "Doe",
  "role": "customer",
  "phone": "+1234567890"
}
```

**Response (201 Created):**
```json
{
  "user": {
    "id": "uuid-here",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "role": "customer",
    "isActive": true,
    "emailVerified": false,
    "phoneVerified": false
  },
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
  "tokenType": "bearer"
}
```

**Password Requirements:**
- Minimum 8 characters
- At least 1 digit
- At least 1 uppercase letter

---

### 2. User Login

**Endpoint:** `POST /api/v1/auth/login`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "user": {
    "id": "uuid-here",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "role": "customer"
  },
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
  "tokenType": "bearer"
}
```

---

### 3. Token Refresh

**Endpoint:** `POST /api/v1/auth/refresh`

**Request Body:**
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200 OK):**
```json
{
  "user": {...},
  "accessToken": "new-access-token",
  "refreshToken": "new-refresh-token",
  "tokenType": "bearer"
}
```

**When to Refresh:**
- Access tokens expire after 30 minutes
- Refresh tokens expire after 7 days
- Automatically refresh when you get a 401 response

---

### 4. Logout

**Endpoint:** `POST /api/v1/auth/logout`

**Headers:**
```
Authorization: Bearer {accessToken}
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

---

## Making Authenticated Requests

All protected endpoints require the access token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### iOS Example (Swift):
```swift
import Foundation

class APIClient {
    static let shared = APIClient()
    let baseURL = "https://trufan-admin-production.railway.app/api/v1"

    private var accessToken: String?
    private var refreshToken: String?

    func setTokens(access: String, refresh: String) {
        self.accessToken = access
        self.refreshToken = refresh

        // Persist to keychain
        KeychainHelper.save(access, forKey: "accessToken")
        KeychainHelper.save(refresh, forKey: "refreshToken")
    }

    func makeRequest<T: Decodable>(
        endpoint: String,
        method: String = "GET",
        body: Data? = nil
    ) async throws -> T {
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let token = accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        if let body = body {
            request.httpBody = body
        }

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        // Handle 401 - token expired, try refresh
        if httpResponse.statusCode == 401 {
            try await refreshAccessToken()
            return try await makeRequest(endpoint: endpoint, method: method, body: body)
        }

        guard httpResponse.statusCode == 200 || httpResponse.statusCode == 201 else {
            throw APIError.httpError(httpResponse.statusCode)
        }

        return try JSONDecoder().decode(T.self, from: data)
    }

    private func refreshAccessToken() async throws {
        guard let refreshToken = refreshToken else {
            throw APIError.noRefreshToken
        }

        let body = ["refreshToken": refreshToken]
        let bodyData = try JSONEncoder().encode(body)

        guard let url = URL(string: "\(baseURL)/auth/refresh") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = bodyData

        let (data, _) = try await URLSession.shared.data(for: request)
        let response = try JSONDecoder().decode(AuthResponse.self, from: data)

        setTokens(access: response.accessToken, refresh: response.refreshToken)
    }
}

// Usage
struct AuthResponse: Codable {
    let user: User
    let accessToken: String
    let refreshToken: String
    let tokenType: String
}

struct User: Codable {
    let id: String
    let email: String
    let firstName: String
    let lastName: String
    let role: String
}

// Login example
Task {
    do {
        let loginBody = ["email": "user@example.com", "password": "password123"]
        let bodyData = try JSONEncoder().encode(loginBody)

        let response: AuthResponse = try await APIClient.shared.makeRequest(
            endpoint: "/auth/login",
            method: "POST",
            body: bodyData
        )

        APIClient.shared.setTokens(
            access: response.accessToken,
            refresh: response.refreshToken
        )

        print("Logged in as: \(response.user.email)")
    } catch {
        print("Login failed: \(error)")
    }
}
```

---

## Key Endpoints for Mobile App

### Parking

**Start Parking Session:**
```
POST /api/v1/parking/sessions
```
Request:
```json
{
  "lotId": "uuid",
  "vehiclePlate": "ABC123"
}
```

**Get Active Session:**
```
GET /api/v1/parking/sessions/active
```

**End Parking Session:**
```
POST /api/v1/parking/sessions/{sessionId}/end
```

---

### Valet Service

**Request Valet:**
```
POST /api/v1/valet/requests
```
Request:
```json
{
  "lotId": "uuid",
  "vehiclePlate": "ABC123",
  "serviceType": "dropoff",
  "notes": "Red sedan, front entrance"
}
```

**Get Valet Request Status:**
```
GET /api/v1/valet/requests/{requestId}
```

---

### Convenience Store

**Get Store Inventory:**
```
GET /api/v1/convenience/stores/{storeId}/inventory
```

**Create Order:**
```
POST /api/v1/convenience/orders
```
Request:
```json
{
  "storeId": "uuid",
  "items": [
    {
      "inventoryItemId": "uuid",
      "quantity": 2
    }
  ],
  "deliveryLocation": "Section A, Row 5"
}
```

**Get Order Status:**
```
GET /api/v1/convenience/orders/{orderId}
```

---

### Opportunities (Partner Offers)

**Get Available Opportunities:**
```
GET /api/v1/opportunities
```

**Accept Opportunity:**
```
POST /api/v1/opportunities/{opportunityId}/accept
```

**Redeem Opportunity:**
```
POST /api/v1/opportunities/{opportunityId}/redeem
```

---

## Error Handling

All errors follow this format:

```json
{
  "error": {
    "code": 400,
    "message": "User-friendly error message",
    "details": ["Additional detail 1", "Additional detail 2"],
    "correlationId": "uuid-for-debugging"
  }
}
```

**Common Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (invalid/expired token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error

---

## Rate Limiting

- **Limit:** 60 requests per minute per IP
- **Burst:** Up to 100 requests
- **Headers:** Check `X-RateLimit-Limit` and `X-RateLimit-Remaining` response headers

---

## Testing

**Health Check:**
```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "TruFan API",
  "environment": "staging"
}
```

**Test Credentials:**

Will be provided separately via secure channel.

---

## Stripe Integration (Payments)

The backend uses **Stripe test mode** for staging.

**Payment Flow:**
1. Mobile app collects payment via Stripe SDK
2. Send `paymentMethodId` to backend
3. Backend processes payment and creates order

Contact backend team for Stripe publishable key.

---

## WebSocket Events (Future)

Real-time updates for:
- Valet request status changes
- Order status updates
- Parking session expiration warnings

WebSocket endpoint: `wss://trufan-admin-production.railway.app/ws`

_(Not yet implemented)_

---

## Support & Issues

- **Backend Issues:** Report to backend team with `correlationId` from error response
- **API Documentation:** See full OpenAPI docs at `/docs` endpoint
- **Emergency Contact:** [Add contact info]

---

## Security Best Practices

1. **Never log tokens** - Don't print or log access/refresh tokens
2. **Use HTTPS only** - Never make HTTP requests
3. **Secure token storage** - Use iOS Keychain for token persistence
4. **Implement token refresh** - Handle 401 responses automatically
5. **Validate SSL certificates** - Don't disable certificate validation
6. **Rate limit handling** - Implement exponential backoff for 429 responses

---

## Changelog

- **2025-11-21:** Initial staging deployment
- API base URL established
- Authentication endpoints live
- Parking, valet, convenience store, and opportunities endpoints available
