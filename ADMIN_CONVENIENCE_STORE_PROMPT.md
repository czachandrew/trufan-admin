# Admin Panel - Convenience Store Inventory Management Implementation

## 🎯 Objective

Implement a complete inventory management system for lot owners to add, manage, and track convenience store items that parkers can purchase. This feature allows parking lot owners to monetize their locations by offering on-premise shopping fulfillment services.

---

## 📁 Project Context

**Backend Location:** `/Users/andrewczachowski/Projects/trufan/backend/`
**Your Location:** (wherever the admin application is)
**Backend API:** `http://localhost:8000/api/v1`
**Backend Docs:** `http://localhost:8000/docs` (OpenAPI/Swagger)

**Key Backend Files to Reference:**
- **Models:** `/Users/andrewczachowski/Projects/trufan/backend/app/models/convenience.py`
- **Schemas:** `/Users/andrewczachowski/Projects/trufan/backend/app/schemas/convenience.py`
- **Services:** `/Users/andrewczachowski/Projects/trufan/backend/app/services/convenience_service.py`
- **Admin Endpoints:** `/Users/andrewczachowski/Projects/trufan/backend/app/api/v1/endpoints/convenience_admin.py`
- **Staff Endpoints:** `/Users/andrewczachowski/Projects/trufan/backend/app/api/v1/endpoints/convenience_staff.py`
- **Specification:** `/Users/andrewczachowski/Projects/trufan/CONVENIENCE_STORE_SPEC.md`
- **Setup Guide:** `/Users/andrewczachowski/Projects/trufan/CONVENIENCE_STORE_SETUP_GUIDE.md`
- **Implementation Details:** `/Users/andrewczachowski/Projects/trufan/CONVENIENCE_STORE_IMPLEMENTATION_SUMMARY.md`

---

## 🏗️ Feature Overview

### Business Context
Parking lot owners can offer convenience items (groceries, food, essentials) from nearby stores. Staff shop for and deliver items to parkers' vehicles while they're away. This:
- Increases parking lot revenue (15% service fee default)
- Adds value for customers (saves time)
- Creates upsell opportunities

### User Flow
1. Lot owner configures store (service fees, parking time bonuses)
2. Lot owner adds items from nearby stores (Walgreens, CVS, etc.)
3. Parker orders items via mobile app while parked
4. Staff fulfills order (shops, stores, delivers)
5. Lot owner earns service fee on each order

---

## 🔐 Authentication

All API requests require JWT Bearer token authentication:

```typescript
headers: {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json'
}
```

**Required Permissions:**
- Venue Admin or Super Admin role
- User must be associated with the venue via `VenueStaff` table

---

## 📡 API Endpoints Reference

### Base URL
```
http://localhost:8000/api/v1
```

### 1. Configuration Management

#### Get Store Configuration
```http
GET /convenience/admin/venues/{venue_identifier}/config
```

**Response Example:**
```json
{
  "id": "uuid",
  "venue_id": "uuid",
  "is_enabled": true,
  "default_service_fee_percent": 15.00,
  "minimum_order_amount": 5.00,
  "maximum_order_amount": 200.00,
  "default_complimentary_parking_minutes": 15,
  "average_fulfillment_time_minutes": 30,
  "welcome_message": "Want us to grab a few things for you while you park?",
  "instructions_message": "Our staff will shop and place items in your vehicle.",
  "storage_locations": ["Vehicle Trunk", "Front Desk", "Refrigerator"],
  "operating_hours": {
    "monday": {"open": "08:00", "close": "20:00"},
    "tuesday": {"open": "08:00", "close": "20:00"}
  },
  "created_at": "2025-11-07T10:00:00Z",
  "updated_at": "2025-11-07T10:00:00Z"
}
```

#### Update Store Configuration
```http
PUT /convenience/admin/venues/{venue_identifier}/config
Content-Type: application/json

{
  "is_enabled": true,
  "default_service_fee_percent": 15.00,
  "minimum_order_amount": 5.00,
  "maximum_order_amount": 200.00,
  "default_complimentary_parking_minutes": 15,
  "average_fulfillment_time_minutes": 30,
  "welcome_message": "Want us to grab a few things for you?",
  "instructions_message": "Items will be placed in your trunk.",
  "storage_locations": ["Vehicle Trunk", "Front Desk", "Refrigerator"],
  "operating_hours": {
    "monday": {"open": "08:00", "close": "20:00"}
  }
}
```

---

### 2. Item Management

#### List All Items
```http
GET /convenience/admin/venues/{venue_identifier}/items?page=1&page_size=50&category=grocery&is_active=true&search=milk
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 50)
- `category` (string): Filter by category (grocery, beverage, food, personal_care, electronics, other)
- `is_active` (bool): Filter by active status
- `search` (string): Search in name, description, tags

**Response Example:**
```json
{
  "items": [
    {
      "id": "uuid",
      "venue_id": "uuid",
      "name": "Gallon of Milk",
      "description": "Whole milk, 1 gallon",
      "image_url": "https://example.com/milk.jpg",
      "category": "grocery",
      "base_price": 4.99,
      "markup_amount": 0.00,
      "markup_percent": 10.00,
      "final_price": 5.49,
      "source_store": "Walgreens",
      "source_address": "5280 W Layton Ave, Greenfield, WI",
      "estimated_shopping_time_minutes": 15,
      "is_active": true,
      "requires_age_verification": false,
      "max_quantity_per_order": 10,
      "tags": ["dairy", "refrigerated", "popular"],
      "sku": "MLK-001",
      "barcode": "012345678901",
      "created_at": "2025-11-07T10:00:00Z",
      "updated_at": "2025-11-07T10:00:00Z",
      "created_by_id": "uuid"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 50
}
```

#### Get Single Item
```http
GET /convenience/admin/venues/{venue_identifier}/items/{item_id}
```

#### Create Item
```http
POST /convenience/admin/venues/{venue_identifier}/items
Content-Type: application/json

{
  "name": "Gallon of Milk",
  "description": "Whole milk, 1 gallon",
  "image_url": "https://example.com/milk.jpg",
  "category": "grocery",
  "base_price": 4.99,
  "markup_amount": 0.00,
  "markup_percent": 10.00,
  "source_store": "Walgreens",
  "source_address": "5280 W Layton Ave, Greenfield, WI",
  "estimated_shopping_time_minutes": 15,
  "is_active": true,
  "requires_age_verification": false,
  "max_quantity_per_order": 10,
  "tags": ["dairy", "refrigerated", "popular"],
  "sku": "MLK-001",
  "barcode": "012345678901"
}
```

**Note:** `final_price` is automatically calculated as:
```
final_price = base_price + markup_amount + (base_price * markup_percent / 100)
```

#### Update Item
```http
PUT /convenience/admin/venues/{venue_identifier}/items/{item_id}
Content-Type: application/json

{
  "name": "Gallon of Milk (Updated)",
  "base_price": 5.49,
  "markup_percent": 15.00,
  "is_active": true
}
```

#### Delete Item
```http
DELETE /convenience/admin/venues/{venue_identifier}/items/{item_id}
```

#### Toggle Item Active Status
```http
PATCH /convenience/admin/venues/{venue_identifier}/items/{item_id}/toggle
```

Response: Returns the updated item with toggled `is_active` status.

#### Bulk Import Items
```http
POST /convenience/admin/venues/{venue_identifier}/items/bulk-import
Content-Type: application/json

{
  "items": [
    {
      "name": "Snickers Bar",
      "category": "food",
      "base_price": 1.49,
      "markup_percent": 20.0,
      "source_store": "CVS",
      "is_active": true,
      "tags": ["snack", "chocolate"]
    },
    {
      "name": "Coca-Cola 20oz",
      "category": "beverage",
      "base_price": 2.49,
      "markup_amount": 0.50,
      "source_store": "Walgreens",
      "is_active": true,
      "tags": ["beverage", "soda"]
    }
  ]
}
```

**Response:**
```json
{
  "created": [
    {
      "id": "uuid",
      "name": "Snickers Bar",
      "final_price": 1.79
    }
  ],
  "failed": [],
  "summary": {
    "total": 2,
    "created": 2,
    "failed": 0
  }
}
```

---

### 3. Order Management

#### List Orders
```http
GET /convenience/admin/venues/{venue_identifier}/orders?page=1&page_size=20&status=confirmed&date_from=2025-11-01
```

**Query Parameters:**
- `page` (int): Page number
- `page_size` (int): Orders per page
- `status` (string): Filter by status (pending, confirmed, shopping, purchased, stored, ready, delivered, completed, cancelled, refunded)
- `date_from` (date): Filter orders from date (YYYY-MM-DD)
- `date_to` (date): Filter orders to date

**Response Example:**
```json
{
  "orders": [
    {
      "id": "uuid",
      "order_number": "CS-1234",
      "venue_name": "Greenfield Plaza",
      "status": "confirmed",
      "total_amount": 16.64,
      "item_count": 3,
      "estimated_ready_time": "2025-11-07T14:30:00Z",
      "created_at": "2025-11-07T13:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

#### Get Order Details
```http
GET /convenience/admin/venues/{venue_identifier}/orders/{order_id}
```

**Response Example:**
```json
{
  "id": "uuid",
  "order_number": "CS-1234",
  "venue_id": "uuid",
  "venue_name": "Greenfield Plaza",
  "user_id": "uuid",
  "user_name": "John Doe",
  "parking_session_id": "uuid",
  "status": "shopping",
  "subtotal": 14.47,
  "service_fee": 2.17,
  "tax": 0.00,
  "tip_amount": 0.00,
  "total_amount": 16.64,
  "payment_status": "captured",
  "payment_intent_id": "pi_xxx",
  "payment_method": "card",
  "assigned_staff_id": "uuid",
  "assigned_staff_name": "Mike Johnson",
  "storage_location": "Trunk",
  "delivery_instructions": "Red Toyota Camry, spot B14",
  "special_instructions": "No substitutions please",
  "receipt_photo_url": null,
  "delivery_photo_url": null,
  "estimated_ready_time": "2025-11-07T14:30:00Z",
  "confirmed_at": "2025-11-07T13:05:00Z",
  "shopping_started_at": "2025-11-07T13:10:00Z",
  "purchased_at": null,
  "stored_at": null,
  "ready_at": null,
  "delivered_at": null,
  "completed_at": null,
  "cancelled_at": null,
  "complimentary_time_added_minutes": 15,
  "rating": null,
  "feedback": null,
  "cancellation_reason": null,
  "refund_amount": null,
  "refund_reason": null,
  "created_at": "2025-11-07T13:00:00Z",
  "updated_at": "2025-11-07T13:10:00Z",
  "items": [
    {
      "id": "uuid",
      "order_id": "uuid",
      "item_id": "uuid",
      "item_name": "Gallon of Milk",
      "item_description": "Whole milk, 1 gallon",
      "item_image_url": "https://example.com/milk.jpg",
      "source_store": "Walgreens",
      "quantity": 1,
      "unit_price": 5.49,
      "line_total": 5.49,
      "status": "pending",
      "substitution_notes": null,
      "actual_price": null,
      "created_at": "2025-11-07T13:00:00Z"
    }
  ],
  "events": [
    {
      "id": "uuid",
      "order_id": "uuid",
      "status": "confirmed",
      "notes": "Order accepted by staff",
      "photo_url": null,
      "location": null,
      "created_by_id": "uuid",
      "created_by_name": "Mike Johnson",
      "created_at": "2025-11-07T13:05:00Z"
    }
  ]
}
```

#### Refund Order
```http
PATCH /convenience/admin/venues/{venue_identifier}/orders/{order_id}/refund
Content-Type: application/json

{
  "refund_amount": 16.64,
  "refund_reason": "Items unavailable at store"
}
```

---

### 4. Analytics/Categories

#### Get Categories
```http
GET /convenience/admin/categories
```

**Response:**
```json
{
  "categories": [
    {
      "value": "grocery",
      "label": "Grocery",
      "icon": "🛒"
    },
    {
      "value": "beverage",
      "label": "Beverage",
      "icon": "🥤"
    },
    {
      "value": "food",
      "label": "Food",
      "icon": "🍔"
    },
    {
      "value": "personal_care",
      "label": "Personal Care",
      "icon": "🧴"
    },
    {
      "value": "electronics",
      "label": "Electronics",
      "icon": "🔌"
    },
    {
      "value": "other",
      "label": "Other",
      "icon": "📦"
    }
  ]
}
```

---

## 🎨 UI Components to Build

### Required Pages/Views

#### 1. **Store Configuration Page**
**Route:** `/venues/:venueId/convenience/settings`

**Components:**
- Toggle to enable/disable feature
- Service fee percentage slider (0-50%)
- Minimum/maximum order amount inputs
- Complimentary parking time input (minutes)
- Average fulfillment time input
- Welcome message textarea
- Instructions message textarea
- Storage locations multi-input (add/remove)
- Operating hours editor (per day of week)
- Save button

**Example Layout:**
```
┌─────────────────────────────────────────┐
│ Convenience Store Settings              │
├─────────────────────────────────────────┤
│ ☑ Enable Convenience Store              │
│                                         │
│ Service Fee: [15]% ─────────────────○  │
│                                         │
│ Order Limits:                           │
│   Minimum: $[5.00]                      │
│   Maximum: $[200.00]                    │
│                                         │
│ Complimentary Parking: [15] minutes    │
│                                         │
│ Welcome Message:                        │
│ ┌─────────────────────────────────────┐│
│ │ Want us to grab a few things for   ││
│ │ you while you park?                 ││
│ └─────────────────────────────────────┘│
│                                         │
│ [Save Changes]                          │
└─────────────────────────────────────────┘
```

#### 2. **Inventory Management Page**
**Route:** `/venues/:venueId/convenience/inventory`

**Components:**
- Data table with items
- Search/filter bar (by category, active status, source store)
- "Add Item" button → opens modal
- "Bulk Import" button → opens modal
- Action buttons per row: Edit, Delete, Toggle Active
- Pagination controls

**Table Columns:**
- Image (thumbnail)
- Name
- Category (badge)
- Base Price
- Markup (% or $)
- Final Price (bold)
- Source Store
- Status (Active/Inactive badge)
- Actions (Edit, Delete, Toggle)

**Example Layout:**
```
┌────────────────────────────────────────────────────────────────────┐
│ Inventory Management                    [+ Add Item] [↑ Bulk Import]│
├────────────────────────────────────────────────────────────────────┤
│ Search: [________] Category: [All ▾] Store: [All ▾] [🔍 Search]   │
├────────────────────────────────────────────────────────────────────┤
│ Image │ Name          │ Category │ Base │ Markup │ Final │ Status │
├────────────────────────────────────────────────────────────────────┤
│ [🥛] │ Gallon Milk   │ Grocery  │$4.99 │ 10%   │$5.49 │ Active  │
│ [🍞] │ Loaf Bread    │ Grocery  │$3.49 │ 10%   │$3.84 │ Active  │
│ [💧] │ Water 6-pack  │ Beverage │$5.99 │ $1.00 │$6.99 │ Inactive│
└────────────────────────────────────────────────────────────────────┘
```

#### 3. **Add/Edit Item Modal**

**Form Fields:**
- Item Name* (text input)
- Description (textarea)
- Category* (dropdown: grocery, beverage, food, personal_care, electronics, other)
- Image URL (text input with preview)
- Base Price* (currency input)
- Markup Type (radio: Percentage / Fixed Amount)
  - If Percentage: Markup % (number input 0-100)
  - If Fixed: Markup $ (currency input)
- Final Price (calculated, read-only, displayed prominently)
- Source Store* (text input with autocomplete for common stores)
- Source Address (text input)
- Estimated Shopping Time (number input, minutes)
- Max Quantity Per Order (number input, default 10)
- Tags (multi-input chips)
- SKU (text input)
- Barcode (text input)
- Active Status (toggle)
- Requires Age Verification (checkbox)

**Calculation Display:**
```
Base Price:    $4.99
Markup (10%):  +$0.50
─────────────────────
Final Price:   $5.49
```

#### 4. **Bulk Import Modal**

**Components:**
- CSV template download link
- File upload dropzone
- Or: Manual entry form (array of items)
- Preview table before import
- Import button
- Results display (success count, errors)

**CSV Template:**
```csv
name,description,category,base_price,markup_percent,markup_amount,source_store,source_address,tags,sku,barcode,is_active
Gallon of Milk,Whole milk 1 gallon,grocery,4.99,10.0,0,Walgreens,5280 W Layton Ave,"dairy,refrigerated",MLK-001,012345678901,true
Loaf of Bread,White bread 20oz,grocery,3.49,10.0,0,Walgreens,,"bakery,popular",BRD-001,,true
```

#### 5. **Orders Dashboard**
**Route:** `/venues/:venueId/convenience/orders`

**Components:**
- Order status filter tabs (All, Pending, Active, Completed, Cancelled)
- Date range picker
- Orders list/table
- Click order → view order details modal
- Refund button (for completed orders)

**Order Card Example:**
```
┌─────────────────────────────────────────┐
│ CS-1234    Shopping    $16.64           │
│ John Doe · 3 items · 2 min ago         │
│ Staff: Mike Johnson                     │
│ [View Details]                          │
└─────────────────────────────────────────┘
```

#### 6. **Order Details Modal**

**Sections:**
- Order info (number, status, created time)
- Customer info (name, parking spot, phone)
- Items list (with quantities, prices)
- Pricing breakdown (subtotal, service fee, tax, tip, total)
- Payment status
- Fulfillment timeline (with event history)
- Staff assignment
- Storage location
- Photos (receipt, delivery)
- Action buttons (based on status):
  - If completed: "Issue Refund"
  - If cancelled: "Issue Partial Refund"

---

## 🛠️ Development Strategy

### Use Agent Deployment Efficiently

**Deploy 3-4 Parallel Agents:**

1. **Agent 1: API Service Layer**
   - Create TypeScript API client
   - All API endpoint functions with proper types
   - Error handling and response types
   - Authentication token injection

2. **Agent 2: Configuration & Settings UI**
   - Store configuration page
   - Form components
   - API integration for config CRUD
   - Form validation

3. **Agent 3: Inventory Management UI**
   - Inventory list/table component
   - Add/Edit item modal
   - Bulk import modal
   - API integration for item CRUD
   - Search/filter logic

4. **Agent 4: Orders Dashboard UI**
   - Orders list component
   - Order details modal
   - Refund functionality
   - Status filtering
   - API integration for orders

**Each agent should:**
- Read the backend code to understand data structures
- Use TypeScript for type safety
- Follow existing admin panel patterns
- Handle errors gracefully with user-friendly messages
- Add loading states
- Validate forms on client side
- Show success/error toasts
- Use existing UI component library

---

## 📚 Backend Code References

### To Understand Data Models:
Read `/Users/andrewczachowski/Projects/trufan/backend/app/models/convenience.py`:
- Line 10-30: Enums (categories, statuses)
- Line 32-90: ConvenienceItem model
- Line 92-190: ConvenienceOrder model
- Line 192-220: ConvenienceOrderItem model
- Line 260-290: ConvenienceStoreConfig model

### To Understand API Contracts:
Read `/Users/andrewczachowski/Projects/trufan/backend/app/schemas/convenience.py`:
- Item schemas (lines 50-120)
- Order schemas (lines 160-280)
- Config schemas (lines 340-370)

### To Understand Business Logic:
Read `/Users/andrewczachowski/Projects/trufan/backend/app/services/convenience_service.py`:
- Pricing calculation (line 130-150)
- Order creation flow (line 200-280)
- Status transitions (line 350-400)

### To See API Implementation:
Read `/Users/andrewczachowski/Projects/trufan/backend/app/api/v1/endpoints/convenience_admin.py`:
- All endpoint handlers
- Permission checks
- Request/response patterns

---

## 🎯 TypeScript Type Definitions

Generate these from backend schemas:

```typescript
// Enums
export enum ConvenienceItemCategory {
  GROCERY = 'grocery',
  BEVERAGE = 'beverage',
  FOOD = 'food',
  PERSONAL_CARE = 'personal_care',
  ELECTRONICS = 'electronics',
  OTHER = 'other'
}

export enum ConvenienceOrderStatus {
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  SHOPPING = 'shopping',
  PURCHASED = 'purchased',
  STORED = 'stored',
  READY = 'ready',
  DELIVERED = 'delivered',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  REFUNDED = 'refunded'
}

// Item Types
export interface ConvenienceItem {
  id: string;
  venue_id: string;
  name: string;
  description?: string;
  image_url?: string;
  category: ConvenienceItemCategory;
  base_price: number;
  markup_amount: number;
  markup_percent: number;
  final_price: number;
  source_store: string;
  source_address?: string;
  estimated_shopping_time_minutes: number;
  is_active: boolean;
  requires_age_verification: boolean;
  max_quantity_per_order: number;
  tags?: string[];
  sku?: string;
  barcode?: string;
  created_at: string;
  updated_at: string;
  created_by_id?: string;
}

export interface ConvenienceItemCreate {
  name: string;
  description?: string;
  image_url?: string;
  category: ConvenienceItemCategory;
  base_price: number;
  markup_amount?: number;
  markup_percent?: number;
  source_store: string;
  source_address?: string;
  estimated_shopping_time_minutes?: number;
  is_active?: boolean;
  requires_age_verification?: boolean;
  max_quantity_per_order?: number;
  tags?: string[];
  sku?: string;
  barcode?: string;
}

// Order Types
export interface ConvenienceOrder {
  id: string;
  order_number: string;
  venue_id: string;
  venue_name?: string;
  user_id: string;
  user_name?: string;
  parking_session_id?: string;
  status: ConvenienceOrderStatus;
  subtotal: number;
  service_fee: number;
  tax: number;
  tip_amount: number;
  total_amount: number;
  payment_status: string;
  payment_intent_id?: string;
  payment_method?: string;
  assigned_staff_id?: string;
  assigned_staff_name?: string;
  storage_location?: string;
  delivery_instructions?: string;
  special_instructions?: string;
  receipt_photo_url?: string;
  delivery_photo_url?: string;
  estimated_ready_time?: string;
  confirmed_at?: string;
  shopping_started_at?: string;
  purchased_at?: string;
  stored_at?: string;
  ready_at?: string;
  delivered_at?: string;
  completed_at?: string;
  cancelled_at?: string;
  complimentary_time_added_minutes: number;
  rating?: number;
  feedback?: string;
  cancellation_reason?: string;
  refund_amount?: number;
  refund_reason?: string;
  created_at: string;
  updated_at: string;
  items: ConvenienceOrderItem[];
  events: ConvenienceOrderEvent[];
}

export interface ConvenienceOrderItem {
  id: string;
  order_id: string;
  item_id?: string;
  item_name: string;
  item_description?: string;
  item_image_url?: string;
  source_store: string;
  quantity: number;
  unit_price: number;
  line_total: number;
  status: string;
  substitution_notes?: string;
  actual_price?: number;
  created_at: string;
}

export interface ConvenienceOrderEvent {
  id: string;
  order_id: string;
  status: string;
  notes?: string;
  photo_url?: string;
  location?: string;
  created_by_id?: string;
  created_by_name?: string;
  created_at: string;
}

// Config Types
export interface ConvenienceStoreConfig {
  id: string;
  venue_id: string;
  is_enabled: boolean;
  default_service_fee_percent: number;
  minimum_order_amount: number;
  maximum_order_amount: number;
  default_complimentary_parking_minutes: number;
  average_fulfillment_time_minutes: number;
  welcome_message: string;
  instructions_message?: string;
  storage_locations: string[];
  operating_hours?: Record<string, { open: string; close: string }>;
  created_at: string;
  updated_at: string;
}

// API Response Types
export interface ItemListResponse {
  items: ConvenienceItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface OrderListResponse {
  orders: ConvenienceOrderSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface ConvenienceOrderSummary {
  id: string;
  order_number: string;
  venue_name?: string;
  status: ConvenienceOrderStatus;
  total_amount: number;
  item_count: number;
  estimated_ready_time?: string;
  created_at: string;
}

export interface BulkImportResult {
  created: Array<{ id: string; name: string; final_price: number }>;
  failed: Array<{ item: any; error: string }>;
  summary: {
    total: number;
    created: number;
    failed: number;
  };
}
```

---

## 🔥 API Service Example

```typescript
// services/convenienceApi.ts
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

export class ConvenienceApiService {
  private getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  // Configuration
  async getConfig(venueId: string): Promise<ConvenienceStoreConfig> {
    const response = await axios.get(
      `${API_BASE}/convenience/admin/venues/${venueId}/config`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async updateConfig(venueId: string, config: Partial<ConvenienceStoreConfig>): Promise<ConvenienceStoreConfig> {
    const response = await axios.put(
      `${API_BASE}/convenience/admin/venues/${venueId}/config`,
      config,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  // Items
  async listItems(
    venueId: string,
    params?: {
      page?: number;
      page_size?: number;
      category?: string;
      is_active?: boolean;
      search?: string;
    }
  ): Promise<ItemListResponse> {
    const response = await axios.get(
      `${API_BASE}/convenience/admin/venues/${venueId}/items`,
      {
        headers: this.getAuthHeaders(),
        params
      }
    );
    return response.data;
  }

  async getItem(venueId: string, itemId: string): Promise<ConvenienceItem> {
    const response = await axios.get(
      `${API_BASE}/convenience/admin/venues/${venueId}/items/${itemId}`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async createItem(venueId: string, item: ConvenienceItemCreate): Promise<ConvenienceItem> {
    const response = await axios.post(
      `${API_BASE}/convenience/admin/venues/${venueId}/items`,
      item,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async updateItem(
    venueId: string,
    itemId: string,
    updates: Partial<ConvenienceItemCreate>
  ): Promise<ConvenienceItem> {
    const response = await axios.put(
      `${API_BASE}/convenience/admin/venues/${venueId}/items/${itemId}`,
      updates,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async deleteItem(venueId: string, itemId: string): Promise<void> {
    await axios.delete(
      `${API_BASE}/convenience/admin/venues/${venueId}/items/${itemId}`,
      { headers: this.getAuthHeaders() }
    );
  }

  async toggleItemActive(venueId: string, itemId: string): Promise<ConvenienceItem> {
    const response = await axios.patch(
      `${API_BASE}/convenience/admin/venues/${venueId}/items/${itemId}/toggle`,
      {},
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async bulkImportItems(
    venueId: string,
    items: ConvenienceItemCreate[]
  ): Promise<BulkImportResult> {
    const response = await axios.post(
      `${API_BASE}/convenience/admin/venues/${venueId}/items/bulk-import`,
      { items },
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  // Orders
  async listOrders(
    venueId: string,
    params?: {
      page?: number;
      page_size?: number;
      status?: string;
      date_from?: string;
      date_to?: string;
    }
  ): Promise<OrderListResponse> {
    const response = await axios.get(
      `${API_BASE}/convenience/admin/venues/${venueId}/orders`,
      {
        headers: this.getAuthHeaders(),
        params
      }
    );
    return response.data;
  }

  async getOrder(venueId: string, orderId: string): Promise<ConvenienceOrder> {
    const response = await axios.get(
      `${API_BASE}/convenience/admin/venues/${venueId}/orders/${orderId}`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  async refundOrder(
    venueId: string,
    orderId: string,
    refundAmount?: number,
    refundReason?: string
  ): Promise<ConvenienceOrder> {
    const response = await axios.patch(
      `${API_BASE}/convenience/admin/venues/${venueId}/orders/${orderId}/refund`,
      {
        refund_amount: refundAmount,
        refund_reason: refundReason
      },
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }

  // Categories
  async getCategories(): Promise<{ categories: Array<{ value: string; label: string; icon: string }> }> {
    const response = await axios.get(
      `${API_BASE}/convenience/admin/categories`,
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }
}

export const convenienceApi = new ConvenienceApiService();
```

---

## ⚠️ Error Handling Pattern

```typescript
// utils/apiErrorHandler.ts
import { AxiosError } from 'axios';
import { toast } from 'your-toast-library';

export function handleApiError(error: unknown, customMessage?: string) {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{
      error: {
        code: number;
        message: string;
        details?: any;
        correlation_id?: string;
      }
    }>;

    const errorData = axiosError.response?.data?.error;
    const statusCode = axiosError.response?.status;

    if (statusCode === 401) {
      toast.error('Session expired. Please log in again.');
      // Redirect to login
      window.location.href = '/login';
      return;
    }

    if (statusCode === 403) {
      toast.error('You do not have permission to perform this action.');
      return;
    }

    if (statusCode === 404) {
      toast.error('Resource not found.');
      return;
    }

    if (statusCode === 422 && errorData?.details) {
      // Validation errors
      const validationErrors = errorData.details as Array<{
        loc: string[];
        msg: string;
      }>;
      const errorMessages = validationErrors.map(e => `${e.loc.join('.')}: ${e.msg}`);
      toast.error(`Validation Error:\n${errorMessages.join('\n')}`);
      return;
    }

    if (errorData?.message) {
      toast.error(customMessage || errorData.message);
      return;
    }
  }

  toast.error(customMessage || 'An unexpected error occurred. Please try again.');
  console.error('API Error:', error);
}

// Usage in components
try {
  await convenienceApi.createItem(venueId, itemData);
  toast.success('Item created successfully!');
} catch (error) {
  handleApiError(error, 'Failed to create item');
}
```

---

## ✅ Testing Strategy

### Manual Testing Checklist

**Configuration:**
- [ ] Enable/disable store
- [ ] Update service fee percentage
- [ ] Set min/max order amounts
- [ ] Configure operating hours
- [ ] Add/remove storage locations

**Items:**
- [ ] Create item with percentage markup
- [ ] Create item with fixed markup
- [ ] Edit item
- [ ] Delete item
- [ ] Toggle item active/inactive
- [ ] Search items
- [ ] Filter by category
- [ ] Bulk import CSV

**Orders:**
- [ ] View order list
- [ ] Filter orders by status
- [ ] View order details
- [ ] Refund completed order

**Error Cases:**
- [ ] Try to create item without required fields
- [ ] Try to set negative prices
- [ ] Try to access without authentication
- [ ] Try to access venue you don't own

---

## 🚀 Implementation Steps

### Phase 1: Foundation (Agent 1)
1. Create API service class with all endpoints
2. Define TypeScript types
3. Create error handling utility
4. Test API connection

### Phase 2: Configuration (Agent 2)
1. Create configuration page
2. Form for all config fields
3. API integration
4. Validation and error handling
5. Success feedback

### Phase 3: Inventory (Agent 3)
1. Create inventory list page
2. Item table/grid component
3. Add/Edit item modal
4. Bulk import modal
5. Search and filtering
6. API integration
7. Loading and error states

### Phase 4: Orders (Agent 4)
1. Create orders list page
2. Order cards/table
3. Order details modal
4. Status filtering
5. Date range filtering
6. Refund functionality
7. API integration

### Phase 5: Polish
1. Add breadcrumbs
2. Add help text/tooltips
3. Add empty states
4. Responsive design
5. Loading skeletons
6. Form validations
7. Confirmation dialogs

---

## 📖 Additional Resources

- **Backend API Docs:** http://localhost:8000/docs
- **Specification:** `/Users/andrewczachowski/Projects/trufan/CONVENIENCE_STORE_SPEC.md`
- **Setup Guide:** `/Users/andrewczachowski/Projects/trufan/CONVENIENCE_STORE_SETUP_GUIDE.md`
- **Implementation Details:** `/Users/andrewczachowski/Projects/trufan/CONVENIENCE_STORE_IMPLEMENTATION_SUMMARY.md`

---

## 💡 Pro Tips

1. **Use Parallel Agents:** Deploy 3-4 agents simultaneously for different features
2. **Read Backend Code:** Understanding the backend helps avoid API contract mismatches
3. **Follow Patterns:** Look at existing admin pages for styling and structure patterns
4. **Type Everything:** Use TypeScript strictly to catch errors at compile time
5. **Handle Errors Well:** Users should never see raw error messages
6. **Show Loading States:** Every async operation should show loading indicators
7. **Validate Early:** Validate forms on client side before API calls
8. **Test Edge Cases:** Empty states, no items, no orders, permission errors
9. **Mobile Responsive:** Ensure all components work on mobile
10. **Accessibility:** Use semantic HTML, ARIA labels, keyboard navigation

---

## 🎯 Success Criteria

Your implementation is successful when:
- ✅ Lot owner can enable/configure convenience store
- ✅ Lot owner can add items (individually and bulk)
- ✅ Items display correctly with images, prices, categories
- ✅ Search and filtering work smoothly
- ✅ Pricing calculations are correct (base + markup = final)
- ✅ Orders display with all relevant information
- ✅ Refund functionality works
- ✅ All API errors are handled gracefully
- ✅ UI is responsive and user-friendly
- ✅ No console errors
- ✅ TypeScript compiles without warnings

---

## 🐛 Known Backend Behaviors

1. **venue_identifier** accepts both UUID and slug (e.g., "venue-001")
2. **final_price** is auto-calculated, don't send it in create/update
3. **Pagination** defaults to page=1, page_size=50
4. **Dates** are in ISO 8601 format (UTC timezone)
5. **Currency** amounts are decimals (not integers in cents)
6. **Status transitions** are validated (can't jump from pending to delivered)
7. **Permissions** are strictly enforced (403 if not venue admin)

---

## 🎉 You've Got This!

This feature will enable lot owners to:
- Increase revenue by 15%+ per order
- Provide exceptional customer value
- Differentiate from competitors
- Build customer loyalty

Use agents efficiently, read the backend code, handle errors gracefully, and build something amazing! 🚀
