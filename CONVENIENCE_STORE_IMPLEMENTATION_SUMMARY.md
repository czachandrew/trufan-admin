# Convenience Store Feature - Technical Implementation Summary

## Executive Summary

This document provides a comprehensive technical overview of the Convenience Store feature implementation for the TruFan parking platform. It includes database schema design, API architecture, authentication flows, business logic, and recommendations for implementation.

**Status**: SPECIFICATION COMPLETE - IMPLEMENTATION PENDING

**Last Updated**: November 7, 2025

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Database Schema](#database-schema)
3. [API Endpoints](#api-endpoints)
4. [Authentication & Authorization](#authentication--authorization)
5. [Order Lifecycle](#order-lifecycle)
6. [Payment Flow](#payment-flow)
7. [Business Logic](#business-logic)
8. [Implementation Checklist](#implementation-checklist)
9. [Security Considerations](#security-considerations)
10. [Performance Optimization](#performance-optimization)
11. [Testing Strategy](#testing-strategy)
12. [Future Enhancements](#future-enhancements)

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
├─────────────────────────────────────────────────────────────┤
│  Customer App  │  Staff App  │  Admin Dashboard  │  API Docs│
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                         API Gateway                          │
├─────────────────────────────────────────────────────────────┤
│  Authentication  │  Rate Limiting  │  Request Validation     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      API Endpoints Layer                     │
├──────────────────┬──────────────────┬───────────────────────┤
│  Customer Routes │  Staff Routes    │  Admin Routes         │
│  /convenience/   │  /convenience/   │  /convenience/admin/  │
│  orders          │  staff/orders    │  venues/{id}/items    │
└──────────────────┴──────────────────┴───────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
├──────────────────┬──────────────────┬───────────────────────┤
│  Item Service    │  Order Service   │  Payment Service      │
│  - CRUD          │  - Create        │  - Authorize          │
│  - Bulk Import   │  - Update Status │  - Capture            │
│  - Validation    │  - Calculate $   │  - Refund             │
└──────────────────┴──────────────────┴───────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       Data Layer                             │
├──────────────────┬──────────────────┬───────────────────────┤
│  PostgreSQL      │  Redis Cache     │  S3/CDN               │
│  - Items         │  - Sessions      │  - Photos             │
│  - Orders        │  - Active Orders │  - Receipts           │
│  - Events        │  - Capacity      │  - Item Images        │
└──────────────────┴──────────────────┴───────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
├──────────────────┬──────────────────┬───────────────────────┤
│  Stripe          │  Twilio          │  Push Notifications   │
│  - Payments      │  - SMS           │  - Status Updates     │
└──────────────────┴──────────────────┴───────────────────────┘
```

### Technology Stack

**Backend:**
- Framework: FastAPI (Python 3.11+)
- ORM: SQLAlchemy
- Database: PostgreSQL 15+
- Cache: Redis 7+
- Task Queue: Celery (for async tasks)
- File Storage: AWS S3 or compatible

**Authentication:**
- JWT tokens (access + refresh)
- Bearer token authentication
- Role-based access control (RBAC)

**Payment Processing:**
- Stripe Payment Intents API
- Payment authorization before shopping
- Payment capture on delivery
- Automatic refunds for cancellations

**Notifications:**
- Twilio SMS for critical updates
- Push notifications via FCM/APNs
- Email for order confirmations

---

## Database Schema

### Entity Relationship Diagram (Text-Based)

```
┌─────────────────────┐
│       venues        │
│─────────────────────│
│ id (PK)             │
│ name                │
│ address             │
└─────────────────────┘
          │
          │ 1:N
          ↓
┌──────────────────────────────┐
│ convenience_store_config     │
│──────────────────────────────│
│ id (PK)                      │
│ venue_id (FK) UNIQUE         │
│ is_enabled                   │
│ default_service_fee_percent  │
│ minimum_order_amount         │
│ maximum_order_amount         │
│ default_complimentary_min    │
│ operating_hours (JSONB)      │
│ storage_locations (ARRAY)    │
└──────────────────────────────┘

┌─────────────────────┐
│       venues        │
│─────────────────────│
│ id (PK)             │
└─────────────────────┘
          │
          │ 1:N
          ↓
┌──────────────────────────────┐
│   convenience_items          │
│──────────────────────────────│
│ id (PK)                      │
│ venue_id (FK)                │
│ name                         │
│ description                  │
│ category                     │
│ base_price                   │
│ markup_amount                │
│ markup_percent               │
│ final_price                  │
│ source_store                 │
│ is_active                    │
│ requires_age_verification    │
│ tags (ARRAY)                 │
│ created_by_id (FK)           │
└──────────────────────────────┘

┌─────────────────────┐         ┌──────────────────────┐
│       users         │         │    venues            │
│─────────────────────│         │──────────────────────│
│ id (PK)             │         │ id (PK)              │
└─────────────────────┘         └──────────────────────┘
     │         │                         │
     │         │ 1:N                     │ 1:N
     │         ↓                         ↓
     │  ┌──────────────────────────────────────┐
     │  │     convenience_orders               │
     │  │──────────────────────────────────────│
     │  │ id (PK)                              │
     │  │ order_number (UNIQUE)                │
     │  │ venue_id (FK)                        │
     │  │ user_id (FK)                         │
     │  │ parking_session_id (FK)              │
     │  │ status                               │
     │  │ subtotal                             │
     │  │ service_fee                          │
     │  │ tax                                  │
     │  │ tip_amount                           │
     │  │ total_amount                         │
     │  │ payment_intent_id                    │
     │  │ assigned_staff_id (FK)               │
     │  │ storage_location                     │
     │  │ delivery_instructions                │
     │  │ receipt_photo_url                    │
     │  │ delivery_photo_url                   │
     │  │ estimated_ready_time                 │
     │  │ [timestamp fields]                   │
     │  │ complimentary_time_added_minutes     │
     │  │ rating                               │
     │  │ feedback                             │
     │  └──────────────────────────────────────┘
     │           │                    │
     │           │ 1:N                │ 1:N
     │           ↓                    ↓
     │  ┌─────────────────────┐  ┌──────────────────────┐
     │  │ convenience_        │  │ convenience_         │
     │  │ order_items         │  │ order_events         │
     │  │─────────────────────│  │──────────────────────│
     │  │ id (PK)             │  │ id (PK)              │
     │  │ order_id (FK)       │  │ order_id (FK)        │
     │  │ item_id (FK)        │  │ status               │
     │  │ quantity            │  │ notes                │
     │  │ unit_price          │  │ photo_url            │
     │  │ line_total          │  │ created_by_id (FK)   │
     │  │ status              │  │ created_at           │
     │  │ substitution_notes  │  └──────────────────────┘
     │  │ actual_price        │
     │  └─────────────────────┘
     │
     └─────── created_by (FK)
```

### Table Specifications

#### 1. convenience_store_config

**Purpose**: Per-venue configuration for the convenience store feature

**Key Fields:**
- `is_enabled`: Feature toggle
- `default_service_fee_percent`: Default markup (e.g., 15%)
- `minimum_order_amount`: Minimum order total (e.g., $5)
- `maximum_order_amount`: Maximum order total (e.g., $200)
- `operating_hours`: JSONB with day-of-week schedules
- `storage_locations`: Array of available storage locations

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE index on `venue_id`

**Constraints:**
- `venue_id` references `venues(id)` ON DELETE CASCADE
- `default_service_fee_percent` BETWEEN 0 AND 100
- `minimum_order_amount` >= 0
- `maximum_order_amount` > minimum_order_amount

#### 2. convenience_items

**Purpose**: Catalog of items available for purchase at each venue

**Key Fields:**
- `venue_id`: Which venue offers this item
- `base_price`: Store price
- `markup_amount`: Fixed dollar markup
- `markup_percent`: Percentage markup
- `final_price`: Price charged to customer
- `source_store`: Where to buy the item
- `category`: Item categorization
- `is_active`: Item availability toggle

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `(venue_id, is_active)`
- INDEX on `category`
- INDEX on `source_store`

**Constraints:**
- `venue_id` references `venues(id)` ON DELETE CASCADE
- `base_price` > 0
- `final_price` > 0
- `max_quantity_per_order` > 0

**Categories:**
- `grocery`: Milk, bread, eggs, etc.
- `food`: Prepared foods, snacks
- `beverage`: Drinks, water, soda
- `personal_care`: Hygiene products
- `electronics`: Chargers, accessories
- `other`: Miscellaneous items

#### 3. convenience_orders

**Purpose**: Customer orders for convenience store items

**Key Fields:**
- `order_number`: Human-readable order ID (e.g., "CS-1234")
- `status`: Current order status
- `subtotal`: Sum of all item prices
- `service_fee`: Venue's markup
- `tax`: Sales tax
- `total_amount`: Final charge
- `payment_intent_id`: Stripe payment intent
- `assigned_staff_id`: Staff member fulfilling order
- `storage_location`: Where items are stored
- Timestamp fields for each status

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE index on `order_number`
- INDEX on `(venue_id, status)`
- INDEX on `user_id`
- INDEX on `parking_session_id`
- INDEX on `status`

**Status Flow:**
```
pending → confirmed → shopping → purchased → stored → ready → delivered → completed
   ↓                                                              ↓
cancelled ←───────────────────────────────────────────────────────┘
```

#### 4. convenience_order_items

**Purpose**: Line items within an order (snapshot of items at time of purchase)

**Key Fields:**
- `order_id`: Parent order
- `item_id`: Reference to catalog item (nullable for deleted items)
- `item_name`: Snapshot of item name
- `quantity`: Number of units
- `unit_price`: Price per unit at time of order
- `line_total`: quantity × unit_price
- `status`: Item-level status (found, not_found, substituted)
- `actual_price`: Real price paid at store

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `order_id`

**Why Snapshot Data?**
Items in the catalog may change price or be deleted. We store a snapshot of item details at the time of order to maintain historical accuracy.

#### 5. convenience_order_events

**Purpose**: Audit log of order status changes

**Key Fields:**
- `order_id`: Associated order
- `status`: New status
- `notes`: Staff notes
- `photo_url`: Optional photo evidence
- `created_by_id`: Staff member who made change
- `created_at`: Timestamp

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `(order_id, created_at)`
- INDEX on `new_status`

**Use Cases:**
- Status change audit trail
- Customer transparency
- Staff accountability
- Debugging order issues
- Analytics on fulfillment times

---

## API Endpoints

### Endpoint Categories

1. **Admin Endpoints**: Venue management (items, configuration)
2. **Customer Endpoints**: Browsing and ordering
3. **Staff Endpoints**: Order fulfillment

### Authentication Matrix

| Endpoint Group | Required Role | Notes |
|---------------|---------------|-------|
| Admin Item Management | VENUE_ADMIN, SUPER_ADMIN | Must own venue |
| Admin Configuration | VENUE_ADMIN, SUPER_ADMIN | Must own venue |
| Admin Orders | VENUE_ADMIN, SUPER_ADMIN | Must own venue |
| Customer Browsing | None (public) | Optional auth for personalization |
| Customer Ordering | CUSTOMER, VENUE_STAFF, VENUE_ADMIN | Must be authenticated |
| Staff Fulfillment | VENUE_STAFF, VENUE_ADMIN | Must be staff at venue |

### Admin Endpoints

#### Item Management

```http
GET /api/v1/convenience/admin/venues/{venue_id}/items
```
**Purpose**: List all items for a venue
**Auth**: Required (VENUE_ADMIN+)
**Query Params**:
- `is_active`: Filter by active status
- `category`: Filter by category
- `source_store`: Filter by source store
- `search`: Search in name/description
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50)

**Response**:
```json
{
  "items": [
    {
      "id": "uuid",
      "venue_id": "uuid",
      "name": "Gallon of Milk",
      "description": "Fresh 2% milk",
      "category": "grocery",
      "base_price": 4.99,
      "markup_percent": 15.0,
      "final_price": 5.74,
      "source_store": "Walgreens",
      "is_active": true,
      "created_at": "2025-11-07T10:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "pages": 2
}
```

---

```http
POST /api/v1/convenience/admin/venues/{venue_id}/items
```
**Purpose**: Create a new item
**Auth**: Required (VENUE_ADMIN+)
**Request Body**:
```json
{
  "name": "Gallon of Milk - 2%",
  "description": "Fresh 2% reduced fat milk",
  "category": "grocery",
  "base_price": 4.99,
  "markup_percent": 15.0,
  "final_price": 5.74,
  "source_store": "Walgreens Main St",
  "source_address": "123 Main St",
  "estimated_shopping_time_minutes": 10,
  "is_active": true,
  "requires_age_verification": false,
  "max_quantity_per_order": 2,
  "tags": ["dairy", "refrigerated"],
  "image_url": "https://cdn.example.com/milk.jpg"
}
```

**Response**: 201 Created
```json
{
  "id": "uuid",
  "venue_id": "uuid",
  "name": "Gallon of Milk - 2%",
  ...
}
```

---

```http
PUT /api/v1/convenience/admin/venues/{venue_id}/items/{item_id}
```
**Purpose**: Update an existing item
**Auth**: Required (VENUE_ADMIN+)

---

```http
DELETE /api/v1/convenience/admin/venues/{venue_id}/items/{item_id}
```
**Purpose**: Delete an item (soft delete recommended)
**Auth**: Required (VENUE_ADMIN+)

---

```http
PATCH /api/v1/convenience/admin/venues/{venue_id}/items/{item_id}/toggle
```
**Purpose**: Toggle item active status
**Auth**: Required (VENUE_ADMIN+)
**Request Body**:
```json
{
  "is_active": false
}
```

---

```http
POST /api/v1/convenience/admin/venues/{venue_id}/items/bulk-import
```
**Purpose**: Bulk import items from CSV
**Auth**: Required (VENUE_ADMIN+)
**Content-Type**: multipart/form-data
**Form Data**:
- `file`: CSV file with item data

**CSV Format**:
```csv
name,description,category,base_price,markup_percent,final_price,source_store,...
```

**Response**:
```json
{
  "imported": 50,
  "errors": [
    {
      "row": 12,
      "error": "Invalid price format"
    }
  ]
}
```

#### Configuration Management

```http
GET /api/v1/convenience/admin/venues/{venue_id}/config
```
**Purpose**: Get venue configuration
**Auth**: Required (VENUE_ADMIN+)

---

```http
PUT /api/v1/convenience/admin/venues/{venue_id}/config
```
**Purpose**: Update venue configuration
**Auth**: Required (VENUE_ADMIN+)
**Request Body**:
```json
{
  "is_enabled": true,
  "default_service_fee_percent": 15.0,
  "minimum_order_amount": 5.0,
  "maximum_order_amount": 200.0,
  "default_complimentary_parking_minutes": 15,
  "average_fulfillment_time_minutes": 30,
  "operating_hours": {
    "monday": {"open": "08:00", "close": "20:00"}
  },
  "storage_locations": ["Trunk", "Front Desk"]
}
```

#### Order Management

```http
GET /api/v1/convenience/admin/venues/{venue_id}/orders
```
**Purpose**: List orders for a venue
**Auth**: Required (VENUE_ADMIN+)
**Query Params**:
- `status`: Filter by status
- `date_from`: Filter by date range
- `date_to`: Filter by date range
- `search`: Search by order number or customer name

---

```http
PATCH /api/v1/convenience/admin/venues/{venue_id}/orders/{order_id}/refund
```
**Purpose**: Refund an order
**Auth**: Required (VENUE_ADMIN+)
**Request Body**:
```json
{
  "refund_amount": 25.99,
  "refund_reason": "Store closed, unable to fulfill"
}
```

### Customer Endpoints

#### Browse Items

```http
GET /api/v1/convenience/venues/{venue_id}/items
```
**Purpose**: Browse available items (public or authenticated)
**Auth**: Optional
**Query Params**:
- `category`: Filter by category
- `search`: Search items
- `page`: Page number
- `limit`: Items per page

---

```http
GET /api/v1/convenience/venues/{venue_id}/items/{item_id}
```
**Purpose**: Get item details
**Auth**: Optional

---

```http
GET /api/v1/convenience/venues/{venue_id}/categories
```
**Purpose**: Get list of available categories with item counts
**Auth**: Optional
**Response**:
```json
{
  "categories": [
    {"name": "grocery", "count": 25},
    {"name": "beverage", "count": 15},
    {"name": "food", "count": 20}
  ]
}
```

#### Order Management

```http
POST /api/v1/convenience/orders
```
**Purpose**: Create a new order
**Auth**: Required (CUSTOMER+)
**Request Body**:
```json
{
  "venue_id": "uuid",
  "parking_session_id": "uuid",
  "items": [
    {"item_id": "uuid", "quantity": 1},
    {"item_id": "uuid", "quantity": 2}
  ],
  "delivery_instructions": "Deliver to trunk",
  "special_instructions": "Please get cold items"
}
```

**Response**: 201 Created
```json
{
  "id": "uuid",
  "order_number": "CS-1234",
  "status": "pending",
  "subtotal": 20.08,
  "service_fee": 3.01,
  "tax": 1.85,
  "total_amount": 24.94,
  "estimated_ready_time": "2025-11-07T10:45:00Z",
  "payment_intent_id": "pi_xxx",
  "payment_status": "authorized"
}
```

---

```http
GET /api/v1/convenience/orders/{order_id}
```
**Purpose**: Get order details
**Auth**: Required (must be order owner or venue staff)

---

```http
GET /api/v1/convenience/my-orders
```
**Purpose**: Get current user's orders
**Auth**: Required (CUSTOMER+)
**Query Params**:
- `status`: Filter by status
- `venue_id`: Filter by venue

---

```http
PATCH /api/v1/convenience/orders/{order_id}/cancel
```
**Purpose**: Cancel an order (only before shopping starts)
**Auth**: Required (must be order owner)
**Request Body**:
```json
{
  "reason": "Changed my mind"
}
```

---

```http
POST /api/v1/convenience/orders/{order_id}/rate
```
**Purpose**: Rate a completed order
**Auth**: Required (must be order owner)
**Request Body**:
```json
{
  "rating": 5,
  "feedback": "Great service, items delivered quickly!"
}
```

### Staff Endpoints

```http
GET /api/v1/convenience/staff/venues/{venue_id}/orders
```
**Purpose**: Get orders for staff fulfillment
**Auth**: Required (VENUE_STAFF+)
**Query Params**:
- `status`: Filter by status (default: pending, confirmed, shopping)

---

```http
PATCH /api/v1/convenience/staff/orders/{order_id}/accept
```
**Purpose**: Accept and confirm an order
**Auth**: Required (VENUE_STAFF+)
**Request Body**:
```json
{
  "notes": "Will shop at Walgreens",
  "estimated_ready_time": "2025-11-07T10:45:00Z"
}
```

---

```http
PATCH /api/v1/convenience/staff/orders/{order_id}/start-shopping
```
**Purpose**: Mark order as shopping in progress
**Auth**: Required (VENUE_STAFF+)

---

```http
PATCH /api/v1/convenience/staff/orders/{order_id}/complete-shopping
```
**Purpose**: Mark shopping as complete
**Auth**: Required (VENUE_STAFF+)
**Request Body**:
```json
{
  "notes": "All items purchased",
  "receipt_photo_url": "https://cdn.example.com/receipt.jpg"
}
```

---

```http
PATCH /api/v1/convenience/staff/orders/{order_id}/store
```
**Purpose**: Mark items as stored
**Auth**: Required (VENUE_STAFF+)
**Request Body**:
```json
{
  "storage_location": "Refrigerator - Shelf 2",
  "notes": "Cold items in fridge"
}
```

---

```http
PATCH /api/v1/convenience/staff/orders/{order_id}/deliver
```
**Purpose**: Mark order as delivered
**Auth**: Required (VENUE_STAFF+)
**Request Body**:
```json
{
  "delivery_photo_url": "https://cdn.example.com/delivery.jpg",
  "notes": "Delivered to trunk"
}
```

---

```http
POST /api/v1/convenience/staff/orders/{order_id}/update-item
```
**Purpose**: Update individual item status (substitutions, not found)
**Auth**: Required (VENUE_STAFF+)
**Request Body**:
```json
{
  "order_item_id": "uuid",
  "status": "substituted",
  "substitution_notes": "Substituted with store brand",
  "actual_price": 4.49
}
```

---

```http
POST /api/v1/convenience/staff/orders/{order_id}/upload-receipt
```
**Purpose**: Upload receipt photo
**Auth**: Required (VENUE_STAFF+)
**Content-Type**: multipart/form-data
**Form Data**:
- `file`: Receipt photo

---

## Authentication & Authorization

### Authentication Flow

```
┌──────────┐                                    ┌──────────┐
│  Client  │                                    │  Server  │
└─────┬────┘                                    └────┬─────┘
      │                                              │
      │  POST /api/v1/auth/login                    │
      │  {email, password}                          │
      ├────────────────────────────────────────────>│
      │                                              │
      │  {access_token, refresh_token, user}        │
      │<────────────────────────────────────────────┤
      │                                              │
      │  GET /api/v1/convenience/items              │
      │  Authorization: Bearer {access_token}       │
      ├────────────────────────────────────────────>│
      │                                              │
      │  Verify token → Get user → Check permissions│
      │                                              │
      │  {items: [...]}                             │
      │<────────────────────────────────────────────┤
      │                                              │
      │  [access_token expires after 1 hour]        │
      │                                              │
      │  POST /api/v1/auth/refresh                  │
      │  {refresh_token}                            │
      ├────────────────────────────────────────────>│
      │                                              │
      │  {access_token, refresh_token}              │
      │<────────────────────────────────────────────┤
      │                                              │
```

### Authorization Rules

#### Role Hierarchy

```
SUPER_ADMIN (level 3)
    ↓
VENUE_ADMIN (level 2)
    ↓
VENUE_STAFF (level 1)
    ↓
CUSTOMER (level 0)
```

#### Permission Matrix

| Action | CUSTOMER | VENUE_STAFF | VENUE_ADMIN | SUPER_ADMIN |
|--------|----------|-------------|-------------|-------------|
| Browse items (public venue) | ✓ | ✓ | ✓ | ✓ |
| Create order | ✓ | ✓ | ✓ | ✓ |
| View own orders | ✓ | ✓ | ✓ | ✓ |
| Cancel own order | ✓ | ✓ | ✓ | ✓ |
| Rate order | ✓ | ✓ | ✓ | ✓ |
| View venue orders | ✗ | ✓ (own venue) | ✓ (own venue) | ✓ (all) |
| Accept/fulfill orders | ✗ | ✓ (own venue) | ✓ (own venue) | ✓ (all) |
| Create/edit items | ✗ | ✗ | ✓ (own venue) | ✓ (all) |
| Edit venue config | ✗ | ✗ | ✓ (own venue) | ✓ (all) |
| Issue refunds | ✗ | ✗ | ✓ (own venue) | ✓ (all) |

#### Ownership Validation

**For venue-scoped operations:**
```python
def check_venue_access(user: User, venue_id: UUID) -> bool:
    """Check if user has access to venue"""

    # Super admins have access to all venues
    if user.role == UserRole.SUPER_ADMIN:
        return True

    # Check if user is associated with venue
    if user.role in [UserRole.VENUE_ADMIN, UserRole.VENUE_STAFF]:
        # Query user's venue associations
        venue_association = db.query(UserVenueAssociation).filter(
            UserVenueAssociation.user_id == user.id,
            UserVenueAssociation.venue_id == venue_id,
            UserVenueAssociation.is_active == True
        ).first()

        return venue_association is not None

    return False
```

**For order operations:**
```python
def check_order_access(user: User, order: ConvenienceOrder, action: str) -> bool:
    """Check if user has access to order"""

    # Customer can only access their own orders
    if user.role == UserRole.CUSTOMER:
        return order.user_id == user.id

    # Staff can access orders from their venue
    if user.role in [UserRole.VENUE_STAFF, UserRole.VENUE_ADMIN]:
        return check_venue_access(user, order.venue_id)

    # Super admin has access to all orders
    if user.role == UserRole.SUPER_ADMIN:
        return True

    return False
```

### Security Best Practices

1. **Token Management**
   - Access tokens expire after 1 hour
   - Refresh tokens expire after 30 days
   - Tokens stored securely (not in localStorage)
   - Logout invalidates refresh token

2. **Input Validation**
   - Validate all user inputs
   - Sanitize search queries
   - Validate file uploads (size, type)
   - Check price calculations server-side

3. **Rate Limiting**
   - 100 requests per minute per user
   - 10 order creations per hour per user
   - 5 failed login attempts before lockout

4. **Data Protection**
   - HTTPS only (TLS 1.3+)
   - Encrypt sensitive data at rest
   - PCI compliance for payment data
   - GDPR compliance for user data

---

## Order Lifecycle

### Status Flow Diagram

```
                      ┌─────────────────────┐
                      │   Order Created     │
                      │   status: pending   │
                      └──────────┬──────────┘
                                 │
                                 ↓
                      ┌─────────────────────┐
                  ┌──→│  Staff Accepts      │
                  │   │  status: confirmed  │
                  │   └──────────┬──────────┘
                  │              │
                  │              ↓
                  │   ┌─────────────────────┐
                  │   │  Staff Starts Shop  │
                  │   │  status: shopping   │
                  │   └──────────┬──────────┘
                  │              │
                  │              ↓
                  │   ┌─────────────────────┐
                  │   │  Shopping Complete  │
                  │   │  status: purchased  │
                  │   └──────────┬──────────┘
                  │              │
                  │              ↓
                  │   ┌─────────────────────┐
                  │   │  Items Stored       │
                  │   │  status: stored     │
                  │   └──────────┬──────────┘
                  │              │
                  │              ↓
                  │   ┌─────────────────────┐
                  │   │  Ready for Pickup   │
                  │   │  status: ready      │
                  │   └──────────┬──────────┘
                  │              │
                  │              ↓
                  │   ┌─────────────────────┐
                  │   │  Items Delivered    │
                  │   │  status: delivered  │
                  │   └──────────┬──────────┘
                  │              │
                  │              ↓
                  │   ┌─────────────────────┐
                  │   │  Order Complete     │
                  │   │  status: completed  │
                  │   └─────────────────────┘
                  │
                  │   ┌─────────────────────┐
                  └──→│  Order Cancelled    │
                      │  status: cancelled  │
                      └─────────────────────┘
```

### Status Transitions

| Current Status | Allowed Next Status | Triggered By | Side Effects |
|---------------|---------------------|--------------|--------------|
| pending | confirmed | Staff accepts order | - Assign staff<br>- Set estimated time<br>- Notify customer |
| pending | cancelled | Customer/Staff cancels | - Refund payment<br>- Notify customer |
| confirmed | shopping | Staff starts shopping | - Update timestamp<br>- Notify customer |
| confirmed | cancelled | Staff/Admin cancels | - Refund payment<br>- Notify customer |
| shopping | purchased | Staff completes shopping | - Upload receipt<br>- Update item statuses<br>- Notify customer |
| shopping | cancelled | Staff/Admin cancels | - Refund payment<br>- Notify customer |
| purchased | stored | Staff stores items | - Set storage location<br>- Notify customer |
| stored | ready | Items ready for pickup | - Notify customer<br>- Send location info |
| ready | delivered | Staff delivers items | - Upload delivery photo<br>- Capture payment<br>- Notify customer<br>- Add parking time |
| delivered | completed | Automatic after 24hrs or customer confirmation | - Request rating<br>- Close order |

### Timing Expectations

| Status Transition | Target Time | Max Acceptable Time |
|------------------|-------------|---------------------|
| pending → confirmed | 5 minutes | 15 minutes |
| confirmed → shopping | 10 minutes | 30 minutes |
| shopping → purchased | 15-20 minutes | 45 minutes |
| purchased → stored | 5 minutes | 15 minutes |
| stored → ready | Immediate | 5 minutes |
| ready → delivered | 10 minutes | 30 minutes |
| **Total (pending → delivered)** | **30-40 minutes** | **90 minutes** |

### Notification Triggers

**To Customer:**
1. **Order Confirmed** (pending → confirmed)
   - "Your order #CS-1234 has been accepted! Our staff will start shopping shortly."

2. **Shopping Started** (confirmed → shopping)
   - "We're shopping for your items at Walgreens. Estimated ready time: 2:30pm"

3. **Items Purchased** (shopping → purchased)
   - "Items purchased! We're heading back to store them safely."

4. **Items Stored** (purchased → stored)
   - "Your items are stored in: Refrigerator - Shelf 2. We'll deliver them soon!"

5. **Ready for Pickup** (stored → ready)
   - "Your order is ready! Let us know when you'd like delivery."

6. **Out for Delivery** (ready → delivered)
   - "We're delivering your items now. You'll receive a confirmation photo shortly."

7. **Delivered** (delivered → completed)
   - "Your order has been delivered! Please rate your experience."

**To Staff:**
1. **New Order** (order created)
   - "New convenience store order #CS-1234 - 3 items - Est. shop time: 15 min"

2. **Order Approaching Deadline** (confirmed/shopping)
   - "Order #CS-1234 approaching estimated ready time in 10 minutes"

3. **Customer Requesting Delivery** (customer action)
   - "Customer requesting delivery for order #CS-1234"

---

## Payment Flow

### Stripe Integration

**Payment Method**: Stripe Payment Intents API

### Payment Lifecycle

```
┌────────────────────────────────────────────────────────────────┐
│                      1. Order Creation                          │
├────────────────────────────────────────────────────────────────┤
│ Customer submits order                                          │
│ Server calculates total amount                                  │
│ Create Stripe PaymentIntent                                     │
│   - amount: $24.94 (in cents: 2494)                            │
│   - currency: 'usd'                                             │
│   - capture_method: 'manual'  ← Important!                     │
│   - metadata: {order_id, venue_id, user_id}                    │
│ Return payment_intent_id to client                              │
│ Client confirms payment (card details)                          │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                      2. Authorization                           │
├────────────────────────────────────────────────────────────────┤
│ Stripe authorizes payment (holds funds on card)                 │
│ Update order:                                                   │
│   - payment_status: 'authorized'                               │
│   - payment_intent_id: 'pi_xxx'                                │
│ Funds held for up to 7 days                                    │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                      3. Shopping Phase                          │
├────────────────────────────────────────────────────────────────┤
│ Staff shops for items                                           │
│ If items cost MORE than estimated:                             │
│   - Update PaymentIntent amount                                │
│   - May require new authorization                              │
│ If items cost LESS than estimated:                             │
│   - Update PaymentIntent amount (downward adjustment OK)       │
│ If items unavailable:                                           │
│   - Adjust PaymentIntent amount accordingly                    │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                      4. Delivery & Capture                      │
├────────────────────────────────────────────────────────────────┤
│ Staff delivers items to customer                                │
│ Capture payment:                                                │
│   - stripe.PaymentIntent.capture(payment_intent_id)            │
│   - amount_to_capture: actual_amount (in cents)                │
│ Update order:                                                   │
│   - payment_status: 'captured'                                 │
│   - completed_at: now()                                        │
│ Funds transferred to venue's account (minus Stripe fees)       │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                      5. Completion                              │
├────────────────────────────────────────────────────────────────┤
│ Order marked as completed                                       │
│ Customer receives receipt                                       │
│ Funds settle in 2-7 business days                              │
└────────────────────────────────────────────────────────────────┘
```

### Cancellation & Refund Flow

```
┌────────────────────────────────────────────────────────────────┐
│               Cancellation BEFORE Shopping                      │
├────────────────────────────────────────────────────────────────┤
│ Cancel PaymentIntent:                                           │
│   - stripe.PaymentIntent.cancel(payment_intent_id)             │
│   - Authorization released immediately                         │
│   - No charge to customer                                       │
│ Update order:                                                   │
│   - status: 'cancelled'                                        │
│   - payment_status: 'cancelled'                                │
│   - cancellation_reason: 'Customer cancelled'                  │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│               Cancellation AFTER Delivery                       │
├────────────────────────────────────────────────────────────────┤
│ Create Refund:                                                  │
│   - stripe.Refund.create(                                      │
│       payment_intent: payment_intent_id,                       │
│       amount: refund_amount,  # Can be partial                 │
│       reason: 'requested_by_customer'                          │
│     )                                                           │
│ Update order:                                                   │
│   - payment_status: 'refunded'                                 │
│   - refund_amount: amount                                      │
│   - refund_reason: reason                                      │
│ Customer receives refund in 5-10 business days                 │
└────────────────────────────────────────────────────────────────┘
```

### Payment Implementation Example

```python
# Order Creation - Authorize Payment
async def create_order_with_payment(
    db: Session,
    order_data: OrderCreate,
    user: User
) -> ConvenienceOrder:
    # Calculate order total
    order_total = calculate_order_total(order_data.items)

    # Create Stripe PaymentIntent
    payment_intent = stripe.PaymentIntent.create(
        amount=int(order_total * 100),  # Convert to cents
        currency='usd',
        capture_method='manual',  # Don't capture immediately
        customer=user.stripe_customer_id,
        metadata={
            'order_type': 'convenience_store',
            'venue_id': str(order_data.venue_id),
            'user_id': str(user.id),
        },
        description=f'Convenience Store Order - {venue.name}'
    )

    # Create order in database
    order = ConvenienceOrder(
        venue_id=order_data.venue_id,
        user_id=user.id,
        status='pending',
        payment_status='authorized',
        payment_intent_id=payment_intent.id,
        total_amount=order_total,
        ...
    )
    db.add(order)
    db.commit()

    return order

# Delivery - Capture Payment
async def capture_order_payment(
    db: Session,
    order: ConvenienceOrder
) -> None:
    # Capture the authorized payment
    payment_intent = stripe.PaymentIntent.capture(
        order.payment_intent_id,
        amount_to_capture=int(order.total_amount * 100)
    )

    # Update order status
    order.payment_status = 'captured'
    order.delivered_at = datetime.utcnow()
    db.commit()

    # Send receipt to customer
    send_receipt_email(order)

# Cancellation - Release or Refund
async def cancel_order_and_refund(
    db: Session,
    order: ConvenienceOrder,
    reason: str
) -> None:
    if order.payment_status == 'authorized':
        # Just cancel the authorization
        stripe.PaymentIntent.cancel(order.payment_intent_id)
        order.payment_status = 'cancelled'
    elif order.payment_status == 'captured':
        # Issue a refund
        refund = stripe.Refund.create(
            payment_intent=order.payment_intent_id,
            amount=int(order.total_amount * 100),
            reason='requested_by_customer'
        )
        order.payment_status = 'refunded'
        order.refund_amount = order.total_amount

    order.status = 'cancelled'
    order.cancellation_reason = reason
    order.cancelled_at = datetime.utcnow()
    db.commit()
```

### Payment Security

1. **PCI Compliance**: Use Stripe Elements for card input (never handle raw card data)
2. **3D Secure**: Enable SCA (Strong Customer Authentication) for EU customers
3. **Fraud Detection**: Leverage Stripe Radar for fraud prevention
4. **Webhook Security**: Verify webhook signatures
5. **Idempotency**: Use idempotency keys to prevent duplicate charges

---

## Business Logic

### Price Calculation

**Formula**:
```
Final Price = Base Price + Markup
Markup = (Markup Amount) + (Base Price × Markup Percent / 100)

Order Subtotal = Σ (Item Final Price × Quantity)
Service Fee = Order Subtotal × Service Fee Percent / 100
Tax = (Order Subtotal + Service Fee) × Tax Rate / 100
Total = Order Subtotal + Service Fee + Tax + Tip
```

**Implementation**:
```python
def calculate_item_final_price(
    base_price: Decimal,
    markup_amount: Decimal = Decimal('0'),
    markup_percent: Decimal = Decimal('0')
) -> Decimal:
    """Calculate final price with markup"""
    markup = markup_amount + (base_price * markup_percent / 100)
    return base_price + markup

def calculate_order_totals(
    items: List[OrderItem],
    service_fee_percent: Decimal,
    tax_rate: Decimal = Decimal('8.0')  # Default 8%
) -> Dict[str, Decimal]:
    """Calculate order totals"""

    # Calculate subtotal
    subtotal = sum(
        item.final_price * item.quantity
        for item in items
    )

    # Calculate service fee
    service_fee = subtotal * service_fee_percent / 100

    # Calculate tax
    taxable_amount = subtotal + service_fee
    tax = taxable_amount * tax_rate / 100

    # Calculate total
    total = subtotal + service_fee + tax

    return {
        'subtotal': subtotal.quantize(Decimal('0.01')),
        'service_fee': service_fee.quantize(Decimal('0.01')),
        'tax': tax.quantize(Decimal('0.01')),
        'total': total.quantize(Decimal('0.01'))
    }
```

### Parking Time Extension

**When**: Order is placed and confirmed

**Logic**:
```python
async def extend_parking_time(
    db: Session,
    order: ConvenienceOrder
) -> None:
    """Extend parking time for convenience order"""

    # Get configuration
    config = get_venue_config(db, order.venue_id)
    minutes_to_add = config.default_complimentary_parking_minutes

    # Find associated parking session
    if order.parking_session_id:
        parking_session = db.query(ParkingSession).filter(
            ParkingSession.id == order.parking_session_id
        ).first()

        if parking_session:
            # Extend end time
            parking_session.end_time += timedelta(minutes=minutes_to_add)

            # Record extension
            order.complimentary_time_added_minutes = minutes_to_add

            db.commit()

            # Notify customer
            send_notification(
                order.user_id,
                f"We've added {minutes_to_add} minutes to your parking session!"
            )
```

### Order Validation

**Pre-Creation Validation**:
```python
def validate_order_creation(
    db: Session,
    order_data: OrderCreate,
    user: User
) -> None:
    """Validate order before creation"""

    # 1. Check venue is enabled
    config = get_venue_config(db, order_data.venue_id)
    if not config.is_enabled:
        raise HTTPException(400, "Convenience store not enabled")

    # 2. Check operating hours
    current_time = datetime.now().time()
    current_day = datetime.now().strftime('%A').lower()

    hours = config.operating_hours.get(current_day)
    if hours:
        if not (hours['open'] <= current_time <= hours['close']):
            raise HTTPException(400, "Store is currently closed")

    # 3. Validate items exist and are active
    for item_data in order_data.items:
        item = db.query(ConvenienceItem).filter(
            ConvenienceItem.id == item_data.item_id,
            ConvenienceItem.venue_id == order_data.venue_id
        ).first()

        if not item:
            raise HTTPException(404, f"Item {item_data.item_id} not found")

        if not item.is_active:
            raise HTTPException(400, f"Item {item.name} is not available")

        if item_data.quantity > item.max_quantity_per_order:
            raise HTTPException(
                400,
                f"Max quantity for {item.name} is {item.max_quantity_per_order}"
            )

    # 4. Calculate and validate order total
    totals = calculate_order_totals(order_data.items)

    if totals['total'] < config.minimum_order_amount:
        raise HTTPException(
            400,
            f"Minimum order amount is ${config.minimum_order_amount}"
        )

    if totals['total'] > config.maximum_order_amount:
        raise HTTPException(
            400,
            f"Maximum order amount is ${config.maximum_order_amount}"
        )

    # 5. Check age verification if needed
    for item_data in order_data.items:
        item = get_item(db, item_data.item_id)
        if item.requires_age_verification:
            if not user.is_age_verified:
                raise HTTPException(
                    400,
                    "Age verification required for some items"
                )
```

### Substitution Handling

**Staff marks item as substituted:**
```python
async def handle_item_substitution(
    db: Session,
    order_item_id: UUID,
    substitution_notes: str,
    actual_price: Decimal
) -> None:
    """Handle item substitution during shopping"""

    # Update order item
    order_item = db.query(ConvenienceOrderItem).filter(
        ConvenienceOrderItem.id == order_item_id
    ).first()

    order_item.status = 'substituted'
    order_item.substitution_notes = substitution_notes
    order_item.actual_price = actual_price

    # Calculate price difference
    price_diff = actual_price - order_item.unit_price

    # Update order total
    order = order_item.order
    order.subtotal += price_diff

    # Recalculate totals
    totals = calculate_order_totals(order)
    order.total_amount = totals['total']

    # Update Stripe PaymentIntent if amount increased significantly
    if price_diff > Decimal('2.00'):
        stripe.PaymentIntent.modify(
            order.payment_intent_id,
            amount=int(order.total_amount * 100)
        )

    db.commit()

    # Notify customer
    send_notification(
        order.user_id,
        f"Item substituted: {order_item.item_name}. {substitution_notes}"
    )
```

---

## Implementation Checklist

### Phase 1: Database & Models (Week 1)

- [ ] Create migration file for all 5 tables
- [ ] Add indexes for performance
- [ ] Create SQLAlchemy models:
  - [ ] ConvenienceStoreConfig
  - [ ] ConvenienceItem
  - [ ] ConvenienceOrder
  - [ ] ConvenienceOrderItem
  - [ ] ConvenienceOrderEvent
- [ ] Add model relationships
- [ ] Create seed data for testing
- [ ] Test migrations up/down

### Phase 2: Core Services (Week 1-2)

- [ ] ItemService
  - [ ] create_item()
  - [ ] update_item()
  - [ ] delete_item()
  - [ ] get_items() with filters
  - [ ] bulk_import_items()
  - [ ] toggle_item_active()
- [ ] ConfigService
  - [ ] get_config()
  - [ ] update_config()
  - [ ] validate_operating_hours()
- [ ] OrderService
  - [ ] create_order()
  - [ ] get_order()
  - [ ] update_order_status()
  - [ ] cancel_order()
  - [ ] calculate_order_totals()
  - [ ] validate_order()
- [ ] Create comprehensive unit tests

### Phase 3: Payment Integration (Week 2)

- [ ] PaymentService
  - [ ] create_payment_intent()
  - [ ] capture_payment()
  - [ ] cancel_payment()
  - [ ] refund_payment()
  - [ ] handle_webhook()
- [ ] Implement payment authorization flow
- [ ] Implement payment capture on delivery
- [ ] Implement refund logic
- [ ] Set up Stripe webhook endpoints
- [ ] Test payment flows (success, failure, refund)

### Phase 4: API Endpoints (Week 2-3)

- [ ] Admin Endpoints
  - [ ] Item management (CRUD)
  - [ ] Bulk import
  - [ ] Configuration management
  - [ ] Order viewing
  - [ ] Refund processing
- [ ] Customer Endpoints
  - [ ] Browse items (public + authenticated)
  - [ ] Get categories
  - [ ] Create order
  - [ ] View orders
  - [ ] Cancel order
  - [ ] Rate order
- [ ] Staff Endpoints
  - [ ] View venue orders
  - [ ] Accept order
  - [ ] Update status
  - [ ] Handle substitutions
  - [ ] Upload photos
- [ ] Add OpenAPI documentation
- [ ] Test all endpoints

### Phase 5: Notifications (Week 3)

- [ ] NotificationService
  - [ ] send_order_confirmation()
  - [ ] send_shopping_started()
  - [ ] send_items_ready()
  - [ ] send_delivery_notification()
  - [ ] send_staff_new_order()
- [ ] Integrate with Twilio (SMS)
- [ ] Integrate with push notifications
- [ ] Create email templates
- [ ] Test notification delivery

### Phase 6: File Upload & Storage (Week 3)

- [ ] Implement S3/CDN integration
- [ ] Receipt photo upload
- [ ] Delivery photo upload
- [ ] Item image upload
- [ ] Image compression/optimization
- [ ] Generate signed URLs for secure access
- [ ] Test file uploads

### Phase 7: Business Logic (Week 3-4)

- [ ] Parking time extension logic
- [ ] Operating hours validation
- [ ] Order minimums/maximums
- [ ] Age verification checks
- [ ] Substitution handling
- [ ] Automatic order completion
- [ ] Test all business rules

### Phase 8: Testing (Week 4)

- [ ] Unit tests (80%+ coverage)
  - [ ] Services
  - [ ] Models
  - [ ] Validators
- [ ] Integration tests
  - [ ] API endpoints
  - [ ] Payment flow
  - [ ] Order lifecycle
- [ ] End-to-end tests
  - [ ] Complete order flow
  - [ ] Cancellation/refund flow
- [ ] Load testing
  - [ ] Concurrent orders
  - [ ] Database performance
- [ ] Security testing
  - [ ] Authentication
  - [ ] Authorization
  - [ ] Input validation

### Phase 9: Admin Dashboard (Week 5)

- [ ] Item management UI
- [ ] Bulk import interface
- [ ] Configuration editor
- [ ] Order management dashboard
- [ ] Analytics/metrics view
- [ ] Staff management

### Phase 10: Documentation (Week 5)

- [x] Lot Owner Setup Guide (COMPLETE)
- [x] Technical Implementation Summary (COMPLETE)
- [ ] API Documentation (auto-generated from OpenAPI)
- [ ] Staff Training Guide
- [ ] Customer FAQ
- [ ] Deployment guide

### Phase 11: Deployment (Week 6)

- [ ] Set up staging environment
- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] Set up monitoring & logging
- [ ] Configure alerts
- [ ] Deploy to production
- [ ] Run production smoke tests
- [ ] Monitor first 24 hours

---

## Security Considerations

### Authentication & Authorization

**Implemented:**
- JWT token-based authentication
- Role-based access control (RBAC)
- Token expiration and refresh
- Venue ownership validation

**To Implement:**
- [ ] Two-factor authentication (2FA) for admin accounts
- [ ] OAuth2 integration (Google, Apple)
- [ ] Session management and concurrent login limits
- [ ] Audit logging for sensitive operations

### Data Protection

**To Implement:**
- [ ] Encrypt sensitive data at rest (PII, payment info)
- [ ] Encrypt data in transit (TLS 1.3+)
- [ ] Implement field-level encryption for sensitive columns
- [ ] Regular security audits
- [ ] GDPR compliance (data export, right to deletion)
- [ ] PCI DSS compliance for payment data

### Input Validation

**To Implement:**
- [ ] Server-side validation for all inputs
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitize outputs)
- [ ] CSRF protection
- [ ] File upload validation (type, size, content)
- [ ] Rate limiting per endpoint

### API Security

**To Implement:**
- [ ] CORS configuration (whitelist origins)
- [ ] Rate limiting (per user, per IP)
- [ ] Request size limits
- [ ] API versioning
- [ ] Webhook signature verification (Stripe)
- [ ] API key management for third-party integrations

### Payment Security

**To Implement:**
- [ ] Never store raw card data
- [ ] Use Stripe Elements for card input
- [ ] Implement 3D Secure (SCA)
- [ ] Fraud detection via Stripe Radar
- [ ] Refund authorization workflow
- [ ] Payment reconciliation

### Privacy

**To Implement:**
- [ ] Privacy policy
- [ ] Terms of service
- [ ] Cookie consent
- [ ] Data retention policy
- [ ] User data export
- [ ] User data deletion (GDPR)

---

## Performance Optimization

### Database Optimization

**Indexes** (from schema):
```sql
-- convenience_items
CREATE INDEX idx_items_venue_active ON convenience_items(venue_id, is_active);
CREATE INDEX idx_items_category ON convenience_items(category);
CREATE INDEX idx_items_source_store ON convenience_items(source_store);

-- convenience_orders
CREATE INDEX idx_orders_venue_status ON convenience_orders(venue_id, status);
CREATE INDEX idx_orders_user ON convenience_orders(user_id);
CREATE INDEX idx_orders_parking_session ON convenience_orders(parking_session_id);
CREATE INDEX idx_orders_number ON convenience_orders(order_number);
CREATE INDEX idx_orders_status ON convenience_orders(status);

-- convenience_order_items
CREATE INDEX idx_order_items_order ON convenience_order_items(order_id);

-- convenience_order_events
CREATE INDEX idx_events_order_created ON convenience_order_events(order_id, created_at);
CREATE INDEX idx_events_status ON convenience_order_events(new_status);
```

**Query Optimization:**
- [ ] Use SELECT only needed columns
- [ ] Implement pagination for large result sets
- [ ] Use eager loading for relationships (joinedload)
- [ ] Cache frequently accessed data (Redis)
- [ ] Use connection pooling
- [ ] Monitor slow queries

### Caching Strategy

**Redis Cache:**
```python
# Cache venue configuration (TTL: 1 hour)
cache_key = f"venue_config:{venue_id}"
config = redis.get(cache_key)
if not config:
    config = db.query(ConvenienceStoreConfig).filter(...).first()
    redis.setex(cache_key, 3600, json.dumps(config))

# Cache active items list (TTL: 15 minutes)
cache_key = f"venue_items:{venue_id}:active"
items = redis.get(cache_key)
if not items:
    items = db.query(ConvenienceItem).filter(...).all()
    redis.setex(cache_key, 900, json.dumps(items))

# Cache order count (TTL: 5 minutes)
cache_key = f"venue_orders_count:{venue_id}:pending"
count = redis.get(cache_key)
if not count:
    count = db.query(ConvenienceOrder).filter(...).count()
    redis.setex(cache_key, 300, count)
```

**Cache Invalidation:**
- Invalidate venue config cache when config is updated
- Invalidate items cache when items are added/updated/deleted
- Invalidate order counts when orders are created/updated

### API Optimization

- [ ] Implement response compression (gzip)
- [ ] Use pagination for list endpoints
- [ ] Implement field filtering (sparse fieldsets)
- [ ] Use CDN for static assets (images)
- [ ] Implement ETag for caching
- [ ] Use HTTP/2 or HTTP/3
- [ ] Optimize JSON serialization

### Background Jobs

**Use Celery for:**
- Sending notifications (don't block API requests)
- Processing bulk imports
- Generating reports
- Cleaning up old data
- Updating metrics

**Example:**
```python
@celery.app.task
def send_order_notification(order_id: str):
    """Send order notification asynchronously"""
    order = db.query(ConvenienceOrder).filter(...).first()
    send_sms(order.user.phone, f"Order {order.order_number} confirmed!")

# Call from API
send_order_notification.delay(str(order.id))
```

### Monitoring & Profiling

- [ ] Application Performance Monitoring (APM)
  - New Relic, DataDog, or Sentry
- [ ] Database query monitoring
  - pg_stat_statements
  - Slow query log
- [ ] API endpoint metrics
  - Response times
  - Error rates
  - Request counts
- [ ] Resource monitoring
  - CPU, memory, disk usage
  - Database connections
  - Redis memory

---

## Testing Strategy

### Unit Tests

**Coverage Target: 80%+**

**Models:**
```python
def test_convenience_item_creation():
    """Test item model creation"""
    item = ConvenienceItem(
        venue_id=venue.id,
        name="Test Item",
        base_price=Decimal('10.00'),
        markup_percent=Decimal('15.00'),
        final_price=Decimal('11.50')
    )
    assert item.final_price == Decimal('11.50')

def test_order_status_transitions():
    """Test valid status transitions"""
    order = ConvenienceOrder(status='pending')
    order.status = 'confirmed'  # Valid
    order.status = 'shopping'   # Valid

    with pytest.raises(ValueError):
        order.status = 'completed'  # Invalid jump
```

**Services:**
```python
def test_calculate_order_totals():
    """Test order total calculation"""
    items = [
        {'price': Decimal('10.00'), 'quantity': 2},
        {'price': Decimal('5.00'), 'quantity': 1}
    ]
    totals = calculate_order_totals(items, service_fee_percent=15)

    assert totals['subtotal'] == Decimal('25.00')
    assert totals['service_fee'] == Decimal('3.75')
    assert totals['total'] > Decimal('25.00')

def test_parking_time_extension():
    """Test parking time is extended correctly"""
    order = create_order(...)
    original_end = parking_session.end_time

    extend_parking_time(order)

    assert parking_session.end_time > original_end
    assert order.complimentary_time_added_minutes == 15
```

### Integration Tests

**API Endpoints:**
```python
def test_create_order_flow(client, auth_token):
    """Test complete order creation flow"""
    # Create order
    response = client.post(
        "/api/v1/convenience/orders",
        json=order_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    order = response.json()

    # Verify payment intent created
    assert order['payment_intent_id'] is not None
    assert order['payment_status'] == 'authorized'

    # Verify order items created
    assert len(order['items']) == 2

def test_staff_order_fulfillment(client, staff_token):
    """Test staff can fulfill orders"""
    order = create_test_order()

    # Accept order
    response = client.patch(
        f"/api/v1/convenience/staff/orders/{order.id}/accept",
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    assert response.status_code == 200
    assert response.json()['status'] == 'confirmed'
```

**Payment Flow:**
```python
def test_payment_authorization():
    """Test payment is authorized correctly"""
    order = create_order(total=Decimal('25.00'))

    # Verify PaymentIntent created
    pi = stripe.PaymentIntent.retrieve(order.payment_intent_id)
    assert pi.amount == 2500  # $25.00 in cents
    assert pi.status == 'requires_capture'

def test_payment_capture_on_delivery():
    """Test payment is captured when delivered"""
    order = create_order_and_deliver()

    # Verify payment captured
    pi = stripe.PaymentIntent.retrieve(order.payment_intent_id)
    assert pi.status == 'succeeded'
    assert order.payment_status == 'captured'

def test_refund_on_cancellation():
    """Test refund is issued on cancellation"""
    order = create_and_cancel_order()

    # Verify refund issued
    refunds = stripe.Refund.list(payment_intent=order.payment_intent_id)
    assert len(refunds.data) == 1
    assert order.payment_status == 'refunded'
```

### End-to-End Tests

**Complete Order Lifecycle:**
```python
@pytest.mark.e2e
def test_complete_order_lifecycle():
    """Test entire order flow from creation to completion"""

    # 1. Customer browses items
    items = browse_items(venue_id)
    assert len(items) > 0

    # 2. Customer creates order
    order = create_order(venue_id, items[:2])
    assert order.status == 'pending'
    assert order.payment_status == 'authorized'

    # 3. Staff accepts order
    accept_order(order.id, staff_token)
    order = get_order(order.id)
    assert order.status == 'confirmed'

    # 4. Staff starts shopping
    start_shopping(order.id, staff_token)
    assert order.status == 'shopping'

    # 5. Staff completes shopping
    complete_shopping(order.id, staff_token, receipt_photo)
    assert order.status == 'purchased'

    # 6. Staff stores items
    store_items(order.id, staff_token, storage_location)
    assert order.status == 'stored'

    # 7. Staff delivers items
    deliver_items(order.id, staff_token, delivery_photo)
    assert order.status == 'delivered'
    assert order.payment_status == 'captured'

    # 8. Customer rates order
    rate_order(order.id, customer_token, rating=5)
    assert order.rating == 5
    assert order.status == 'completed'
```

### Load Testing

**Tools**: Locust, Apache JMeter, or k6

**Scenarios:**
```python
from locust import HttpUser, task, between

class ConvenienceStoreUser(HttpUser):
    wait_time = between(1, 5)

    @task(3)
    def browse_items(self):
        """Browse items (common action)"""
        self.client.get(f"/api/v1/convenience/venues/{venue_id}/items")

    @task(1)
    def create_order(self):
        """Create order (less common)"""
        self.client.post(
            "/api/v1/convenience/orders",
            json=order_data,
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(2)
    def view_my_orders(self):
        """View orders"""
        self.client.get(
            "/api/v1/convenience/my-orders",
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

**Performance Targets:**
- API response time: < 200ms (p95)
- Order creation: < 500ms
- Database queries: < 100ms
- Concurrent users: 1000+
- Orders per minute: 100+

---

## Future Enhancements

### Phase 2 Features (6-12 months)

1. **Repeat Orders & Favorites**
   - Save favorite items
   - Quick reorder previous orders
   - "Reorder last order" button

2. **Scheduled Orders**
   - "Have this ready by 3pm"
   - Pre-order for future parking sessions
   - Recurring orders (daily coffee)

3. **Subscription Items**
   - "Coffee every visit"
   - Auto-order when checking in
   - Subscription management

4. **Store Inventory Integration**
   - Real-time inventory from stores
   - Automatic price updates
   - Out-of-stock notifications

5. **Advanced Search**
   - Full-text search
   - Filters (dietary, allergens)
   - Barcode scanning

6. **Loyalty & Rewards**
   - Points for orders
   - Free item after X orders
   - Referral rewards
   - Tier-based benefits

7. **Bundle Deals**
   - Pre-made bundles (Breakfast, Snack Pack)
   - Bulk discounts
   - Meal deals

8. **Gift Orders**
   - Send items to someone else's car
   - Gift cards
   - Surprise deliveries

9. **Partnerships**
   - Partner with specific stores
   - Exclusive items
   - Sponsored products

10. **Analytics Dashboard**
    - Sales metrics
    - Popular items
    - Peak times
    - Staff performance
    - Customer insights

### Technical Improvements

1. **Mobile Apps**
   - Native iOS app
   - Native Android app
   - Offline mode

2. **Real-time Updates**
   - WebSocket for live order tracking
   - Push notifications
   - Live staff location

3. **AI/ML Features**
   - Personalized recommendations
   - Demand forecasting
   - Dynamic pricing
   - Fraud detection

4. **Advanced Payment**
   - Split payments
   - Buy now, pay later
   - Crypto payments
   - Gift card support

5. **Internationalization**
   - Multi-language support
   - Multi-currency
   - Regional customization

---

## Conclusion

This technical implementation summary provides a comprehensive blueprint for implementing the Convenience Store feature. The architecture is designed to be:

- **Scalable**: Handles growth in venues, orders, and users
- **Secure**: Implements best practices for authentication, authorization, and data protection
- **Performant**: Optimized database queries, caching, and async processing
- **Maintainable**: Clean architecture, comprehensive testing, and documentation
- **Extensible**: Modular design allows for easy addition of new features

### Key Success Factors

1. **Strong Foundation**: Robust database schema and model relationships
2. **Security First**: Authentication, authorization, and data protection from day one
3. **User Experience**: Fast API responses, clear error messages, intuitive workflows
4. **Payment Reliability**: Proper Stripe integration with authorization and capture flow
5. **Testing**: Comprehensive test coverage ensures reliability
6. **Monitoring**: Observability into system performance and issues
7. **Documentation**: Clear guides for developers, staff, and venue owners

### Next Steps

1. Review and approve this technical specification
2. Set up development environment
3. Begin Phase 1 implementation (Database & Models)
4. Regular progress reviews and adjustments
5. Iterate based on feedback and real-world usage

---

**Document Version**: 1.0
**Last Updated**: November 7, 2025
**Author**: TruFan Engineering Team
**Status**: Ready for Implementation
