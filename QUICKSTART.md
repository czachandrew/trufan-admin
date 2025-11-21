# TruFan Quick Start Guide

Get the TruFan backend up and running in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- Basic understanding of REST APIs

## Steps

### 1. Clone and Setup

```bash
# Navigate to project directory
cd trufan

# Copy environment configuration
cp .env.example .env
```

### 2. Generate Secret Key

```bash
# Generate a secure secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Copy the output and update SECRET_KEY in .env file
```

### 3. Start Services

```bash
# Start all services (database, redis, api)
make setup

# Or manually:
# docker-compose up -d
# docker-compose exec api alembic upgrade head
# docker-compose exec api python /app/../scripts/seed_data.py
```

This will:
- Build Docker containers
- Start PostgreSQL, Redis, and FastAPI
- Run database migrations
- Seed sample data

### 4. Verify Installation

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"TruFan API","environment":"development"}
```

### 5. Explore the API

Open your browser to:
- **API Documentation**: http://localhost:8000/api/v1/docs
- **Alternative Docs**: http://localhost:8000/api/v1/redoc

### 6. Test Authentication

```bash
# Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123",
    "first_name": "Test",
    "last_name": "User"
  }'

# Save the access_token from the response

# Get user profile
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 7. Use Sample Data

The seed script creates sample accounts:

| Role | Email | Password |
|------|-------|----------|
| Super Admin | admin@trufan.com | Admin123! |
| Venue Admin | venue.admin@example.com | VenueAdmin123! |
| Staff | staff@example.com | Staff123! |
| Customer | customer1@example.com | Customer123! |

### 8. Common Commands

```bash
# View logs
make logs

# Stop services
make down

# Run tests
make test

# Access database
make db-shell

# Access API container
make shell
```

## Next Steps

1. **Read API Documentation**: Check `docs/API.md` for detailed endpoint documentation
2. **Explore Database Schema**: See models in `backend/app/models/`
3. **Run Tests**: `make test` to ensure everything works
4. **Customize Configuration**: Update `.env` with your settings
5. **Implement Additional Services**: Add venue, parking, ticketing endpoints

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs

# Restart services
make restart
```

### Database connection errors

```bash
# Ensure PostgreSQL is running
docker-compose ps db

# Check database logs
docker-compose logs db
```

### Port already in use

If port 8000 is already in use, edit `docker-compose.yml`:

```yaml
api:
  ports:
    - "8001:8000"  # Change 8001 to any available port
```

## Support

- **Issues**: Report bugs in GitHub Issues
- **Documentation**: See README.md for comprehensive documentation
- **API Docs**: http://localhost:8000/api/v1/docs

Happy coding!
