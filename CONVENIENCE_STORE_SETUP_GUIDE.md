# Convenience Store Feature - Lot Owner Setup Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Step-by-Step Setup](#step-by-step-setup)
4. [Managing Items](#managing-items)
5. [Order Fulfillment](#order-fulfillment)
6. [Pricing Strategy](#pricing-strategy)
7. [Staff Training](#staff-training)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [Sample Data & Templates](#sample-data--templates)

---

## Introduction

### What is the Convenience Store Feature?

The Convenience Store feature allows your parking lot to offer on-premise shopping services to parked customers. While customers are at appointments, haircuts, or events, your staff can shop for them at nearby stores and deliver items to their vehicles or designated pickup locations.

### Business Benefits

- **Additional Revenue Stream**: 15% average service fee on all orders
- **Increased Customer Satisfaction**: Provide time-saving convenience
- **Competitive Advantage**: Stand out from other parking facilities
- **Parking Time Extension**: Incentivize longer stays with complimentary time
- **Customer Loyalty**: Build relationships through exceptional service

### How It Works

1. **Customer Orders**: Parker browses your catalog and places an order through the app
2. **Payment Hold**: Customer's payment method is authorized (not charged)
3. **Staff Shops**: Your team shops at the designated store
4. **Storage**: Items are stored in refrigerators, lockers, or secure areas
5. **Delivery**: Staff delivers to customer's vehicle or pickup location
6. **Payment Capture**: Final payment is processed upon delivery

---

## Getting Started

### Prerequisites

Before enabling the convenience store feature, ensure you have:

- [ ] Active TruFan venue account
- [ ] Venue Admin or Super Admin role
- [ ] Stripe payment account connected (for payment processing)
- [ ] At least one nearby store for shopping (within 10 minutes)
- [ ] Storage space for items (refrigerator for perishables, secure area for other items)
- [ ] Trained staff member(s) to fulfill orders
- [ ] Vehicle or method to transport items from stores

### Initial Planning

#### 1. Identify Source Stores

List nearby stores where you'll shop for items:
- **Distance**: Within 5-10 minute walk or drive
- **Store Types**: Pharmacies (CVS, Walgreens), grocery stores, convenience stores
- **Operating Hours**: Must overlap with your venue hours
- **Payment**: Ensure staff can easily purchase items

Example stores to consider:
- Walgreens (0.2 miles away)
- CVS Pharmacy (0.3 miles away)
- 7-Eleven (0.5 miles away)
- Local grocery store (0.8 miles away)

#### 2. Plan Storage Locations

Designate secure areas for storing items:
- **Cold Storage**: Mini-fridge or cooler for perishables
- **Dry Storage**: Secure shelf or locker for non-perishables
- **High-Value Storage**: Locked cabinet for electronics or expensive items
- **Customer Pickup Area**: Front desk, valet station, or dedicated counter

Example storage setup:
```
Location 1: Front Desk Refrigerator (cold items)
Location 2: Staff Office Shelf (dry goods)
Location 3: Locker Area, Lockers 1-5 (larger items)
Location 4: Vehicle Trunk (valet delivery)
```

#### 3. Determine Pricing Strategy

Decide on your markup approach:
- **Service Fee Percentage**: 10-20% is typical (15% recommended)
- **Minimum Order**: $5-10 to ensure profitability
- **Maximum Order**: $100-200 to manage risk
- **Complimentary Parking**: 15-30 minutes added to parking time

---

## Step-by-Step Setup

### Step 1: Enable the Feature

**API Request:**
```bash
PUT /api/v1/convenience/admin/venues/{venue_id}/config
Authorization: Bearer {your_access_token}
Content-Type: application/json

{
  "is_enabled": true,
  "default_service_fee_percent": 15.00,
  "minimum_order_amount": 5.00,
  "maximum_order_amount": 200.00,
  "default_complimentary_parking_minutes": 15,
  "average_fulfillment_time_minutes": 30,
  "welcome_message": "Want us to grab a few things for you while you park?",
  "instructions_message": "Our staff will shop for you at nearby stores and deliver items to your vehicle.",
  "storage_locations": [
    "Vehicle Trunk",
    "Front Desk",
    "Refrigerator",
    "Locker 1",
    "Locker 2",
    "Locker 3",
    "Locker 4",
    "Locker 5"
  ],
  "operating_hours": {
    "monday": {"open": "08:00", "close": "20:00"},
    "tuesday": {"open": "08:00", "close": "20:00"},
    "wednesday": {"open": "08:00", "close": "20:00"},
    "thursday": {"open": "08:00", "close": "20:00"},
    "friday": {"open": "08:00", "close": "22:00"},
    "saturday": {"open": "09:00", "close": "22:00"},
    "sunday": {"open": "10:00", "close": "18:00"}
  }
}
```

**Expected Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "venue_id": "venue-uuid",
  "is_enabled": true,
  "default_service_fee_percent": 15.00,
  "minimum_order_amount": 5.00,
  "maximum_order_amount": 200.00,
  "created_at": "2025-11-07T10:00:00Z",
  "updated_at": "2025-11-07T10:00:00Z"
}
```

### Step 2: Add Your First Items

Start with 10-20 popular, high-demand items. You can always add more later.

**Single Item Creation:**
```bash
POST /api/v1/convenience/admin/venues/{venue_id}/items
Authorization: Bearer {your_access_token}
Content-Type: application/json

{
  "name": "Gallon of Milk - 2%",
  "description": "Fresh 2% reduced fat milk, 1 gallon",
  "category": "grocery",
  "base_price": 4.99,
  "markup_percent": 15.00,
  "final_price": 5.74,
  "source_store": "Walgreens (Main St)",
  "source_address": "123 Main St, City, ST 12345",
  "estimated_shopping_time_minutes": 10,
  "is_active": true,
  "requires_age_verification": false,
  "max_quantity_per_order": 2,
  "tags": ["dairy", "refrigerated", "popular"],
  "image_url": "https://your-cdn.com/milk.jpg"
}
```

**Bulk Import (CSV):**
```bash
POST /api/v1/convenience/admin/venues/{venue_id}/items/bulk-import
Authorization: Bearer {your_access_token}
Content-Type: multipart/form-data

file: items.csv
```

### Step 3: Test Your First Order

Before going live, place a test order yourself:

1. Browse items as a customer
2. Add items to cart
3. Place order
4. Have staff fulfill the order
5. Complete delivery
6. Verify payment processing

**Test Order Creation:**
```bash
POST /api/v1/convenience/orders
Authorization: Bearer {customer_access_token}
Content-Type: application/json

{
  "venue_id": "venue-uuid",
  "items": [
    {
      "item_id": "item-uuid-1",
      "quantity": 1
    },
    {
      "item_id": "item-uuid-2",
      "quantity": 2
    }
  ],
  "delivery_instructions": "Please deliver to my vehicle - Blue Honda Accord, license plate ABC123",
  "special_instructions": "Please get the items from the refrigerated section",
  "parking_session_id": "session-uuid"
}
```

### Step 4: Train Your Staff

See [Staff Training](#staff-training) section for comprehensive training materials.

### Step 5: Go Live

1. Announce the feature to customers via email/push notification
2. Create signage at your venue
3. Update your website and app store listings
4. Monitor first week closely
5. Gather feedback and adjust

---

## Managing Items

### Item Categories

Organize items into categories for easy browsing:

| Category | Examples |
|----------|----------|
| `grocery` | Milk, bread, eggs, butter, cheese |
| `food` | Sandwiches, snacks, chips, candy |
| `beverage` | Water, soda, juice, coffee, energy drinks |
| `personal_care` | Toothpaste, deodorant, shampoo, soap |
| `electronics` | Chargers, batteries, headphones |
| `other` | Miscellaneous items |

### Popular Starter Items

Based on successful implementations, these items have high demand:

**Top 20 Starter Items:**

1. Bottled Water (24-pack)
2. Gallon of Milk (2%)
3. Loaf of Bread (whole wheat)
4. Eggs (dozen)
5. Energy Drink (Red Bull, Monster)
6. Coffee (Starbucks bottled)
7. Snack Pack (chips variety)
8. Candy Bars (variety)
9. Gatorade (variety pack)
10. Phone Charger (iPhone/Android)
11. Pain Reliever (Advil/Tylenol)
12. Toothbrush + Toothpaste Kit
13. Deodorant
14. Tissues (travel pack)
15. Hand Sanitizer
16. Batteries (AA/AAA)
17. Granola Bars (box)
18. Peanut Butter
19. Jelly/Jam
20. Cereal (popular brands)

### Pricing Formula

Calculate final price using this formula:

```
Final Price = Base Price + (Base Price × Markup Percent / 100)
```

**Example 1: Percentage Markup**
```
Item: Gallon of Milk
Base Price: $4.99
Markup: 15%
Final Price: $4.99 + ($4.99 × 0.15) = $5.74
```

**Example 2: Fixed Markup**
```
Item: Phone Charger
Base Price: $19.99
Fixed Markup: $5.00
Final Price: $19.99 + $5.00 = $24.99
```

**Example 3: Hybrid Markup**
```
Item: Expensive Item
Base Price: $50.00
Fixed Markup: $3.00
Percentage Markup: 10%
Final Price: $50.00 + $3.00 + ($50.00 × 0.10) = $58.00
```

### Updating Items

**Update Single Item:**
```bash
PUT /api/v1/convenience/admin/venues/{venue_id}/items/{item_id}
Authorization: Bearer {your_access_token}
Content-Type: application/json

{
  "base_price": 5.49,
  "final_price": 6.31,
  "is_active": true
}
```

**Toggle Item Active/Inactive:**
```bash
PATCH /api/v1/convenience/admin/venues/{venue_id}/items/{item_id}/toggle
Authorization: Bearer {your_access_token}
Content-Type: application/json

{
  "is_active": false
}
```

**Delete Item:**
```bash
DELETE /api/v1/convenience/admin/venues/{venue_id}/items/{item_id}
Authorization: Bearer {your_access_token}
```

### Item Best Practices

1. **Keep Prices Updated**: Check store prices weekly and update accordingly
2. **Seasonal Items**: Add seasonal items (sunscreen in summer, hand warmers in winter)
3. **High-Margin Items**: Include items with good profit margins (energy drinks, convenience items)
4. **Clear Photos**: Use high-quality images of items
5. **Accurate Descriptions**: Include brand names, sizes, and variants
6. **Stock Availability**: Mark items inactive if temporarily unavailable
7. **Age-Restricted Items**: Set `requires_age_verification: true` for alcohol/tobacco

---

## Order Fulfillment

### Order Lifecycle

```
pending → confirmed → shopping → purchased → stored → ready → delivered → completed
```

### Staff Workflow

#### 1. Receive Order (Status: pending)

When a new order comes in:

**View Pending Orders:**
```bash
GET /api/v1/convenience/staff/venues/{venue_id}/orders?status=pending
Authorization: Bearer {staff_access_token}
```

**Response:**
```json
{
  "orders": [
    {
      "id": "order-uuid",
      "order_number": "CS-1234",
      "status": "pending",
      "total_amount": 25.99,
      "items_count": 3,
      "customer_name": "John Doe",
      "created_at": "2025-11-07T10:15:00Z",
      "estimated_ready_time": "2025-11-07T10:45:00Z"
    }
  ]
}
```

#### 2. Accept Order (Status: pending → confirmed)

```bash
PATCH /api/v1/convenience/staff/orders/{order_id}/accept
Authorization: Bearer {staff_access_token}
Content-Type: application/json

{
  "notes": "Will shop at Walgreens",
  "estimated_ready_time": "2025-11-07T10:45:00Z"
}
```

#### 3. Start Shopping (Status: confirmed → shopping)

```bash
PATCH /api/v1/convenience/staff/orders/{order_id}/start-shopping
Authorization: Bearer {staff_access_token}
Content-Type: application/json

{
  "notes": "Heading to Walgreens now"
}
```

#### 4. Complete Shopping (Status: shopping → purchased)

After purchasing items at the store:

```bash
PATCH /api/v1/convenience/staff/orders/{order_id}/complete-shopping
Authorization: Bearer {staff_access_token}
Content-Type: application/json

{
  "notes": "All items found and purchased",
  "receipt_photo_url": "https://your-cdn.com/receipts/order-1234.jpg"
}
```

**Upload Receipt Photo:**
```bash
POST /api/v1/convenience/staff/orders/{order_id}/upload-receipt
Authorization: Bearer {staff_access_token}
Content-Type: multipart/form-data

file: receipt.jpg
```

#### 5. Store Items (Status: purchased → stored)

```bash
PATCH /api/v1/convenience/staff/orders/{order_id}/store
Authorization: Bearer {staff_access_token}
Content-Type: application/json

{
  "storage_location": "Refrigerator - Shelf 2",
  "notes": "Milk and eggs stored in fridge"
}
```

#### 6. Deliver to Customer (Status: stored → delivered)

```bash
PATCH /api/v1/convenience/staff/orders/{order_id}/deliver
Authorization: Bearer {staff_access_token}
Content-Type: application/json

{
  "delivery_photo_url": "https://your-cdn.com/delivery/order-1234.jpg",
  "notes": "Delivered to customer's trunk"
}
```

### Handling Substitutions

If an item is unavailable:

```bash
POST /api/v1/convenience/staff/orders/{order_id}/update-item
Authorization: Bearer {staff_access_token}
Content-Type: application/json

{
  "order_item_id": "item-uuid",
  "status": "substituted",
  "substitution_notes": "Original brand unavailable, substituted with store brand",
  "actual_price": 4.49
}
```

**Or mark as not found:**
```json
{
  "order_item_id": "item-uuid",
  "status": "not_found",
  "substitution_notes": "Item out of stock"
}
```

### Handling Cancellations

**Customer Cancellation (before shopping starts):**
```bash
PATCH /api/v1/convenience/orders/{order_id}/cancel
Authorization: Bearer {customer_access_token}
Content-Type: application/json

{
  "reason": "Changed my mind"
}
```

**Staff Cancellation:**
```bash
PATCH /api/v1/convenience/admin/venues/{venue_id}/orders/{order_id}/refund
Authorization: Bearer {admin_access_token}
Content-Type: application/json

{
  "refund_amount": 25.99,
  "refund_reason": "Store closed, unable to fulfill order"
}
```

---

## Pricing Strategy

### Recommended Markup Structure

| Item Type | Base Price | Recommended Markup | Example |
|-----------|------------|-------------------|---------|
| Low-value items | $1-5 | 20-25% | $2 item → $2.40-2.50 |
| Medium-value items | $5-15 | 15-20% | $10 item → $11.50-12.00 |
| High-value items | $15-50 | 10-15% | $30 item → $33.00-34.50 |
| Premium items | $50+ | 10% + fixed fee | $60 item → $66.00-70.00 |

### Service Fee Structure

**Option 1: Percentage Only**
- Service fee: 15% of subtotal
- Simple and transparent
- Scales with order size

**Option 2: Flat Fee + Percentage**
- Base service fee: $3.00
- Plus: 10% of subtotal
- Better for small orders

**Option 3: Tiered Pricing**
- Orders $5-15: 20% service fee
- Orders $15-30: 15% service fee
- Orders $30+: 10% service fee

### Example Order Calculations

**Example 1: Small Order**
```
Items:
- Bottled Water: $5.99 (base) → $6.89 (15% markup)
- Granola Bars: $4.49 (base) → $5.16 (15% markup)

Subtotal: $12.05
Service Fee (15%): $1.81
Tax (8%): $1.11
Total: $14.97

Your Profit: $1.81
```

**Example 2: Medium Order**
```
Items:
- Gallon of Milk: $4.99 → $5.74
- Loaf of Bread: $3.49 → $4.01
- Eggs (dozen): $3.99 → $4.59
- Butter: $4.99 → $5.74

Subtotal: $20.08
Service Fee (15%): $3.01
Tax (8%): $1.85
Total: $24.94

Your Profit: $3.01
```

**Example 3: Large Order**
```
Items:
- Phone Charger: $19.99 → $22.99
- Headphones: $29.99 → $34.49
- Power Bank: $39.99 → $45.99

Subtotal: $103.47
Service Fee (15%): $15.52
Tax (8%): $9.52
Total: $128.51

Your Profit: $15.52
```

### Profitability Analysis

**Average Order Revenue:**
- Average order value: $20-30
- Average service fee: $3-5
- Orders per day: 5-10
- Monthly revenue: $450-1,500

**Cost Considerations:**
- Staff time: ~30 minutes per order
- Transportation: Minimal (nearby stores)
- Storage: One-time setup cost
- Payment processing: 2.9% + $0.30 (Stripe)

**Break-Even Analysis:**
```
Cost per Order:
- Staff time (30 min @ $15/hr): $7.50
- Payment processing (2.9%): $0.60-0.90
- Gas/transport: $0.50
Total Cost: ~$8.60-9.00

Required Service Fee: ~$9-10
Required Order Size: $60-70 @ 15% markup

Recommendation: Focus on orders $20+ for profitability
```

---

## Staff Training

### Training Checklist

Before staff begins fulfilling orders:

- [ ] Review order fulfillment workflow
- [ ] Practice using the staff app/dashboard
- [ ] Understand payment and authorization process
- [ ] Learn storage location system
- [ ] Know how to handle substitutions
- [ ] Understand refund process
- [ ] Practice customer communication
- [ ] Complete mock order from start to finish

### Staff Training Manual

#### Module 1: Understanding the Service

**What is the Convenience Store Feature?**
- Customers order items through the app while parked
- We shop for them at nearby stores
- We store and deliver items to their vehicle
- Provides convenience and saves customers time

**Why It Matters:**
- Additional revenue for the business
- Enhanced customer experience
- Competitive advantage

#### Module 2: Order Fulfillment Process

**Step 1: Receive & Review Order**
1. Check your staff dashboard for new orders
2. Review order details:
   - Items requested
   - Quantities
   - Source store
   - Customer notes
   - Delivery instructions
3. Verify you can fulfill within estimated time

**Step 2: Accept Order**
1. Tap "Accept Order"
2. Add estimated completion time
3. Customer receives notification

**Step 3: Shop for Items**
1. Bring order list and payment method
2. Navigate to designated store
3. Find all items on the list
4. Check for quality and expiration dates
5. Purchase items and keep receipt
6. Take photo of receipt

**Step 4: Handle Substitutions**
- **Item Out of Stock**: Try to find similar alternative
- **Contact Customer**: If possible, ask for approval
- **Document Changes**: Note what was substituted and why
- **Price Adjustments**: Record actual price paid

**Step 5: Store Items**
1. Return to venue
2. Store items in designated location:
   - Cold items → Refrigerator
   - Dry goods → Shelf/locker
   - High-value → Locked cabinet
3. Label with order number if needed
4. Update order status

**Step 6: Deliver to Customer**
1. Contact customer when ready
2. Bring items to designated location:
   - Vehicle (trunk, front seat)
   - Pickup counter
   - Locker
3. Take delivery photo
4. Confirm delivery in system
5. Wish customer a great day

#### Module 3: Using the Staff App

**Logging In:**
```
1. Open staff dashboard
2. Enter credentials
3. Select your venue
```

**Viewing Orders:**
```
1. Tap "Orders" tab
2. Filter by status (pending, in-progress, completed)
3. Tap order to view details
```

**Updating Order Status:**
```
1. Open order
2. Tap status dropdown
3. Select new status
4. Add notes (optional)
5. Tap "Update"
```

**Uploading Photos:**
```
1. Tap "Upload Receipt" or "Upload Delivery Photo"
2. Take photo or select from library
3. Confirm upload
```

#### Module 4: Customer Service

**Communication Tips:**
- Be professional and friendly
- Respond promptly to questions
- Set clear expectations
- Update customers on delays
- Handle complaints gracefully

**Common Customer Questions:**

**Q: How long will it take?**
A: "Most orders are ready within 30-45 minutes. I'll update you with a more specific time once I accept your order."

**Q: What if an item is unavailable?**
A: "I'll look for a similar alternative and contact you for approval if needed. If we can't find a suitable substitute, we'll adjust your order and refund the difference."

**Q: Where will you deliver my items?**
A: "I'll deliver directly to your vehicle trunk [or other location]. I'll text you when I'm on my way."

**Q: Can I change my order?**
A: "Yes, you can modify your order before I start shopping. Once I've started shopping, changes may not be possible."

#### Module 5: Handling Problems

**Issue: Store is closed**
- Contact customer immediately
- Offer alternative store or refund
- Cancel order if necessary

**Issue: Item much more expensive than listed**
- Purchase anyway if difference is minor (<$2)
- Contact customer if difference is significant
- Offer to substitute or remove item

**Issue: Customer not available for delivery**
- Text/call customer
- Store items securely
- Leave note with storage location
- Follow up after 30 minutes

**Issue: Customer wants refund**
- Direct to admin/manager
- Process refund through system
- Document reason

#### Module 6: Safety & Security

**Shopping Safety:**
- Travel during daylight when possible
- Be aware of surroundings
- Keep phone charged
- Inform team when leaving/returning

**Item Security:**
- Never leave items unattended
- Lock storage areas
- Verify customer identity before delivery
- Report suspicious activity

**Payment Security:**
- Use company credit card only
- Keep receipts for all purchases
- Never use personal funds (unless reimbursed)
- Report lost/stolen payment methods immediately

### Staff Performance Metrics

Track these metrics to evaluate staff performance:

- **Average Fulfillment Time**: 20-40 minutes (target: 30 minutes)
- **Order Accuracy**: 95%+ (items found vs. items requested)
- **Customer Rating**: 4.5+ stars average
- **Substitution Rate**: <10% of items
- **On-Time Delivery**: 90%+ delivered within estimated time

---

## Best Practices

### For Lot Owners

1. **Start Small**: Begin with 10-20 popular items, expand based on demand
2. **Monitor Pricing**: Check source store prices weekly, update your prices
3. **Seasonal Adjustments**: Add seasonal items (ice cream in summer, hot cocoa in winter)
4. **Customer Feedback**: Regularly ask customers what items they want
5. **Staff Incentives**: Consider bonuses/tips for high-rated orders
6. **Quality Control**: Randomly audit orders for accuracy and quality
7. **Marketing**: Promote the feature through signage, email, and push notifications
8. **Analytics**: Track most popular items, peak times, average order value

### For Staff

1. **Efficiency**: Plan your shopping route to minimize time
2. **Quality**: Check expiration dates and product quality
3. **Communication**: Keep customers updated on order status
4. **Professionalism**: Represent the business positively
5. **Problem Solving**: Handle issues proactively
6. **Organization**: Keep storage areas clean and organized
7. **Accuracy**: Double-check orders before marking complete

### For Customer Experience

1. **Fast Fulfillment**: Aim for 30-minute turnaround
2. **Clear Photos**: Include high-quality item images in catalog
3. **Accurate Pricing**: Keep prices up-to-date to avoid surprises
4. **Proactive Communication**: Update customers on any delays or issues
5. **Flexible Delivery**: Offer multiple delivery/pickup options
6. **Quality Guarantee**: Stand behind product quality
7. **Easy Cancellation**: Allow cancellations before shopping starts

---

## Troubleshooting

### Common Issues & Solutions

#### Issue 1: No Orders Coming In

**Possible Causes:**
- Feature not enabled properly
- Items not visible/active
- Prices too high
- Customers unaware of feature

**Solutions:**
- Verify feature is enabled: `GET /api/v1/convenience/admin/venues/{venue_id}/config`
- Check item active status: `GET /api/v1/convenience/admin/venues/{venue_id}/items`
- Review pricing against competitors
- Market the feature through email, signage, app notifications

#### Issue 2: High Cancellation Rate

**Possible Causes:**
- Long fulfillment times
- Items frequently unavailable
- Poor communication
- Pricing complaints

**Solutions:**
- Reduce estimated fulfillment time
- Update item availability more frequently
- Send regular status updates to customers
- Review pricing strategy

#### Issue 3: Low Profit Margins

**Possible Causes:**
- Markup too low
- Staff taking too long (high labor cost)
- Small order values

**Solutions:**
- Increase service fee from 10% to 15-20%
- Train staff on efficient shopping routes
- Implement minimum order amount ($10-15)
- Focus marketing on high-margin items

#### Issue 4: Staff Overwhelmed

**Possible Causes:**
- Too many simultaneous orders
- Inefficient processes
- Poor training
- Inadequate staffing

**Solutions:**
- Limit concurrent orders
- Create shopping route maps for nearby stores
- Provide additional training
- Schedule dedicated shopping staff during peak hours

#### Issue 5: Storage Space Issues

**Possible Causes:**
- Insufficient storage capacity
- Items not picked up promptly
- Poor organization

**Solutions:**
- Invest in additional storage (mini-fridges, lockers)
- Set pickup deadlines (4 hours)
- Implement storage location system
- Consolidate orders when possible

#### Issue 6: Payment Processing Errors

**Possible Causes:**
- Insufficient funds on customer card
- Payment authorization expired
- Stripe configuration issue

**Solutions:**
- Verify Stripe account is properly connected
- Ensure payment authorizations before shopping
- Implement payment retry logic
- Contact customer for alternative payment method

### Technical Issues

#### API Error: 401 Unauthorized

**Cause**: Invalid or expired access token

**Solution**:
```bash
# Refresh your access token
POST /api/v1/auth/refresh
Authorization: Bearer {refresh_token}

# Use new access token in subsequent requests
```

#### API Error: 403 Forbidden

**Cause**: Insufficient permissions for the action

**Solution**:
- Verify user has correct role (VENUE_ADMIN or SUPER_ADMIN)
- Check venue ownership/association
- Contact administrator to update permissions

#### API Error: 404 Not Found

**Cause**: Resource (item, order, venue) doesn't exist

**Solution**:
- Verify IDs are correct
- Check if item/order has been deleted
- Ensure venue_id matches your venue

#### API Error: 422 Validation Error

**Cause**: Invalid request data

**Solution**:
- Review request body against API specification
- Check required fields are included
- Verify data types (strings, numbers, booleans)
- Ensure price calculations are correct

---

## Sample Data & Templates

### CSV Template for Bulk Import

Create a file named `convenience_items.csv`:

```csv
name,description,category,base_price,markup_percent,final_price,source_store,source_address,estimated_shopping_time_minutes,requires_age_verification,max_quantity_per_order,tags,image_url
"Gallon of Milk - 2%","Fresh 2% reduced fat milk, 1 gallon",grocery,4.99,15.00,5.74,"Walgreens Main St","123 Main St, City, ST 12345",10,false,2,"dairy,refrigerated,popular",https://example.com/milk.jpg
"Loaf of Bread - Wheat","Whole wheat bread, 20oz loaf",grocery,3.49,15.00,4.01,"Walgreens Main St","123 Main St, City, ST 12345",10,false,3,"bakery,popular",https://example.com/bread.jpg
"Eggs - Large Dozen","Grade A large eggs, 12 count",grocery,3.99,15.00,4.59,"Walgreens Main St","123 Main St, City, ST 12345",10,false,2,"dairy,refrigerated,popular",https://example.com/eggs.jpg
"Bottled Water - 24pk","Purified bottled water, 24 pack",beverage,5.99,15.00,6.89,"CVS Pharmacy","456 Oak Ave, City, ST 12345",15,false,2,"beverage,popular",https://example.com/water.jpg
"Energy Drink - Red Bull","Red Bull energy drink, 12oz can",beverage,2.99,20.00,3.59,"7-Eleven","789 Elm St, City, ST 12345",5,false,6,"beverage,energy,popular",https://example.com/redbull.jpg
"Phone Charger - Lightning","Apple Lightning cable, 6ft",electronics,19.99,15.00,22.99,"CVS Pharmacy","456 Oak Ave, City, ST 12345",10,false,1,"electronics,accessories",https://example.com/charger.jpg
"Pain Reliever - Advil","Advil pain reliever, 24 tablets",personal_care,8.99,15.00,10.34,"Walgreens Main St","123 Main St, City, ST 12345",5,false,2,"health,medicine",https://example.com/advil.jpg
"Toothbrush + Paste Kit","Travel toothbrush and toothpaste set",personal_care,5.99,15.00,6.89,"CVS Pharmacy","456 Oak Ave, City, ST 12345",5,false,2,"personal_care,travel",https://example.com/toothbrush.jpg
"Snack Mix - Variety","Assorted snack mix, 18 pack",food,12.99,15.00,14.94,"7-Eleven","789 Elm St, City, ST 12345",10,false,2,"snacks,variety,popular",https://example.com/snacks.jpg
"Coffee - Starbucks","Starbucks Frappuccino, 4 pack",beverage,7.99,15.00,9.19,"Walgreens Main St","123 Main St, City, ST 12345",5,false,2,"beverage,coffee,refrigerated",https://example.com/coffee.jpg
```

**Upload via API:**
```bash
curl -X POST \
  https://api.trufan.com/api/v1/convenience/admin/venues/{venue_id}/items/bulk-import \
  -H "Authorization: Bearer {your_access_token}" \
  -F "file=@convenience_items.csv"
```

### Sample Configuration

**Complete Venue Configuration:**
```json
{
  "is_enabled": true,
  "default_service_fee_percent": 15.00,
  "minimum_order_amount": 5.00,
  "maximum_order_amount": 200.00,
  "default_complimentary_parking_minutes": 15,
  "average_fulfillment_time_minutes": 30,
  "operating_hours": {
    "monday": {"open": "08:00", "close": "20:00"},
    "tuesday": {"open": "08:00", "close": "20:00"},
    "wednesday": {"open": "08:00", "close": "20:00"},
    "thursday": {"open": "08:00", "close": "20:00"},
    "friday": {"open": "08:00", "close": "22:00"},
    "saturday": {"open": "09:00", "close": "22:00"},
    "sunday": {"open": "10:00", "close": "18:00"}
  },
  "welcome_message": "Want us to grab a few things for you while you park?",
  "instructions_message": "Our staff will shop for you at nearby stores and deliver items to your vehicle or a designated pickup location. Most orders ready in 30 minutes!",
  "storage_locations": [
    "Vehicle Trunk",
    "Front Seat",
    "Front Desk",
    "Refrigerator - Shelf 1",
    "Refrigerator - Shelf 2",
    "Dry Storage - Shelf 1",
    "Dry Storage - Shelf 2",
    "Locker 1",
    "Locker 2",
    "Locker 3",
    "Locker 4",
    "Locker 5",
    "Valet Station"
  ]
}
```

### Sample Order Scenarios

**Scenario 1: Quick Essentials Order**
```json
{
  "customer": "Sarah Johnson",
  "items": [
    {"name": "Bottled Water 24pk", "quantity": 1, "price": 6.89},
    {"name": "Granola Bars", "quantity": 1, "price": 5.74}
  ],
  "subtotal": 12.63,
  "service_fee": 1.89,
  "tax": 1.16,
  "total": 15.68,
  "delivery": "Vehicle Trunk",
  "notes": "Please deliver to blue Honda Accord, space A5"
}
```

**Scenario 2: Grocery Run Order**
```json
{
  "customer": "Mike Chen",
  "items": [
    {"name": "Gallon of Milk", "quantity": 1, "price": 5.74},
    {"name": "Loaf of Bread", "quantity": 1, "price": 4.01},
    {"name": "Eggs - Dozen", "quantity": 1, "price": 4.59},
    {"name": "Butter", "quantity": 1, "price": 5.74}
  ],
  "subtotal": 20.08,
  "service_fee": 3.01,
  "tax": 1.85,
  "total": 24.94,
  "delivery": "Front Desk Pickup",
  "notes": "Will pick up after haircut appointment (around 2pm)"
}
```

**Scenario 3: Emergency Items Order**
```json
{
  "customer": "Emily Davis",
  "items": [
    {"name": "Phone Charger - Lightning", "quantity": 1, "price": 22.99},
    {"name": "Pain Reliever", "quantity": 1, "price": 10.34},
    {"name": "Bottled Water", "quantity": 1, "price": 1.15}
  ],
  "subtotal": 34.48,
  "service_fee": 5.17,
  "tax": 3.17,
  "total": 42.82,
  "delivery": "Valet Station",
  "notes": "Need charger ASAP - phone died"
}
```

---

## Revenue Optimization Tips

### Increasing Order Value

1. **Bundle Deals**: Create pre-made bundles (e.g., "Breakfast Bundle" = milk, bread, eggs)
2. **Suggested Items**: Recommend complementary items during checkout
3. **Popular Items**: Highlight best-sellers prominently
4. **Seasonal Promotions**: Offer limited-time items or discounts
5. **Minimum Order Incentive**: Free delivery or parking time for orders over $25

### Maximizing Profit

1. **High-Margin Items**: Stock items with good profit margins (energy drinks, electronics accessories)
2. **Bulk Purchases**: Buy popular items in bulk from warehouse stores for lower cost
3. **Dynamic Pricing**: Adjust prices during peak times or high demand
4. **Service Tier Options**: Offer express service for higher fee
5. **Partner Discounts**: Negotiate discounts with source stores for volume purchasing

### Improving Efficiency

1. **Batch Orders**: Fulfill multiple orders in single shopping trip
2. **Shopping Routes**: Create optimized routes to nearby stores
3. **Inventory Stocking**: Pre-purchase frequently ordered items
4. **Delivery Zones**: Group deliveries by parking area
5. **Scheduled Shopping**: Set specific shopping times (e.g., hourly)

### Marketing Strategies

1. **First Order Discount**: Offer 10% off first convenience store order
2. **Loyalty Program**: Free item after 5 orders
3. **Parking Bundle**: Discount on parking when ordering convenience items
4. **Referral Program**: $5 credit for referring friends
5. **Social Proof**: Display "100+ orders fulfilled this month" in app

---

## Getting Help

### Support Resources

- **Documentation**: https://docs.trufan.com/convenience-store
- **API Reference**: https://api.trufan.com/docs
- **Support Email**: support@trufan.com
- **Phone Support**: 1-800-TRUFAN-1 (available M-F 9am-5pm EST)

### Feedback

We'd love to hear from you! Share your feedback on:
- Feature requests
- Improvement suggestions
- Bug reports
- Success stories

Email: feedback@trufan.com

---

## Conclusion

The Convenience Store feature is a powerful way to add value to your parking service while generating additional revenue. By following this guide, you'll be able to successfully implement and operate this feature at your venue.

**Key Takeaways:**
- Start small with 10-20 popular items
- Focus on efficient fulfillment (30-minute target)
- Train staff thoroughly before going live
- Monitor pricing and adjust regularly
- Prioritize customer communication and service
- Track metrics and optimize over time

**Success Metrics to Track:**
- Orders per day/week/month
- Average order value
- Customer satisfaction rating (target: 4.5+)
- Fulfillment time (target: 30 minutes)
- Repeat customer rate
- Revenue per month
- Profit margin

Good luck with your convenience store implementation! If you have questions or need assistance, don't hesitate to reach out to our support team.

---

**Version**: 1.0
**Last Updated**: November 7, 2025
**Author**: TruFan Product Team
