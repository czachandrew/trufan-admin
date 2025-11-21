# CORS Configuration Fix

## Issue

Frontend running on `http://localhost:3001` was getting CORS errors when trying to authenticate:

```
Access to XMLHttpRequest at 'http://localhost:8000/api/v1/auth/login' from origin 'http://localhost:3001'
has been blocked by CORS policy: Response to preflight request doesn't pass access control check:
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Root Cause

The `.env` file had `ALLOWED_ORIGINS` set to only include ports 3000 and 8000:

```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

But the frontend was running on port **3001**.

## Solution

### 1. Updated `.env` file

Added `http://localhost:3001` to the allowed origins:

```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:8000
```

### 2. Recreated API container

A simple `restart` doesn't reload environment variables from `.env`. Had to force recreate:

```bash
docker-compose up -d --force-recreate api
```

## Verification

### Preflight Request Test
```bash
curl -X OPTIONS \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -i http://localhost:8000/api/v1/auth/login
```

**Response:**
```
HTTP/1.1 200 OK
access-control-allow-origin: http://localhost:3001
access-control-allow-credentials: true
access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
access-control-allow-headers: Content-Type
```

✅ **CORS is working!**

### Actual Login Test
```bash
curl -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Origin: http://localhost:3001' \
  -H 'Content-Type: application/json' \
  -d '{"email":"czachandrew@gmail.com","password":"password"}'
```

**Response:**
```
HTTP/1.1 200 OK
access-control-allow-origin: http://localhost:3001
access-control-allow-credentials: true

{
  "user": {...},
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "bearer"
}
```

✅ **Login working with CORS!**

---

## Current CORS Configuration

**File:** `.env`

```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:8000
```

**How it works:**
1. Environment variable is read by `app/core/config.py`
2. Converted to a list in `Settings.cors_origins` property
3. Passed to FastAPI's `CORSMiddleware` in `app/main.py`

---

## Adding More Origins

To add more allowed origins (e.g., for production):

1. Edit `.env`:
```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,https://admin.trufan.com,https://app.trufan.com
```

2. Recreate API container:
```bash
docker-compose up -d --force-recreate api
```

**Note:** For production, be specific about origins. Don't use wildcards unless absolutely necessary.

---

## Troubleshooting

### CORS still not working after .env change?

1. **Verify environment variable in container:**
   ```bash
   docker-compose exec api printenv ALLOWED_ORIGINS
   ```

2. **Force recreate (not just restart):**
   ```bash
   docker-compose up -d --force-recreate api
   ```

3. **Check CORS middleware is configured:**
   ```bash
   docker-compose exec api python -c "from app.core.config import settings; print(settings.cors_origins)"
   ```

### Frontend still getting CORS errors?

1. **Clear browser cache** - Old preflight responses might be cached
2. **Check browser console** - See exact error message
3. **Use browser DevTools Network tab** - Check if preflight (OPTIONS) request succeeded
4. **Verify frontend is making requests to correct URL** - Should be `http://localhost:8000/api/v1/...`

---

## Security Notes

### Development
- ✅ Allow localhost origins (3000, 3001, 8000)
- ✅ Allow credentials (needed for cookies/auth)

### Production
- ⚠️ Only allow specific production domains
- ⚠️ Never use `allow_origins=["*"]` with `allow_credentials=True`
- ⚠️ Use HTTPS origins only
- ⚠️ Be explicit about allowed methods and headers

**Example production config:**
```env
ALLOWED_ORIGINS=https://admin.trufan.com,https://app.trufan.com
```

---

**Fixed:** 2025-11-03
**Status:** ✅ Working
**Tested:** Preflight + Login both successful
