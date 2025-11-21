# TruFan iOS Convenience Store Feature - Complete Implementation Guide

> **Mission**: Build a production-ready iOS convenience store feature that allows parkers to order items from nearby stores while parked, with staff fulfillment and delivery to their vehicle.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Business Context & User Value](#business-context--user-value)
3. [User Experience Requirements](#user-experience-requirements)
4. [Technical Architecture](#technical-architecture)
5. [API Integration Guide](#api-integration-guide)
6. [SwiftUI Implementation Strategy](#swiftui-implementation-strategy)
7. [Feature Requirements & Acceptance Criteria](#feature-requirements--acceptance-criteria)
8. [Data Models & State Management](#data-models--state-management)
9. [Networking Layer](#networking-layer)
10. [Error Handling & Edge Cases](#error-handling--edge-cases)
11. [Testing Strategy](#testing-strategy)
12. [Agent Deployment Strategy](#agent-deployment-strategy)

---

## Executive Summary

### What We're Building

A mobile convenience store within the TruFan parking app that enables parkers to:
- Browse available items from nearby stores (Walgreens, CVS, 7-Eleven, etc.)
- Order items while parked at an appointment, event, or haircut
- Have parking lot staff shop, store, and deliver items to their vehicle
- Extend their parking time automatically when ordering
- Track order status in real-time from shopping to delivery

### Why It Matters

**For Customers:**
- Saves time - items ready when they return
- Convenience - no extra shopping trip needed
- Peace of mind - extends parking automatically

**For Lot Owners:**
- Additional revenue stream (15% average service fee)
- Competitive differentiation
- Increased customer satisfaction and loyalty

**For TruFan:**
- New revenue opportunity
- Enhanced platform value
- Deeper customer engagement

### Key Metrics
- Average order value: $20-30
- Service fee: 15% default
- Fulfillment time: 30 minutes target
- Customer satisfaction: 4.5+ stars target

---

## Business Context & User Value

### The Problem We're Solving

Parkers often need items (groceries, snacks, phone chargers, pain relievers) but don't have time to shop while at appointments. They either:
1. Skip the items (lost convenience)
2. Make a separate trip later (wasted time)
3. Cut their appointment short (rushed experience)

### Our Solution

**One-Tap Shopping While Parked:**
```
Park → Order Items → Attend Appointment → Return to Items in Vehicle
```

The parking lot staff handles:
1. Shopping at nearby stores
2. Storing items safely (refrigerated if needed)
3. Delivering to vehicle trunk or designated location

### User Journey Example

**Sarah's Story:**
```
09:00 AM - Sarah parks for 10:00 AM hair appointment
09:02 AM - Opens TruFan app, sees "Need anything while you park?"
09:04 AM - Orders milk, bread, eggs (delivery: trunk)
09:05 AM - Payment authorized, parking extended +15 min
09:10 AM - Notification: "Staff is shopping for your items!"
09:40 AM - Notification: "Items purchased and stored in fridge"
10:45 AM - Sarah returns, items already in her trunk
10:46 AM - Notification: "How was your order?" (rating prompt)
```

**Result:** Sarah saved 20 minutes and a grocery store trip, lot owner earned $3 service fee.

---

## User Experience Requirements

### UX Principles

1. **Frictionless Discovery**
   - Feature prominently displayed when parking session active
   - Clear value proposition: "We'll shop while you're away"
   - Visual: Nearby store logos (Walgreens, CVS, etc.)

2. **Fast Ordering**
   - Maximum 3 taps from app open to order placed
   - Smart defaults (delivery to trunk, typical quantities)
   - Predictive search and popular items featured

3. **Transparent Pricing**
   - Show breakdown: Base price + Service fee + Tax = Total
   - No hidden fees or surprises
   - Clear indication of complimentary parking time added

4. **Real-Time Updates**
   - Push notifications for each status change
   - In-app order tracking with visual timeline
   - Staff name and photo when available

5. **Trust & Safety**
   - Photos of receipt and delivery
   - Clear cancellation policy
   - Customer rating system
   - Secure payment (Stripe)

### Screen Flow

```
Main Parking View
    ↓
[Convenience Store Banner] "Need anything?"
    ↓
Browse Items (Categories + Search)
    ↓
Item Details → Add to Cart
    ↓
Shopping Cart Review
    ↓
Delivery Options + Instructions
    ↓
Payment Confirmation
    ↓
Order Placed (Access Code)
    ↓
Order Tracking (Real-time Status)
    ↓
Delivered → Rate Experience
```

### Key UX Patterns

**1. Progressive Disclosure**
- Show essentials first (name, price, image)
- Details available on tap (description, source store, tags)
- Advanced options hidden but accessible (substitution preferences)

**2. Smart Defaults**
- Default quantity: 1
- Default delivery: Vehicle trunk
- Default tip: 15% (customizable)
- Default payment: Saved method

**3. Contextual Guidance**
- First-time user: Inline tips and examples
- Empty cart: "Popular items" suggestions
- Long fulfillment time: "Busy right now, ~45 min" warning
- Store closed: "Opens at 8 AM tomorrow" message

**4. Error Prevention**
- Minimum order validation before checkout ($5 minimum)
- Out-of-stock indicators before add-to-cart
- Duplicate order warning ("You ordered this 10 min ago")
- Operating hours check ("Store opens in 30 minutes")

**5. Feedback & Reassurance**
- Immediate confirmation: "Order received!"
- Expected timeline: "Ready by 2:30 PM"
- Staff assignment: "Mike is shopping for you"
- Visual progress bar: Shopping → Purchased → Stored → Delivered

---

## Technical Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      iOS App (SwiftUI)                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Presentation Layer                       │  │
│  │  - ConvenienceStoreView (Browse)                     │  │
│  │  - ItemDetailView                                     │  │
│  │  - ShoppingCartView                                   │  │
│  │  - CheckoutView                                       │  │
│  │  - OrderTrackingView                                  │  │
│  │  - OrderHistoryView                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↕                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              ViewModel Layer                          │  │
│  │  - ConvenienceStoreViewModel                         │  │
│  │  - ItemListViewModel                                  │  │
│  │  - CartViewModel                                      │  │
│  │  - OrderViewModel                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↕                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Service Layer                            │  │
│  │  - ConvenienceAPIService                             │  │
│  │  - ImageCacheService                                  │  │
│  │  - NotificationService                                │  │
│  │  - PaymentService                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↕                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Data Layer                               │  │
│  │  - APIClient (URLSession wrapper)                    │  │
│  │  - LocalStorage (UserDefaults/Keychain)              │  │
│  │  - CacheManager                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                  TruFan Backend API                          │
│                  (FastAPI + PostgreSQL)                      │
│                                                              │
│  /api/v1/convenience/venues/{venue_id}/items               │
│  /api/v1/convenience/orders                                │
│  /api/v1/convenience/orders/{order_id}                     │
│  /api/v1/convenience/payments/simulate                     │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**UI Framework:**
- SwiftUI (iOS 15+)
- Combine for reactive programming
- AsyncImage for image loading
- SF Symbols for icons

**Networking:**
- URLSession with async/await
- Codable for JSON parsing
- Custom APIClient wrapper

**State Management:**
- @StateObject for ViewModels
- @EnvironmentObject for shared state
- @Published for reactive updates
- Combine publishers for streams

**Data Persistence:**
- UserDefaults for preferences
- Keychain for access codes
- In-memory cache for images
- Optional: CoreData for offline support

**Payment:**
- Stripe iOS SDK (future integration)
- Currently: Simulated payment endpoint

**Notifications:**
- Local notifications for order updates
- Push notifications (APNs) for real-time status

**Dependencies:**
- Minimal external dependencies
- Prefer native Swift/iOS APIs
- Consider: SDWebImage for advanced image caching

---

## API Integration Guide

### Base Configuration

```swift
// Configuration.swift
enum APIConfiguration {
    static let baseURL = "http://localhost:8000"
    static let apiVersion = "v1"

    static var baseAPIURL: String {
        "\(baseURL)/api/\(apiVersion)"
    }

    // Endpoints
    enum Endpoint {
        case items(venueId: String)
        case itemDetail(venueId: String, itemId: String)
        case categories(venueId: String)
        case createOrder
        case orderDetail(orderId: String)
        case myOrders
        case cancelOrder(orderId: String)
        case rateOrder(orderId: String)
        case simulatePayment

        var path: String {
            switch self {
            case .items(let venueId):
                return "/convenience/venues/\(venueId)/items"
            case .itemDetail(let venueId, let itemId):
                return "/convenience/venues/\(venueId)/items/\(itemId)"
            case .categories(let venueId):
                return "/convenience/venues/\(venueId)/categories"
            case .createOrder:
                return "/convenience/orders"
            case .orderDetail(let orderId):
                return "/convenience/orders/\(orderId)"
            case .myOrders:
                return "/convenience/my-orders"
            case .cancelOrder(let orderId):
                return "/convenience/orders/\(orderId)/cancel"
            case .rateOrder(let orderId):
                return "/convenience/orders/\(orderId)/rate"
            case .simulatePayment:
                return "/convenience/payments/simulate"
            }
        }
    }
}
```

### API Endpoints Reference

#### 1. Browse Items

```swift
// GET /api/v1/convenience/venues/{venue_id}/items
// Query params: ?category=grocery&search=milk&page=1&limit=50

struct ItemsResponse: Codable {
    let items: [ConvenienceItem]
    let total: Int
    let page: Int
    let pages: Int
}

struct ConvenienceItem: Codable, Identifiable {
    let id: String
    let venueId: String
    let name: String
    let description: String?
    let imageUrl: String?
    let category: ItemCategory
    let basePrice: Decimal
    let markupAmount: Decimal
    let markupPercent: Decimal
    let finalPrice: Decimal
    let sourceStore: String
    let sourceAddress: String?
    let estimatedShoppingTimeMinutes: Int
    let isActive: Bool
    let requiresAgeVerification: Bool
    let maxQuantityPerOrder: Int
    let tags: [String]?
    let sku: String?
    let barcode: String?
    let createdAt: Date
    let updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case id, name, description, category, tags, sku, barcode
        case venueId = "venue_id"
        case imageUrl = "image_url"
        case basePrice = "base_price"
        case markupAmount = "markup_amount"
        case markupPercent = "markup_percent"
        case finalPrice = "final_price"
        case sourceStore = "source_store"
        case sourceAddress = "source_address"
        case estimatedShoppingTimeMinutes = "estimated_shopping_time_minutes"
        case isActive = "is_active"
        case requiresAgeVerification = "requires_age_verification"
        case maxQuantityPerOrder = "max_quantity_per_order"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

enum ItemCategory: String, Codable, CaseIterable {
    case grocery
    case food
    case beverage
    case personalCare = "personal_care"
    case electronics
    case other

    var displayName: String {
        switch self {
        case .grocery: return "Grocery"
        case .food: return "Food"
        case .beverage: return "Beverage"
        case .personalCare: return "Personal Care"
        case .electronics: return "Electronics"
        case .other: return "Other"
        }
    }

    var icon: String {
        switch self {
        case .grocery: return "cart.fill"
        case .food: return "fork.knife"
        case .beverage: return "cup.and.saucer.fill"
        case .personalCare: return "paintbrush.fill"
        case .electronics: return "bolt.fill"
        case .other: return "ellipsis.circle.fill"
        }
    }
}
```

#### 2. Create Order

```swift
// POST /api/v1/convenience/orders

struct CreateOrderRequest: Codable {
    let venueId: String
    let parkingSessionId: String?
    let items: [OrderItemRequest]
    let deliveryInstructions: String?
    let specialInstructions: String?

    enum CodingKeys: String, CodingKey {
        case items
        case venueId = "venue_id"
        case parkingSessionId = "parking_session_id"
        case deliveryInstructions = "delivery_instructions"
        case specialInstructions = "special_instructions"
    }
}

struct OrderItemRequest: Codable {
    let itemId: String
    let quantity: Int

    enum CodingKeys: String, CodingKey {
        case quantity
        case itemId = "item_id"
    }
}

struct OrderResponse: Codable {
    let id: String
    let orderNumber: String
    let status: OrderStatus
    let subtotal: Decimal
    let serviceFee: Decimal
    let tax: Decimal
    let totalAmount: Decimal
    let estimatedReadyTime: Date?
    let paymentIntentId: String?
    let paymentStatus: String
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id, status, subtotal, tax
        case orderNumber = "order_number"
        case serviceFee = "service_fee"
        case totalAmount = "total_amount"
        case estimatedReadyTime = "estimated_ready_time"
        case paymentIntentId = "payment_intent_id"
        case paymentStatus = "payment_status"
        case createdAt = "created_at"
    }
}

enum OrderStatus: String, Codable {
    case pending
    case confirmed
    case shopping
    case purchased
    case stored
    case ready
    case delivered
    case completed
    case cancelled
    case refunded

    var displayName: String {
        switch self {
        case .pending: return "Pending Confirmation"
        case .confirmed: return "Confirmed"
        case .shopping: return "Shopping in Progress"
        case .purchased: return "Items Purchased"
        case .stored: return "Items Stored"
        case .ready: return "Ready for Pickup"
        case .delivered: return "Delivered"
        case .completed: return "Completed"
        case .cancelled: return "Cancelled"
        case .refunded: return "Refunded"
        }
    }

    var icon: String {
        switch self {
        case .pending: return "clock.fill"
        case .confirmed: return "checkmark.circle.fill"
        case .shopping: return "cart.fill"
        case .purchased: return "bag.fill"
        case .stored: return "archivebox.fill"
        case .ready: return "bell.fill"
        case .delivered: return "shippingbox.fill"
        case .completed: return "checkmark.seal.fill"
        case .cancelled: return "xmark.circle.fill"
        case .refunded: return "arrow.uturn.backward.circle.fill"
        }
    }

    var color: Color {
        switch self {
        case .pending: return .orange
        case .confirmed: return .blue
        case .shopping: return .purple
        case .purchased: return .indigo
        case .stored: return .teal
        case .ready: return .green
        case .delivered, .completed: return .green
        case .cancelled, .refunded: return .red
        }
    }
}
```

#### 3. Get Order Details

```swift
// GET /api/v1/convenience/orders/{order_id}

struct OrderDetailResponse: Codable {
    let id: String
    let orderNumber: String
    let venueId: String
    let userId: String
    let parkingSessionId: String?
    let status: OrderStatus
    let subtotal: Decimal
    let serviceFee: Decimal
    let tax: Decimal
    let tipAmount: Decimal
    let totalAmount: Decimal
    let paymentStatus: String
    let paymentIntentId: String?
    let paymentMethod: String?
    let assignedStaffId: String?
    let storageLocation: String?
    let deliveryInstructions: String?
    let specialInstructions: String?
    let receiptPhotoUrl: String?
    let deliveryPhotoUrl: String?
    let estimatedReadyTime: Date?
    let confirmedAt: Date?
    let shoppingStartedAt: Date?
    let purchasedAt: Date?
    let storedAt: Date?
    let readyAt: Date?
    let deliveredAt: Date?
    let completedAt: Date?
    let cancelledAt: Date?
    let complimentaryTimeAddedMinutes: Int
    let rating: Int?
    let feedback: String?
    let cancellationReason: String?
    let refundAmount: Decimal?
    let refundReason: String?
    let createdAt: Date
    let updatedAt: Date
    let items: [OrderItem]
    let events: [OrderEvent]

    // CodingKeys omitted for brevity - follow snake_case to camelCase pattern
}

struct OrderItem: Codable, Identifiable {
    let id: String
    let orderId: String
    let itemId: String?
    let itemName: String
    let itemDescription: String?
    let itemImageUrl: String?
    let sourceStore: String
    let quantity: Int
    let unitPrice: Decimal
    let lineTotal: Decimal
    let status: String
    let substitutionNotes: String?
    let actualPrice: Decimal?
    let createdAt: Date

    // CodingKeys omitted for brevity
}

struct OrderEvent: Codable, Identifiable {
    let id: String
    let orderId: String
    let status: String
    let notes: String?
    let photoUrl: String?
    let location: String?
    let createdById: String?
    let createdAt: Date

    // CodingKeys omitted for brevity
}
```

#### 4. Simulate Payment

```swift
// POST /api/v1/convenience/payments/simulate

struct SimulatePaymentRequest: Codable {
    let sessionId: String
    let amount: Decimal
    let shouldSucceed: Bool

    enum CodingKeys: String, CodingKey {
        case amount
        case sessionId = "session_id"
        case shouldSucceed = "should_succeed"
    }
}

struct SimulatePaymentResponse: Codable {
    let paymentId: String
    let sessionId: String
    let amount: Decimal
    let status: String
    let message: String

    enum CodingKeys: String, CodingKey {
        case amount, status, message
        case paymentId = "payment_id"
        case sessionId = "session_id"
    }
}
```

#### 5. My Orders

```swift
// GET /api/v1/convenience/my-orders?status=active&venue_id={venue_id}

struct MyOrdersResponse: Codable {
    let orders: [OrderSummary]
    let total: Int
}

struct OrderSummary: Codable, Identifiable {
    let id: String
    let orderNumber: String
    let venueName: String
    let status: OrderStatus
    let totalAmount: Decimal
    let itemCount: Int
    let estimatedReadyTime: Date?
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id, status
        case orderNumber = "order_number"
        case venueName = "venue_name"
        case totalAmount = "total_amount"
        case itemCount = "item_count"
        case estimatedReadyTime = "estimated_ready_time"
        case createdAt = "created_at"
    }
}
```

#### 6. Cancel Order

```swift
// PATCH /api/v1/convenience/orders/{order_id}/cancel

struct CancelOrderRequest: Codable {
    let reason: String
}

// Response: OrderDetailResponse
```

#### 7. Rate Order

```swift
// POST /api/v1/convenience/orders/{order_id}/rate

struct RateOrderRequest: Codable {
    let rating: Int // 1-5
    let feedback: String?
}

// Response: OrderDetailResponse
```

---

## SwiftUI Implementation Strategy

### 1. Main Convenience Store View

```swift
// ConvenienceStoreView.swift
import SwiftUI

struct ConvenienceStoreView: View {
    @StateObject private var viewModel: ConvenienceStoreViewModel
    @State private var selectedCategory: ItemCategory?
    @State private var searchText: String = ""
    @State private var showingCart: Bool = false

    init(venueId: String) {
        _viewModel = StateObject(wrappedValue: ConvenienceStoreViewModel(venueId: venueId))
    }

    var body: some View {
        NavigationView {
            ZStack {
                VStack(spacing: 0) {
                    // Search Bar
                    SearchBar(text: $searchText, placeholder: "Search items...")
                        .padding()

                    // Category Filter
                    CategoryScrollView(selectedCategory: $selectedCategory)

                    // Items List or Grid
                    if viewModel.isLoading {
                        LoadingView()
                    } else if viewModel.filteredItems.isEmpty {
                        EmptyStateView(
                            icon: "cart.fill",
                            title: "No items found",
                            message: "Try adjusting your search or filters"
                        )
                    } else {
                        ItemsGridView(
                            items: viewModel.filteredItems,
                            onAddToCart: { item in
                                viewModel.addToCart(item)
                            }
                        )
                    }
                }

                // Floating Cart Button
                VStack {
                    Spacer()
                    FloatingCartButton(
                        itemCount: viewModel.cartItemCount,
                        total: viewModel.cartTotal
                    ) {
                        showingCart = true
                    }
                    .padding()
                }
            }
            .navigationTitle("Convenience Store")
            .navigationBarItems(trailing: cartButton)
            .sheet(isPresented: $showingCart) {
                ShoppingCartView(viewModel: viewModel.cartViewModel)
            }
            .alert(item: $viewModel.error) { error in
                Alert(
                    title: Text("Error"),
                    message: Text(error.localizedDescription),
                    dismissButton: .default(Text("OK"))
                )
            }
        }
        .task {
            await viewModel.loadItems()
        }
    }

    private var cartButton: some View {
        Button(action: { showingCart = true }) {
            Image(systemName: "cart.fill")
                .overlay(
                    viewModel.cartItemCount > 0 ?
                        Badge(count: viewModel.cartItemCount) : nil
                )
        }
    }
}
```

### 2. Item Card Component

```swift
// ItemCard.swift
struct ItemCard: View {
    let item: ConvenienceItem
    let onAddToCart: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Image
            AsyncImage(url: URL(string: item.imageUrl ?? "")) { phase in
                switch phase {
                case .empty:
                    ProgressView()
                        .frame(height: 150)
                case .success(let image):
                    image
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                        .frame(height: 150)
                        .clipped()
                case .failure:
                    Image(systemName: "photo")
                        .frame(height: 150)
                        .foregroundColor(.gray)
                @unknown default:
                    EmptyView()
                }
            }
            .background(Color.gray.opacity(0.1))
            .cornerRadius(8)

            // Name
            Text(item.name)
                .font(.headline)
                .lineLimit(2)

            // Source Store
            HStack {
                Image(systemName: "storefront")
                    .font(.caption)
                Text(item.sourceStore)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            // Category Tag
            Text(item.category.displayName)
                .font(.caption2)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(Color.blue.opacity(0.1))
                .foregroundColor(.blue)
                .cornerRadius(4)

            Spacer()

            // Pricing
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    if item.markupPercent > 0 || item.markupAmount > 0 {
                        Text(item.basePrice.asCurrency())
                            .font(.caption)
                            .strikethrough()
                            .foregroundColor(.secondary)
                    }
                    Text(item.finalPrice.asCurrency())
                        .font(.title3)
                        .fontWeight(.bold)
                }

                Spacer()

                // Add to Cart Button
                Button(action: onAddToCart) {
                    Image(systemName: "plus.circle.fill")
                        .font(.title2)
                        .foregroundColor(.blue)
                }
            }
        }
        .padding()
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.1), radius: 4, x: 0, y: 2)
    }
}
```

### 3. Shopping Cart View

```swift
// ShoppingCartView.swift
struct ShoppingCartView: View {
    @ObservedObject var viewModel: CartViewModel
    @Environment(\.dismiss) var dismiss
    @State private var showingCheckout = false

    var body: some View {
        NavigationView {
            ZStack {
                if viewModel.items.isEmpty {
                    EmptyCartView()
                } else {
                    VStack(spacing: 0) {
                        // Cart Items List
                        ScrollView {
                            LazyVStack(spacing: 12) {
                                ForEach(viewModel.items) { cartItem in
                                    CartItemRow(
                                        item: cartItem,
                                        onIncrement: { viewModel.incrementQuantity(cartItem.id) },
                                        onDecrement: { viewModel.decrementQuantity(cartItem.id) },
                                        onRemove: { viewModel.removeItem(cartItem.id) }
                                    )
                                }
                            }
                            .padding()
                        }

                        Divider()

                        // Price Summary
                        PriceSummaryView(
                            subtotal: viewModel.subtotal,
                            serviceFee: viewModel.serviceFee,
                            tax: viewModel.tax,
                            total: viewModel.total
                        )
                        .padding()

                        // Checkout Button
                        Button(action: {
                            if viewModel.validateMinimumOrder() {
                                showingCheckout = true
                            }
                        }) {
                            Text("Proceed to Checkout")
                                .font(.headline)
                                .foregroundColor(.white)
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.blue)
                                .cornerRadius(12)
                        }
                        .padding(.horizontal)
                        .padding(.bottom)
                        .disabled(viewModel.items.isEmpty)
                    }
                }
            }
            .navigationTitle("Shopping Cart")
            .navigationBarItems(leading: Button("Close") { dismiss() })
            .sheet(isPresented: $showingCheckout) {
                CheckoutView(viewModel: viewModel.checkoutViewModel)
            }
        }
    }
}

struct CartItemRow: View {
    let item: CartItem
    let onIncrement: () -> Void
    let onDecrement: () -> Void
    let onRemove: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            // Image
            AsyncImage(url: URL(string: item.imageUrl ?? "")) { image in
                image.resizable()
            } placeholder: {
                Color.gray.opacity(0.2)
            }
            .frame(width: 60, height: 60)
            .cornerRadius(8)

            // Details
            VStack(alignment: .leading, spacing: 4) {
                Text(item.name)
                    .font(.subheadline)
                    .fontWeight(.medium)
                Text(item.sourceStore)
                    .font(.caption)
                    .foregroundColor(.secondary)
                Text(item.unitPrice.asCurrency())
                    .font(.caption)
                    .fontWeight(.semibold)
            }

            Spacer()

            // Quantity Controls
            HStack(spacing: 12) {
                Button(action: onDecrement) {
                    Image(systemName: "minus.circle.fill")
                        .foregroundColor(.gray)
                }

                Text("\(item.quantity)")
                    .font(.headline)
                    .frame(minWidth: 30)

                Button(action: onIncrement) {
                    Image(systemName: "plus.circle.fill")
                        .foregroundColor(.blue)
                }
            }

            // Remove Button
            Button(action: onRemove) {
                Image(systemName: "trash")
                    .foregroundColor(.red)
            }
        }
        .padding()
        .background(Color.gray.opacity(0.05))
        .cornerRadius(12)
    }
}
```

### 4. Checkout View

```swift
// CheckoutView.swift
struct CheckoutView: View {
    @ObservedObject var viewModel: CheckoutViewModel
    @Environment(\.dismiss) var dismiss
    @State private var deliveryInstructions = ""
    @State private var specialInstructions = ""
    @State private var showingOrderConfirmation = false

    var body: some View {
        NavigationView {
            Form {
                // Order Summary Section
                Section(header: Text("Order Summary")) {
                    ForEach(viewModel.items) { item in
                        HStack {
                            Text("\(item.quantity)x \(item.name)")
                            Spacer()
                            Text(item.lineTotal.asCurrency())
                        }
                    }
                }

                // Delivery Section
                Section(header: Text("Delivery Details")) {
                    TextField("Delivery instructions (e.g., 'Blue Honda, Trunk')", text: $deliveryInstructions)
                    TextField("Special instructions (optional)", text: $specialInstructions)
                }

                // Parking Extension Info
                Section {
                    HStack {
                        Image(systemName: "clock.fill")
                            .foregroundColor(.green)
                        Text("Complimentary parking time")
                        Spacer()
                        Text("+\(viewModel.complimentaryParkingMinutes) min")
                            .fontWeight(.bold)
                    }
                } header: {
                    Text("Bonus")
                } footer: {
                    Text("Your parking session will be automatically extended")
                }

                // Price Summary Section
                Section(header: Text("Payment")) {
                    HStack {
                        Text("Subtotal")
                        Spacer()
                        Text(viewModel.subtotal.asCurrency())
                    }
                    HStack {
                        Text("Service Fee (\(viewModel.serviceFeePercent)%)")
                        Spacer()
                        Text(viewModel.serviceFee.asCurrency())
                    }
                    HStack {
                        Text("Tax")
                        Spacer()
                        Text(viewModel.tax.asCurrency())
                    }
                    HStack {
                        Text("Total")
                            .fontWeight(.bold)
                        Spacer()
                        Text(viewModel.total.asCurrency())
                            .fontWeight(.bold)
                    }
                }

                // Place Order Button
                Section {
                    Button(action: {
                        Task {
                            await placeOrder()
                        }
                    }) {
                        HStack {
                            Spacer()
                            if viewModel.isPlacingOrder {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle())
                            } else {
                                Text("Place Order")
                                    .fontWeight(.bold)
                            }
                            Spacer()
                        }
                    }
                    .disabled(viewModel.isPlacingOrder)
                }
            }
            .navigationTitle("Checkout")
            .navigationBarItems(leading: Button("Cancel") { dismiss() })
            .alert(item: $viewModel.error) { error in
                Alert(
                    title: Text("Error"),
                    message: Text(error.localizedDescription),
                    dismissButton: .default(Text("OK"))
                )
            }
            .fullScreenCover(isPresented: $showingOrderConfirmation) {
                if let order = viewModel.placedOrder {
                    OrderConfirmationView(order: order)
                }
            }
        }
    }

    private func placeOrder() async {
        let success = await viewModel.placeOrder(
            deliveryInstructions: deliveryInstructions,
            specialInstructions: specialInstructions
        )

        if success {
            showingOrderConfirmation = true
        }
    }
}
```

### 5. Order Tracking View

```swift
// OrderTrackingView.swift
struct OrderTrackingView: View {
    @StateObject private var viewModel: OrderTrackingViewModel
    let orderId: String

    init(orderId: String) {
        self.orderId = orderId
        _viewModel = StateObject(wrappedValue: OrderTrackingViewModel(orderId: orderId))
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                if let order = viewModel.order {
                    // Order Header
                    OrderHeaderCard(order: order)

                    // Status Timeline
                    StatusTimelineView(
                        currentStatus: order.status,
                        events: order.events
                    )

                    // Items List
                    OrderItemsSection(items: order.items)

                    // Delivery Info
                    if let deliveryInstructions = order.deliveryInstructions {
                        DeliveryInfoCard(instructions: deliveryInstructions)
                    }

                    // Photos
                    if let receiptUrl = order.receiptPhotoUrl {
                        PhotoCard(title: "Receipt", url: receiptUrl)
                    }
                    if let deliveryUrl = order.deliveryPhotoUrl {
                        PhotoCard(title: "Delivery Proof", url: deliveryUrl)
                    }

                    // Action Buttons
                    if order.status == .pending || order.status == .confirmed {
                        CancelOrderButton {
                            viewModel.showCancelConfirmation = true
                        }
                    }

                    if order.status == .delivered && order.rating == nil {
                        RateOrderButton {
                            viewModel.showRatingSheet = true
                        }
                    }
                } else if viewModel.isLoading {
                    ProgressView()
                        .padding()
                } else {
                    Text("Order not found")
                        .foregroundColor(.secondary)
                }
            }
            .padding()
        }
        .navigationTitle("Order #\(viewModel.order?.orderNumber ?? "")")
        .task {
            await viewModel.loadOrder()
        }
        .refreshable {
            await viewModel.refreshOrder()
        }
        .confirmationDialog(
            "Cancel Order",
            isPresented: $viewModel.showCancelConfirmation
        ) {
            Button("Cancel Order", role: .destructive) {
                Task {
                    await viewModel.cancelOrder()
                }
            }
            Button("Keep Order", role: .cancel) {}
        } message: {
            Text("Are you sure you want to cancel this order? You will receive a full refund if shopping hasn't started.")
        }
        .sheet(isPresented: $viewModel.showRatingSheet) {
            if let order = viewModel.order {
                RatingView(orderId: order.id) { rating, feedback in
                    Task {
                        await viewModel.rateOrder(rating: rating, feedback: feedback)
                    }
                }
            }
        }
    }
}

struct StatusTimelineView: View {
    let currentStatus: OrderStatus
    let events: [OrderEvent]

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Order Progress")
                .font(.headline)

            ForEach(OrderStatus.allStatusSteps, id: \.self) { status in
                TimelineStepView(
                    status: status,
                    isCompleted: status.rawValue <= currentStatus.rawValue,
                    isCurrent: status == currentStatus,
                    event: events.first { $0.status == status.rawValue }
                )
            }
        }
        .padding()
        .background(Color.gray.opacity(0.05))
        .cornerRadius(12)
    }
}

struct TimelineStepView: View {
    let status: OrderStatus
    let isCompleted: Bool
    let isCurrent: Bool
    let event: OrderEvent?

    var body: some View {
        HStack(spacing: 12) {
            // Status Icon
            ZStack {
                Circle()
                    .fill(isCompleted ? status.color : Color.gray.opacity(0.2))
                    .frame(width: 40, height: 40)

                Image(systemName: status.icon)
                    .foregroundColor(.white)
            }

            // Status Info
            VStack(alignment: .leading, spacing: 4) {
                Text(status.displayName)
                    .font(.subheadline)
                    .fontWeight(isCurrent ? .bold : .regular)

                if let event = event {
                    Text(event.createdAt.formatted())
                        .font(.caption)
                        .foregroundColor(.secondary)

                    if let notes = event.notes {
                        Text(notes)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }

            Spacer()

            if isCurrent {
                ProgressView()
                    .progressViewStyle(CircularProgressViewStyle())
            } else if isCompleted {
                Image(systemName: "checkmark")
                    .foregroundColor(.green)
            }
        }
    }
}
```

---

## Data Models & State Management

### ViewModel Pattern

```swift
// ConvenienceStoreViewModel.swift
import Foundation
import Combine

@MainActor
class ConvenienceStoreViewModel: ObservableObject {
    @Published var items: [ConvenienceItem] = []
    @Published var filteredItems: [ConvenienceItem] = []
    @Published var selectedCategory: ItemCategory?
    @Published var searchText: String = ""
    @Published var isLoading: Bool = false
    @Published var error: IdentifiableError?

    @Published var cart: [CartItem] = []

    private let venueId: String
    private let apiService: ConvenienceAPIService
    private var cancellables = Set<AnyCancellable>()

    var cartItemCount: Int {
        cart.reduce(0) { $0 + $1.quantity }
    }

    var cartTotal: Decimal {
        cart.reduce(Decimal(0)) { $0 + $1.lineTotal }
    }

    var cartViewModel: CartViewModel {
        CartViewModel(
            cart: cart,
            venueId: venueId,
            apiService: apiService,
            onCartUpdate: { [weak self] updatedCart in
                self?.cart = updatedCart
            }
        )
    }

    init(venueId: String, apiService: ConvenienceAPIService = .shared) {
        self.venueId = venueId
        self.apiService = apiService

        setupBindings()
    }

    private func setupBindings() {
        // Filter items when search text or category changes
        Publishers.CombineLatest($searchText, $selectedCategory)
            .debounce(for: 0.3, scheduler: DispatchQueue.main)
            .sink { [weak self] searchText, category in
                self?.filterItems(searchText: searchText, category: category)
            }
            .store(in: &cancellables)
    }

    func loadItems() async {
        isLoading = true
        defer { isLoading = false }

        do {
            let response = try await apiService.getItems(venueId: venueId)
            items = response.items
            filteredItems = items
        } catch {
            self.error = IdentifiableError(error: error)
        }
    }

    private func filterItems(searchText: String, category: ItemCategory?) {
        var filtered = items

        // Filter by category
        if let category = category {
            filtered = filtered.filter { $0.category == category }
        }

        // Filter by search text
        if !searchText.isEmpty {
            filtered = filtered.filter {
                $0.name.localizedCaseInsensitiveContains(searchText) ||
                $0.description?.localizedCaseInsensitiveContains(searchText) == true ||
                $0.tags?.contains(where: { $0.localizedCaseInsensitiveContains(searchText) }) == true
            }
        }

        filteredItems = filtered
    }

    func addToCart(_ item: ConvenienceItem, quantity: Int = 1) {
        if let index = cart.firstIndex(where: { $0.itemId == item.id }) {
            // Item already in cart, increment quantity
            cart[index].quantity += quantity
        } else {
            // Add new item to cart
            let cartItem = CartItem(
                id: UUID().uuidString,
                itemId: item.id,
                name: item.name,
                imageUrl: item.imageUrl,
                sourceStore: item.sourceStore,
                unitPrice: item.finalPrice,
                quantity: quantity
            )
            cart.append(cartItem)
        }

        // Show success feedback
        HapticManager.shared.impact(.medium)
    }
}
```

### Cart Management

```swift
// CartViewModel.swift
@MainActor
class CartViewModel: ObservableObject {
    @Published var items: [CartItem]
    @Published var isLoading: Bool = false
    @Published var error: IdentifiableError?

    private let venueId: String
    private let apiService: ConvenienceAPIService
    private let onCartUpdate: ([CartItem]) -> Void

    // Configuration (from venue config)
    let serviceFeePercent: Decimal = 15.0
    let taxRate: Decimal = 8.0
    let minimumOrderAmount: Decimal = 5.0

    var subtotal: Decimal {
        items.reduce(Decimal(0)) { $0 + $1.lineTotal }
    }

    var serviceFee: Decimal {
        (subtotal * serviceFeePercent / 100).rounded(2)
    }

    var tax: Decimal {
        ((subtotal + serviceFee) * taxRate / 100).rounded(2)
    }

    var total: Decimal {
        (subtotal + serviceFee + tax).rounded(2)
    }

    var checkoutViewModel: CheckoutViewModel {
        CheckoutViewModel(
            items: items,
            venueId: venueId,
            subtotal: subtotal,
            serviceFee: serviceFee,
            tax: tax,
            total: total,
            apiService: apiService
        )
    }

    init(
        cart: [CartItem],
        venueId: String,
        apiService: ConvenienceAPIService,
        onCartUpdate: @escaping ([CartItem]) -> Void
    ) {
        self.items = cart
        self.venueId = venueId
        self.apiService = apiService
        self.onCartUpdate = onCartUpdate
    }

    func incrementQuantity(_ itemId: String) {
        if let index = items.firstIndex(where: { $0.id == itemId }) {
            items[index].quantity += 1
            onCartUpdate(items)
        }
    }

    func decrementQuantity(_ itemId: String) {
        if let index = items.firstIndex(where: { $0.id == itemId }) {
            if items[index].quantity > 1 {
                items[index].quantity -= 1
                onCartUpdate(items)
            } else {
                removeItem(itemId)
            }
        }
    }

    func removeItem(_ itemId: String) {
        items.removeAll { $0.id == itemId }
        onCartUpdate(items)
    }

    func validateMinimumOrder() -> Bool {
        subtotal >= minimumOrderAmount
    }
}

struct CartItem: Identifiable, Codable {
    let id: String
    let itemId: String
    let name: String
    let imageUrl: String?
    let sourceStore: String
    let unitPrice: Decimal
    var quantity: Int

    var lineTotal: Decimal {
        unitPrice * Decimal(quantity)
    }
}
```

### Checkout Flow

```swift
// CheckoutViewModel.swift
@MainActor
class CheckoutViewModel: ObservableObject {
    @Published var items: [CartItem]
    @Published var isPlacingOrder: Bool = false
    @Published var error: IdentifiableError?
    @Published var placedOrder: OrderResponse?

    let venueId: String
    let subtotal: Decimal
    let serviceFee: Decimal
    let tax: Decimal
    let total: Decimal
    let serviceFeePercent: Decimal
    let complimentaryParkingMinutes: Int = 15

    private let apiService: ConvenienceAPIService

    init(
        items: [CartItem],
        venueId: String,
        subtotal: Decimal,
        serviceFee: Decimal,
        tax: Decimal,
        total: Decimal,
        serviceFeePercent: Decimal = 15.0,
        apiService: ConvenienceAPIService = .shared
    ) {
        self.items = items
        self.venueId = venueId
        self.subtotal = subtotal
        self.serviceFee = serviceFee
        self.tax = tax
        self.total = total
        self.serviceFeePercent = serviceFeePercent
        self.apiService = apiService
    }

    func placeOrder(
        deliveryInstructions: String,
        specialInstructions: String
    ) async -> Bool {
        isPlacingOrder = true
        defer { isPlacingOrder = false }

        do {
            // Create order
            let orderItems = items.map { OrderItemRequest(itemId: $0.itemId, quantity: $0.quantity) }
            let request = CreateOrderRequest(
                venueId: venueId,
                parkingSessionId: getCurrentParkingSessionId(),
                items: orderItems,
                deliveryInstructions: deliveryInstructions.isEmpty ? nil : deliveryInstructions,
                specialInstructions: specialInstructions.isEmpty ? nil : specialInstructions
            )

            let order = try await apiService.createOrder(request: request)

            // Simulate payment
            let paymentSuccess = try await simulatePayment(orderId: order.id, amount: order.totalAmount)

            if paymentSuccess {
                placedOrder = order

                // Clear cart
                items.removeAll()

                // Show success notification
                showSuccessNotification(orderNumber: order.orderNumber)

                return true
            } else {
                throw ConvenienceStoreError.paymentFailed
            }
        } catch {
            self.error = IdentifiableError(error: error)
            return false
        }
    }

    private func simulatePayment(orderId: String, amount: Decimal) async throws -> Bool {
        let request = SimulatePaymentRequest(
            sessionId: orderId,
            amount: amount,
            shouldSucceed: true
        )

        let response = try await apiService.simulatePayment(request: request)
        return response.status == "completed"
    }

    private func getCurrentParkingSessionId() -> String? {
        // TODO: Get from parking session manager
        return UserDefaults.standard.string(forKey: "currentParkingSessionId")
    }

    private func showSuccessNotification(orderNumber: String) {
        let content = UNMutableNotificationContent()
        content.title = "Order Placed!"
        content.body = "Your order #\(orderNumber) has been placed. We'll notify you when staff starts shopping."
        content.sound = .default

        let request = UNNotificationRequest(
            identifier: UUID().uuidString,
            content: content,
            trigger: nil
        )

        UNUserNotificationCenter.current().add(request)
    }
}
```

---

## Networking Layer

### API Client

```swift
// APIClient.swift
import Foundation

actor APIClient {
    static let shared = APIClient()

    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder

    init(session: URLSession = .shared) {
        self.session = session

        // Configure decoder
        self.decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .iso8601

        // Configure encoder
        self.encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.dateEncodingStrategy = .iso8601
    }

    func request<T: Decodable>(
        _ endpoint: APIConfiguration.Endpoint,
        method: HTTPMethod = .get,
        body: Encodable? = nil,
        headers: [String: String] = [:]
    ) async throws -> T {
        let url = try buildURL(endpoint: endpoint)
        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue

        // Add default headers
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // Add custom headers
        for (key, value) in headers {
            request.setValue(value, forHTTPHeaderField: key)
        }

        // Add authentication token if available
        if let token = getAuthToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        // Add body if present
        if let body = body {
            request.httpBody = try encoder.encode(body)
        }

        // Execute request
        let (data, response) = try await session.data(for: request)

        // Validate response
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            throw try decodeError(from: data, statusCode: httpResponse.statusCode)
        }

        // Decode response
        return try decoder.decode(T.self, from: data)
    }

    private func buildURL(endpoint: APIConfiguration.Endpoint) throws -> URL {
        guard let url = URL(string: APIConfiguration.baseAPIURL + endpoint.path) else {
            throw APIError.invalidURL
        }
        return url
    }

    private func getAuthToken() -> String? {
        // TODO: Implement token management
        return UserDefaults.standard.string(forKey: "authToken")
    }

    private func decodeError(from data: Data, statusCode: Int) throws -> APIError {
        if let errorResponse = try? decoder.decode(ErrorResponse.self, from: data) {
            return APIError.serverError(
                code: statusCode,
                message: errorResponse.error.message,
                correlationId: errorResponse.error.correlationId
            )
        }
        return APIError.httpError(statusCode: statusCode)
    }
}

enum HTTPMethod: String {
    case get = "GET"
    case post = "POST"
    case put = "PUT"
    case patch = "PATCH"
    case delete = "DELETE"
}

enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case httpError(statusCode: Int)
    case serverError(code: Int, message: String, correlationId: String?)
    case decodingError(Error)
    case networkError(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .httpError(let statusCode):
            return "HTTP error: \(statusCode)"
        case .serverError(_, let message, _):
            return message
        case .decodingError(let error):
            return "Failed to decode response: \(error.localizedDescription)"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        }
    }
}

struct ErrorResponse: Codable {
    let error: ErrorDetail

    struct ErrorDetail: Codable {
        let code: Int
        let message: String
        let correlationId: String?

        enum CodingKeys: String, CodingKey {
            case code, message
            case correlationId = "correlation_id"
        }
    }
}
```

### Convenience API Service

```swift
// ConvenienceAPIService.swift
import Foundation

class ConvenienceAPIService {
    static let shared = ConvenienceAPIService()

    private let client = APIClient.shared

    // MARK: - Items

    func getItems(
        venueId: String,
        category: ItemCategory? = nil,
        search: String? = nil,
        page: Int = 1,
        limit: Int = 50
    ) async throws -> ItemsResponse {
        var endpoint = APIConfiguration.Endpoint.items(venueId: venueId)
        // TODO: Add query parameters
        return try await client.request(endpoint)
    }

    func getItem(venueId: String, itemId: String) async throws -> ConvenienceItem {
        let endpoint = APIConfiguration.Endpoint.itemDetail(venueId: venueId, itemId: itemId)
        return try await client.request(endpoint)
    }

    // MARK: - Orders

    func createOrder(request: CreateOrderRequest) async throws -> OrderResponse {
        let endpoint = APIConfiguration.Endpoint.createOrder
        return try await client.request(endpoint, method: .post, body: request)
    }

    func getOrder(orderId: String) async throws -> OrderDetailResponse {
        let endpoint = APIConfiguration.Endpoint.orderDetail(orderId: orderId)
        return try await client.request(endpoint)
    }

    func getMyOrders(status: String? = nil, venueId: String? = nil) async throws -> MyOrdersResponse {
        let endpoint = APIConfiguration.Endpoint.myOrders
        // TODO: Add query parameters
        return try await client.request(endpoint)
    }

    func cancelOrder(orderId: String, reason: String) async throws -> OrderDetailResponse {
        let endpoint = APIConfiguration.Endpoint.cancelOrder(orderId: orderId)
        let request = CancelOrderRequest(reason: reason)
        return try await client.request(endpoint, method: .patch, body: request)
    }

    func rateOrder(orderId: String, rating: Int, feedback: String?) async throws -> OrderDetailResponse {
        let endpoint = APIConfiguration.Endpoint.rateOrder(orderId: orderId)
        let request = RateOrderRequest(rating: rating, feedback: feedback)
        return try await client.request(endpoint, method: .post, body: request)
    }

    // MARK: - Payment

    func simulatePayment(request: SimulatePaymentRequest) async throws -> SimulatePaymentResponse {
        let endpoint = APIConfiguration.Endpoint.simulatePayment
        return try await client.request(endpoint, method: .post, body: request)
    }
}
```

---

## Error Handling & Edge Cases

### Error Handling Strategy

```swift
// ConvenienceStoreError.swift
enum ConvenienceStoreError: LocalizedError {
    case itemNotFound
    case venueNotFound
    case orderNotFound
    case minimumOrderNotMet(minimum: Decimal)
    case maximumOrderExceeded(maximum: Decimal)
    case storeNotEnabled
    case storeClosed(opensAt: String)
    case insufficientStock
    case paymentFailed
    case orderAlreadyCancelled
    case cannotCancelOrder
    case invalidRating
    case networkError
    case unknown(Error)

    var errorDescription: String? {
        switch self {
        case .itemNotFound:
            return "Item not found"
        case .venueNotFound:
            return "Venue not found"
        case .orderNotFound:
            return "Order not found"
        case .minimumOrderNotMet(let minimum):
            return "Minimum order amount is \(minimum.asCurrency())"
        case .maximumOrderExceeded(let maximum):
            return "Maximum order amount is \(maximum.asCurrency())"
        case .storeNotEnabled:
            return "Convenience store is not available at this venue"
        case .storeClosed(let opensAt):
            return "Store is currently closed. Opens at \(opensAt)"
        case .insufficientStock:
            return "Some items are out of stock"
        case .paymentFailed:
            return "Payment failed. Please try again or use a different payment method."
        case .orderAlreadyCancelled:
            return "This order has already been cancelled"
        case .cannotCancelOrder:
            return "This order cannot be cancelled. Shopping has already started."
        case .invalidRating:
            return "Please provide a rating between 1 and 5 stars"
        case .networkError:
            return "Network error. Please check your connection and try again."
        case .unknown(let error):
            return error.localizedDescription
        }
    }

    var recoverysuggestion: String? {
        switch self {
        case .minimumOrderNotMet:
            return "Add more items to your cart to meet the minimum order requirement."
        case .maximumOrderExceeded:
            return "Remove some items from your cart to stay within the maximum order limit."
        case .storeClosed:
            return "You can browse items and place your order when the store opens."
        case .paymentFailed:
            return "Please verify your payment information and try again."
        case .networkError:
            return "Check your internet connection and try again."
        default:
            return nil
        }
    }
}

struct IdentifiableError: Identifiable {
    let id = UUID()
    let error: Error

    var localizedDescription: String {
        if let convenienceError = error as? ConvenienceStoreError {
            return convenienceError.errorDescription ?? "An error occurred"
        }
        return error.localizedDescription
    }
}
```

### Edge Cases to Handle

**1. Empty States**
```swift
// EmptyStateView.swift
struct EmptyStateView: View {
    let icon: String
    let title: String
    let message: String
    let actionTitle: String?
    let action: (() -> Void)?

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 60))
                .foregroundColor(.gray)

            Text(title)
                .font(.title2)
                .fontWeight(.semibold)

            Text(message)
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)

            if let actionTitle = actionTitle, let action = action {
                Button(action: action) {
                    Text(actionTitle)
                        .fontWeight(.semibold)
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .padding()
    }
}

// Usage examples:
EmptyStateView(
    icon: "cart.fill",
    title: "Your cart is empty",
    message: "Browse items and add them to your cart to get started",
    actionTitle: "Browse Items",
    action: { /* navigate to browse */ }
)

EmptyStateView(
    icon: "doc.text.magnifyingglass",
    title: "No items found",
    message: "Try adjusting your search or filters",
    actionTitle: nil,
    action: nil
)

EmptyStateView(
    icon: "bag.fill",
    title: "No orders yet",
    message: "Your order history will appear here",
    actionTitle: "Start Shopping",
    action: { /* navigate to store */ }
)
```

**2. Network Error Handling**
```swift
// RetryableView.swift
struct RetryableView<Content: View>: View {
    let isLoading: Bool
    let error: Error?
    let retry: () async -> Void
    @ViewBuilder let content: () -> Content

    var body: some View {
        Group {
            if isLoading {
                ProgressView()
            } else if let error = error {
                ErrorView(error: error, retry: retry)
            } else {
                content()
            }
        }
    }
}

struct ErrorView: View {
    let error: Error
    let retry: () async -> Void

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 50))
                .foregroundColor(.orange)

            Text("Something went wrong")
                .font(.headline)

            Text(error.localizedDescription)
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)

            Button(action: {
                Task {
                    await retry()
                }
            }) {
                Label("Try Again", systemImage: "arrow.clockwise")
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
    }
}
```

**3. Loading States**
```swift
// LoadingView.swift
struct LoadingView: View {
    let message: String?

    init(message: String? = nil) {
        self.message = message
    }

    var body: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.5)

            if let message = message {
                Text(message)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
    }
}

// Skeleton loading for list items
struct SkeletonItemCard: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Rectangle()
                .fill(Color.gray.opacity(0.2))
                .frame(height: 150)
                .cornerRadius(8)

            Rectangle()
                .fill(Color.gray.opacity(0.2))
                .frame(height: 20)
                .cornerRadius(4)

            Rectangle()
                .fill(Color.gray.opacity(0.2))
                .frame(width: 100, height: 16)
                .cornerRadius(4)
        }
        .padding()
        .redacted(reason: .placeholder)
        .shimmering() // Custom modifier for shimmer effect
    }
}
```

**4. Validation**
```swift
// OrderValidator.swift
struct OrderValidator {
    static func validate(
        cart: [CartItem],
        minimumAmount: Decimal,
        maximumAmount: Decimal
    ) -> Result<Void, ConvenienceStoreError> {
        // Check empty cart
        guard !cart.isEmpty else {
            return .failure(.minimumOrderNotMet(minimum: minimumAmount))
        }

        // Calculate total
        let total = cart.reduce(Decimal(0)) { $0 + $1.lineTotal }

        // Check minimum
        if total < minimumAmount {
            return .failure(.minimumOrderNotMet(minimum: minimumAmount))
        }

        // Check maximum
        if total > maximumAmount {
            return .failure(.maximumOrderExceeded(maximum: maximumAmount))
        }

        return .success(())
    }
}
```

**5. Operating Hours Check**
```swift
// OperatingHoursChecker.swift
struct OperatingHoursChecker {
    let operatingHours: [String: OperatingHours]

    struct OperatingHours: Codable {
        let open: String // "08:00"
        let close: String // "20:00"
    }

    func isOpen(at date: Date = Date()) -> (open: Bool, message: String?) {
        let calendar = Calendar.current
        let weekday = calendar.component(.weekday, from: date)
        let weekdayString = weekdayName(for: weekday)

        guard let hours = operatingHours[weekdayString.lowercased()] else {
            return (false, "Store hours not available")
        }

        let currentTime = timeString(from: date)

        if currentTime >= hours.open && currentTime <= hours.close {
            return (true, nil)
        } else {
            if currentTime < hours.open {
                return (false, "Store opens at \(formattedTime(hours.open))")
            } else {
                return (false, "Store closed. Opens tomorrow at \(formattedTime(hours.open))")
            }
        }
    }

    private func weekdayName(for weekday: Int) -> String {
        let weekdays = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        return weekdays[weekday - 1]
    }

    private func timeString(from date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: date)
    }

    private func formattedTime(_ time: String) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        if let date = formatter.date(from: time) {
            formatter.dateFormat = "h:mm a"
            return formatter.string(from: date)
        }
        return time
    }
}
```

---

## Testing Strategy

### Unit Tests

```swift
// ConvenienceStoreViewModelTests.swift
import XCTest
@testable import TruFan

@MainActor
class ConvenienceStoreViewModelTests: XCTestCase {
    var sut: ConvenienceStoreViewModel!
    var mockAPIService: MockConvenienceAPIService!

    override func setUp() {
        super.setUp()
        mockAPIService = MockConvenienceAPIService()
        sut = ConvenienceStoreViewModel(venueId: "test-venue", apiService: mockAPIService)
    }

    override func tearDown() {
        sut = nil
        mockAPIService = nil
        super.tearDown()
    }

    func testLoadItems_Success() async {
        // Given
        let expectedItems = [
            ConvenienceItem.mock(id: "1", name: "Milk"),
            ConvenienceItem.mock(id: "2", name: "Bread")
        ]
        mockAPIService.itemsToReturn = expectedItems

        // When
        await sut.loadItems()

        // Then
        XCTAssertEqual(sut.items.count, 2)
        XCTAssertEqual(sut.items[0].name, "Milk")
        XCTAssertFalse(sut.isLoading)
        XCTAssertNil(sut.error)
    }

    func testLoadItems_Failure() async {
        // Given
        mockAPIService.shouldFail = true

        // When
        await sut.loadItems()

        // Then
        XCTAssertTrue(sut.items.isEmpty)
        XCTAssertNotNil(sut.error)
        XCTAssertFalse(sut.isLoading)
    }

    func testFilterItems_ByCategory() {
        // Given
        sut.items = [
            ConvenienceItem.mock(id: "1", category: .grocery),
            ConvenienceItem.mock(id: "2", category: .beverage)
        ]

        // When
        sut.selectedCategory = .grocery

        // Then
        XCTAssertEqual(sut.filteredItems.count, 1)
        XCTAssertEqual(sut.filteredItems[0].category, .grocery)
    }

    func testAddToCart_NewItem() {
        // Given
        let item = ConvenienceItem.mock(id: "1", name: "Milk", finalPrice: 5.99)

        // When
        sut.addToCart(item)

        // Then
        XCTAssertEqual(sut.cart.count, 1)
        XCTAssertEqual(sut.cart[0].quantity, 1)
        XCTAssertEqual(sut.cartTotal, 5.99)
    }

    func testAddToCart_ExistingItem() {
        // Given
        let item = ConvenienceItem.mock(id: "1", name: "Milk", finalPrice: 5.99)
        sut.addToCart(item)

        // When
        sut.addToCart(item)

        // Then
        XCTAssertEqual(sut.cart.count, 1)
        XCTAssertEqual(sut.cart[0].quantity, 2)
        XCTAssertEqual(sut.cartTotal, 11.98)
    }
}

// Mock API Service
class MockConvenienceAPIService: ConvenienceAPIService {
    var itemsToReturn: [ConvenienceItem] = []
    var shouldFail = false

    override func getItems(
        venueId: String,
        category: ItemCategory?,
        search: String?,
        page: Int,
        limit: Int
    ) async throws -> ItemsResponse {
        if shouldFail {
            throw APIError.networkError(NSError(domain: "test", code: -1))
        }
        return ItemsResponse(items: itemsToReturn, total: itemsToReturn.count, page: 1, pages: 1)
    }
}

// Test Helpers
extension ConvenienceItem {
    static func mock(
        id: String = UUID().uuidString,
        name: String = "Test Item",
        category: ItemCategory = .grocery,
        basePrice: Decimal = 5.00,
        finalPrice: Decimal = 5.75
    ) -> ConvenienceItem {
        ConvenienceItem(
            id: id,
            venueId: "test-venue",
            name: name,
            description: nil,
            imageUrl: nil,
            category: category,
            basePrice: basePrice,
            markupAmount: 0,
            markupPercent: 15,
            finalPrice: finalPrice,
            sourceStore: "Test Store",
            sourceAddress: nil,
            estimatedShoppingTimeMinutes: 15,
            isActive: true,
            requiresAgeVerification: false,
            maxQuantityPerOrder: 10,
            tags: nil,
            sku: nil,
            barcode: nil,
            createdAt: Date(),
            updatedAt: Date()
        )
    }
}
```

### UI Tests

```swift
// ConvenienceStoreUITests.swift
import XCTest

class ConvenienceStoreUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        app = XCUIApplication()
        app.launch()
    }

    func testBrowseItems() {
        // Navigate to convenience store
        app.buttons["ConvenienceStore"].tap()

        // Verify items are displayed
        XCTAssertTrue(app.otherElements["ItemsGrid"].exists)

        // Verify at least one item is visible
        let firstItem = app.buttons.matching(identifier: "ItemCard").element(boundBy: 0)
        XCTAssertTrue(firstItem.exists)
    }

    func testAddToCart() {
        app.buttons["ConvenienceStore"].tap()

        // Add item to cart
        let addButton = app.buttons.matching(identifier: "AddToCartButton").element(boundBy: 0)
        addButton.tap()

        // Verify cart badge updates
        let cartBadge = app.otherElements["CartBadge"]
        XCTAssertTrue(cartBadge.exists)
        XCTAssertEqual(cartBadge.label, "1")
    }

    func testCheckoutFlow() {
        app.buttons["ConvenienceStore"].tap()

        // Add item
        app.buttons.matching(identifier: "AddToCartButton").element(boundBy: 0).tap()

        // Open cart
        app.buttons["CartButton"].tap()

        // Proceed to checkout
        app.buttons["ProceedToCheckout"].tap()

        // Fill delivery instructions
        let instructionsField = app.textFields["DeliveryInstructions"]
        instructionsField.tap()
        instructionsField.typeText("Blue Honda, Trunk")

        // Place order
        app.buttons["PlaceOrder"].tap()

        // Verify order confirmation
        XCTAssertTrue(app.staticTexts.matching(NSPredicate(format: "label CONTAINS[c] 'Order Placed'")).element.exists)
    }
}
```

### Integration Tests

```swift
// OrderFlowIntegrationTests.swift
import XCTest
@testable import TruFan

class OrderFlowIntegrationTests: XCTestCase {
    var apiService: ConvenienceAPIService!

    override func setUp() {
        super.setUp()
        apiService = ConvenienceAPIService.shared
    }

    func testCompleteOrderFlow() async throws {
        // 1. Browse items
        let itemsResponse = try await apiService.getItems(venueId: "test-venue")
        XCTAssertFalse(itemsResponse.items.isEmpty)

        let testItem = itemsResponse.items[0]

        // 2. Create order
        let orderRequest = CreateOrderRequest(
            venueId: "test-venue",
            parkingSessionId: nil,
            items: [OrderItemRequest(itemId: testItem.id, quantity: 1)],
            deliveryInstructions: "Test delivery",
            specialInstructions: nil
        )

        let order = try await apiService.createOrder(request: orderRequest)
        XCTAssertNotNil(order.id)
        XCTAssertEqual(order.status, .pending)

        // 3. Simulate payment
        let paymentRequest = SimulatePaymentRequest(
            sessionId: order.id,
            amount: order.totalAmount,
            shouldSucceed: true
        )

        let paymentResponse = try await apiService.simulatePayment(request: paymentRequest)
        XCTAssertEqual(paymentResponse.status, "completed")

        // 4. Verify order status
        let orderDetail = try await apiService.getOrder(orderId: order.id)
        XCTAssertEqual(orderDetail.paymentStatus, "captured")

        // 5. Rate order (after it's completed)
        // Note: This would fail in real scenario as order needs to be delivered first
        // Just demonstrating the API call
    }
}
```

### Key Test Scenarios

1. **Item Browsing**
   - Load items successfully
   - Handle empty item list
   - Filter by category
   - Search items
   - Handle network errors

2. **Shopping Cart**
   - Add item to cart
   - Update quantity
   - Remove item
   - Calculate totals correctly
   - Persist cart across sessions

3. **Checkout**
   - Validate minimum order
   - Validate maximum order
   - Create order successfully
   - Handle payment failure
   - Show confirmation

4. **Order Tracking**
   - Load order details
   - Display status timeline
   - Show real-time updates
   - Handle missing order

5. **Error Handling**
   - Network failures
   - Invalid data
   - Server errors
   - Timeout scenarios

---

## Feature Requirements & Acceptance Criteria

### Must-Have Features (MVP)

#### 1. Browse Items
**User Story:** As a parker, I want to browse available items so I can see what I can order.

**Acceptance Criteria:**
- ✓ Display grid/list of items with image, name, price, source store
- ✓ Filter by category (Grocery, Beverage, Food, etc.)
- ✓ Search by item name, description, or tags
- ✓ Show item availability status
- ✓ Display estimated shopping time
- ✓ Handle empty states gracefully
- ✓ Load items asynchronously with loading indicator
- ✓ Cache images for performance

**Edge Cases:**
- No items available
- All items inactive
- Network failure
- Slow image loading

#### 2. Add to Cart
**User Story:** As a parker, I want to add items to my cart so I can order multiple items at once.

**Acceptance Criteria:**
- ✓ Tap "Add to Cart" button to add item
- ✓ Update cart badge with item count
- ✓ Show visual feedback when item added (animation/toast)
- ✓ Increment quantity if item already in cart
- ✓ Persist cart across app sessions
- ✓ Display cart total
- ✓ Allow quick quantity adjustment

**Edge Cases:**
- Maximum quantity per item
- Item becomes inactive while in cart
- Cart exceeds maximum order amount

#### 3. Shopping Cart Management
**User Story:** As a parker, I want to review and modify my cart before checkout.

**Acceptance Criteria:**
- ✓ View all cart items with thumbnails
- ✓ Adjust quantities (increment/decrement)
- ✓ Remove items from cart
- ✓ See price breakdown (subtotal, service fee, tax, total)
- ✓ See complimentary parking time bonus
- ✓ Validate minimum order amount
- ✓ Warn if approaching maximum order amount

**Edge Cases:**
- Empty cart
- Single item in cart
- Minimum order not met
- Maximum order exceeded

#### 4. Checkout & Payment
**User Story:** As a parker, I want to complete my order with payment so staff can start shopping.

**Acceptance Criteria:**
- ✓ Enter delivery instructions (vehicle description, location)
- ✓ Optionally add special instructions
- ✓ Review order summary
- ✓ See complimentary parking time extension
- ✓ Process payment (simulated for now)
- ✓ Receive order confirmation with order number
- ✓ Clear cart after successful order
- ✓ Handle payment failures gracefully

**Edge Cases:**
- Payment declined
- Network interruption during payment
- Order creation fails after payment
- Operating hours restriction

#### 5. Order Tracking
**User Story:** As a parker, I want to track my order status so I know when items will be ready.

**Acceptance Criteria:**
- ✓ View current order status with visual timeline
- ✓ See status updates in real-time (or on refresh)
- ✓ Display estimated ready time
- ✓ Show assigned staff member (if available)
- ✓ View order items and pricing
- ✓ See delivery/storage location
- ✓ View receipt photo (when available)
- ✓ View delivery proof photo (when delivered)

**Edge Cases:**
- Order not found
- Network error during refresh
- Status not updating

#### 6. Order History
**User Story:** As a parker, I want to see my past orders so I can reorder or track spending.

**Acceptance Criteria:**
- ✓ List all orders (active and completed)
- ✓ Filter by status (active, completed, cancelled)
- ✓ Display order number, date, total, status
- ✓ Tap to view order details
- ✓ Show empty state for no orders

**Edge Cases:**
- No order history
- Pagination for many orders
- Deleted venue/items

#### 7. Cancel Order
**User Story:** As a parker, I want to cancel my order if my plans change.

**Acceptance Criteria:**
- ✓ Cancel button visible for pending/confirmed orders
- ✓ Show confirmation dialog with refund policy
- ✓ Enter cancellation reason
- ✓ Receive immediate refund confirmation
- ✓ Update order status to cancelled
- ✓ Prevent cancellation once shopping started

**Edge Cases:**
- Already shopping (cannot cancel)
- Already delivered (must contact support)
- Network failure during cancellation

#### 8. Rate & Review
**User Story:** As a parker, I want to rate my order so the lot owner knows my experience.

**Acceptance Criteria:**
- ✓ Prompt to rate after order delivered
- ✓ 5-star rating selector
- ✓ Optional feedback text
- ✓ Submit rating
- ✓ Show confirmation
- ✓ Only allow rating once per order

**Edge Cases:**
- Order not yet delivered
- Already rated
- Network failure during submission

### Nice-to-Have Features (Future)

#### 1. Favorites & Quick Reorder
- Save frequently ordered items
- One-tap reorder from history
- "Reorder last order" button

#### 2. Real-Time Push Notifications
- Order confirmed
- Shopping started
- Items purchased
- Ready for pickup
- Delivered

#### 3. Item Details Page
- Larger images
- Full description
- Nutritional info (if available)
- Similar items
- Reviews from other parkers

#### 4. Advanced Filters
- Price range
- Source store
- Tags (dairy, organic, gluten-free)
- Availability (in-stock only)

#### 5. Delivery Preferences
- Save default delivery location
- Multiple vehicle profiles
- Delivery time preferences

#### 6. Payment Methods
- Save multiple payment methods
- Apple Pay integration
- Google Pay integration
- Split payment

#### 7. Loyalty & Rewards
- Points for orders
- Discounts for frequent buyers
- Referral bonuses

#### 8. Scheduled Orders
- "Have this ready by 2 PM"
- Recurring orders
- Pre-order for future parking

---

## Agent Deployment Strategy

### Recommended Agent Breakdown

Deploy **4-6 parallel agents** working on different features simultaneously:

#### Agent 1: Foundation & Networking
**Responsibility:** Core infrastructure
**Tasks:**
1. Create API client with async/await
2. Implement all API service methods
3. Define all data models (Codable structs)
4. Error handling infrastructure
5. Networking utilities (retry, timeout)
6. Unit tests for API client

**Files to Create:**
- `APIClient.swift`
- `ConvenienceAPIService.swift`
- `ConvenienceModels.swift`
- `APIConfiguration.swift`
- `APIError.swift`
- `APIClientTests.swift`

**Estimated Time:** 6-8 hours

---

#### Agent 2: Browse Items & Cart
**Responsibility:** Item browsing and shopping cart
**Tasks:**
1. ConvenienceStoreView (browse screen)
2. ItemCard component
3. CategoryFilter component
4. SearchBar component
5. ShoppingCartView
6. CartItemRow component
7. ConvenienceStoreViewModel
8. CartViewModel
9. Image caching service

**Files to Create:**
- `ConvenienceStoreView.swift`
- `ItemCard.swift`
- `CategoryFilter.swift`
- `ShoppingCartView.swift`
- `ConvenienceStoreViewModel.swift`
- `CartViewModel.swift`
- `ImageCacheService.swift`

**Estimated Time:** 8-10 hours

---

#### Agent 3: Checkout & Payment
**Responsibility:** Order placement and payment flow
**Tasks:**
1. CheckoutView
2. PriceSummaryView component
3. DeliveryInstructionsForm component
4. OrderConfirmationView
5. CheckoutViewModel
6. Payment simulation integration
7. Order validation logic
8. Success/failure handling

**Files to Create:**
- `CheckoutView.swift`
- `OrderConfirmationView.swift`
- `CheckoutViewModel.swift`
- `OrderValidator.swift`
- `PriceSummaryView.swift`

**Estimated Time:** 6-8 hours

---

#### Agent 4: Order Tracking & History
**Responsibility:** Order management and tracking
**Tasks:**
1. OrderTrackingView
2. StatusTimelineView component
3. OrderItemsSection component
4. OrderHistoryView
5. OrderDetailView
6. OrderTrackingViewModel
7. OrderHistoryViewModel
8. Real-time status updates (polling or push)

**Files to Create:**
- `OrderTrackingView.swift`
- `StatusTimelineView.swift`
- `OrderHistoryView.swift`
- `OrderTrackingViewModel.swift`
- `OrderHistoryViewModel.swift`

**Estimated Time:** 8-10 hours

---

#### Agent 5: Cancel & Rating
**Responsibility:** Order cancellation and feedback
**Tasks:**
1. CancelOrderView
2. RatingView
3. FeedbackForm component
4. Cancellation logic
5. Rating submission
6. Confirmation dialogs
7. Error handling for cancellation

**Files to Create:**
- `CancelOrderView.swift`
- `RatingView.swift`
- `OrderActionViewModel.swift`

**Estimated Time:** 4-6 hours

---

#### Agent 6: Shared Components & Polish
**Responsibility:** Reusable UI components and polish
**Tasks:**
1. LoadingView
2. EmptyStateView
3. ErrorView
4. Badge component
5. FloatingCartButton
6. Toast/Alert system
7. Haptic feedback manager
8. Accessibility labels
9. Dark mode support

**Files to Create:**
- `LoadingView.swift`
- `EmptyStateView.swift`
- `ErrorView.swift`
- `FloatingCartButton.swift`
- `ToastManager.swift`
- `HapticManager.swift`
- `Utilities.swift`

**Estimated Time:** 6-8 hours

---

### Parallel vs Sequential Execution

**Parallel (can work simultaneously):**
- Agent 1 (Foundation) → Start first, others depend on it
- Agent 2, 3, 4, 5 → Start after Agent 1 completes data models
- Agent 6 → Can start anytime, used by all others

**Dependencies:**
```
Agent 1 (Foundation)
    ↓ (models & API service ready)
    ├→ Agent 2 (Browse & Cart)
    ├→ Agent 3 (Checkout)
    ├→ Agent 4 (Tracking)
    ├→ Agent 5 (Cancel & Rate)
    └→ Agent 6 (Shared Components) ← Used by all
```

**Optimal Workflow:**
1. **Day 1:** Agent 1 completes foundation (8 hrs)
2. **Day 2-3:** Agents 2, 3, 4, 5, 6 work in parallel (16-20 hrs)
3. **Day 4:** Integration testing and bug fixes (8 hrs)
4. **Day 5:** Polish, accessibility, edge cases (8 hrs)

**Total Estimated Time:** 40-50 hours across 5 agents

---

### Integration Points

Each agent should:

1. **Read existing code** to understand patterns
   - Check `TruFanApp.swift` for app structure
   - Review existing networking patterns
   - Follow existing ViewModels as templates

2. **Follow naming conventions**
   - ViewModels: `[Feature]ViewModel.swift`
   - Views: `[Feature]View.swift`
   - Services: `[Service]Service.swift`
   - Models: Plural for collections, singular for single

3. **Use dependency injection**
   - Pass APIService to ViewModels
   - Make services injectable for testing
   - Use protocols for mockability

4. **Handle errors consistently**
   - Use IdentifiableError for alerts
   - Provide user-friendly messages
   - Include recovery suggestions

5. **Add loading states**
   - Show ProgressView during async operations
   - Disable buttons when processing
   - Provide visual feedback

6. **Test as you build**
   - Unit tests for ViewModels
   - UI tests for critical flows
   - Integration tests for API calls

---

## Success Criteria & Validation

### Definition of Done

The iOS Convenience Store feature is complete when:

1. **Functional Requirements**
   - ✓ User can browse items by category and search
   - ✓ User can add items to cart and adjust quantities
   - ✓ User can checkout with delivery instructions
   - ✓ Payment simulation works (success and failure)
   - ✓ User receives order confirmation
   - ✓ User can track order status with timeline
   - ✓ User can view order history
   - ✓ User can cancel pending orders
   - ✓ User can rate completed orders

2. **Non-Functional Requirements**
   - ✓ All API calls handle errors gracefully
   - ✓ Loading states shown for async operations
   - ✓ Empty states for no data scenarios
   - ✓ Images load asynchronously with placeholders
   - ✓ Cart persists across app sessions
   - ✓ No memory leaks or retain cycles
   - ✓ Smooth scrolling performance (60fps)
   - ✓ Accessible with VoiceOver

3. **Code Quality**
   - ✓ All code compiles without warnings
   - ✓ SwiftLint passes (if configured)
   - ✓ Unit test coverage >70%
   - ✓ UI tests cover happy paths
   - ✓ Code follows Swift style guide
   - ✓ ViewModels are testable
   - ✓ No hardcoded strings (use localization)

4. **UI/UX**
   - ✓ Consistent with existing app design
   - ✓ Supports light and dark mode
   - ✓ Works on all iPhone sizes (SE to Pro Max)
   - ✓ Animations are smooth
   - ✓ Haptic feedback on key actions
   - ✓ Keyboard dismisses appropriately
   - ✓ Safe area insets respected

5. **Documentation**
   - ✓ README updated with feature description
   - ✓ API service methods documented
   - ✓ Complex logic has inline comments
   - ✓ ViewModels have header comments
   - ✓ Known issues documented

---

## Final Notes & Best Practices

### SwiftUI Best Practices

1. **Prefer @StateObject over @ObservedObject for ownership**
   ```swift
   @StateObject private var viewModel = MyViewModel()
   ```

2. **Use @EnvironmentObject for shared state**
   ```swift
   @EnvironmentObject var authManager: AuthManager
   ```

3. **Extract complex views into components**
   - Keep views small and focused
   - Aim for <200 lines per file
   - Reuse components across screens

4. **Use enums for state management**
   ```swift
   enum LoadingState<T> {
       case idle
       case loading
       case success(T)
       case failure(Error)
   }
   ```

5. **Prefer async/await over Combine for simple async tasks**
   ```swift
   Task {
       await viewModel.loadData()
   }
   ```

6. **Use `.task` modifier for loading data**
   ```swift
   .task {
       await viewModel.loadItems()
   }
   ```

### Performance Tips

1. **Lazy load images**
   - Use AsyncImage with placeholder
   - Implement image caching
   - Consider SDWebImage for advanced caching

2. **Lazy load lists**
   ```swift
   LazyVStack {
       ForEach(items) { item in
           ItemRow(item: item)
       }
   }
   ```

3. **Avoid heavy computations in body**
   - Compute in ViewModel
   - Use computed properties wisely
   - Cache expensive calculations

4. **Debounce search**
   ```swift
   .debounce(for: 0.3, scheduler: DispatchQueue.main)
   ```

### Accessibility

1. **Add accessibility labels**
   ```swift
   .accessibilityLabel("Add \(item.name) to cart")
   ```

2. **Group related elements**
   ```swift
   .accessibilityElement(children: .combine)
   ```

3. **Support Dynamic Type**
   ```swift
   Text("Title")
       .font(.headline)
       .minimumScaleFactor(0.5)
   ```

4. **Test with VoiceOver**
   - Enable VoiceOver in Simulator
   - Navigate through all screens
   - Ensure all buttons are labeled

### Error Messages

**Good:**
- "Minimum order is $5.00. Add $2.50 more to checkout."
- "Store opens at 8:00 AM. You can browse items now."
- "Payment failed. Please check your card and try again."

**Bad:**
- "Error 400"
- "Invalid request"
- "Something went wrong"

### User Feedback

**Visual:**
- Loading spinners
- Skeleton screens
- Progress bars

**Tactile:**
- Haptic feedback on add to cart
- Haptic feedback on order placed
- Haptic feedback on errors

**Auditory:**
- System sounds for success
- Error sounds for failures

---

## Conclusion

This guide provides everything needed to build a production-ready iOS convenience store feature for TruFan. The architecture is:

- **Scalable:** Modular components, MVVM pattern
- **Maintainable:** Clear separation of concerns, testable code
- **User-Friendly:** Intuitive UI, helpful error messages
- **Performant:** Async/await, image caching, lazy loading
- **Reliable:** Comprehensive error handling, validation

### Next Steps

1. **Review** this document with the team
2. **Set up** development environment
3. **Deploy** Agent 1 (Foundation) first
4. **Parallel deploy** Agents 2-6 once foundation ready
5. **Integrate** and test all components
6. **Polish** UI/UX and accessibility
7. **Submit** for review

### Resources

- **Backend API:** http://localhost:8000/docs
- **Design System:** (Reference existing TruFan iOS app)
- **Apple HIG:** https://developer.apple.com/design/human-interface-guidelines/
- **SwiftUI Tutorials:** https://developer.apple.com/tutorials/swiftui

---

**Document Version:** 1.0
**Last Updated:** November 7, 2025
**Author:** TruFan Engineering Team
**Status:** Ready for Implementation

---

**Good luck building an amazing convenience store experience!** 🚀📱
