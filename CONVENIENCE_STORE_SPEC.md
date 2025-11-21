# On-Premise Convenience Store Feature Specification

## Overview
Allow parking lot owners to offer on-premise purchasing and fulfillment of items from nearby stores. Parkers can order items (groceries, food, essentials) while parked, and staff will shop, store, and deliver items to the parker's vehicle or a designated pickup location.

## Business Model
- **Target Use Case**: Parker is at a haircut, appointment, or event
- **Value Proposition**: Save time by having staff shop for you while you're busy
- **Revenue Model**: Service fee/markup on items, increased parking value
- **Fulfillment**: Staff shops at nearby stores, delivers to vehicle/locker

---

## Database Schema

### 1. `convenience_items`
Items available for purchase at a venue.

```sql
CREATE TABLE convenience_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,

    -- Item details
    name VARCHAR(200) NOT NULL,
    description TEXT,
    image_url TEXT,
    category VARCHAR(50), -- 'grocery', 'food', 'beverage', 'personal_care', 'electronics', 'other'

    -- Pricing
    base_price DECIMAL(10, 2) NOT NULL, -- Cost at store
    markup_amount DECIMAL(10, 2) DEFAULT 0, -- Fixed markup
    markup_percent DECIMAL(5, 2) DEFAULT 0, -- Percentage markup
    final_price DECIMAL(10, 2) NOT NULL, -- What customer pays

    -- Source
    source_store VARCHAR(200) NOT NULL, -- 'Walgreens', 'CVS', 'Local Bodega'
    source_address TEXT,
    estimated_shopping_time_minutes INT DEFAULT 15,

    -- Availability
    is_active BOOLEAN DEFAULT TRUE,
    requires_age_verification BOOLEAN DEFAULT FALSE, -- For alcohol, tobacco
    max_quantity_per_order INT DEFAULT 10,

    -- Metadata
    tags TEXT[], -- ['dairy', 'refrigerated', 'popular']
    sku VARCHAR(100),
    barcode VARCHAR(100),

    -- Time tracking
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by_id UUID REFERENCES users(id) ON DELETE SET NULL,

    INDEX(venue_id, is_active),
    INDEX(category),
    INDEX(source_store)
);
```

### 2. `convenience_orders`
Orders placed by parkers.

```sql
CREATE TABLE convenience_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(20) UNIQUE NOT NULL, -- 'CS-1234'

    -- Relationships
    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parking_session_id UUID REFERENCES valet_sessions(id) ON DELETE SET NULL,

    -- Order details
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    -- Status flow: pending → confirmed → shopping → purchased → stored → ready → delivered → completed
    -- Can also be: cancelled, refunded

    -- Pricing
    subtotal DECIMAL(10, 2) NOT NULL, -- Sum of item prices
    service_fee DECIMAL(10, 2) NOT NULL, -- Lot's fee for service
    tax DECIMAL(10, 2) DEFAULT 0,
    tip_amount DECIMAL(10, 2) DEFAULT 0,
    total_amount DECIMAL(10, 2) NOT NULL,

    -- Payment
    payment_status VARCHAR(30) DEFAULT 'pending', -- pending, authorized, captured, refunded
    payment_intent_id VARCHAR(200), -- Stripe payment intent
    payment_method VARCHAR(50), -- card, apple_pay, google_pay

    -- Fulfillment
    assigned_staff_id UUID REFERENCES users(id) ON DELETE SET NULL,
    storage_location VARCHAR(100), -- 'Trunk', 'Locker 5', 'Front Desk Fridge'
    delivery_instructions TEXT,
    special_instructions TEXT,

    -- Proof
    receipt_photo_url TEXT,
    delivery_photo_url TEXT,

    -- Timing
    estimated_ready_time TIMESTAMP,
    confirmed_at TIMESTAMP,
    shopping_started_at TIMESTAMP,
    purchased_at TIMESTAMP,
    stored_at TIMESTAMP,
    ready_at TIMESTAMP,
    delivered_at TIMESTAMP,
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,

    -- Parking integration
    complimentary_time_added_minutes INT DEFAULT 0,

    -- Rating
    rating INT CHECK (rating >= 1 AND rating <= 5),
    feedback TEXT,

    -- Metadata
    cancellation_reason TEXT,
    refund_amount DECIMAL(10, 2),
    refund_reason TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX(venue_id, status),
    INDEX(user_id),
    INDEX(parking_session_id),
    INDEX(order_number),
    INDEX(status)
);
```

### 3. `convenience_order_items`
Line items in an order.

```sql
CREATE TABLE convenience_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES convenience_orders(id) ON DELETE CASCADE,
    item_id UUID REFERENCES convenience_items(id) ON DELETE SET NULL,

    -- Snapshot of item at time of order (in case item changes/deleted)
    item_name VARCHAR(200) NOT NULL,
    item_description TEXT,
    item_image_url TEXT,
    source_store VARCHAR(200),

    -- Pricing at time of order
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL,
    line_total DECIMAL(10, 2) NOT NULL, -- quantity * unit_price

    -- Fulfillment
    status VARCHAR(30) DEFAULT 'pending', -- pending, found, not_found, substituted, delivered
    substitution_notes TEXT,
    actual_price DECIMAL(10, 2), -- Actual price paid at store

    created_at TIMESTAMP DEFAULT NOW(),

    INDEX(order_id)
);
```

### 4. `convenience_order_events`
Status change history for orders.

```sql
CREATE TABLE convenience_order_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES convenience_orders(id) ON DELETE CASCADE,

    status VARCHAR(30) NOT NULL,
    notes TEXT,
    photo_url TEXT,
    location VARCHAR(100),

    created_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX(order_id, created_at)
);
```

### 5. `convenience_store_config`
Configuration for convenience store feature per venue.

```sql
CREATE TABLE convenience_store_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venue_id UUID NOT NULL UNIQUE REFERENCES venues(id) ON DELETE CASCADE,

    -- Feature toggle
    is_enabled BOOLEAN DEFAULT TRUE,

    -- Pricing
    default_service_fee_percent DECIMAL(5, 2) DEFAULT 15.00,
    minimum_order_amount DECIMAL(10, 2) DEFAULT 5.00,
    maximum_order_amount DECIMAL(10, 2) DEFAULT 200.00,

    -- Timing
    default_complimentary_parking_minutes INT DEFAULT 15,
    average_fulfillment_time_minutes INT DEFAULT 30,

    -- Availability
    operating_hours JSONB, -- {"monday": {"open": "08:00", "close": "20:00"}, ...}

    -- Messaging
    welcome_message TEXT DEFAULT 'Want us to grab a few things for you while you park?',
    instructions_message TEXT,

    -- Storage locations available
    storage_locations TEXT[] DEFAULT ARRAY['Vehicle Trunk', 'Front Desk', 'Refrigerator', 'Locker'],

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints

### For Lot Owners (Venue Management)

#### Item Management
```
GET    /api/v1/convenience/admin/venues/{venue_id}/items
POST   /api/v1/convenience/admin/venues/{venue_id}/items
GET    /api/v1/convenience/admin/venues/{venue_id}/items/{item_id}
PUT    /api/v1/convenience/admin/venues/{venue_id}/items/{item_id}
DELETE /api/v1/convenience/admin/venues/{venue_id}/items/{item_id}
PATCH  /api/v1/convenience/admin/venues/{venue_id}/items/{item_id}/toggle
POST   /api/v1/convenience/admin/venues/{venue_id}/items/bulk-import
```

#### Configuration
```
GET    /api/v1/convenience/admin/venues/{venue_id}/config
PUT    /api/v1/convenience/admin/venues/{venue_id}/config
```

#### Order Management
```
GET    /api/v1/convenience/admin/venues/{venue_id}/orders
GET    /api/v1/convenience/admin/venues/{venue_id}/orders/{order_id}
PATCH  /api/v1/convenience/admin/venues/{venue_id}/orders/{order_id}/refund
```

### For Parkers (Customers)

#### Browse Items
```
GET    /api/v1/convenience/venues/{venue_id}/items
GET    /api/v1/convenience/venues/{venue_id}/items/{item_id}
GET    /api/v1/convenience/venues/{venue_id}/categories
```

#### Order Management
```
POST   /api/v1/convenience/orders
GET    /api/v1/convenience/orders/{order_id}
GET    /api/v1/convenience/my-orders
PATCH  /api/v1/convenience/orders/{order_id}/cancel
POST   /api/v1/convenience/orders/{order_id}/rate
```

### For Staff (Fulfillment)

#### Order Fulfillment
```
GET    /api/v1/convenience/staff/venues/{venue_id}/orders
GET    /api/v1/convenience/staff/orders/{order_id}
PATCH  /api/v1/convenience/staff/orders/{order_id}/accept
PATCH  /api/v1/convenience/staff/orders/{order_id}/start-shopping
PATCH  /api/v1/convenience/staff/orders/{order_id}/complete-shopping
PATCH  /api/v1/convenience/staff/orders/{order_id}/store
PATCH  /api/v1/convenience/staff/orders/{order_id}/deliver
POST   /api/v1/convenience/staff/orders/{order_id}/update-item
POST   /api/v1/convenience/staff/orders/{order_id}/upload-receipt
```

---

## Stripe Payment Flow

1. **Order Creation**: Create Stripe PaymentIntent with amount
2. **Authorization**: Hold funds on customer's card
3. **Shopping**: Staff shops for items
4. **Adjustment**: Update PaymentIntent if actual cost differs
5. **Capture**: Capture payment when order is delivered
6. **Refund**: Issue refund if order cancelled or items unavailable

---

## Order Status Flow

```
pending → confirmed → shopping → purchased → stored → ready → delivered → completed
                ↓                                                    ↓
           cancelled ←───────────────────────────────────────────────┘
```

**Status Definitions:**
- `pending`: Order placed, awaiting staff confirmation
- `confirmed`: Staff accepted order, preparing to shop
- `shopping`: Staff actively shopping at store
- `purchased`: Items purchased, returning to venue
- `stored`: Items stored in designated location
- `ready`: Items ready for pickup/delivery
- `delivered`: Items delivered to customer
- `completed`: Transaction complete, customer satisfied
- `cancelled`: Order cancelled (by customer or staff)
- `refunded`: Payment refunded

---

## Parking Time Extension

When a convenience order is placed:
1. Check `convenience_store_config.default_complimentary_parking_minutes`
2. Automatically extend the associated `parking_session` or `valet_session`
3. Send notification to user about extended time
4. Record extension in `convenience_orders.complimentary_time_added_minutes`

---

## Notifications

### To Customer:
- Order confirmed
- Shopping started
- Items purchased
- Items stored (with location)
- Items ready for pickup
- Items delivered

### To Staff:
- New order received
- Order approaching estimated ready time
- Customer requesting delivery

---

## Implementation Checklist

### Database
- [ ] Create migration for all 5 tables
- [ ] Add indexes for performance
- [ ] Create sample seed data

### Models
- [ ] ConvenienceItem
- [ ] ConvenienceOrder
- [ ] ConvenienceOrderItem
- [ ] ConvenienceOrderEvent
- [ ] ConvenienceStoreConfig

### Services
- [ ] ItemService (CRUD, bulk import)
- [ ] OrderService (create, update status, calculate pricing)
- [ ] PaymentService (Stripe integration)
- [ ] FulfillmentService (staff operations)
- [ ] NotificationService (SMS/push for status updates)

### API Endpoints
- [ ] Admin endpoints (item management, config)
- [ ] Customer endpoints (browse, order)
- [ ] Staff endpoints (fulfillment)

### Business Logic
- [ ] Calculate pricing (base + markup + service fee + tax)
- [ ] Validate order minimums/maximums
- [ ] Check operating hours
- [ ] Extend parking time automatically
- [ ] Handle substitutions
- [ ] Process refunds

### Testing
- [ ] Unit tests for all services
- [ ] Integration tests for payment flow
- [ ] End-to-end order flow test

### Documentation
- [ ] Lot Owner Setup Guide
- [ ] API Documentation
- [ ] Staff Training Guide

---

## Lot Owner Setup Guide (High-Level)

### Step 1: Enable Feature
1. Navigate to venue settings
2. Enable "Convenience Store" feature
3. Configure service fee percentage (default 15%)
4. Set minimum order amount
5. Set complimentary parking time

### Step 2: Add Items
**Required for each item:**
- Item name (e.g., "Gallon of Milk")
- Base price (store price)
- Markup % or fixed amount
- Source store (e.g., "Walgreens across street")
- Category (Grocery, Food, Beverage, etc.)

**Optional:**
- Photo of item
- Description
- Estimated shopping time

**Bulk Import:**
- Upload CSV with items
- Template provided

### Step 3: Configure Storage Locations
- Define where items will be stored
- Examples: "Front desk fridge", "Locker area", "Staff office"
- For valet: "Customer's trunk", "Front seat"

### Step 4: Train Staff
- How to accept orders
- How to shop efficiently
- How to update order status
- How to handle substitutions
- How to deliver to customer

### Step 5: Go Live
- Test with sample order
- Announce to customers
- Monitor first week closely

---

## Revenue Example

**Order:**
- 1x Gallon of Milk: $4.99 (store price)
- 1x Loaf of Bread: $3.49 (store price)
- Subtotal: $8.48

**Lot's Markup:**
- Service fee (15%): $1.27
- **Total to customer**: $9.75

**Lot's Profit**: $1.27 (minus staff time)

**Additional Value:**
- Increased parking appeal
- Customer convenience
- Parking time extension incentive

---

## Future Enhancements

- [ ] Repeat orders / Favorites
- [ ] Scheduled orders (e.g., "Have this ready by 3pm")
- [ ] Subscription items (e.g., "Coffee every visit")
- [ ] Integration with store inventory APIs
- [ ] Real-time price updates
- [ ] Loyalty rewards
- [ ] Bundle deals
- [ ] Gift orders (send to someone else's car)
