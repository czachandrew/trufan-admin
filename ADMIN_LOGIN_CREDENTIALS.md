# Admin Login Credentials

## Your Account

**Email:** `czachandrew@gmail.com`
**Password:** `password`
**Role:** `super_admin` (full system access)

**User ID:** `bee59b64-edc5-4bc7-b5ef-b051362444b3`

---

## Login Endpoint

```bash
POST http://localhost:8000/api/v1/auth/login
Content-Type: application/json

{
  "email": "czachandrew@gmail.com",
  "password": "password"
}
```

---

## Example Response

```json
{
  "user": {
    "id": "bee59b64-edc5-4bc7-b5ef-b051362444b3",
    "email": "czachandrew@gmail.com",
    "firstName": "Andrew",
    "lastName": "Czachowski",
    "role": "super_admin",
    "isActive": true,
    "emailVerified": true
  },
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "tokenType": "bearer"
}
```

---

## Using in Frontend

### Axios Setup

```typescript
// src/api/client.ts
import axios from 'axios';

const client = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
});

// Add token to all requests
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Login Function

```typescript
// src/api/auth.ts
export async function login(email: string, password: string) {
  const response = await client.post('/auth/login', {
    email,
    password,
  });

  // Store tokens
  localStorage.setItem('access_token', response.data.accessToken);
  localStorage.setItem('refresh_token', response.data.refreshToken);

  return response.data;
}
```

---

## User Permissions

As a **super_admin**, you have access to:

✅ **All Parking Management**
- View/create/edit/delete parking lots
- Manage parking spaces
- Monitor all sessions
- Process refunds
- Add notes to sessions

✅ **All Opportunity Management**
- View all partner opportunities
- Create/edit/delete opportunities
- View analytics for all partners
- Validate and complete claims

✅ **User Management**
- View all users
- View user history
- Manage user accounts
- Access user analytics

✅ **System Analytics**
- Parking analytics across all lots
- Revenue reports
- Opportunity performance metrics
- System-wide statistics

---

## Available Roles

The system has 4 role levels:

1. **`customer`** - Regular parking users
2. **`venue_staff`** - Venue employees (limited access)
3. **`venue_admin`** - Venue managers (lot-specific access)
4. **`super_admin`** - You! (full system access)

---

## Quick Test Commands

### Test Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "czachandrew@gmail.com",
    "password": "password"
  }'
```

### Test Protected Endpoint
```bash
# Replace TOKEN with your access token
curl http://localhost:8000/api/v1/parking/lots \
  -H "Authorization: Bearer TOKEN"
```

---

## Token Expiration

- **Access Token:** Valid for ~1 year (for development convenience)
- **Refresh Token:** Valid for ~1 year

In production, these should be much shorter (15-60 minutes for access token).

---

## Changing Password

To change your password later, you can use:

```bash
docker-compose exec api python -m scripts.create_admin_user
```

This will update your password if the user already exists.

---

## Security Notes

⚠️ **Development Only**
- This password is for development/testing only
- Change it before production
- Never commit real credentials to git

---

## Next Steps

1. **Test Login in Frontend**
   - Use the login endpoint
   - Store the access token
   - Set up axios interceptor

2. **Test Protected Endpoints**
   - Try fetching parking lots: `GET /parking/lots`
   - Try fetching opportunities: `GET /partner/opportunities`

3. **Build Out Admin UI**
   - Dashboard with real data
   - Parking lot management
   - Session monitoring

---

## Support

If you have issues logging in:

1. Check the backend is running: `docker-compose ps`
2. Check API health: `curl http://localhost:8000/health`
3. Recreate user: `docker-compose exec api python -m scripts.create_admin_user`
4. Check logs: `docker-compose logs api`

---

**Created:** 2025-11-03
**Status:** ✅ Active and verified
