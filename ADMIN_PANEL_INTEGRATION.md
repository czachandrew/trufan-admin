# TruFan Admin Panel - Backend Integration Guide

## API Endpoint

**Production API Base URL:**
```
https://trufan-admin-production.railway.app/api/v1
```

Replace `trufan-admin-production` with the actual Railway domain.

---

## Authentication

### Admin Login

**Endpoint:** `POST /api/v1/auth/login`

**Request:**
```json
{
  "email": "admin@trufan.com",
  "password": "your-admin-password"
}
```

**Response:**
```json
{
  "user": {
    "id": "uuid",
    "email": "admin@trufan.com",
    "firstName": "Admin",
    "lastName": "User",
    "role": "super_admin",
    "venueId": null
  },
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
  "tokenType": "bearer"
}
```

**User Roles:**
- `super_admin` - Full system access
- `admin` - Administrative access
- `venue_admin` - Venue-specific admin
- `operator` - Venue operations (valet, convenience store)
- `customer` - End users (mobile app)

---

## Environment Configuration

Update your Vue.js admin panel `.env` file:

```bash
VITE_API_BASE_URL=https://trufan-admin-production.railway.app/api/v1
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_51SVxMJLtdOKEjwvLL9cHfH1shnur1EUoPmDZjKd5OBb7oRqOUI9PzQcydku0NaWjXug63nWwqTyooUjWYZCImR1M00hufWCq5p
```

Update your `src/config/api.ts` (or equivalent):

```typescript
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add interceptor for auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refreshToken,
        });

        const { accessToken, refreshToken: newRefreshToken } = response.data;

        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', newRefreshToken);

        originalRequest.headers.Authorization = `Bearer ${accessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
```

---

## Admin Endpoints

### Dashboard Stats

**Get Overview Stats:**
```
GET /api/v1/admin/dashboard/stats
```

Response:
```json
{
  "totalUsers": 1234,
  "activeParking": 56,
  "todayRevenue": "12345.67",
  "activeValetRequests": 8,
  "pendingOrders": 12
}
```

---

### User Management

**List Users:**
```
GET /api/v1/admin/users?page=1&limit=20&role=customer&search=john
```

**Get User Details:**
```
GET /api/v1/admin/users/{userId}
```

**Create User:**
```
POST /api/v1/admin/users
```
Body:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "firstName": "John",
  "lastName": "Doe",
  "role": "operator",
  "venueId": "venue-uuid"
}
```

**Update User:**
```
PUT /api/v1/admin/users/{userId}
```

**Deactivate User:**
```
POST /api/v1/admin/users/{userId}/deactivate
```

---

### Venue Management

**List Venues:**
```
GET /api/v1/admin/venues
```

**Create Venue:**
```
POST /api/v1/admin/venues
```
Body:
```json
{
  "name": "Madison Square Garden",
  "address": {
    "street": "4 Pennsylvania Plaza",
    "city": "New York",
    "state": "NY",
    "zipCode": "10001",
    "country": "USA"
  },
  "settings": {
    "parkingEnabled": true,
    "valetEnabled": true,
    "convenienceStoreEnabled": true
  }
}
```

**Update Venue:**
```
PUT /api/v1/admin/venues/{venueId}
```

---

### Parking Lot Management

**List Parking Lots:**
```
GET /api/v1/admin/parking/lots?venueId={venueId}
```

**Create Parking Lot:**
```
POST /api/v1/admin/parking/lots
```
Body:
```json
{
  "name": "North Parking Garage",
  "venueId": "venue-uuid",
  "capacity": 500,
  "location": {
    "latitude": 40.7505,
    "longitude": -73.9934
  },
  "pricing": {
    "hourlyRate": "5.00",
    "dailyMax": "40.00",
    "eventRate": "25.00"
  },
  "isPublic": true
}
```

**View Active Sessions:**
```
GET /api/v1/admin/parking/sessions?lotId={lotId}&status=active
```

---

### Valet Management

**List Valet Requests:**
```
GET /api/v1/admin/valet/requests?status=pending&venueId={venueId}
```

**Assign Valet Worker:**
```
POST /api/v1/admin/valet/requests/{requestId}/assign
```
Body:
```json
{
  "workerId": "worker-uuid"
}
```

**Update Request Status:**
```
PUT /api/v1/admin/valet/requests/{requestId}/status
```
Body:
```json
{
  "status": "in_progress"
}
```

---

### Convenience Store Management

**List Stores:**
```
GET /api/v1/admin/convenience/stores?venueId={venueId}
```

**Create Store:**
```
POST /api/v1/admin/convenience/stores
```
Body:
```json
{
  "name": "Main Concessions",
  "venueId": "venue-uuid",
  "location": "Section 100",
  "isActive": true
}
```

**Manage Inventory:**
```
GET /api/v1/admin/convenience/stores/{storeId}/inventory
POST /api/v1/admin/convenience/inventory
PUT /api/v1/admin/convenience/inventory/{itemId}
DELETE /api/v1/admin/convenience/inventory/{itemId}
```

**Inventory Item Structure:**
```json
{
  "storeId": "store-uuid",
  "categoryId": "category-uuid",
  "name": "Coca-Cola",
  "description": "12 oz can",
  "sku": "COKE-12OZ",
  "basePrice": "3.50",
  "markupPercent": 0,
  "markupAmount": "0.50",
  "stockQuantity": 100,
  "lowStockThreshold": 20,
  "isActive": true,
  "imageUrl": "https://example.com/coke.jpg"
}
```

**View Orders:**
```
GET /api/v1/admin/convenience/orders?storeId={storeId}&status=pending
```

**Update Order Status:**
```
PUT /api/v1/admin/convenience/orders/{orderId}/status
```
Body:
```json
{
  "status": "preparing",
  "notes": "Order is being prepared"
}
```

---

### Partner Opportunities

**List Opportunities:**
```
GET /api/v1/admin/opportunities?venueId={venueId}
```

**Create Opportunity:**
```
POST /api/v1/admin/opportunities
```
Body:
```json
{
  "partnerId": "partner-uuid",
  "venueId": "venue-uuid",
  "title": "20% Off Pizza",
  "description": "Get 20% off your order at Joe's Pizza",
  "offerType": "discount",
  "discountPercent": 20,
  "startDate": "2025-11-21T00:00:00Z",
  "endDate": "2025-12-31T23:59:59Z",
  "maxRedemptions": 1000,
  "isActive": true
}
```

**View Analytics:**
```
GET /api/v1/admin/opportunities/{opportunityId}/analytics
```

---

### Reports & Analytics

**Revenue Report:**
```
GET /api/v1/admin/reports/revenue?startDate=2025-11-01&endDate=2025-11-30&venueId={venueId}
```

**Usage Report:**
```
GET /api/v1/admin/reports/usage?startDate=2025-11-01&endDate=2025-11-30&venueId={venueId}
```

**Popular Items:**
```
GET /api/v1/admin/reports/popular-items?storeId={storeId}&limit=10
```

---

## Current Admin Panel Routes

Update your existing routes to use the new backend:

### Already Implemented in Admin Panel:

1. **Dashboard** (`/`) - Needs to call `/api/v1/admin/dashboard/stats`
2. **Inventory Management** (`/inventory`) - Already working with backend
3. **Categories** (`/categories`) - Already working with backend
4. **Orders** (`/orders`) - Already working with backend
5. **Login** (`/login`) - Already working with auth endpoints

### Quick Integration Checklist:

- [x] Login/Auth flow - Already integrated
- [x] Convenience store inventory - Already integrated
- [x] Order management - Already integrated
- [ ] Update API base URL to Railway
- [ ] Add CORS configuration to backend for admin panel domain
- [ ] Test all existing features with Railway backend
- [ ] Add venue selector (super admin)
- [ ] Add user management pages
- [ ] Add parking lot management
- [ ] Add valet management
- [ ] Add reports/analytics

---

## Venue Context

For `venue_admin` and `operator` roles, the backend automatically filters data by their assigned `venueId`.

For `super_admin` users, you need to:

1. **Show venue selector** in UI
2. **Pass venueId** in requests:
   - Query param: `?venueId={uuid}`
   - Or store in Pinia/Vuex and include in requests

Example:
```typescript
// In your Pinia store
export const useVenueStore = defineStore('venue', {
  state: () => ({
    currentVenueId: null as string | null,
  }),
  actions: {
    setVenue(venueId: string) {
      this.currentVenueId = venueId;
      localStorage.setItem('selected_venue_id', venueId);
    },
  },
});

// In your API calls
const venueStore = useVenueStore();
const response = await api.get('/admin/convenience/stores', {
  params: { venueId: venueStore.currentVenueId },
});
```

---

## Error Handling

All errors follow this format:

```json
{
  "error": {
    "code": 400,
    "message": "Validation error",
    "details": ["Field 'email' is required"],
    "correlationId": "uuid-for-debugging"
  }
}
```

Display `message` to users, log `correlationId` for debugging.

---

## CORS Configuration

Backend ALLOWED_ORIGINS currently set to:
```
http://localhost:3000
```

**Action Required:** Add your production admin panel domain to backend ALLOWED_ORIGINS once deployed.

---

## Testing Credentials

**Super Admin:**
- Email: [Will be provided]
- Password: [Will be provided]

**Venue Admin:**
- Email: [Will be provided]
- Password: [Will be provided]

---

## Health Check

Test backend connectivity:
```bash
curl https://trufan-admin-production.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "TruFan API",
  "environment": "staging"
}
```

---

## API Documentation

Interactive API docs (Swagger UI):
```
https://trufan-admin-production.railway.app/docs
```

ReDoc documentation:
```
https://trufan-admin-production.railway.app/redoc
```

---

## Support & Issues

- **Backend Issues:** Include `correlationId` from error response
- **New Feature Requests:** Contact backend team
- **Emergency:** [Add contact info]

---

## Deployment Checklist

Before going live with admin panel:

1. [ ] Update VITE_API_BASE_URL to Railway URL
2. [ ] Test login with admin credentials
3. [ ] Verify all existing inventory/order features work
4. [ ] Test token refresh flow
5. [ ] Add Railway domain to backend ALLOWED_ORIGINS
6. [ ] Set up error monitoring (Sentry)
7. [ ] Configure production environment variables
8. [ ] Test with production Stripe keys (when ready)

---

## Changelog

- **2025-11-21:** Initial staging deployment
- Backend deployed to Railway
- All admin endpoints available
- Test credentials created
