# TruFan - Comprehensive Venue and Event Management Platform

TruFan is a production-ready backend system for managing venues, events, parking, ticketing, concessions, and merchant operations. Built with FastAPI, PostgreSQL, and Redis, it provides a robust API for comprehensive venue management.

## Features

- **Authentication & Authorization**: JWT-based authentication with refresh tokens, role-based access control
- **User Management**: Multi-role system (customer, staff, admin, super admin)
- **Venue Management**: Multi-venue support with staff assignments and permissions
- **Event Management**: Event creation, ticketing, capacity management
- **Parking Management**: Dynamic pricing, space tracking, session management
- **Order System**: Concessions, merchandise, delivery tracking
- **Payment Processing**: Stripe Connect integration with split payments
- **Security**: Rate limiting, CORS, input validation, audit logging
- **Observability**: Correlation IDs, structured logging, health checks

## Tech Stack

- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Authentication**: JWT with refresh tokens
- **Payments**: Stripe Connect
- **Notifications**: Twilio (SMS), SMTP (Email)
- **ORM**: SQLAlchemy with Alembic migrations
- **Testing**: pytest with coverage
- **Containerization**: Docker & Docker Compose

## Project Structure

```
trufan/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/    # API route handlers
│   │   │       └── router.py     # Route aggregation
│   │   ├── core/                 # Core functionality
│   │   │   ├── config.py         # Configuration
│   │   │   ├── database.py       # Database setup
│   │   │   ├── security.py       # Auth utilities
│   │   │   ├── redis_client.py   # Redis client
│   │   │   ├── logging_config.py # Logging setup
│   │   │   └── dependencies.py   # FastAPI dependencies
│   │   ├── models/               # SQLAlchemy models
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── services/             # Business logic
│   │   ├── middleware/           # Custom middleware
│   │   └── main.py              # FastAPI application
│   ├── tests/                   # Test suite
│   ├── Dockerfile
│   └── requirements.txt
├── shared/                      # Shared code/types
├── migrations/                  # Database migrations
├── scripts/                     # Utility scripts
├── docs/                        # Documentation
├── docker-compose.yml
├── .env.example
└── README.md
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+ (if running locally)
- Redis 7+ (if running locally)

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd trufan
```

2. **Set up environment variables**

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `SECRET_KEY`: Generate with `openssl rand -hex 32`
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `STRIPE_SECRET_KEY`: Your Stripe secret key
- `TWILIO_*`: Twilio credentials for SMS

3. **Start with Docker Compose**

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- FastAPI application (port 8000)

4. **Run database migrations**

```bash
docker-compose exec api alembic upgrade head
```

5. **Seed the database (optional)**

```bash
docker-compose exec api python /app/../scripts/seed_data.py
```

6. **Access the API**

- API: http://localhost:8000
- Interactive docs: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc
- Health check: http://localhost:8000/health

## Development Setup

### Local Development (without Docker)

1. **Create virtual environment**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up local database**

```bash
# Create PostgreSQL database
createdb trufan

# Run migrations
alembic upgrade head
```

4. **Run the development server**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Creating Database Migrations

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Running Tests

```bash
# Run all tests
docker-compose exec api pytest

# Run with coverage
docker-compose exec api pytest --cov=app --cov-report=html

# Run specific test file
docker-compose exec api pytest tests/test_auth.py

# Run specific test
docker-compose exec api pytest tests/test_auth.py::TestLogin::test_login_success
```

## API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

Response:
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "customer",
    "is_active": true
  },
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ..."
}
```

### User Endpoints

#### Get Current User
```http
GET /api/v1/users/me
Authorization: Bearer {access_token}
```

#### Update Profile
```http
PATCH /api/v1/users/me
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "first_name": "Jane",
  "phone": "+9876543210"
}
```

### Rate Limiting

All endpoints are rate-limited to prevent abuse:
- Default: 60 requests per minute per IP
- Burst: 100 requests

Rate limit info is included in response headers:
- `X-RateLimit-Limit`: Maximum requests per minute
- `X-RateLimit-Remaining`: Remaining requests in current window

### Error Responses

All errors follow a consistent format:

```json
{
  "error": {
    "code": 400,
    "message": "Validation error",
    "details": [...],
    "correlation_id": "uuid"
  }
}
```

Status codes:
- `200 OK`: Success
- `201 Created`: Resource created
- `204 No Content`: Success with no response body
- `400 Bad Request`: Invalid request
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Database Schema

### Core Tables

- **users**: User accounts with authentication
- **venues**: Venue information and configuration
- **venue_staff**: Staff assignments to venues
- **events**: Events at venues
- **tickets**: Event tickets with QR codes
- **parking_lots**: Parking lot configuration
- **parking_sessions**: Active parking sessions
- **orders**: Customer orders
- **order_items**: Items in orders
- **payments**: Payment transactions
- **payment_splits**: Revenue sharing splits
- **audit_logs**: Audit trail for financial transactions

See individual model files in `backend/app/models/` for detailed schemas.

## Security Features

- **Password Security**: Bcrypt hashing with salt
- **JWT Tokens**: Access tokens (30 min) and refresh tokens (7 days)
- **SQL Injection Protection**: Parameterized queries via SQLAlchemy
- **Input Validation**: Pydantic schemas with comprehensive validation
- **Rate Limiting**: Per-IP rate limiting with Redis
- **CORS**: Configurable allowed origins
- **Audit Logging**: All financial transactions logged
- **Correlation IDs**: Request tracing for debugging

## Deployment

### Production Checklist

- [ ] Set strong `SECRET_KEY` (min 32 characters)
- [ ] Configure `ALLOWED_ORIGINS` for CORS
- [ ] Set `DEBUG=False`
- [ ] Use production database with backups
- [ ] Configure Redis persistence
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation
- [ ] Set up automated backups
- [ ] Configure Stripe webhook endpoints
- [ ] Test disaster recovery procedures

### Environment Variables

See `.env.example` for all configuration options.

## Monitoring and Logging

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "TruFan API",
  "environment": "production"
}
```

### Logging

Logs include correlation IDs for request tracing:

```
2024-01-15 10:30:45 - app.api - INFO - [a1b2c3d4-...] User logged in: user@example.com
```

## Sample Data

The seed script creates:
- 5 sample users (admin, venue admin, staff, 2 customers)
- 2 sample venues (Madison Square Garden, Crypto.com Arena)
- 2 sample events (concert, basketball game)
- 2 parking lots

Login credentials:
- Super Admin: `admin@trufan.com` / `Admin123!`
- Venue Admin: `venue.admin@example.com` / `VenueAdmin123!`
- Staff: `staff@example.com` / `Staff123!`
- Customer: `customer1@example.com` / `Customer123!`

## Testing Credentials

For Stripe testing, use test card numbers:
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`

## Contributing

1. Create a feature branch
2. Make your changes
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Redis Connection Issues

```bash
# Check Redis status
docker-compose exec redis redis-cli ping
# Should return: PONG

# View Redis logs
docker-compose logs redis
```

### API Issues

```bash
# View API logs
docker-compose logs api

# Restart API
docker-compose restart api

# Rebuild API container
docker-compose up -d --build api
```

## License

[Your License]

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: [docs-url]
- Email: support@trufan.com
