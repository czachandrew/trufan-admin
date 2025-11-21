# Railway Deployment Guide - TruFan Backend

## Quick Start (15 minutes to deployment)

This guide will get your FastAPI backend deployed to Railway with PostgreSQL and Redis for internal testing.

---

## Prerequisites

- GitHub account (to connect your repo)
- Railway account (sign up at https://railway.app - free tier available)
- Your Stripe test API keys
- Your Twilio credentials (or we'll disable SMS for now)

---

## Step 1: Prepare Your Repository

### Option A: Deploy from GitHub (Recommended)

1. Push your code to GitHub if you haven't already:
```bash
cd /Users/andrewczachowski/Projects/trufan
git init  # if not already a git repo
git add .
git commit -m "Prepare for Railway deployment"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### Option B: Deploy from CLI

Install Railway CLI:
```bash
npm install -g @railway/cli
railway login
```

---

## Step 2: Create Railway Project

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Authorize Railway to access your GitHub
4. Select your `trufan` repository
5. Railway will detect the Python project automatically

---

## Step 3: Add PostgreSQL Database

1. In your Railway project dashboard, click "New" → "Database" → "PostgreSQL"
2. Railway will automatically:
   - Provision a PostgreSQL 15 instance
   - Create a `DATABASE_URL` environment variable
   - Connect it to your app service

---

## Step 4: Add Redis

1. Click "New" → "Database" → "Redis"
2. Railway will automatically:
   - Provision a Redis instance
   - Create a `REDIS_URL` environment variable
   - Connect it to your app service

---

## Step 5: Configure Environment Variables

In your Railway project, click on your app service, then go to "Variables" tab.

**Add these variables:**

```bash
# JWT Configuration (CRITICAL - USE THIS NEW KEY)
SECRET_KEY=b0ac340f09f36452e4ecd4e1c608b872f1680af1179ac62275ad6a7843b2ae20
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# API Configuration
API_V1_PREFIX=/api/v1
PROJECT_NAME=TruFan API
DEBUG=True
ENVIRONMENT=staging

# CORS - UPDATE WITH YOUR ACTUAL DOMAINS
ALLOWED_ORIGINS=https://your-railway-app.railway.app,https://your-admin-domain.com,https://localhost:3000

# Stripe Configuration (USE YOUR ACTUAL TEST KEYS)
STRIPE_SECRET_KEY=sk_test_YOUR_ACTUAL_STRIPE_TEST_KEY
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_ACTUAL_STRIPE_TEST_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_ACTUAL_WEBHOOK_SECRET

# Twilio Configuration (OPTIONAL - Can use placeholder for now)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Email Configuration (OPTIONAL - Can configure later)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=noreply@trufan.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=100
```

**IMPORTANT:** Railway will automatically set `DATABASE_URL` and `REDIS_URL` - don't manually set these!

---

## Step 6: Configure Railway Build

Railway should auto-detect your Python project, but let's verify the settings:

1. Click on your app service → "Settings" tab
2. **Root Directory:** Leave as `/` (or set to `backend` if Railway isn't detecting it)
3. **Build Command:** Should auto-detect or use: `pip install -r backend/requirements.txt`
4. **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**OR** create a `railway.json` file in your project root:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "cd backend && pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

## Step 7: Run Database Migrations

Once your app is deployed, you need to run migrations.

### Option A: Using Railway CLI (Easiest)

```bash
# Connect to your Railway project
railway link

# Run migrations
railway run alembic upgrade head

# Optional: Seed test data
railway run python scripts/seed_data.py
```

### Option B: Using Railway Shell

1. In Railway dashboard, go to your app service
2. Click "Settings" → "Deploy" section
3. Find the deployed service and open the shell
4. Run:
```bash
cd backend
alembic upgrade head
```

---

## Step 8: Get Your API URL

1. In Railway dashboard, click on your app service
2. Go to "Settings" → "Networking"
3. Click "Generate Domain"
4. Railway will give you a URL like: `https://trufan-production.up.railway.app`
5. **Save this URL** - you'll need it for your mobile app!

---

## Step 9: Test Your Deployment

### Test Health Endpoint

```bash
curl https://your-railway-url.railway.app/health
```

Should return:
```json
{
  "status": "healthy",
  "service": "TruFan API",
  "environment": "staging"
}
```

### Test Authentication

```bash
# Register a user
curl -X POST https://your-railway-url.railway.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test1234!",
    "first_name": "Test",
    "last_name": "User",
    "role": "customer"
  }'

# Login
curl -X POST https://your-railway-url.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test1234!"
  }'
```

---

## Step 10: Update Your Mobile App

Update your mobile app's API configuration to point to your Railway URL:

```swift
// iOS - Update your API base URL
let baseURL = "https://your-railway-url.railway.app/api/v1"
```

---

## Monitoring & Debugging

### View Logs

In Railway dashboard:
1. Click on your app service
2. Go to "Deployments" tab
3. Click on the latest deployment
4. View real-time logs

### Common Issues

**Build fails:**
- Check that `requirements.txt` is in the correct location
- Verify Python version compatibility

**Database connection fails:**
- Make sure PostgreSQL service is running
- Check that `DATABASE_URL` is automatically set

**App crashes on startup:**
- Check logs for missing environment variables
- Verify migrations have been run

**CORS errors from mobile app:**
- Update `ALLOWED_ORIGINS` to include your actual domains
- Add `*` temporarily for testing (NOT for production!)

---

## Cost Estimate

Railway Free Tier includes:
- $5 of credit per month
- Enough for ~500 hours of uptime

For testing phase, expect:
- **App Service:** ~$5-10/month
- **PostgreSQL:** ~$5/month (with backups)
- **Redis:** ~$2/month
- **Total:** ~$12-17/month (first month mostly covered by free credit)

---

## Next Steps After Deployment

1. **Update ALLOWED_ORIGINS** with your actual Railway domain
2. **Configure Stripe webhook** in Stripe Dashboard to point to `https://your-railway-url.railway.app/api/v1/payments/webhook`
3. **Set up monitoring** (Railway has built-in metrics)
4. **Test all endpoints** from your mobile app
5. **Create admin user** for testing
6. **Document your Railway URL** for your testing team

---

## Critical Environment Variables Checklist

Before distributing to testers, verify these are set:

- [x] `SECRET_KEY` - New secure key generated (NOT the dev key)
- [x] `DATABASE_URL` - Auto-set by Railway PostgreSQL
- [x] `REDIS_URL` - Auto-set by Railway Redis
- [ ] `STRIPE_SECRET_KEY` - Your actual Stripe test key
- [ ] `STRIPE_PUBLISHABLE_KEY` - Your actual Stripe test key
- [ ] `STRIPE_WEBHOOK_SECRET` - Your actual webhook secret
- [x] `ALLOWED_ORIGINS` - Updated with Railway domain
- [x] `DEBUG` - Set to True for internal testing (logs will help)
- [x] `ENVIRONMENT` - Set to "staging"

---

## Rollback Strategy

If something goes wrong:

1. In Railway dashboard, go to "Deployments"
2. Find a previous working deployment
3. Click "..." → "Redeploy"
4. Railway will rollback to that version

---

## Production Migration (Future)

When ready to move to DigitalOcean:

1. Set `DEBUG=False` and `ENVIRONMENT=production`
2. Use production Stripe keys (not test)
3. Set up proper SSL certificates
4. Configure automated backups
5. Set up proper monitoring and alerting
6. Export data from Railway PostgreSQL
7. Import to DigitalOcean PostgreSQL

---

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Deployment issues: Check Railway logs first
- Database issues: Verify `DATABASE_URL` format matches PostgreSQL connection string

---

## Generated Credentials

**SECRET_KEY (save this):**
```
b0ac340f09f36452e4ecd4e1c608b872f1680af1179ac62275ad6a7843b2ae20
```

**Railway URL (after deployment):**
```
https://[YOUR-PROJECT-NAME].up.railway.app
```

---

Good luck with your deployment! Once Railway is configured, subsequent deployments will be automatic on git push.
