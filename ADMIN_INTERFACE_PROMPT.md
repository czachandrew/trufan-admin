# TruFan Parking Management Admin Interface - Complete Implementation Guide

## Project Overview

Build a comprehensive web-based admin interface for TruFan parking facility operators. This interface allows parking lot/structure owners to manage all aspects of their parking operations, from monitoring active sessions to managing opportunities and processing refunds.

**Target Users:** Parking facility owners/operators (lots, structures, garages, valet services, meters)

**Future Scope:** This will expand into a full TruFan management platform, but initially focuses exclusively on parking operations and opportunity management.

---

## Tech Stack

### Frontend Framework
- **Vue 3** (Composition API with `<script setup>`)
- **TypeScript** for type safety
- **Vite** for build tooling

### State Management
- **Pinia** for global state management
- Organized stores by domain (parking, opportunities, auth, etc.)

### Routing
- **Vue Router** for navigation
- Route guards for authentication

### UI Framework
- **Shadcn-vue** (Vue port of shadcn/ui)
  - Tailwind CSS for styling
  - Radix Vue for accessible primitives
  - Customizable component library
- **Alternative:** Vuetify 3 or Naive UI if preferred
- **Icons:** Lucide Vue or Heroicons

### HTTP Client
- **Axios** for API requests
- Interceptors for auth tokens and error handling

### Form Handling
- **VeeValidate** with Zod for validation
- Form components from shadcn-vue

### Data Visualization
- **Chart.js** with vue-chartjs for analytics
- Real-time parking utilization charts

### Date/Time
- **date-fns** or **Day.js** for date manipulation

### Additional Tools
- **Zod** for runtime type validation
- **TanStack Query (Vue Query)** for server state management (optional but recommended)

---

## Architecture Overview

```
src/
├── api/                  # API client and endpoints
│   ├── client.ts        # Axios instance with interceptors
│   ├── parking.ts       # Parking API calls
│   ├── opportunities.ts # Opportunities API calls
│   └── auth.ts          # Authentication API calls
├── assets/              # Static assets
├── components/          # Reusable components
│   ├── ui/             # shadcn-vue components
│   ├── parking/        # Parking-specific components
│   ├── opportunities/  # Opportunity components
│   └── common/         # Shared components
├── composables/         # Vue composables
│   ├── useAuth.ts
│   ├── useParking.ts
│   └── useOpportunities.ts
├── layouts/             # Layout components
│   ├── DashboardLayout.vue
│   └── AuthLayout.vue
├── router/              # Vue Router configuration
│   └── index.ts
├── stores/              # Pinia stores
│   ├── auth.ts
│   ├── parking.ts
│   └── opportunities.ts
├── types/               # TypeScript type definitions
│   ├── parking.ts
│   ├── opportunity.ts
│   └── api.ts
├── utils/               # Utility functions
│   ├── formatters.ts
│   ├── validators.ts
│   └── constants.ts
├── views/               # Page components
│   ├── Dashboard.vue
│   ├── Lots/
│   ├── Sessions/
│   ├── Opportunities/
│   └── Auth/
├── App.vue
└── main.ts
```

---

## API Integration

### Base Configuration

**Base URL:** `https://api.trufan.com/api/v1` (dev: `http://localhost:8000/api/v1`)

**Authentication:** JWT Bearer token
```
Authorization: Bearer {access_token}
```

**Response Format:** All responses use `snake_case`. Configure axios to transform keys:

```typescript
// src/api/client.ts
import axios from 'axios';
import { camelCase, snakeCase } from 'lodash-es';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Transform request data to snake_case
client.interceptors.request.use((config) => {
  if (config.data) {
    config.data = transformKeys(config.data, snakeCase);
  }
  return config;
});

// Transform response data to camelCase
client.interceptors.response.use((response) => {
  if (response.data) {
    response.data = transformKeys(response.data, camelCase);
  }
  return response;
});

// Add auth token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default client;
```

---

## API Endpoints Reference

### Authentication

#### POST /auth/login
```typescript
// Request
{
  email: string;
  password: string;
}

// Response
{
  user: {
    id: string;
    email: string;
    firstName: string;
    lastName: string;
    role: 'admin' | 'operator' | 'customer';
    isActive: boolean;
    emailVerified: boolean;
    createdAt: string;
  };
  accessToken: string;
  refreshToken: string;
  tokenType: 'bearer';
}
```

#### POST /auth/refresh
```typescript
// Request
{
  refreshToken: string;
}

// Response
{
  accessToken: string;
  refreshToken: string;
  tokenType: 'bearer';
}
```

---

### Parking Lots

#### GET /parking/lots
Public endpoint - Returns all available parking lots

```typescript
// Response
Array<{
  id: string;
  venueId: string | null;
  name: string;
  description: string | null;
  locationAddress: string | null;
  totalSpaces: number;
  availableSpaces: number;
  locationLat: string | null;
  locationLng: string | null;
  pricingConfig: {
    baseRate?: number;
    hourlyRate?: number;
    maxDaily?: number;
    dynamicMultiplier?: number;
  };
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}>
```

#### GET /parking/lots/{lotId}
Get specific lot details

#### POST /parking/lots ⚠️ NEEDS IMPLEMENTATION
Create new parking lot (admin only)

```typescript
// Request
{
  name: string;
  description?: string;
  locationAddress?: string;
  totalSpaces: number;
  locationLat?: number;
  locationLng?: number;
  pricingConfig: {
    baseRate: number;
    hourlyRate: number;
    maxDaily?: number;
  };
  venueId?: string;
}
```

#### PUT /parking/lots/{lotId} ⚠️ NEEDS IMPLEMENTATION
Update parking lot

#### DELETE /parking/lots/{lotId} ⚠️ NEEDS IMPLEMENTATION
Deactivate parking lot

---

### Parking Sessions

#### GET /parking/sessions ⚠️ NEEDS IMPLEMENTATION
Get all sessions with filtering

```typescript
// Query Parameters
{
  lotId?: string;
  status?: 'active' | 'completed' | 'cancelled' | 'expired';
  startDate?: string;  // ISO 8601
  endDate?: string;
  vehiclePlate?: string;
  page?: number;
  limit?: number;
}

// Response
{
  sessions: Array<ParkingSession>;
  total: number;
  page: number;
  limit: number;
}
```

#### GET /parking/sessions/{accessCode}
Get session by access code

```typescript
// Response
{
  id: string;
  lotId: string;
  lotName: string;
  spaceNumber: string | null;
  vehiclePlate: string;
  vehicleMake: string | null;
  vehicleModel: string | null;
  vehicleColor: string | null;
  startTime: string;
  expiresAt: string | null;
  endTime: string | null;
  basePrice: string;
  actualPrice: string | null;
  status: 'active' | 'pending_payment' | 'completed' | 'cancelled' | 'expired';
  accessCode: string;
  createdAt: string;
}
```

#### POST /parking/sessions
Create new session (public)

#### POST /parking/sessions/{accessCode}/extend
Extend parking session

```typescript
// Request
{
  accessCode: string;
  additionalHours: number;
}
```

#### POST /parking/sessions/{accessCode}/end
End session early

#### POST /parking/sessions/{sessionId}/refund ⚠️ NEEDS IMPLEMENTATION
Process refund (admin only)

```typescript
// Request
{
  reason: string;
  amount?: number;  // If null, refunds full amount
  notes?: string;
}

// Response
{
  refundId: string;
  amount: number;
  status: 'pending' | 'completed';
  processedAt: string;
}
```

#### POST /parking/sessions/{sessionId}/notes ⚠️ NEEDS IMPLEMENTATION
Add admin note to session

```typescript
// Request
{
  note: string;
  isInternal: boolean;  // If true, not visible to customer
}
```

#### GET /parking/sessions/{sessionId}/history ⚠️ NEEDS IMPLEMENTATION
Get session event history (extensions, payments, notes, status changes)

```typescript
// Response
Array<{
  id: string;
  eventType: 'created' | 'extended' | 'payment' | 'refund' | 'note' | 'status_change';
  description: string;
  metadata: Record<string, any>;
  createdBy: string | null;
  createdAt: string;
}>
```

---

### Parking Spaces

#### GET /parking/lots/{lotId}/spaces ⚠️ NEEDS IMPLEMENTATION
Get all spaces for a lot

```typescript
// Response
Array<{
  id: string;
  lotId: string;
  spaceNumber: string;
  spaceType: 'standard' | 'handicap' | 'ev' | 'valet';
  isOccupied: boolean;
  isActive: boolean;
  currentSession?: {
    id: string;
    vehiclePlate: string;
    expiresAt: string;
  };
  createdAt: string;
  updatedAt: string;
}>
```

#### POST /parking/lots/{lotId}/spaces ⚠️ NEEDS IMPLEMENTATION
Add parking space

```typescript
// Request
{
  spaceNumber: string;
  spaceType: 'standard' | 'handicap' | 'ev' | 'valet';
}
```

#### PUT /parking/spaces/{spaceId} ⚠️ NEEDS IMPLEMENTATION
Update space

#### DELETE /parking/spaces/{spaceId} ⚠️ NEEDS IMPLEMENTATION
Deactivate space

---

### Opportunities (Partner Management)

#### GET /partner/opportunities
List partner's opportunities (requires partner API key or admin auth)

```typescript
// Headers
{
  'X-API-Key': 'partner_api_key' // OR Authorization: Bearer admin_token
}

// Response
Array<{
  id: string;
  partnerId: string;
  title: string;
  valueProposition: string;
  opportunityType: 'experience' | 'convenience' | 'discovery' | 'bundle';
  triggerRules: Record<string, any>;
  valueDetails: Record<string, any>;
  validFrom: string;
  validUntil: string;
  totalCapacity: number | null;
  usedCapacity: number;
  priorityScore: number;
  isActive: boolean;
  isApproved: boolean;
  createdAt: string;
}>
```

#### POST /partner/opportunities
Create new opportunity

```typescript
// Request
{
  title: string;
  valueProposition: string;
  opportunityType: 'experience' | 'convenience' | 'discovery' | 'bundle';
  triggerRules: {
    timeRemainingMin?: number;
    timeRemainingMax?: number;
    daysOfWeek?: string[];
    timeOfDayStart?: string;  // HH:mm format
    timeOfDayEnd?: string;
  };
  valueDetails: {
    discountPercentage?: number;
    discountFixedAmount?: number;
    parkingExtensionMinutes?: number;
    perks?: string[];
  };
  validFrom: string;  // ISO 8601
  validUntil: string;
  totalCapacity?: number;
  priorityScore?: number;
  locationLat: string;
  locationLng: string;
  address: string;
  walkingDistanceMeters?: number;
}
```

#### PUT /partner/opportunities/{opportunityId}
Update opportunity

#### DELETE /partner/opportunities/{opportunityId}
Deactivate opportunity

#### GET /partner/analytics
Get opportunity analytics

```typescript
// Query Parameters
{
  dateStart?: string;  // ISO 8601 date
  dateEnd?: string;
  opportunityId?: string;
}

// Response
{
  period: {
    start: string;
    end: string;
  };
  engagement: {
    uniqueUsers: number;
    impressions: number;
    views: number;
    claims: number;
    redemptions: number;
    redemptionRate: number;
  };
  value: {
    avgTransaction: string;
    totalRevenue: string;
    platformFees: string;
    netRevenue: string;
  };
}
```

#### POST /partner/opportunities/{opportunityId}/validate
Validate claim code

```typescript
// Request
{
  claimCode: string;
}

// Response
{
  valid: boolean;
  user: {
    id: string;
    firstName: string;
    lastName: string;
  };
  opportunity: {
    id: string;
    title: string;
    valueDetails: Record<string, any>;
  };
  claimedAt: string;
}
```

#### POST /partner/opportunities/{opportunityId}/complete
Mark opportunity as redeemed

```typescript
// Query Parameters
{
  claimCode: string;
  transactionAmount?: number;
}

// Status: 204 No Content
```

---

### Analytics & Reports ⚠️ NEEDS IMPLEMENTATION

#### GET /admin/analytics/parking
Parking analytics dashboard data

```typescript
// Query Parameters
{
  lotId?: string;
  startDate?: string;
  endDate?: string;
}

// Response
{
  period: {
    start: string;
    end: string;
  };
  utilization: {
    avgOccupancyRate: number;
    peakOccupancyRate: number;
    peakOccupancyTime: string;
    totalSessions: number;
    avgSessionDuration: number;  // minutes
  };
  revenue: {
    totalRevenue: number;
    avgRevenuePerSession: number;
    refundsProcessed: number;
    refundAmount: number;
  };
  occupancyByHour: Array<{
    hour: number;
    avgOccupancy: number;
  }>;
  occupancyByDay: Array<{
    day: string;
    avgOccupancy: number;
  }>;
}
```

#### GET /admin/analytics/opportunities
Opportunities analytics (admin view across all partners)

---

### Users

#### GET /admin/users ⚠️ NEEDS IMPLEMENTATION
List users with filtering

```typescript
// Query Parameters
{
  search?: string;
  role?: 'admin' | 'operator' | 'customer';
  page?: number;
  limit?: number;
}

// Response
{
  users: Array<User>;
  total: number;
  page: number;
  limit: number;
}
```

#### GET /admin/users/{userId}
Get user details

#### GET /admin/users/{userId}/parking-history
Get user's parking history

```typescript
// Response
Array<{
  id: string;
  lotName: string;
  vehiclePlate: string;
  startTime: string;
  endTime: string | null;
  duration: number;  // minutes
  amount: string;
  status: string;
}>
```

#### GET /admin/users/{userId}/opportunities
Get user's opportunity interactions

---

## Data Models (TypeScript)

### Parking Types

```typescript
// src/types/parking.ts

export interface ParkingLot {
  id: string;
  venueId: string | null;
  name: string;
  description: string | null;
  locationAddress: string | null;
  totalSpaces: number;
  availableSpaces: number;
  locationLat: string | null;
  locationLng: string | null;
  pricingConfig: PricingConfig;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface PricingConfig {
  baseRate?: number;
  hourlyRate?: number;
  maxDaily?: number;
  dynamicMultiplier?: number;
}

export interface ParkingSpace {
  id: string;
  lotId: string;
  spaceNumber: string;
  spaceType: 'standard' | 'handicap' | 'ev' | 'valet';
  isOccupied: boolean;
  isActive: boolean;
  currentSession?: {
    id: string;
    vehiclePlate: string;
    expiresAt: string;
  };
  createdAt: string;
  updatedAt: string;
}

export interface ParkingSession {
  id: string;
  lotId: string;
  lotName: string;
  spaceNumber: string | null;
  spaceId: string | null;
  userId: string | null;
  vehiclePlate: string;
  vehicleMake: string | null;
  vehicleModel: string | null;
  vehicleColor: string | null;
  startTime: string;
  expiresAt: string | null;
  endTime: string | null;
  basePrice: string;
  actualPrice: string | null;
  dynamicMultiplier: string;
  status: ParkingStatus;
  accessCode: string;
  contactEmail: string | null;
  contactPhone: string | null;
  lastNotificationSent: string | null;
  createdAt: string;
  updatedAt: string;
}

export type ParkingStatus = 'active' | 'pending_payment' | 'completed' | 'cancelled' | 'expired';

export interface SessionEvent {
  id: string;
  eventType: 'created' | 'extended' | 'payment' | 'refund' | 'note' | 'status_change';
  description: string;
  metadata: Record<string, any>;
  createdBy: string | null;
  createdAt: string;
}

export interface SessionNote {
  id: string;
  sessionId: string;
  note: string;
  isInternal: boolean;
  createdBy: string;
  createdAt: string;
}
```

### Opportunity Types

```typescript
// src/types/opportunity.ts

export interface Opportunity {
  id: string;
  partnerId: string;
  title: string;
  valueProposition: string;
  opportunityType: OpportunityType;
  triggerRules: TriggerRules;
  valueDetails: ValueDetails;
  validFrom: string;
  validUntil: string;
  totalCapacity: number | null;
  usedCapacity: number;
  priorityScore: number;
  locationLat: string;
  locationLng: string;
  address: string;
  walkingDistanceMeters: number | null;
  isActive: boolean;
  isApproved: boolean;
  createdAt: string;
}

export type OpportunityType = 'experience' | 'convenience' | 'discovery' | 'bundle' | 'exclusive';

export interface TriggerRules {
  timeRemainingMin?: number;
  timeRemainingMax?: number;
  daysOfWeek?: string[];
  timeOfDayStart?: string;
  timeOfDayEnd?: string;
}

export interface ValueDetails {
  discountPercentage?: number;
  discountFixedAmount?: number;
  fixedValueUsd?: number;
  originalPrice?: number;
  parkingExtensionMinutes?: number;
  perks?: string[];
}

export interface OpportunityAnalytics {
  period: {
    start: string;
    end: string;
  };
  engagement: {
    uniqueUsers: number;
    impressions: number;
    views: number;
    claims: number;
    redemptions: number;
    redemptionRate: number;
  };
  value: {
    avgTransaction: string;
    totalRevenue: string;
    platformFees: string;
    netRevenue: string;
  };
}

export interface ClaimValidation {
  valid: boolean;
  user: {
    id: string;
    firstName: string;
    lastName: string;
  };
  opportunity: {
    id: string;
    title: string;
    valueDetails: ValueDetails;
  };
  claimedAt: string;
}
```

---

## Core Features & UI Requirements

### 1. Dashboard (Home Page)

**Route:** `/dashboard`

**Layout:** Full-width dashboard with cards/widgets

**Real-time Data:**
- Current active sessions count
- Total revenue today
- Occupancy rate across all lots
- Active opportunities count
- Recent activity feed

**Widgets:**
- **Occupancy Overview Card**
  - Total spaces vs. occupied
  - Percentage occupancy
  - Chart showing occupancy by lot

- **Revenue Card**
  - Today's revenue
  - Week's revenue
  - Month's revenue
  - Trend indicator (↑↓)

- **Active Sessions Card**
  - Count of active sessions
  - Expiring soon (< 30 min)
  - Link to view all

- **Opportunities Card**
  - Active opportunities count
  - Acceptance rate today
  - Top performing opportunity

- **Recent Activity**
  - Real-time feed of:
    - New sessions started
    - Sessions expired/completed
    - Opportunities accepted
    - Refunds processed
  - Last 10-20 items with timestamps

**Charts:**
- Occupancy rate over last 24 hours (line chart)
- Revenue by lot (bar chart)
- Session duration distribution (histogram)

---

### 2. Parking Lots Management

**Route:** `/lots`

**Features:**
- List view of all parking lots
- Grid or table layout
- Filter by: Active/Inactive, Location
- Search by name or address
- Sort by: Name, Total Spaces, Occupancy, Revenue

**Lot Card/Row Shows:**
- Lot name
- Address
- Total spaces / Available spaces
- Current occupancy percentage with progress bar
- Status badge (Active/Inactive)
- Quick actions: View Details, Edit, Deactivate

**Create/Edit Lot Form:**
- Lot name (required)
- Description
- Address with map picker (optional Google Maps integration)
- Total spaces (required)
- Pricing configuration:
  - Base rate
  - Hourly rate
  - Max daily rate
  - Enable dynamic pricing toggle
- Active/Inactive status

**Lot Detail View:**
- Overview section (all lot info)
- Real-time space availability visualization
- Active sessions list
- Revenue analytics for this lot
- Space management (add/edit spaces)
- Map showing lot location

---

### 3. Parking Spaces Management

**Route:** `/lots/{lotId}/spaces`

**Features:**
- Visual grid layout showing all spaces
- Color coding:
  - Green: Available
  - Red: Occupied
  - Gray: Inactive
  - Blue: Handicap
  - Yellow: EV charging
  - Purple: Valet

**Space Card Shows:**
- Space number
- Space type icon
- Status (occupied/available)
- Current vehicle plate (if occupied)
- Time remaining (if occupied)
- Quick actions: View Session, Edit, Deactivate

**Add/Edit Space:**
- Space number (required, unique within lot)
- Space type dropdown
- Active/Inactive status

**Bulk Operations:**
- Select multiple spaces
- Bulk activate/deactivate
- Bulk change type

---

### 4. Active Sessions Monitor

**Route:** `/sessions`

**Features:**
- Real-time list of all sessions
- Default view: Active sessions only
- Filter by:
  - Status (Active, Completed, Expired, Cancelled)
  - Lot
  - Date range
  - Vehicle plate
- Search: Vehicle plate, access code, contact email
- Sort by: Start time, Expiration, Duration, Amount

**Session List Table Columns:**
- Access code (clickable)
- Vehicle plate (bold)
- Lot name
- Space number
- Start time (relative: "2 hours ago")
- Expires at (relative: "in 45 min") with urgency color coding:
  - Red: < 15 min
  - Orange: 15-30 min
  - Green: > 30 min
- Duration (calculated)
- Amount
- Status badge
- Actions dropdown:
  - View Details
  - Extend Time
  - End Session
  - Process Refund
  - Add Note

**Real-time Updates:**
- Auto-refresh every 30 seconds OR
- WebSocket connection for live updates
- Show notification when session expires

**Bulk Operations:**
- Select multiple sessions
- Bulk extend (add X hours to all)
- Bulk notifications (send reminder SMS/email)

---

### 5. Session Detail View

**Route:** `/sessions/{sessionId}`

**Sections:**

**Session Overview Card:**
- Access code (large, monospace, copyable)
- Status badge
- Vehicle information (plate, make, model, color)
- Lot and space information
- Contact information (email, phone)
- Start time, expiration time, end time
- Duration (calculated)
- Pricing breakdown (base price, dynamic multiplier, final price)

**Timeline:**
- Visual timeline of session events:
  - Session created
  - Payment received
  - Extensions
  - Notes added
  - Status changes
  - Refunds processed
  - Session ended

**Actions Panel:**
- **Extend Time** button
  - Modal with hours input
  - Shows new expiration time
  - Recalculates price

- **End Session Early** button
  - Confirmation dialog
  - Option to refund difference

- **Process Refund** button
  - Modal with:
    - Reason dropdown
    - Amount input (defaults to full amount)
    - Internal notes

- **Add Note** button
  - Modal with:
    - Note text area
    - Internal note toggle (hide from customer)

**Related Information:**
- User information (if session linked to user account)
- User's parking history
- Opportunities accepted during this session

---

### 6. Expiring Sessions Alert

**Route:** `/sessions/expiring`

**Features:**
- List of sessions expiring in next 60 minutes
- Sorted by expiration time (soonest first)
- Auto-refresh every 60 seconds
- Countdown timer for each session
- Quick actions:
  - Send expiration notification
  - Extend time
  - Contact customer

**Visual Design:**
- Urgent/attention-grabbing design
- Red/orange color scheme
- Large countdown timers
- One-click actions

---

### 7. Opportunities Management

**Route:** `/opportunities`

**Features:**
- List view of all opportunities
- Filter by:
  - Status (Active, Inactive, Expired)
  - Type (Experience, Convenience, Discovery, Bundle)
  - Date range
- Search by title, partner name
- Sort by: Created date, Valid until, Priority score, Usage

**Opportunity Card/Row Shows:**
- Title with emoji/icon
- Value proposition (truncated)
- Type badge
- Status badge (Active/Inactive/Expired)
- Validity period
- Capacity: Used/Total with progress bar
- Acceptance rate
- Quick actions: View Details, Edit, Deactivate, View Analytics

**Create/Edit Opportunity Form:**

**Basic Information:**
- Title (required)
- Value proposition (textarea, required)
- Opportunity type (dropdown)

**Value Details:**
- Discount type: Percentage or Fixed Amount
- Discount value
- Original price (optional, for reference)
- Parking extension (minutes)
- Perks (multi-select or tags)

**Trigger Rules:**
- Time remaining (min-max range in minutes)
- Days of week (multi-select)
- Time of day (start-end time pickers)

**Availability:**
- Valid from (date picker)
- Valid until (date picker)
- Total capacity (optional, null = unlimited)

**Location:**
- Address (required)
- Location coordinates (auto-populate from address)
- Walking distance from lot (meters)

**Advanced:**
- Priority score (1-100)
- Auto-approve toggle

**Preview Panel:**
- Shows how opportunity will appear to users
- Value badge preview
- Mobile view preview

---

### 8. Opportunity Detail & Analytics

**Route:** `/opportunities/{opportunityId}`

**Sections:**

**Opportunity Overview:**
- All opportunity details
- Edit button
- Activate/Deactivate toggle
- Capacity usage progress bar
- QR code for easy sharing

**Analytics Dashboard:**
- Date range picker
- Key metrics cards:
  - Impressions
  - Views (click-through rate)
  - Acceptances (acceptance rate)
  - Redemptions (redemption rate)
  - Revenue generated
  - Avg transaction amount

**Charts:**
- Acceptance trend over time (line chart)
- Acceptance by hour of day (bar chart)
- Acceptance by day of week (bar chart)

**Recent Interactions:**
- Table of recent user interactions:
  - User name (if available)
  - Interaction type (Impressed, Viewed, Accepted, Completed)
  - Timestamp
  - Claim code (if accepted)
  - Transaction amount (if completed)

**Claim Validation:**
- Input field for claim code
- Validate button
- Shows user info and value details if valid

---

### 9. User Management

**Route:** `/users`

**Features:**
- List view of all users
- Filter by:
  - Role (Admin, Operator, Customer)
  - Status (Active, Inactive, Verified)
- Search by: Name, Email, Phone
- Sort by: Created date, Last login, Total sessions

**User List Table Columns:**
- Name
- Email
- Role badge
- Status (Active/Inactive)
- Email verified badge
- Phone verified badge
- Total parking sessions
- Last login (relative)
- Actions: View Details, Edit, Deactivate

**User Detail View:**
- User information
- Parking history
  - All sessions with details
  - Total spent
  - Avg session duration
- Opportunity interactions
  - Accepted opportunities
  - Redemption history
- Account activity timeline

---

### 10. Reports & Analytics

**Route:** `/analytics`

**Tabs:**
- Parking Analytics
- Opportunity Analytics
- Revenue Reports
- User Analytics

**Global Filters:**
- Date range picker
- Lot selector (all/specific)
- Export button (CSV/PDF)

**Parking Analytics:**
- Occupancy trends
- Peak hours heatmap
- Session duration distribution
- Revenue by lot
- Popular spaces/areas

**Opportunity Analytics:**
- Overall performance metrics
- Top performing opportunities
- Conversion funnel
- Partner performance comparison

**Revenue Reports:**
- Daily/Weekly/Monthly revenue
- Revenue by lot
- Revenue by opportunity
- Refunds breakdown
- Revenue trend projection

---

### 11. Settings

**Route:** `/settings`

**Sections:**

**Account Settings:**
- Profile information
- Email/Password change
- Notification preferences

**Parking Configuration:**
- Default pricing
- Dynamic pricing rules
- Notification templates
- Grace period settings
- Auto-extend settings

**Opportunity Settings:**
- Auto-approval rules
- Commission rates
- Default capacity limits

**Integrations:**
- Payment gateway configuration (Stripe)
- SMS provider configuration (Twilio)
- Email provider configuration
- Webhook URLs

---

## State Management (Pinia Stores)

### Auth Store

```typescript
// src/stores/auth.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { User } from '@/types/user';
import { login as apiLogin, refresh as apiRefresh } from '@/api/auth';

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const accessToken = ref<string | null>(null);
  const refreshToken = ref<string | null>(null);

  const isAuthenticated = computed(() => !!user.value && !!accessToken.value);
  const isAdmin = computed(() => user.value?.role === 'admin');
  const isOperator = computed(() => user.value?.role === 'operator' || user.value?.role === 'admin');

  async function login(email: string, password: string) {
    const response = await apiLogin(email, password);
    user.value = response.user;
    accessToken.value = response.accessToken;
    refreshToken.value = response.refreshToken;

    // Persist to localStorage
    localStorage.setItem('access_token', response.accessToken);
    localStorage.setItem('refresh_token', response.refreshToken);
  }

  async function refreshAccessToken() {
    if (!refreshToken.value) throw new Error('No refresh token');

    const response = await apiRefresh(refreshToken.value);
    accessToken.value = response.accessToken;
    refreshToken.value = response.refreshToken;

    localStorage.setItem('access_token', response.accessToken);
    localStorage.setItem('refresh_token', response.refreshToken);
  }

  function logout() {
    user.value = null;
    accessToken.value = null;
    refreshToken.value = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  function initialize() {
    const token = localStorage.getItem('access_token');
    const refresh = localStorage.getItem('refresh_token');
    if (token && refresh) {
      accessToken.value = token;
      refreshToken.value = refresh;
      // Optionally fetch current user info
    }
  }

  return {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    isAdmin,
    isOperator,
    login,
    logout,
    refreshAccessToken,
    initialize,
  };
});
```

### Parking Store

```typescript
// src/stores/parking.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { ParkingLot, ParkingSession, ParkingSpace } from '@/types/parking';
import * as parkingApi from '@/api/parking';

export const useParkingStore = defineStore('parking', () => {
  const lots = ref<ParkingLot[]>([]);
  const selectedLot = ref<ParkingLot | null>(null);
  const sessions = ref<ParkingSession[]>([]);
  const spaces = ref<ParkingSpace[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const activeSessions = computed(() =>
    sessions.value.filter(s => s.status === 'active')
  );

  const expiringSoon = computed(() =>
    activeSessions.value.filter(s => {
      if (!s.expiresAt) return false;
      const expiresIn = new Date(s.expiresAt).getTime() - Date.now();
      return expiresIn > 0 && expiresIn < 60 * 60 * 1000; // 1 hour
    })
  );

  const totalOccupancy = computed(() => {
    const total = lots.value.reduce((sum, lot) => sum + lot.totalSpaces, 0);
    const available = lots.value.reduce((sum, lot) => sum + lot.availableSpaces, 0);
    const occupied = total - available;
    return total > 0 ? (occupied / total) * 100 : 0;
  });

  async function fetchLots() {
    loading.value = true;
    error.value = null;
    try {
      lots.value = await parkingApi.getLots();
    } catch (e: any) {
      error.value = e.message;
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function fetchSessions(filters?: any) {
    loading.value = true;
    error.value = null;
    try {
      sessions.value = await parkingApi.getSessions(filters);
    } catch (e: any) {
      error.value = e.message;
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function extendSession(accessCode: string, additionalHours: number) {
    const session = await parkingApi.extendSession(accessCode, additionalHours);
    // Update session in array
    const index = sessions.value.findIndex(s => s.accessCode === accessCode);
    if (index !== -1) {
      sessions.value[index] = session;
    }
    return session;
  }

  async function endSession(accessCode: string) {
    const session = await parkingApi.endSession(accessCode);
    const index = sessions.value.findIndex(s => s.accessCode === accessCode);
    if (index !== -1) {
      sessions.value[index] = session;
    }
    return session;
  }

  // Add more actions as needed...

  return {
    lots,
    selectedLot,
    sessions,
    spaces,
    loading,
    error,
    activeSessions,
    expiringSoon,
    totalOccupancy,
    fetchLots,
    fetchSessions,
    extendSession,
    endSession,
  };
});
```

### Opportunities Store

```typescript
// src/stores/opportunities.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Opportunity, OpportunityAnalytics } from '@/types/opportunity';
import * as opportunitiesApi from '@/api/opportunities';

export const useOpportunitiesStore = defineStore('opportunities', () => {
  const opportunities = ref<Opportunity[]>([]);
  const selectedOpportunity = ref<Opportunity | null>(null);
  const analytics = ref<OpportunityAnalytics | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const activeOpportunities = computed(() =>
    opportunities.value.filter(o => o.isActive && new Date(o.validUntil) > new Date())
  );

  const expiringSoon = computed(() =>
    activeOpportunities.value.filter(o => {
      const daysUntilExpiry = (new Date(o.validUntil).getTime() - Date.now()) / (1000 * 60 * 60 * 24);
      return daysUntilExpiry < 7;
    })
  );

  async function fetchOpportunities() {
    loading.value = true;
    error.value = null;
    try {
      opportunities.value = await opportunitiesApi.getPartnerOpportunities();
    } catch (e: any) {
      error.value = e.message;
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function createOpportunity(data: any) {
    const opportunity = await opportunitiesApi.createOpportunity(data);
    opportunities.value.push(opportunity);
    return opportunity;
  }

  async function updateOpportunity(id: string, data: any) {
    const updated = await opportunitiesApi.updateOpportunity(id, data);
    const index = opportunities.value.findIndex(o => o.id === id);
    if (index !== -1) {
      opportunities.value[index] = updated;
    }
    return updated;
  }

  async function fetchAnalytics(dateStart?: string, dateEnd?: string, opportunityId?: string) {
    analytics.value = await opportunitiesApi.getAnalytics({ dateStart, dateEnd, opportunityId });
  }

  async function validateClaim(opportunityId: string, claimCode: string) {
    return await opportunitiesApi.validateClaim(opportunityId, claimCode);
  }

  async function completeClaim(opportunityId: string, claimCode: string, transactionAmount?: number) {
    return await opportunitiesApi.completeClaim(opportunityId, claimCode, transactionAmount);
  }

  return {
    opportunities,
    selectedOpportunity,
    analytics,
    loading,
    error,
    activeOpportunities,
    expiringSoon,
    fetchOpportunities,
    createOpportunity,
    updateOpportunity,
    fetchAnalytics,
    validateClaim,
    completeClaim,
  };
});
```

---

## UI Components Architecture

### Layout Components

**DashboardLayout.vue**
- Sidebar navigation
- Top header with user menu
- Breadcrumbs
- Main content area
- Footer (optional)

**Sidebar Navigation Items:**
- Dashboard (home icon)
- Parking Lots (parking icon)
- Active Sessions (car icon)
- Expiring Soon (clock icon with badge)
- Opportunities (gift icon)
- Users (users icon)
- Analytics (chart icon)
- Settings (gear icon)

### Reusable Components

**StatusBadge.vue**
- Props: status (string), variant (success, warning, danger, info)
- Color-coded badge with appropriate styling

**DataTable.vue**
- Props: columns, data, loading, pagination
- Sortable columns
- Filterable
- Row selection
- Pagination controls
- Empty state

**ConfirmDialog.vue**
- Props: title, message, confirmText, cancelText, variant
- Composable: useConfirm()

**LoadingSpinner.vue**
- Full-page overlay
- Inline spinner
- Skeleton loaders

**StatCard.vue**
- Props: title, value, icon, trend, trendValue
- Used on dashboard for KPIs

**ChartCard.vue**
- Wrapper for charts
- Props: title, type (line, bar, pie)
- Loading state
- Empty state

### Parking-Specific Components

**LotCard.vue**
- Display lot information
- Occupancy progress bar
- Quick actions

**SessionCard.vue**
- Display session summary
- Countdown timer
- Status badge
- Quick actions

**SpaceGrid.vue**
- Visual grid of parking spaces
- Color-coded by status and type
- Click to view details

**ExtendSessionDialog.vue**
- Modal form to extend parking
- Hours input with validation
- Price calculation preview

**RefundDialog.vue**
- Modal form to process refund
- Reason selection
- Amount input
- Notes textarea

**AddNoteDialog.vue**
- Modal form to add note
- Note textarea
- Internal note toggle

### Opportunity Components

**OpportunityCard.vue**
- Display opportunity summary
- Value badge
- Capacity progress bar
- Quick actions

**OpportunityForm.vue**
- Complete form for create/edit
- Multi-step wizard (optional)
- Validation with VeeValidate + Zod
- Live preview panel

**ClaimValidation.vue**
- Input field for claim code
- Validate button
- Display validation result

**AnalyticsChart.vue**
- Reusable chart component for opportunity analytics
- Multiple chart types

---

## Routing Configuration

```typescript
// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import DashboardLayout from '@/layouts/DashboardLayout.vue';
import AuthLayout from '@/layouts/AuthLayout.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/auth',
      component: AuthLayout,
      children: [
        {
          path: 'login',
          name: 'login',
          component: () => import('@/views/Auth/Login.vue'),
        },
        {
          path: 'forgot-password',
          name: 'forgot-password',
          component: () => import('@/views/Auth/ForgotPassword.vue'),
        },
      ],
    },
    {
      path: '/',
      component: DashboardLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: '/dashboard',
        },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('@/views/Dashboard.vue'),
        },
        {
          path: 'lots',
          name: 'lots',
          component: () => import('@/views/Lots/LotsList.vue'),
        },
        {
          path: 'lots/:id',
          name: 'lot-detail',
          component: () => import('@/views/Lots/LotDetail.vue'),
        },
        {
          path: 'lots/:id/spaces',
          name: 'lot-spaces',
          component: () => import('@/views/Lots/SpacesManagement.vue'),
        },
        {
          path: 'sessions',
          name: 'sessions',
          component: () => import('@/views/Sessions/SessionsList.vue'),
        },
        {
          path: 'sessions/expiring',
          name: 'sessions-expiring',
          component: () => import('@/views/Sessions/ExpiringSessions.vue'),
        },
        {
          path: 'sessions/:id',
          name: 'session-detail',
          component: () => import('@/views/Sessions/SessionDetail.vue'),
        },
        {
          path: 'opportunities',
          name: 'opportunities',
          component: () => import('@/views/Opportunities/OpportunitiesList.vue'),
        },
        {
          path: 'opportunities/new',
          name: 'opportunity-create',
          component: () => import('@/views/Opportunities/OpportunityForm.vue'),
        },
        {
          path: 'opportunities/:id',
          name: 'opportunity-detail',
          component: () => import('@/views/Opportunities/OpportunityDetail.vue'),
        },
        {
          path: 'opportunities/:id/edit',
          name: 'opportunity-edit',
          component: () => import('@/views/Opportunities/OpportunityForm.vue'),
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('@/views/Users/UsersList.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'users/:id',
          name: 'user-detail',
          component: () => import('@/views/Users/UserDetail.vue'),
          meta: { requiresAdmin: true },
        },
        {
          path: 'analytics',
          name: 'analytics',
          component: () => import('@/views/Analytics/AnalyticsDashboard.vue'),
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/views/Settings.vue'),
        },
      ],
    },
  ],
});

// Navigation guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } });
  } else if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next({ name: 'dashboard' });
  } else {
    next();
  }
});

export default router;
```

---

## Styling & Design System

### Color Palette (Tailwind Config)

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        // Primary brand colors
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        },
        // Status colors
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444',
        info: '#3b82f6',
        // Parking-specific
        occupied: '#ef4444',
        available: '#10b981',
        expiring: '#f59e0b',
        inactive: '#6b7280',
      },
    },
  },
};
```

### Component Styling Guidelines

- **Spacing:** Use Tailwind spacing scale (4, 8, 12, 16, 24, 32, 48, 64)
- **Border Radius:** Consistent rounded corners (rounded-lg for cards, rounded-md for buttons)
- **Shadows:** Subtle shadows for elevation (shadow-sm, shadow-md, shadow-lg)
- **Typography:** Clear hierarchy (text-3xl for headings, text-base for body)
- **Responsive:** Mobile-first, breakpoints at sm:, md:, lg:, xl:
- **Dark Mode:** Support dark mode using Tailwind's dark: prefix (optional for v1)

### Mobile Optimization

- **Touch Targets:** Minimum 44x44px for buttons and interactive elements
- **Responsive Tables:** Convert to stacked cards on mobile
- **Hamburger Menu:** Collapsible sidebar on mobile
- **Bottom Navigation:** Consider bottom nav bar for mobile (optional)
- **Viewport:** Set appropriate viewport meta tag

---

## Real-time Features

### Auto-refresh Strategy

**Option 1: Polling (Simple)**
- Use `setInterval` to refetch data every 30-60 seconds
- Stop polling when user is inactive (visibility API)
- Show "Updated X seconds ago" indicator

```typescript
// src/composables/useAutoRefresh.ts
import { onMounted, onUnmounted, ref } from 'vue';

export function useAutoRefresh(callback: () => void, interval = 30000) {
  const lastUpdated = ref<Date>(new Date());
  let timer: number;

  onMounted(() => {
    timer = setInterval(() => {
      if (document.visibilityState === 'visible') {
        callback();
        lastUpdated.value = new Date();
      }
    }, interval);
  });

  onUnmounted(() => {
    clearInterval(timer);
  });

  return { lastUpdated };
}
```

**Option 2: WebSocket (Advanced - Future)**
- Real-time updates via WebSocket connection
- Backend emits events for session changes, new opportunities, etc.
- Client listens and updates UI immediately

---

## Form Validation

Use VeeValidate with Zod schemas:

```typescript
// Example: Extend Session Form Validation
import { z } from 'zod';

export const extendSessionSchema = z.object({
  additionalHours: z.number()
    .min(0.5, 'Minimum 30 minutes')
    .max(24, 'Maximum 24 hours'),
});

export type ExtendSessionInput = z.infer<typeof extendSessionSchema>;
```

```vue
<!-- ExtendSessionDialog.vue -->
<template>
  <Dialog>
    <form @submit="onSubmit">
      <Field name="additionalHours" v-slot="{ field, errorMessage }">
        <input
          v-bind="field"
          type="number"
          step="0.5"
          :class="{ 'border-red-500': errorMessage }"
        />
        <span v-if="errorMessage" class="text-red-500 text-sm">
          {{ errorMessage }}
        </span>
      </Field>
      <button type="submit">Extend</button>
    </form>
  </Dialog>
</template>

<script setup lang="ts">
import { useForm, Field } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import { extendSessionSchema } from '@/schemas/parking';

const { handleSubmit } = useForm({
  validationSchema: toTypedSchema(extendSessionSchema),
});

const onSubmit = handleSubmit(async (values) => {
  // Handle submission
});
</script>
```

---

## Error Handling

### API Error Interceptor

```typescript
// src/api/client.ts
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 Unauthorized - refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const authStore = useAuthStore();
      try {
        await authStore.refreshAccessToken();
        return client(originalRequest);
      } catch (refreshError) {
        authStore.logout();
        router.push('/auth/login');
        return Promise.reject(refreshError);
      }
    }

    // Handle other errors
    const message = error.response?.data?.error?.message || 'An error occurred';
    toast.error(message);

    return Promise.reject(error);
  }
);
```

### Toast Notifications

Use a toast library like **vue-toastification** or build custom:

```typescript
// src/utils/toast.ts
import { useToast } from 'vue-toastification';

const toast = useToast();

export const showSuccess = (message: string) => {
  toast.success(message);
};

export const showError = (message: string) => {
  toast.error(message);
};

export const showInfo = (message: string) => {
  toast.info(message);
};
```

---

## Implementation Checklist

### Phase 1: Foundation (Week 1)
- [ ] Initialize Vue 3 + Vite + TypeScript project
- [ ] Install and configure Tailwind CSS
- [ ] Install shadcn-vue components
- [ ] Set up Vue Router with auth guards
- [ ] Set up Pinia stores
- [ ] Create API client with axios
- [ ] Implement authentication (login/logout)
- [ ] Create base layouts (Dashboard, Auth)
- [ ] Create navigation sidebar
- [ ] Set up TypeScript types

### Phase 2: Core Parking Features (Week 2)
- [ ] Dashboard view with KPI cards
- [ ] Parking lots list view
- [ ] Lot detail view
- [ ] Active sessions list
- [ ] Session detail view
- [ ] Extend session functionality
- [ ] End session functionality
- [ ] Expiring sessions alert page
- [ ] Session search and filters

### Phase 3: Advanced Parking (Week 3)
- [ ] Parking spaces management
- [ ] Visual space grid
- [ ] Add/edit lot functionality
- [ ] Add/edit space functionality
- [ ] Process refund functionality
- [ ] Add session notes
- [ ] Session history timeline
- [ ] User parking history
- [ ] Real-time auto-refresh

### Phase 4: Opportunities (Week 4)
- [ ] Opportunities list view
- [ ] Opportunity detail view
- [ ] Create/edit opportunity form
- [ ] Opportunity analytics dashboard
- [ ] Claim code validation
- [ ] Complete redemption flow
- [ ] Opportunity filters and search

### Phase 5: Analytics & Reports (Week 5)
- [ ] Parking analytics dashboard
- [ ] Opportunity analytics dashboard
- [ ] Revenue reports
- [ ] Charts and visualizations
- [ ] Export functionality (CSV)
- [ ] Custom date range filtering

### Phase 6: Users & Settings (Week 6)
- [ ] User management (admin only)
- [ ] User detail with history
- [ ] Settings page
- [ ] Account settings
- [ ] Parking configuration
- [ ] Notification preferences

### Phase 7: Polish & Optimization (Week 7)
- [ ] Mobile responsive design
- [ ] Loading states and skeletons
- [ ] Error handling and user feedback
- [ ] Form validation on all forms
- [ ] Toast notifications
- [ ] Accessibility audit
- [ ] Performance optimization
- [ ] Browser testing (Chrome, Safari, Firefox)

### Phase 8: Testing & Deployment (Week 8)
- [ ] Unit tests for stores
- [ ] Unit tests for composables
- [ ] Integration tests for critical flows
- [ ] E2E tests with Playwright (optional)
- [ ] Build for production
- [ ] Deploy to hosting (Vercel, Netlify, etc.)
- [ ] Set up CI/CD pipeline

---

## Development Best Practices

### Code Organization
- One component per file
- Use Composition API with `<script setup>`
- Extract reusable logic into composables
- Keep components small and focused
- Use TypeScript for type safety

### Performance
- Lazy load route components
- Use `v-memo` for expensive renders
- Debounce search inputs
- Paginate large lists
- Optimize images
- Code splitting

### Accessibility
- Use semantic HTML
- Add ARIA labels where needed
- Ensure keyboard navigation
- Test with screen readers
- Color contrast compliance (WCAG AA)

### Git Workflow
- Feature branches for each feature
- Descriptive commit messages
- PR reviews before merging
- Keep main branch deployable

### Documentation
- Add JSDoc comments to complex functions
- Document component props and emits
- Maintain README with setup instructions
- Document API integration patterns

---

## Environment Variables

```env
# .env.development
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_NAME=TruFan Parking Admin

# .env.production
VITE_API_BASE_URL=https://api.trufan.com/api/v1
VITE_APP_NAME=TruFan Parking Admin
```

---

## Testing Strategy

### Unit Tests (Vitest)
- Test Pinia stores
- Test composables
- Test utility functions
- Test API client transformations

### Component Tests (Vue Test Utils)
- Test component rendering
- Test user interactions
- Test props and emits
- Test conditional rendering

### E2E Tests (Playwright - Optional)
- Test critical user flows:
  - Login → View sessions → Extend session
  - Create lot → Add spaces → Monitor
  - Create opportunity → View analytics
  - Process refund

---

## Deployment

### Build Command
```bash
npm run build
# Output: dist/ directory
```

### Hosting Options
- **Vercel** (recommended for Vue/Vite)
- **Netlify**
- **AWS S3 + CloudFront**
- **Azure Static Web Apps**

### CI/CD Pipeline (GitHub Actions Example)

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-artifact@v3
        with:
          name: dist
          path: dist/
      # Deploy to hosting provider
```

---

## Future Enhancements

### Phase 2 Features (Post-MVP)
- [ ] WebSocket for real-time updates
- [ ] Push notifications for expiring sessions
- [ ] Mobile app (React Native or Flutter)
- [ ] Advanced analytics with predictions
- [ ] Multi-language support (i18n)
- [ ] Dark mode toggle
- [ ] Bulk operations (bulk extend, bulk refund)
- [ ] CSV import for lots/spaces
- [ ] QR code generation for lots
- [ ] Integration with external parking systems
- [ ] SMS notifications to users
- [ ] Email notifications
- [ ] Automated reports (daily/weekly)
- [ ] Stripe payment integration
- [ ] Valet mode with check-in/check-out
- [ ] Reservation system
- [ ] Dynamic pricing algorithms
- [ ] Waitlist for full lots

---

## Support & Resources

### Vue 3 Documentation
- https://vuejs.org/
- https://router.vuejs.org/
- https://pinia.vuejs.org/

### UI Libraries
- shadcn-vue: https://www.shadcn-vue.com/
- Tailwind CSS: https://tailwindcss.com/

### Additional Tools
- VeeValidate: https://vee-validate.logaretm.com/
- Chart.js: https://www.chartjs.org/
- vue-chartjs: https://vue-chartjs.org/
- date-fns: https://date-fns.org/

---

## Final Notes

This is a **comprehensive, production-ready** admin interface for parking facility management. Focus on:

1. **User Experience:** Intuitive navigation, fast load times, clear feedback
2. **Data Accuracy:** Real-time updates, accurate calculations
3. **Reliability:** Proper error handling, data validation
4. **Scalability:** Code organization for future expansion
5. **Mobile-First:** Responsive design for operators on the go

**Timeline:** 6-8 weeks for complete MVP with all core features.

**Team Size:** 1-2 frontend developers (with Claude assistance)

**Start with:** Phase 1 (Foundation) and Phase 2 (Core Parking), then iterate based on operator feedback.

Good luck building the TruFan Parking Admin! 🚀
