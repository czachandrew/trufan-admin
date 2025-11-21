# TruFan Convenience Store - Mobile UX/Product Specification

## Executive Summary

This document provides comprehensive UX/product recommendations for implementing the convenience store feature in TruFan's iOS mobile parking app. The feature allows users to order items from nearby stores while parked at venues, with venue staff handling shopping and delivery to their vehicle.

**Key Insight**: The user is at a haircut/event and suddenly realizes they forgot something. The experience must be frictionless, requiring minimal cognitive load during a busy moment.

---

## 1. User Flow & Experience

### 1.1 Discovery & Entry Points

#### When Should Convenience Store Be Discoverable?

**PRIMARY RECOMMENDATION: Multi-Context Discovery**

The convenience store should be discoverable in multiple contexts, not just during active parking:

**Context 1: During Active Parking Session (Primary)**
- **Rationale**: User is already parked, time-locked to a venue, and looking for ways to maximize their time
- **Entry Point**: Prominent "Shop While You Park" card on parking session detail screen
- **Timing**: Show immediately after payment is confirmed and parking is active
- **Psychology**: User has committed time to the venue and is receptive to value-added services

**Context 2: Pre-Parking (Browse Mode)**
- **Rationale**: User might realize they need items while browsing parking options
- **Entry Point**: "Convenience Store Available" badge on lot detail screens
- **Use Case**: "I'm going to a haircut at this venue, and I could pick up groceries too"
- **Psychology**: Influences parking lot selection - adds value proposition

**Context 3: Parking Session Creation Flow**
- **Rationale**: Natural upsell moment when user is already in transaction mode
- **Entry Point**: Optional "Add items to order" step after vehicle info, before payment
- **Use Case**: "While I'm entering my info, I remember I need milk"
- **Psychology**: Reduces friction by combining transactions

**Context 4: Post-Parking (Home Tab)**
- **Rationale**: User opens app hours later and remembers they need something
- **Entry Point**: Dedicated "Convenience" tab in bottom navigation (4th tab)
- **Use Case**: "I'm already parked at my haircut, let me check if I can order something"
- **Psychology**: Standalone feature discovery for power users

**RECOMMENDED IMPLEMENTATION PRIORITY**:
1. During active parking (highest conversion)
2. Pre-parking browse mode (influences lot selection)
3. Dedicated tab (power user engagement)
4. Inline during parking creation (optional, A/B test)

#### Should It Only Be Available During Active Parking?

**RECOMMENDATION: No - But Heavily Prioritize Active Sessions**

**Allow ordering in 3 states:**

1. **Active Parking Session (Optimal)** ✅
   - Full feature access
   - Automatic parking time extension
   - Delivery to vehicle location
   - Highest priority fulfillment
   - **Best Experience**: Staff knows exactly where customer is

2. **Future Reservation (Limited)** ⚠️
   - Can browse and add to cart
   - Can schedule order for arrival time
   - Prompts to confirm parking before checkout
   - **Use Case**: "I'm heading to my haircut in 30 minutes, prepare my order"
   - **Risk Mitigation**: Require parking confirmation before staff shops

3. **No Active Session (Browse Only)** 🔍
   - Can browse items and prices
   - Can add to favorites
   - Checkout requires starting a parking session
   - **Use Case**: "Let me see what's available before I commit to parking here"
   - **Psychology**: Discovery and education phase

**WHY NOT RESTRICT TO ACTIVE PARKING ONLY**:
- User journey isn't always linear
- Pre-shopping reduces decision time during actual parking
- Browsing capability drives lot selection
- Favorites/cart persistence increases conversion later

**CLEAR MESSAGING REQUIRED**:
- "Start parking to enable delivery" banner on checkout
- "Available when you park at [Venue Name]" on browse screens
- Progressive disclosure: show capability, require parking for fulfillment

### 1.2 Optimal Entry Points & Navigation

#### Information Architecture

```
Bottom Tab Navigation:
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│  Home   │Sessions │   Map   │  Shop   │ Profile │
│   🏠    │   🅿️    │   🗺️    │   🛒    │   👤    │
└─────────┴─────────┴─────────┴─────────┴─────────┘
```

**Tab 4: "Shop" (Convenience Store)**
- Icon: Shopping cart or store icon
- Label: "Shop" or "Store"
- Badge: Shows cart item count
- Persistent access to feature
- Filters by currently parked venue or shows all available venues

#### Primary Entry Flow (During Active Parking)

**Session Detail Screen → Shop Card:**

```
┌─────────────────────────────────────┐
│ 🅿️ Downtown Garage - Space A-101   │
│ Expires in 1h 23m                   │
├─────────────────────────────────────┤
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🛒 Shop While You Park          │ │
│ │                                 │ │
│ │ Want us to grab a few things?   │ │
│ │ Get 15 min FREE parking added   │ │
│ │                                 │ │
│ │ [Browse Store] →                │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Vehicle: ABC123                     │
│ [Extend Time] [End Session]         │
└─────────────────────────────────────┘
```

**Visual Treatment:**
- Eye-catching card with gradient background
- Prominent placement above fold
- Clear value proposition: "FREE parking time"
- Dismissible but returns on next session view
- Shows personalized item suggestions if available

#### Secondary Entry Flow (Pre-Parking Browse)

**Lot Detail Screen → Convenience Badge:**

```
┌─────────────────────────────────────┐
│ Downtown Garage                     │
│ 123 Main St • 45 spaces available   │
├─────────────────────────────────────┤
│ 🛒 Convenience Store Available      │
│ Order while you park                │
├─────────────────────────────────────┤
│ Base Rate: $10.00                   │
│ Hourly: $5.00/hr                    │
│                                     │
│ [View Store Items]                  │
│ [Continue to Park]                  │
└─────────────────────────────────────┘
```

### 1.3 Key User Moments & States

#### Moment 1: Realization ("Oh no, I forgot milk!")

**Context**: User just sat down for haircut and realizes they need something
**Mental State**: Mild panic, distracted, busy
**UX Response**:
- One-tap access from active session screen
- Search-first interface
- Voice search option
- Recent/popular items front and center
- Quick add to cart (no detail views required)

**Screen Design Priority**:
1. Search bar (persistent, top position)
2. "Popular Items" carousel (one-tap add)
3. Recent orders (reorder in one tap)
4. Categories (if search doesn't help)

#### Moment 2: Browsing ("What's available?")

**Context**: User has a few minutes, exploring options
**Mental State**: Curious but cautious about pricing
**UX Response**:
- Clear pricing (final price, not base price)
- Service fee transparency upfront
- Estimated total updates in real-time
- Visual browsing (images important)
- Category organization

#### Moment 3: Checkout ("Will this be expensive?")

**Context**: Ready to order but concerned about cost/delivery
**Mental State**: Decision point, price-sensitive
**UX Response**:
- Clear pricing breakdown before payment
- Show time benefit: "You're getting 15 min free parking ($7.50 value)"
- Estimated delivery time prominent
- Delivery instructions easy to modify
- Payment method pre-filled from parking payment

#### Moment 4: Waiting ("Where are my items?")

**Context**: Order placed, waiting for delivery
**Mental State**: Anticipation, occasional anxiety
**UX Response**:
- Push notifications at each status change
- Visual progress tracker (linear, not circular)
- Estimated time remaining
- Ability to message staff
- Clear delivery location confirmation

#### Moment 5: Receiving ("Am I getting the right stuff?")

**Context**: Staff approaching with items
**Mental State**: Verification, slight skepticism
**UX Response**:
- Order summary easily accessible
- Photo of receipt available
- Clear item list
- Easy dispute/rating flow
- Immediate rating prompt (while experience is fresh)

---

## 2. Browse & Search Experience

### 2.1 Display Approach

**RECOMMENDATION: Hybrid Display with Context-Aware Switching**

#### Default View: Grid with Large Images (Pinterest-Style)

**Rationale**:
- Mobile users scan quickly with eyes, not reading
- Food/product purchases are visual decisions
- 2-column grid maximizes information density
- Familiar pattern from DoorDash, Instacart, Amazon

**Grid Specifications**:
```
┌─────────────────────────────────────┐
│ Search: "milk, eggs..."       🔍   │
├─────────────────────────────────────┤
│ Categories: [All▾][Grocery][Food]  │
├─────────────────────────────────────┤
│ ┌────────────┐  ┌────────────┐     │
│ │  [IMAGE]   │  │  [IMAGE]   │     │
│ │  Milk 2%   │  │  Eggs 12ct │     │
│ │  $5.74     │  │  $4.59     │     │
│ │  Walgreens │  │  Walgreens │     │
│ │  [+ Add]   │  │  [+ Add]   │     │
│ └────────────┘  └────────────┘     │
│                                     │
│ ┌────────────┐  ┌────────────┐     │
│ │  [IMAGE]   │  │  [IMAGE]   │     │
│ │  Bread     │  │  Coffee    │     │
│ │  $4.01     │  │  $9.19     │     │
│ │  Walgreens │  │  CVS       │     │
│ │  [+ Add]   │  │  [+ Add]   │     │
│ └────────────┘  └────────────┘     │
│                                     │
└─────────────────────────────────────┘
```

**Card Information Hierarchy**:
1. **Image**: 60% of card (high-quality product photo)
2. **Name**: Bold, 16pt, max 2 lines with ellipsis
3. **Price**: Large, prominent ($5.74 not $5.74 USD)
4. **Store**: Small, gray, one line
5. **Add Button**: Full width, primary color

#### Alternative View: List with Details (On User Toggle)

**Rationale**:
- Some users prefer dense information
- Better for price comparison
- Faster scrolling through many items
- Accessibility consideration (easier to read)

**List Specifications**:
```
┌─────────────────────────────────────┐
│ ┌─────┬───────────────────────────┐ │
│ │[IMG]│ Gallon of Milk - 2%       │ │
│ │     │ Fresh 2% reduced fat milk │ │
│ │     │ Walgreens • 10 min        │ │
│ │     │ $5.74           [+ Add]   │ │
│ └─────┴───────────────────────────┘ │
│                                     │
│ ┌─────┬───────────────────────────┐ │
│ │[IMG]│ Large Eggs - Dozen        │ │
│ │     │ Grade A large eggs        │ │
│ │     │ Walgreens • 10 min        │ │
│ │     │ $4.59           [+ Add]   │ │
│ └─────┴───────────────────────────┘ │
└─────────────────────────────────────┘
```

**View Toggle**: Icon in top right (grid/list icons)

#### Recommendation: Default to Grid, Remember User Preference

**Implementation**:
- First-time users see grid (more engaging)
- Toggle button in top right corner
- Preference saved in user settings
- Same preference applies across venues

### 2.2 Search Functionality

**RECOMMENDATION: Smart Search with Progressive Disclosure**

#### Search Bar Design

**Position**: Persistent header, always visible
**Placeholder**: "Search milk, eggs, snacks..." (specific examples)
**Icon**: Magnifying glass left, microphone right
**Behavior**:
- Tapping opens keyboard immediately
- Shows recent searches below
- Displays search results in real-time (as user types)

#### Search Algorithm Priority

**Multi-factor ranking**:
1. **Exact Name Match** (highest priority)
   - "milk" → "Gallon of Milk - 2%"
2. **Partial Name Match**
   - "mil" → "Milk", "Military-grade batteries" (less relevant)
3. **Category Match**
   - "dairy" → All dairy items
4. **Tag Match**
   - "refrigerated" → Milk, eggs, cheese
5. **Description Match** (lowest priority)
   - "vitamin D" → Milk (if in description)

**Search Enhancements**:
- **Fuzzy matching**: "mlk" → "milk" suggestions
- **Autocorrect**: Common misspellings
- **Synonyms**: "soda" = "pop" = "soft drink"
- **Brand awareness**: "Advil" → Pain relievers

#### Voice Search

**Why Include Voice Search**:
- User's hands might be full
- Faster than typing on mobile
- Natural for shopping ("milk, bread, eggs")
- Accessibility benefit

**Implementation**:
- Microphone icon in search bar (right side)
- Press and hold to speak
- Shows speech-to-text in real-time
- Automatically executes search
- Falls back to text edit if misheard

#### Search Results Display

**Zero Results State**:
```
┌─────────────────────────────────────┐
│ No results for "organic kale"      │
│                                     │
│ Try:                                │
│ • "lettuce" or "salad"             │
│ • Browse "Grocery" category         │
│                                     │
│ Suggest this item to venue →       │
└─────────────────────────────────────┘
```

**Partial Results**:
- Show closest matches
- "Showing results for 'milk'" (if searched "mlik")
- Suggest alternative categories

#### Recent Searches

**Display**: Below search bar when focused
**Content**: Last 5 searches
**Behavior**: Tap to re-search instantly
**Clear**: X icon to remove individual or clear all

### 2.3 Filtering & Sorting

**RECOMMENDATION: Minimal Filters, Smart Defaults**

#### Why Minimal Filters

**Rationale**:
- User is in a hurry (at haircut)
- Too many options increase cognitive load
- Most users won't use complex filters
- Convenience store = limited inventory (not Amazon)
- Search + categories should cover 95% of needs

#### Filter Options (Collapsed by Default)

**Location in UI**: Filter icon in top bar, opens bottom sheet

**Available Filters**:

1. **Price Range** (Most useful)
   - Slider: $0 - $50+
   - Presets: Under $5, Under $10, Under $20
   - Shows count: "23 items under $10"

2. **Store/Source** (If multiple stores available)
   - Checkboxes: Walgreens, CVS, 7-Eleven
   - Useful for brand loyalty
   - Shows distance: "Walgreens (0.2 mi)"

3. **Shopping Time** (Unique to this use case)
   - Quick items: <10 min shopping time
   - Standard items: 10-20 min
   - All items
   - Rationale: User might be in a rush

4. **In Stock / Available**
   - Toggle: Hide unavailable items
   - Default: ON (don't show what you can't buy)

**Filters to AVOID**:
- ❌ Brand (too granular, search instead)
- ❌ Size (specified in item name)
- ❌ Rating (not applicable - staff shoppers)
- ❌ "Organic", "Gluten-free" etc (use search/tags)

#### Sorting Options

**Default Sort**: "Recommended"
- Algorithm: Popular items + quick shopping time + in stock
- Rationale: Show what converts best

**Available Sorts**:
1. **Recommended** (default)
2. **Price: Low to High**
3. **Price: High to Low**
4. **Fastest Shopping Time**
5. **Alphabetical**

**Sort Control**: Dropdown in top bar, next to filter icon

**Sort Persistence**: Remembers per session, resets to Recommended on new session

### 2.4 Pagination Strategy

**RECOMMENDATION: Infinite Scroll with Smart Loading**

#### Why Infinite Scroll

**Rationale**:
- Standard pattern for mobile shopping apps
- No cognitive load of clicking "Next"
- Natural gesture (scrolling)
- Maintains browsing flow
- Expected behavior (DoorDash, Instacart, Amazon all use it)

#### Implementation Details

**Initial Load**: 20 items
- **Rationale**: Enough to fill 3-4 screens, fast load time
- Shows variety without overwhelming
- Covers most common needs

**Progressive Load**: 10 items per trigger
- Triggers when user scrolls to 5 items from bottom
- Subtle loading indicator (spinner at bottom)
- Seamless insertion (no jarring UI changes)

**Performance Optimizations**:
- **Image lazy loading**: Only load images in viewport + 1 screen ahead
- **Virtualization**: Recycle list items (React Native FlatList)
- **Skeleton screens**: Show placeholder cards while loading
- **Cache**: Store loaded items in memory for session

#### Edge Cases

**End of Catalog**:
```
┌─────────────────────────────────────┐
│ [Last few items displayed]          │
│                                     │
│ ─── That's everything we have ───  │
│                                     │
│ Can't find what you need?           │
│ [Request an Item]                   │
└─────────────────────────────────────┘
```

**Slow Network**:
- Show skeleton cards immediately
- Display "Loading..." text after 2 seconds
- Timeout after 10 seconds with retry button
- Cache previous results for instant back navigation

**No Items Available**:
```
┌─────────────────────────────────────┐
│ 🏪 Store Not Available              │
│                                     │
│ The convenience store is currently  │
│ closed or unavailable.              │
│                                     │
│ Operating Hours:                    │
│ Mon-Fri: 8am - 8pm                 │
│ Sat-Sun: 9am - 6pm                 │
│                                     │
│ [Browse Other Venues]               │
└─────────────────────────────────────┘
```

#### Accessibility Considerations

- Screen reader announces "Loading more items"
- Focus management: Don't jump focus on load
- High contrast mode support for loading indicators
- Voice control: "Load more" command

---

## 3. Ordering Experience

### 3.1 Cart Management

**RECOMMENDATION: Persistent Cart with Smart Defaults**

#### Cart Design Philosophy

**Key Principles**:
1. **Always visible**: Cart icon in top right with badge count
2. **Instant feedback**: Add animations, haptic feedback
3. **Easy editing**: Modify quantities without leaving browse
4. **Smart persistence**: Save cart across app restarts
5. **Venue-aware**: Separate carts per venue or prompt to clear

#### Add to Cart Interaction

**Quick Add (From Browse Screen)**:
```
┌────────────┐
│  [IMAGE]   │
│  Milk 2%   │  ← Tap anywhere on card
│  $5.74     │
│  [+ Add]   │  ← Or tap this button specifically
└────────────┘
       ↓
┌────────────┐
│  [IMAGE]   │
│  Milk 2%   │
│  $5.74     │
│  [- 1 +]   │  ← Inline quantity selector
└────────────┘
```

**Interaction Details**:
- First tap: Adds 1 to cart, button changes to quantity selector
- Animated: Item image "flies" to cart icon (satisfying visual feedback)
- Haptic: Light tap feedback (iOS haptic engine)
- Cart badge: Updates with animation (+1 bounce)
- Toast notification: "Milk added to cart" (dismissible, 2 seconds)

**Quantity Adjustment**:
- Minus button: Decrements, at 0 removes from cart
- Plus button: Increments, max determined by item settings
- Number: Tappable, opens numpad for direct entry
- Long press minus: Removes item immediately (with confirmation)

#### Shopping Cart View

**Access**: Tap cart icon in top right (any screen)
**Display**: Full screen modal with bottom sheet option

**Cart Screen Layout**:
```
┌─────────────────────────────────────┐
│ ← Cart (3 items)            [Clear]│
├─────────────────────────────────────┤
│ Downtown Garage                     │
│ Delivery to: Vehicle (Space A-101)  │
├─────────────────────────────────────┤
│ ┌─────┬───────────────┬───────────┐ │
│ │[IMG]│ Milk 2%       │ [- 1 +]   │ │
│ │     │ Walgreens     │ $5.74     │ │
│ └─────┴───────────────┴───────────┘ │
│                                     │
│ ┌─────┬───────────────┬───────────┐ │
│ │[IMG]│ Eggs - Dozen  │ [- 2 +]   │ │
│ │     │ Walgreens     │ $9.18     │ │
│ └─────┴───────────────┴───────────┘ │
│                                     │
│ ┌─────┬───────────────┬───────────┐ │
│ │[IMG]│ Bread         │ [- 1 +]   │ │
│ │     │ Walgreens     │ $4.01     │ │
│ └─────┴───────────────┴───────────┘ │
├─────────────────────────────────────┤
│ Add more items                  [+] │
├─────────────────────────────────────┤
│ Subtotal:                    $18.93 │
│ Service Fee (15%):            $2.84 │
│ Tax (est.):                   $1.75 │
│ ─────────────────────────────────── │
│ Total:                        $23.52│
│                                     │
│ 🎁 You'll get 15 min free parking   │
│    (Worth $7.50)                    │
├─────────────────────────────────────┤
│ [Continue to Checkout]              │
└─────────────────────────────────────┘
```

**Cart Features**:

1. **Venue Context**: Shows which venue this cart is for
2. **Delivery Location**: Shows where items will be delivered
3. **Editable Items**: Inline quantity adjustment, no separate edit mode
4. **Add More**: Quick button to return to browse without losing cart
5. **Pricing Breakdown**: Transparent, real-time calculation
6. **Value Highlight**: Emphasize free parking benefit
7. **Minimum Order**: Warning if below minimum ("Add $3 more to checkout")

#### Cart Persistence Strategy

**Scenario 1: Same Venue, Same Session**
- Cart persists indefinitely
- User can leave app, come back hours later
- Associated with parking session ID

**Scenario 2: Different Venue**
- Prompt: "You have items for Downtown Garage. Start a new cart for City Center?"
- Options: "Keep Both" or "Clear Previous Cart"
- Default: Keep both, filter by active parking session

**Scenario 3: Session Expired**
- Cart persists but shows warning: "Your parking session has ended"
- Options: "Start New Session" or "Clear Cart"
- Items remain saved (user might want to re-park and order)

**Scenario 4: App Killed/Restarted**
- Cart saved to local storage (AsyncStorage)
- Loads automatically on app restart
- Validates items still available (could be out of stock)

#### Empty Cart States

**Empty Cart (Never Added)**:
```
┌─────────────────────────────────────┐
│ Your cart is empty                  │
│                                     │
│         🛒                          │
│                                     │
│ Start adding items to get them      │
│ delivered to your vehicle           │
│                                     │
│ [Browse Items]                      │
└─────────────────────────────────────┘
```

**Empty Cart (Cleared)**:
```
┌─────────────────────────────────────┐
│ Cart cleared                        │
│                                     │
│ Popular Items:                      │
│ ┌────────┐ ┌────────┐ ┌────────┐  │
│ │ Milk   │ │ Eggs   │ │ Bread  │  │
│ └────────┘ └────────┘ └────────┘  │
│                                     │
│ [Browse All Items]                  │
└─────────────────────────────────────┘
```

### 3.2 Checkout Flow

**RECOMMENDATION: Single-Page Checkout with Progressive Disclosure**

#### Checkout Philosophy

**Key Principles**:
1. **Minimize steps**: All on one screen, no multi-step wizard
2. **Smart defaults**: Pre-fill everything possible from parking session
3. **Clear expectations**: Show delivery time and cost upfront
4. **Easy editing**: Tap any field to modify
5. **Security**: Reuse payment method from parking (if possible)

#### Checkout Screen Design

```
┌─────────────────────────────────────┐
│ ← Checkout                          │
├─────────────────────────────────────┤
│ Order Summary (3 items)         [Edit]│
│ Milk, Eggs, Bread +more             │
│ $23.52 total                        │
├─────────────────────────────────────┤
│ 📍 Delivery Location                │
│ Vehicle: Blue Honda Accord (ABC123) │
│ Space: A-101                        │
│ [Change]                            │
├─────────────────────────────────────┤
│ 📝 Instructions (Optional)          │
│ [Tap to add special instructions]   │
│                                     │
│ Examples:                           │
│ • "Please place in trunk"          │
│ • "I prefer organic milk"          │
│ • "Get brand X if available"       │
├─────────────────────────────────────┤
│ ⏱️ Estimated Time                   │
│ Ready in 30-45 minutes              │
│                                     │
│ We'll notify you at each step       │
├─────────────────────────────────────┤
│ 💳 Payment                          │
│ •••• 4242 (from parking session)    │
│ [Use Different Card]                │
├─────────────────────────────────────┤
│ Price Breakdown:                    │
│ Items subtotal:           $18.93    │
│ Service fee (15%):         $2.84    │
│ Tax (8%):                  $1.75    │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│ Total:                    $23.52    │
│                                     │
│ 🎁 15 min free parking included     │
│    ($7.50 value)                    │
├─────────────────────────────────────┤
│ By placing order, you agree to      │
│ Terms of Service and Privacy Policy │
├─────────────────────────────────────┤
│ [Place Order - $23.52]              │
└─────────────────────────────────────┘
```

#### Checkout Fields & Smart Defaults

**1. Delivery Location**
- **Source**: Parking session vehicle info
- **Default**: "Vehicle: [Make] [Model] ([Plate]) - Space [Number]"
- **Alternatives**: "Front Desk Pickup", "Valet Station"
- **Editing**: Tap "Change" opens bottom sheet with options
- **Validation**: Must be associated with active parking session

**2. Special Instructions**
- **Optional**: Empty by default
- **Character limit**: 500 characters
- **Placeholder**: "Any special requests? (optional)"
- **Examples shown**: Common instructions to guide user
- **Use cases**:
  - Brand preferences: "Get Advil, not generic"
  - Delivery preferences: "Place in back seat"
  - Substitutions: "If out of 2%, get whole milk"

**3. Payment Method**
- **Default**: Reuse payment from parking session (if available)
- **Display**: Last 4 digits, card brand icon
- **Change**: "Use Different Card" opens payment sheet
- **Security**: Uses Stripe Payment Intent, funds authorized not captured
- **New Card**: Full payment entry if no previous payment

**4. Contact Information**
- **Auto-filled**: From parking session (email/phone)
- **Hidden**: Not shown in checkout (already collected)
- **Editable**: Link to "Update contact info" in case of error

#### Checkout Validation

**Pre-submit Checks**:
1. ✅ Cart not empty
2. ✅ Meets minimum order amount
3. ✅ Doesn't exceed maximum order amount
4. ✅ Active parking session exists
5. ✅ Venue convenience store is open (operating hours)
6. ✅ Payment method valid
7. ✅ All items still in stock

**Error States**:

**Below Minimum Order**:
```
┌─────────────────────────────────────┐
│ ⚠️ Minimum order is $5.00           │
│ Your cart: $3.50                    │
│ Add $1.50 more to checkout          │
│                                     │
│ [Add More Items]                    │
└─────────────────────────────────────┘
```

**Store Closed**:
```
┌─────────────────────────────────────┐
│ ⚠️ Store Currently Closed           │
│                                     │
│ Opens tomorrow at 8:00 AM           │
│                                     │
│ Your cart is saved. Come back later!│
│ [OK]                                │
└─────────────────────────────────────┘
```

**Item Out of Stock**:
```
┌─────────────────────────────────────┐
│ ⚠️ Some items are unavailable       │
│                                     │
│ • Milk 2% - Out of stock           │
│                                     │
│ Remove these items to continue?     │
│ [Remove] [Cancel]                   │
└─────────────────────────────────────┘
```

### 3.3 Payment Integration

**RECOMMENDATION: Seamless Payment with Authorization Hold**

#### Payment Strategy

**Use Stripe Payment Intent with Authorization Flow**:
1. **Authorization** (Checkout): Hold funds, don't capture
2. **Adjustment** (During Shopping): Update amount if needed
3. **Capture** (Delivery): Charge final amount
4. **Release** (Cancellation): Release hold if order cancelled

**Why This Approach**:
- Protects customer from overcharging
- Allows for substitutions and price changes
- Staff might find items are more/less expensive than listed
- Best practice for delivery/service businesses

#### Payment Method Collection

**Scenario 1: Reuse from Parking (Optimal)**
- If user paid for parking with card, reuse that payment method
- Stripe Customer ID stored from parking transaction
- Display: "•••• 4242 (from parking)"
- One-tap checkout: No re-entering card details
- **UX Win**: Reduces friction significantly

**Scenario 2: New Payment Method**
- User paying for parking with cash/other method
- Or user wants different card for convenience store
- Display: "Add payment method"
- Use Stripe Payment Element (optimized mobile input)
- Option to save for future orders

#### Payment Sheet Design (If New Card Needed)

```
┌─────────────────────────────────────┐
│ ← Add Payment Method                │
├─────────────────────────────────────┤
│ Card Number                         │
│ [1234 5678 9012 3456]               │
│                                     │
│ Expiry         CVC                  │
│ [MM/YY]        [123]                │
│                                     │
│ Billing ZIP                         │
│ [12345]                             │
│                                     │
│ ☑️ Save for future orders           │
├─────────────────────────────────────┤
│ [Add Card]                          │
└─────────────────────────────────────┘
```

**Stripe Elements**: Use pre-built, mobile-optimized components
**Validation**: Real-time, inline error messages
**Security**: PCI compliant, card details never touch your servers

#### Payment Confirmation

**After Placing Order**:
```
┌─────────────────────────────────────┐
│           Order Placed! ✅          │
│                                     │
│      Order #CS-1234                 │
│                                     │
│ We've authorized $23.52             │
│ on your card ending in 4242.        │
│                                     │
│ You'll only be charged the actual   │
│ amount after items are delivered.   │
│                                     │
│ [Track Order]                       │
└─────────────────────────────────────┘
```

**Key Messages**:
- Order number (for support/tracking)
- Authorization language (not "charged")
- Reassurance about final amount
- Clear next step (track order)

#### Payment Error Handling

**Declined Card**:
```
┌─────────────────────────────────────┐
│ ⚠️ Payment Declined                 │
│                                     │
│ Your card was declined by your bank.│
│                                     │
│ Please try a different card or      │
│ contact your bank for details.      │
│                                     │
│ [Try Different Card] [Cancel]       │
└─────────────────────────────────────┘
```

**Insufficient Funds**:
```
┌─────────────────────────────────────┐
│ ⚠️ Insufficient Funds               │
│                                     │
│ Your card doesn't have enough       │
│ available credit for this order.    │
│                                     │
│ [Try Different Card] [Cancel]       │
└─────────────────────────────────────┘
```

**Network Error**:
```
┌─────────────────────────────────────┐
│ ⚠️ Connection Error                 │
│                                     │
│ We couldn't process your payment.   │
│ Please check your connection and    │
│ try again.                          │
│                                     │
│ [Retry] [Cancel]                    │
└─────────────────────────────────────┘
```

### 3.4 Special Instructions / Delivery Notes

**RECOMMENDATION: Flexible Instructions with Smart Suggestions**

#### Instruction Types

**1. Delivery Instructions** (How/where to deliver)
- Pre-filled: Vehicle info from parking session
- Editable: "Place in trunk", "Meet at front desk"
- Default: "Deliver to [Vehicle] in Space [Number]"

**2. Special Instructions** (Shopping preferences)
- Free-form text field
- Character limit: 500
- Examples/suggestions shown
- Optional

#### Smart Instruction Suggestions

**Display**: Chips below instruction field that populate on tap

**Suggestion Categories**:

**Delivery Preferences**:
- "Place in trunk"
- "Place on front seat"
- "Meet me at vehicle"
- "Leave at front desk"

**Brand Preferences**:
- "Name brand only"
- "Generic brands OK"
- "Store brand preferred"

**Substitution Guidance**:
- "Call if item unavailable"
- "No substitutions please"
- "Similar items OK"

**Special Requests**:
- "Check expiration dates"
- "Choose ripest produce"
- "Extra bags please"

**Implementation**:
```
┌─────────────────────────────────────┐
│ Special Instructions (Optional)     │
│ ┌─────────────────────────────────┐ │
│ │ [Tap to add instructions]       │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Common requests:                    │
│ [Place in trunk] [Name brand only]  │
│ [No substitutions] [Call if out]    │
│                                     │
│ 123 characters remaining            │
└─────────────────────────────────────┘
```

**Tap Chip**: Adds text to field (doesn't replace, appends)
**Multiple Chips**: Can select multiple, separated by commas
**Custom Text**: User can always type freely

#### Instructions Display (Order Tracking)

**Staff View**: Instructions prominent, highlighted
**Customer View**: Their instructions echoed back for confirmation

```
┌─────────────────────────────────────┐
│ Your Instructions:                  │
│ "Place in trunk. Name brand milk    │
│  only. Call if unavailable."        │
│                                     │
│ [Edit Instructions]                 │
└─────────────────────────────────────┘
```

---

## 4. Order Tracking & Status

### 4.1 Status Definitions & User-Facing Language

**RECOMMENDATION: Clear, Human Language for Each Status**

#### Status Mapping (Backend → User-Facing)

| Backend Status | User-Facing Label | Description | Estimated Time |
|---------------|-------------------|-------------|----------------|
| `pending` | "Confirming Order" | We're reviewing your order | ~2 min |
| `confirmed` | "Order Confirmed" | Staff accepted your order | ~5 min |
| `shopping` | "Shopping Now" | Staff is at the store | ~15-20 min |
| `purchased` | "Items Purchased" | Staff is heading back | ~5 min |
| `stored` | "Items Secured" | Items are safely stored | ~10 min |
| `ready` | "Ready for Delivery" | Items ready to deliver | ~5 min |
| `delivered` | "Delivered" | Items delivered to you | Complete |
| `completed` | "Order Complete" | Transaction finished | Complete |
| `cancelled` | "Order Cancelled" | Order was cancelled | N/A |

**Why Use Human Language**:
- "Shopping Now" more engaging than "In Progress"
- Builds trust with specific actions
- Manages expectations with time estimates
- Reduces anxiety by showing progress

### 4.2 Visual Progress Tracker

**RECOMMENDATION: Linear Progress with Active State Highlights**

#### Progress Tracker Design

```
┌─────────────────────────────────────┐
│ Order #CS-1234                      │
│ Downtown Garage                     │
├─────────────────────────────────────┤
│                                     │
│ ✅ Order Confirmed                  │
│ │  2:15 PM                          │
│ │                                   │
│ ✅ Shopping Now                     │
│ │  2:18 PM                          │
│ │  Staff is at Walgreens            │
│ │                                   │
│ 🔵 Items Purchased                  │ ← Current
│ │  2:34 PM (just now)               │
│ │  Heading back to venue            │
│ │                                   │
│ ⚪ Items Secured                    │
│ │  Est. 5 min                       │
│ │                                   │
│ ⚪ Ready for Delivery                │
│ │  Est. 10 min                      │
│ │                                   │
│ ⚪ Delivered                         │
│    Est. 15 min                      │
│                                     │
└─────────────────────────────────────┘
```

**Visual Elements**:
- **Checkmark (✅)**: Completed steps (green)
- **Filled Circle (🔵)**: Current step (blue, pulsing animation)
- **Empty Circle (⚪)**: Future steps (gray)
- **Line**: Connects steps vertically
- **Timestamps**: Actual time for completed, estimate for upcoming
- **Contextual Note**: Extra info for current step

**Animation**:
- When status changes, current circle pulses
- Previous step gets checkmark with subtle bounce
- Scroll to current step automatically

#### Compact Progress Bar (Collapsed View)

**For Main Orders List**:
```
┌─────────────────────────────────────┐
│ Order #CS-1234               $23.52 │
│ Milk, Eggs, Bread                   │
│ ▓▓▓▓▓▓▓▓▓░░░░░░░░ 60% Shopping Now  │
│ Est. 15 min remaining               │
└─────────────────────────────────────┘
```

**Percentage Mapping**:
- Confirmed: 20%
- Shopping: 40%
- Purchased: 60%
- Secured: 80%
- Delivered: 100%

### 4.3 Push Notifications Strategy

**RECOMMENDATION: Timely, Actionable Notifications**

#### Notification Principles

1. **Critical only**: Don't spam, only important status changes
2. **Actionable**: Include quick actions where possible
3. **Contextual**: Show relevant info in notification
4. **Respectful**: Don't notify between 10 PM - 8 AM unless urgent
5. **Personalized**: Use item names, not just "order"

#### Notification Schedule

**1. Order Confirmed** (High Priority)
```
🛒 TruFan Convenience

Order Confirmed!
Staff will start shopping for your items in ~5 minutes.

Milk, Eggs, Bread
Order #CS-1234

[View Order]
```

**Timing**: Immediately after staff accepts
**Tap Action**: Opens order detail screen
**Sound**: Default notification sound

**2. Shopping Started** (Medium Priority)
```
🛒 TruFan Convenience

Shopping Now at Walgreens
Your items should be ready in ~20 minutes.

Order #CS-1234

[Track Progress]
```

**Timing**: When staff marks "shopping_started"
**Tap Action**: Opens order tracking screen
**Sound**: Subtle notification sound

**3. Items Purchased** (Medium Priority)
```
🛒 TruFan Convenience

Items Purchased!
Staff is heading back with your items.

Order #CS-1234 • Ready in ~10 min

[Track Order]
```

**Timing**: When staff completes shopping
**Tap Action**: Opens order tracking
**Sound**: Subtle notification sound

**4. Ready for Delivery** (High Priority)
```
🛒 TruFan Convenience

Items Ready!
Staff will deliver to your vehicle shortly.

Blue Honda Accord • Space A-101

[View Details]
```

**Timing**: When staff marks ready
**Tap Action**: Opens order detail with delivery info
**Sound**: Default notification sound

**5. Delivered** (High Priority)
```
🛒 TruFan Convenience

Delivered! ✅
Your items have been delivered to your vehicle.

Enjoy! Please rate your experience.

[Rate Order]
```

**Timing**: When staff confirms delivery
**Tap Action**: Opens rating screen
**Sound**: Success/completion sound
**Rich Action**: "Rate 5 stars" button in notification

**6. Issue / Delay** (Critical Priority)
```
🛒 TruFan Convenience

Update on Your Order
Some items are unavailable. Staff will contact you.

Order #CS-1234

[View Details] [Contact Staff]
```

**Timing**: If staff marks items as unavailable
**Tap Action**: Opens order detail with issue explanation
**Sound**: Alert sound
**Rich Actions**: Quick contact button

#### Notifications NOT to Send

- ❌ "Items stored" - too granular, user doesn't care
- ❌ "Staff assigned" - internal detail
- ❌ Marketing/promotional - keep it transactional
- ❌ Multiple for same status - wait for meaningful change

#### Notification Preferences (Settings)

**Allow Users to Control**:
```
┌─────────────────────────────────────┐
│ Notification Settings               │
├─────────────────────────────────────┤
│ Order Updates               [ON]    │
│ Notify me about order status        │
│                                     │
│ Delivery Ready              [ON]    │
│ When items are ready to deliver     │
│                                     │
│ Issues & Delays             [ON]    │
│ If there are problems               │
│                                     │
│ Quiet Hours                         │
│ 10:00 PM - 8:00 AM          [ON]    │
└─────────────────────────────────────┘
```

**Default**: All ON (user must opt-out)
**Quiet Hours**: Suggested but not forced

### 4.4 Real-Time Updates Approach

**RECOMMENDATION: Polling with WebSocket Fallback**

#### Update Strategy

**Primary: Intelligent Polling**
- Poll every 30 seconds when order is active
- Poll every 60 seconds when order is "secured" or "ready"
- Stop polling when order is delivered/completed
- Resume polling if app comes to foreground

**Why Polling**:
- Simpler implementation than WebSockets
- More reliable on mobile (no connection persistence issues)
- Less battery drain than constant WebSocket connection
- 30-second delay is acceptable for this use case

**Fallback: WebSockets** (Future Enhancement)
- For instant updates if desired
- Use Socket.io or native WebSockets
- Implement reconnection logic
- More complex but better UX

**Push Notifications: Critical Updates Only**
- Don't rely on polling for critical updates
- Push notification triggers immediate poll
- Ensures user sees update even if app is backgrounded

#### Update Indicators

**Subtle Loading States**:
```
┌─────────────────────────────────────┐
│ Order #CS-1234                 ↻    │ ← Refresh icon
│ Shopping Now                        │
│ Last updated: 1 minute ago          │
└─────────────────────────────────────┘
```

**Pull to Refresh**:
- Standard gesture on order detail and order list
- Triggers immediate poll
- Shows native refresh spinner
- Haptic feedback on release

**Auto-Refresh Indicator**:
- Small pulsing dot or text: "Checking for updates..."
- Only shown during actual network request
- Dismisses immediately after response

### 4.5 Delivery Confirmation

**RECOMMENDATION: Photo Proof + Easy Rating**

#### Delivery Flow

**Step 1: Staff Confirms Delivery**
- Staff taps "Deliver" in their app
- Takes photo of items in vehicle (optional but encouraged)
- Adds delivery note if needed

**Step 2: Customer Receives Notification**
```
🛒 TruFan Convenience

Delivered! ✅
Your items have been delivered to your vehicle.

[View Delivery Photo] [Rate Experience]
```

**Step 3: Customer Views Confirmation**
```
┌─────────────────────────────────────┐
│ Order Delivered ✅                  │
│                                     │
│ Delivered to:                       │
│ Blue Honda Accord, Space A-101      │
│                                     │
│ Delivery Photo:                     │
│ ┌─────────────────────────────────┐ │
│ │                                 │ │
│ │  [Photo of items in trunk]      │ │
│ │                                 │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Items:                              │
│ ✓ Milk 2%                           │
│ ✓ Eggs - Dozen                      │
│ ✓ Bread                             │
│                                     │
│ Receipt: [View Receipt Photo]       │
│                                     │
│ Final Charge: $23.52                │
│ (Authorized amount: $23.52)         │
│                                     │
│ How was your experience?            │
│ ⭐⭐⭐⭐⭐                              │
│                                     │
│ [Submit Rating]                     │
└─────────────────────────────────────┘
```

**Delivery Confirmation Features**:
1. **Photo Proof**: Reassures customer items are delivered
2. **Location Confirmation**: Echo back where delivered
3. **Item Checklist**: All items marked as delivered
4. **Receipt Access**: Transparency on actual prices
5. **Final Charge**: Show final amount charged vs. authorized
6. **Immediate Rating**: Capture feedback while fresh

#### Delivery Issues

**Report Issue Flow**:
```
┌─────────────────────────────────────┐
│ Report an Issue                     │
├─────────────────────────────────────┤
│ What's wrong with your order?       │
│                                     │
│ ⚪ Items missing                    │
│ ⚪ Wrong items delivered            │
│ ⚪ Items damaged                    │
│ ⚪ Can't find items in vehicle      │
│ ⚪ Other issue                      │
│                                     │
│ Additional details:                 │
│ ┌─────────────────────────────────┐ │
│ │ [Describe the issue]            │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Submit Issue]                      │
└─────────────────────────────────────┘
```

**Issue Resolution**:
- Automatically notifies venue staff
- Creates support ticket
- Option for immediate refund (partial or full)
- Follow-up from support team

---

## 5. Parking Integration

### 5.1 Free Parking Time Benefit

**RECOMMENDATION: Make It Impossible to Miss**

#### Why This Matters

**Key Insight**: Free parking time is THE compelling reason to use this feature.
- Haircut costs $30, user gets $7.50 in free parking
- Effectively reduces net cost of items
- Creates viral word-of-mouth: "I got free parking!"

#### Highlighting the Benefit

**Location 1: Browse Screen (Banner)**
```
┌─────────────────────────────────────┐
│ 🎁 Get 15 minutes FREE parking      │
│    with any order                   │
└─────────────────────────────────────┘
```

**Location 2: Cart Screen (Prominent Box)**
```
┌─────────────────────────────────────┐
│ 💰 You're Saving:                   │
│                                     │
│ 15 min free parking:      $7.50 ✅  │
│ (Downtown Garage rate)              │
│                                     │
│ Your order total:         $23.52    │
│ Net cost:                 $16.02    │
└─────────────────────────────────────┘
```

**Location 3: Checkout Screen (Highlighted)**
```
┌─────────────────────────────────────┐
│ Order Total:              $23.52    │
│                                     │
│ 🎁 BONUS: 15 min FREE parking       │
│    Worth $7.50!                     │
│    Your parking extended to 3:45 PM │
└─────────────────────────────────────┘
```

**Location 4: Confirmation Screen (Celebrate)**
```
┌─────────────────────────────────────┐
│ Order Placed! ✅                    │
│                                     │
│ 🎉 You got 15 min free parking!     │
│                                     │
│ Your parking now expires at:        │
│ 3:45 PM (was 3:30 PM)              │
│                                     │
│ Enjoy your extra time!              │
└─────────────────────────────────────┘
```

**Location 5: Push Notification**
```
🎁 TruFan Convenience

Bonus! 15 min free parking added
Your parking now expires at 3:45 PM

Order #CS-1234
```

#### Calculating the Value

**Show in Real-Time**:
```javascript
// Example calculation
parkingRate = venue.hourlyRate // e.g., $30/hour
freeMinutes = 15
freeValue = (parkingRate / 60) * freeMinutes // $7.50

display = `15 min free parking (Worth $${freeValue})`
```

**Dynamic Display**:
- Different venues have different rates
- Show actual dollar value based on venue
- Higher-priced venues = more impressive savings
- Makes benefit tangible and comparable

### 5.2 Session Management

**RECOMMENDATION: Intelligent Session Extension with Clear Communication**

#### Automatic Extension Logic

**Trigger**: When order is placed and payment authorized
**Amount**: Venue's configured `default_complimentary_parking_minutes` (typically 15 min)
**Timing**: Applied immediately, not when delivered

**Extension Rules**:

1. **Active Session**: Add minutes to current expiration
   - Current expires: 3:30 PM
   - Order placed: 2:45 PM
   - New expiration: 3:45 PM (added 15 min)

2. **Expiring Soon Session**: Add minutes, send notification
   - Current expires: 2:50 PM (5 min left)
   - Order placed: 2:45 PM
   - New expiration: 3:05 PM
   - Alert: "Great timing! Your parking was about to expire"

3. **Multiple Orders**: Stack extensions
   - First order: +15 min
   - Second order: +15 min more
   - Total: +30 min from original expiration

4. **Maximum Cap**: Don't exceed venue's max session length
   - If max session is 4 hours, cap total at 4 hours
   - Show: "Extended to maximum allowed time (4 hours)"

#### Extension Confirmation UI

**In-App Notification (Toast)**:
```
┌─────────────────────────────────────┐
│ 🎉 Parking Extended!                │
│ Your session now expires at 3:45 PM │
│ (+15 minutes free)                  │
└─────────────────────────────────────┘
```

**Parking Session Screen Update**:
```
┌─────────────────────────────────────┐
│ 🅿️ Downtown Garage - Space A-101   │
│                                     │
│ Expires: 3:45 PM                    │
│ (Extended by 15 min 🎁)             │
│                                     │
│ Time remaining: 1h 38m              │
└─────────────────────────────────────┘
```

**Extension History** (Detail View):
```
┌─────────────────────────────────────┐
│ Parking History                     │
│                                     │
│ Started: 2:00 PM (2 hours booked)   │
│ Original expiration: 4:00 PM        │
│                                     │
│ Extensions:                         │
│ • 2:45 PM: +15 min (Order CS-1234) ✅│
│ • 3:20 PM: +15 min (Order CS-1235) ✅│
│                                     │
│ Current expiration: 4:30 PM         │
│ Total free time: 30 minutes ($15!)  │
└─────────────────────────────────────┘
```

#### What If Parking Expires During Order?

**Scenario**: User orders at 2:55 PM, parking expires at 3:00 PM, order delivered at 3:30 PM

**Handling**:

**Option 1: Extend Immediately (Recommended)**
- When order is placed, extend by 15 minutes automatically
- 3:00 PM → 3:15 PM
- If order takes longer, send "extend parking?" prompt
- User can extend further via standard flow

**Option 2: Extend Based on Estimated Delivery**
- Calculate estimated delivery time (e.g., 35 minutes)
- Extend parking to cover delivery time + buffer (45 minutes)
- More generous but could be abused

**Recommended: Option 1 + Proactive Prompt**

**Prompt When Order Running Long**:
```
┌─────────────────────────────────────┐
│ ⏰ Parking Expiring Soon            │
│                                     │
│ Your parking expires in 5 minutes,  │
│ but your order is still being       │
│ prepared.                           │
│                                     │
│ Extend parking to ensure delivery?  │
│                                     │
│ [Add 30 min - $15] [Add 1 hr - $30]│
│ [I'm leaving]                       │
└─────────────────────────────────────┘
```

**Timing**: Send notification when:
- Parking expires in 10 minutes AND
- Order status is NOT delivered

**Smart Defaults**:
- Suggest extension length based on order status
- If "shopping", suggest 30 min
- If "purchased", suggest 15 min

#### Multiple Parking Sessions

**Scenario**: User ends parking session but order is still active

**Handling**:

**Warning on Session End**:
```
┌─────────────────────────────────────┐
│ ⚠️ Active Order                     │
│                                     │
│ You have an active convenience      │
│ order that hasn't been delivered.   │
│                                     │
│ Order #CS-1234 - Shopping Now       │
│                                     │
│ Ending parking now means you'll     │
│ need to arrange pickup separately.  │
│                                     │
│ [Keep Parking] [End & Pickup Later]│
└─────────────────────────────────────┘
```

**If User Ends Anyway**:
- Order continues (not cancelled)
- Delivery method changes from "Vehicle" to "Front Desk Pickup"
- Send notification: "Your items will be held at front desk"
- Staff notified of delivery method change

### 5.3 Location/Vehicle Information Handling

**RECOMMENDATION: Seamless Data Reuse with Easy Editing**

#### Data Flow

**Source**: Parking session creation
**Stored**: In parking session record
**Reused**: In convenience order automatically
**Editable**: User can override if needed

#### Vehicle Information Used

**From Parking Session**:
- License plate (primary identifier)
- Make and model (helps staff find vehicle)
- Color (visual confirmation)
- Space number (exact location)
- Contact info (email/phone)

**Display in Convenience Order**:
```
┌─────────────────────────────────────┐
│ Delivery Location                   │
│                                     │
│ 🚗 Blue Honda Accord                │
│    License: ABC123                  │
│    Space: A-101 (Level 2)           │
│                                     │
│ From your parking session           │
│ [Edit Delivery Details]             │
└─────────────────────────────────────┘
```

#### Editing Delivery Location

**Use Cases for Editing**:
1. User moved vehicles (valet service)
2. User wants pickup at different location
3. Space number changed
4. Delivery to companion's vehicle

**Edit Flow**:
```
┌─────────────────────────────────────┐
│ Edit Delivery Location              │
├─────────────────────────────────────┤
│ Delivery Method:                    │
│ ⚫ My Vehicle (ABC123)               │
│ ⚪ Front Desk Pickup                 │
│ ⚪ Different Vehicle                 │
│                                     │
│ [If "My Vehicle" selected:]         │
│                                     │
│ Current Space: A-101                │
│ [Change Space]                      │
│                                     │
│ Additional Instructions:            │
│ ┌─────────────────────────────────┐ │
│ │ [e.g., "I moved to Space B-205"]│ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Save Changes]                      │
└─────────────────────────────────────┘
```

#### Vehicle Verification (For Staff)

**Staff View Shows**:
- Large photo of vehicle (if available from parking session)
- License plate in large text
- Make, model, color
- Space number with floor/level
- Map/layout view showing space location

**Reduces Errors**:
- Staff can visually confirm vehicle
- Less risk of wrong delivery
- Customer feels confident (saw verification)

#### Privacy Considerations

**What to Show/Hide**:
- ✅ Show: License plate, space number (needed for delivery)
- ✅ Show: Make, model, color (helps identification)
- ❌ Hide: Full name in staff app (use first name only)
- ❌ Hide: Full phone/email (show masked: •••-•••-1234)
- ✅ Show: Photo of vehicle (if user uploaded during parking)

**Data Retention**:
- Order data stored for 90 days
- Vehicle info associated with order only
- After 90 days, anonymize or delete
- GDPR/CCPA compliant

---

## 6. Edge Cases & Error States

### 6.1 Store Closed

**Scenario**: User tries to order when convenience store is closed

#### Prevention (Proactive)

**Before Checkout**:
```
┌─────────────────────────────────────┐
│ 🕐 Store Currently Closed           │
│                                     │
│ The convenience store is closed but │
│ will reopen tomorrow at 8:00 AM.    │
│                                     │
│ Your cart is saved. Come back when  │
│ the store is open!                  │
│                                     │
│ Operating Hours:                    │
│ Mon-Fri: 8:00 AM - 8:00 PM         │
│ Sat-Sun: 9:00 AM - 6:00 PM         │
│                                     │
│ [Set Reminder] [OK]                 │
└─────────────────────────────────────┘
```

**During Browse**:
- Banner at top: "Store opens at 8:00 AM tomorrow"
- Grayed-out "Add to Cart" buttons
- Items still visible for browsing
- Cart persists but checkout disabled

#### Opening Hours Display

**Show Hours Everywhere**:
- Store browse screen header
- Venue detail screen (before parking)
- Cart screen
- Checkout screen (if attempting)

**Smart Messaging**:
- "Opens in 2 hours" (if today)
- "Opens tomorrow at 8:00 AM" (if closed for the day)
- "Closed on Sundays" (if day is closed)
- "Currently Open • Closes at 8:00 PM" (if open now)

#### Edge Case: Order Placed Just Before Closing

**Scenario**: User orders at 7:55 PM, store closes at 8:00 PM

**Handling**:
1. **Warning Before Checkout**:
```
┌─────────────────────────────────────┐
│ ⚠️ Store Closing Soon               │
│                                     │
│ The store closes in 5 minutes.      │
│ Orders may not be fulfilled tonight.│
│                                     │
│ Continue with order?                │
│ [Yes, Order Now] [Cancel]           │
└─────────────────────────────────────┘
```

2. **If Accepted**: Order placed but marked for next day
3. **Staff Decision**: Staff can accept or defer to next day
4. **Customer Notified**: "Your order will be ready tomorrow at 9:00 AM"

### 6.2 Items Out of Stock

**Scenario**: Staff discovers items aren't available while shopping

#### Staff-Side Handling

**Staff marks item as unavailable**:
- Select item in order
- Choose: "Out of Stock", "Wrong Price", or "Substituted"
- Add note (optional): "Store is out of 2% milk"
- Take photo of empty shelf (optional, builds trust)

#### Customer Notification

**Real-Time Alert**:
```
┌─────────────────────────────────────┐
│ 🔔 Order Update                     │
│                                     │
│ Some items aren't available:        │
│                                     │
│ ❌ Milk 2% - Out of stock           │
│                                     │
│ Staff notes:                        │
│ "Store is out of 2% milk. Would you │
│  like whole milk or 1% instead?"    │
│                                     │
│ [Accept Substitution] [Remove Item] │
│ [Message Staff]                     │
└─────────────────────────────────────┘
```

**Options**:
1. **Accept Substitution**: Staff gets suggested alternative
2. **Remove Item**: Adjust order total, refund difference
3. **Message Staff**: Quick chat to discuss options

#### Automatic Price Adjustment

**If Item Removed**:
```
Original Order:
- Milk 2%: $5.74
- Eggs: $4.59
- Bread: $4.01
Subtotal: $14.34
Service Fee (15%): $2.15
Total: $16.49

Updated Order:
- Eggs: $4.59
- Bread: $4.01
Subtotal: $8.60 ❌ Below minimum order!
```

**Below Minimum Handling**:
```
┌─────────────────────────────────────┐
│ ⚠️ Order Below Minimum              │
│                                     │
│ After removing unavailable item,    │
│ your order is below the $10 minimum.│
│                                     │
│ Current total: $8.60                │
│ Need: $1.40 more                    │
│                                     │
│ [Add Items] [Cancel Order]          │
└─────────────────────────────────────┘
```

**Options**:
1. Let user add more items quickly
2. Cancel order and full refund
3. Offer popular low-cost add-ons (candy, drinks)

#### Substitution Preferences (Proactive)

**During Checkout (Optional)**:
```
┌─────────────────────────────────────┐
│ If items are unavailable:           │
│                                     │
│ ⚫ Contact me for substitutions      │
│ ⚪ Staff can choose similar items    │
│ ⚪ Remove unavailable items          │
│ ⚪ Cancel entire order               │
└─────────────────────────────────────┘
```

**Smart Default**: "Contact me" - gives user control

### 6.3 Payment Failures

**Scenario**: Payment authorization or capture fails

#### Authorization Failure (At Checkout)

**Cause**: Card declined, insufficient funds, expired card

**Immediate Error**:
```
┌─────────────────────────────────────┐
│ ❌ Payment Failed                   │
│                                     │
│ Your card ending in 4242 was        │
│ declined.                           │
│                                     │
│ Reason: Insufficient funds          │
│                                     │
│ Your order has not been placed.     │
│                                     │
│ [Try Different Card] [Cancel]       │
└─────────────────────────────────────┘
```

**Helpful Actions**:
- Link to "Why was my card declined?" help article
- Suggest trying different card
- Show alternative payment methods (Apple Pay, etc.)
- Don't lose cart contents

#### Capture Failure (At Delivery)

**Cause**: Card expired, authorization hold released, card cancelled

**More Serious**: Staff already shopped, items purchased

**Handling**:
1. **Attempt Capture**: When marking "delivered"
2. **If Fails**: Alert venue staff and customer immediately
3. **Customer Notification**:
```
┌─────────────────────────────────────┐
│ ⚠️ Payment Issue                    │
│                                     │
│ We couldn't charge your card for    │
│ your delivered order.               │
│                                     │
│ Order #CS-1234 - $23.52            │
│                                     │
│ Please update your payment method   │
│ to complete your order.             │
│                                     │
│ [Update Payment Method]             │
└─────────────────────────────────────┘
```

4. **Venue Staff Notification**: Hold items until payment resolved
5. **Grace Period**: 24 hours to update payment
6. **Escalation**: After 24 hours, charge on file or collections

#### Payment Retry Logic

**Automatic Retries**:
- Retry capture 3 times with exponential backoff
- 5 minutes, 15 minutes, 30 minutes
- Only for temporary failures (network issues)
- Not for permanent failures (insufficient funds)

**Manual Retry**:
- User can manually retry from order detail screen
- "Retry Payment" button
- Shows reason for previous failure

### 6.4 Delivery Issues

**Scenario**: Problems with final delivery to customer

#### Issue Types & Resolutions

**Issue 1: Can't Find Items in Vehicle**

**Customer Report**:
```
┌─────────────────────────────────────┐
│ Issue: Can't find items             │
│                                     │
│ The order shows delivered, but I    │
│ don't see items in my vehicle.      │
│                                     │
│ [View Delivery Photo]               │
│ [Contact Staff] [Report Missing]    │
└─────────────────────────────────────┘
```

**Resolution Steps**:
1. Show delivery photo (if available)
2. Contact venue staff immediately
3. Staff checks if items in wrong vehicle
4. Re-deliver or refund within 15 minutes

**Issue 2: Wrong Items Delivered**

**Customer Report**:
```
┌─────────────────────────────────────┐
│ Issue: Wrong items                  │
│                                     │
│ Which items are wrong?              │
│                                     │
│ ☑️ Milk 2% (received whole milk)    │
│ ☑️ Bread (received wrong brand)     │
│ ☐ Eggs (correct)                    │
│                                     │
│ [Submit Issue]                      │
└─────────────────────────────────────┘
```

**Resolution**:
1. Partial refund for incorrect items immediately
2. Option to re-shop for correct items (if time allows)
3. Apply credit to next order
4. Apology message from venue

**Issue 3: Items Damaged/Spoiled**

**Customer Report**:
```
┌─────────────────────────────────────┐
│ Issue: Damaged items                │
│                                     │
│ Please describe the issue:          │
│ ┌─────────────────────────────────┐ │
│ │ Eggs are cracked, milk is warm  │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Add photo: [📷 Take Photo]          │
│                                     │
│ [Submit Issue]                      │
└─────────────────────────────────────┘
```

**Resolution**:
1. Request photo proof
2. Automatic full refund (no questions for first issue)
3. Offer immediate re-shopping (if still available)
4. Venue reviews staff handling for improvement

**Issue 4: Vehicle Changed/Moved**

**Scenario**: User moved vehicle after order, staff can't find it

**Proactive Prevention**:
- Notification when order is "ready": "Confirm your vehicle location"
- User can update space number
- Alert staff to location change

**Reactive Handling**:
- Staff marks "can't locate vehicle"
- Customer receives notification: "Where's your vehicle?"
- Customer updates location
- Staff re-attempts delivery

#### Universal Issue Resolution Flow

**Every Issue Includes**:
1. **Apology**: "We're sorry for the inconvenience"
2. **Immediate Action**: Refund, re-delivery, or credit
3. **Compensation**: 10-20% credit on next order
4. **Follow-Up**: "How did we handle your issue?" survey
5. **Root Cause**: Venue reviews incident, improves process

**Refund Speed**:
- Approved refunds processed immediately (not 3-5 days)
- Shows in app: "Refunded: $5.74 • Returns to card in 3-5 days"
- Builds trust with instant resolution

#### Staff Training Implications

**Preventing Delivery Issues**:
- Photo required for all deliveries
- Double-check license plate before delivery
- Confirm space number on arrival
- Knock on window if customer present
- Clear notes on delivery location in staff app

**UX Consideration**: Make it easy for staff to do the right thing
- Simple photo upload (one tap from delivery screen)
- Auto-fill delivery notes from customer instructions
- Clear vehicle identification in staff app

---

## Implementation Recommendations

### Phase 1: MVP (Weeks 1-4)

**Core Features**:
1. ✅ Browse items (grid view, search, categories)
2. ✅ Add to cart (basic cart management)
3. ✅ Checkout (reuse parking payment)
4. ✅ Order tracking (basic status updates, polling)
5. ✅ Push notifications (critical statuses only)
6. ✅ Parking integration (auto-extend on order)

**Simplified Edge Cases**:
- Store closed: Prevent checkout, show hours
- Out of stock: Staff removes, customer gets notification
- Payment failure: Standard error, retry flow
- Delivery issues: Basic "Report Issue" form

**Success Metrics**:
- Order completion rate >70%
- Average fulfillment time <40 min
- Customer satisfaction >4.0/5.0
- Repeat order rate >20%

### Phase 2: Enhancements (Weeks 5-8)

**UX Improvements**:
1. ✅ Voice search
2. ✅ List view toggle
3. ✅ Advanced filtering
4. ✅ Delivery photo proof
5. ✅ Real-time chat with staff
6. ✅ Substitution preferences

**Edge Case Refinements**:
- Smart out-of-stock handling (suggestions)
- Proactive parking expiration warnings
- Intelligent retry logic for payments

### Phase 3: Optimization (Weeks 9-12)

**Advanced Features**:
1. ✅ Personalized recommendations
2. ✅ Favorites and quick reorder
3. ✅ WebSocket real-time updates
4. ✅ Gamification (points, badges)
5. ✅ Venue rating system
6. ✅ Social sharing

**Analytics & Testing**:
- A/B test cart vs. checkout flow
- Optimize search algorithm
- Refine notification timing
- Improve parking time messaging

---

## Success Criteria

### User Experience Metrics

**Efficiency**:
- Search to checkout: <2 minutes
- Browse to checkout: <3 minutes
- Order to delivery: <40 minutes average

**Satisfaction**:
- Post-order rating: >4.5/5.0
- Net Promoter Score (NPS): >50
- Issue resolution satisfaction: >90%

**Engagement**:
- Return order rate: >30%
- Cart abandonment rate: <40%
- Push notification opt-in: >80%

### Business Metrics

**Conversion**:
- Browse-to-order: >15%
- Cart-to-checkout: >70%
- Order completion: >90%

**Revenue**:
- Average order value: >$25
- Orders per active parking session: >20%
- Revenue per parking session increase: >15%

**Operational**:
- Fulfillment success rate: >95%
- Refund rate: <5%
- Staff fulfillment time: <30 min average

---

## Conclusion

The TruFan convenience store feature has massive potential to transform parking from a commodity into a value-added service. The key to success is **removing friction at every step** while **highlighting the parking time benefit**.

**Remember the User**:
- They're at a haircut, busy, distracted
- They just realized they need something
- They want it to be effortless
- They love getting free stuff (parking time)

**Design Principles**:
1. **Make it obvious**: Convenience store highly visible during parking
2. **Make it fast**: One-tap ordering, minimal steps
3. **Make it trustworthy**: Photos, updates, transparent pricing
4. **Make it rewarding**: Free parking time prominently displayed
5. **Make it forgiving**: Easy issue resolution, friendly errors

**The Experience Should Feel Like**:
- Texting a friend to grab you something
- Having a personal shopper
- Getting a bonus (free parking)
- Saving time (not spending it)

If you nail these principles, users will **love** this feature and tell everyone about it. That's when you know you've succeeded.

---

**Document Version**: 1.0
**Last Updated**: November 7, 2025
**Author**: UX/Product Analysis for TruFan
**Status**: Ready for Implementation
