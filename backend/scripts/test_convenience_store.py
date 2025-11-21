#!/usr/bin/env python3
"""
Test convenience store feature for valet service.
Run with: docker-compose exec api python -m scripts.test_convenience_store
"""
import requests
import json
from datetime import datetime
from decimal import Decimal

BASE_URL = "http://localhost:8000/api/v1"


def print_section(title):
    """Print a section header."""
    print("\n" + "="*70)
    print(title)
    print("="*70 + "\n")


def print_result(test_name, success, details=""):
    """Print test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"   {details}")


def test_convenience_store():
    """Test complete convenience store workflow."""

    print_section("CONVENIENCE STORE SYSTEM TESTS")

    # Login as valet worker (for admin/staff operations)
    print("Logging in as valet worker...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "valet1@greenfieldparking.com",
            "password": "password"
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return

    staff_token = login_response.json()['access_token']
    print(f"✅ Logged in as staff successfully\n")

    staff_headers = {
        "Authorization": f"Bearer {staff_token}",
        "Content-Type": "application/json"
    }

    # Login as customer
    print("Logging in as customer...")
    customer_login = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "czachandrew@gmail.com",
            "password": "password"
        }
    )

    if customer_login.status_code != 200:
        print(f"❌ Customer login failed: {customer_login.status_code}")
        print(f"Response: {customer_login.text}")
        return

    customer_token = customer_login.json()['access_token']
    print(f"✅ Logged in as customer successfully\n")

    customer_headers = {
        "Authorization": f"Bearer {customer_token}",
        "Content-Type": "application/json"
    }

    venue_id = "380ccab9-fa83-4c25-894f-7021ba6714ef"  # Greenfield Plaza

    # TEST 1: Configure convenience store
    print_section("TEST 1: Configure Convenience Store")

    store_config = {
        "is_enabled": True,
        "default_service_fee_percent": 15.00,
        "minimum_order_amount": 5.00,
        "maximum_order_amount": 200.00,
        "default_complimentary_parking_minutes": 15,
        "average_fulfillment_time_minutes": 30,
        "welcome_message": "Want us to grab a few things for you while you park?",
        "storage_locations": ["Vehicle Trunk", "Front Desk", "Refrigerator", "Locker"]
    }

    config_response = requests.put(
        f"{BASE_URL}/convenience/admin/venues/{venue_id}/config",
        headers=staff_headers,
        json=store_config
    )

    if config_response.status_code in [200, 201]:
        config_data = config_response.json()
        print_result("Configure store", True,
                    f"Service fee: {config_data.get('default_service_fee_percent')}%, Min order: ${config_data.get('minimum_order_amount')}")
    else:
        print_result("Configure store", False, f"Status: {config_response.status_code}")
        print(f"Response: {config_response.text}")

    # TEST 2: Add individual items
    print_section("TEST 2: Add Individual Items")

    items_to_add = [
        {
            "name": "Gallon of Milk",
            "description": "Whole milk, 1 gallon",
            "category": "grocery",
            "base_price": 4.99,
            "markup_percent": 10.00,
            "final_price": 5.49,
            "source_store": "Walgreens",
            "source_address": "5280 W Layton Ave, Greenfield, WI",
            "is_active": True,
            "tags": ["dairy", "refrigerated", "popular"]
        },
        {
            "name": "Loaf of Bread",
            "description": "White bread, 20oz",
            "category": "grocery",
            "base_price": 3.49,
            "markup_percent": 10.00,
            "final_price": 3.84,
            "source_store": "Walgreens",
            "is_active": True,
            "tags": ["bakery", "popular"]
        },
        {
            "name": "Bottled Water (6-pack)",
            "description": "Spring water, 16.9oz bottles",
            "category": "beverage",
            "base_price": 5.99,
            "markup_amount": 1.00,
            "final_price": 6.99,
            "source_store": "CVS",
            "is_active": True,
            "tags": ["beverage", "water"]
        },
        {
            "name": "Tylenol (24-count)",
            "description": "Extra strength pain relief",
            "category": "personal_care",
            "base_price": 8.99,
            "markup_percent": 15.00,
            "final_price": 10.34,
            "source_store": "Walgreens",
            "is_active": True,
            "tags": ["medicine", "health"]
        }
    ]

    added_items = []
    for item_data in items_to_add:
        add_response = requests.post(
            f"{BASE_URL}/convenience/admin/venues/{venue_id}/items",
            headers=staff_headers,
            json=item_data
        )

        if add_response.status_code in [200, 201]:
            item = add_response.json()
            added_items.append(item)
            print_result(f"Add item: {item_data['name']}", True,
                        f"Base: ${item_data['base_price']}, Final: ${item_data['final_price']}")
        else:
            print_result(f"Add item: {item_data['name']}", False,
                        f"Status: {add_response.status_code}")
            print(f"Response: {add_response.text}")

    # TEST 3: Bulk import items
    print_section("TEST 3: Bulk Import Items")

    bulk_items = [
        {
            "name": "Snickers Bar",
            "category": "food",
            "base_price": 1.29,
            "markup_percent": 20.00,
            "final_price": 1.55,
            "source_store": "Walgreens",
            "is_active": True
        },
        {
            "name": "Coke (2-liter)",
            "category": "beverage",
            "base_price": 2.49,
            "markup_percent": 15.00,
            "final_price": 2.86,
            "source_store": "Walgreens",
            "is_active": True
        },
        {
            "name": "AAA Batteries (4-pack)",
            "category": "electronics",
            "base_price": 6.99,
            "markup_percent": 20.00,
            "final_price": 8.39,
            "source_store": "CVS",
            "is_active": True
        }
    ]

    bulk_response = requests.post(
        f"{BASE_URL}/convenience/admin/venues/{venue_id}/items/bulk-import",
        headers=staff_headers,
        json={"items": bulk_items}
    )

    if bulk_response.status_code in [200, 201]:
        bulk_result = bulk_response.json()
        imported_count = bulk_result.get('imported_count', len(bulk_items))
        print_result("Bulk import", True, f"Imported {imported_count} items")
    else:
        print_result("Bulk import", False, f"Status: {bulk_response.status_code}")
        print(f"Response: {bulk_response.text}")

    # TEST 4: Browse items as customer
    print_section("TEST 4: Browse Items as Customer")

    browse_response = requests.get(
        f"{BASE_URL}/convenience/venues/{venue_id}/items",
        headers=customer_headers
    )

    if browse_response.status_code == 200:
        items = browse_response.json()
        item_count = len(items) if isinstance(items, list) else items.get('items', [])
        print_result("Browse items", True, f"Found {len(item_count) if isinstance(item_count, list) else item_count} available items")

        # Get categories
        categories_response = requests.get(
            f"{BASE_URL}/convenience/venues/{venue_id}/categories",
            headers=customer_headers
        )

        if categories_response.status_code == 200:
            categories = categories_response.json()
            print(f"   Categories: {', '.join(categories if isinstance(categories, list) else categories.get('categories', []))}")
    else:
        print_result("Browse items", False, f"Status: {browse_response.status_code}")

    # TEST 5: Create a valet session for parking integration
    print_section("TEST 5: Create Valet Session for Order")

    session_data = {
        "venue_id": venue_id,
        "vehicle_plate": "ORDER123",
        "vehicle_make": "Honda",
        "vehicle_model": "Civic",
        "vehicle_color": "Blue",
        "contact_phone": "+15555551111"
    }

    session_response = requests.post(
        f"{BASE_URL}/valet/sessions",
        headers=customer_headers,
        json=session_data
    )

    if session_response.status_code != 201:
        print_result("Create valet session", False, f"Status: {session_response.status_code}")
        print(f"Response: {session_response.text}")
        parking_session_id = None
    else:
        session = session_response.json()
        parking_session_id = session['id']
        print_result("Create valet session", True, f"Session: {session['ticket_number']}")

    # TEST 6: Create an order
    print_section("TEST 6: Create Convenience Order")

    # Use the first few added items
    order_items = []
    if len(added_items) >= 2:
        order_items.append({
            "item_id": added_items[0]['id'],
            "quantity": 1
        })
        order_items.append({
            "item_id": added_items[1]['id'],
            "quantity": 2
        })

    order_data = {
        "venue_id": venue_id,
        "parking_session_id": parking_session_id,
        "items": order_items,
        "delivery_instructions": "Please leave in trunk",
        "special_instructions": "Call when ready",
        "payment_method": "card"
    }

    create_order_response = requests.post(
        f"{BASE_URL}/convenience/orders",
        headers=customer_headers,
        json=order_data
    )

    if create_order_response.status_code not in [200, 201]:
        print_result("Create order", False, f"Status: {create_order_response.status_code}")
        print(f"Response: {create_order_response.text}")
        return

    order = create_order_response.json()
    order_id = order['id']
    order_number = order.get('order_number', 'N/A')

    print_result("Create order", True, f"Order: {order_number}")
    print(f"   Subtotal: ${order.get('subtotal', 0):.2f}")
    print(f"   Service fee: ${order.get('service_fee', 0):.2f}")
    print(f"   Total: ${order.get('total_amount', 0):.2f}")
    print(f"   Status: {order.get('status', 'unknown')}")

    if order.get('complimentary_time_added_minutes'):
        print(f"   🎁 Complimentary parking: {order['complimentary_time_added_minutes']} minutes")

    # TEST 7: Verify pricing calculation
    print_section("TEST 7: Verify Pricing Calculation")

    # Calculate expected pricing
    expected_subtotal = 0
    if len(added_items) >= 2:
        expected_subtotal = added_items[0]['final_price'] + (added_items[1]['final_price'] * 2)

    expected_service_fee = expected_subtotal * 0.15  # 15% service fee
    expected_total = expected_subtotal + expected_service_fee

    actual_subtotal = float(order.get('subtotal', 0))
    actual_service_fee = float(order.get('service_fee', 0))
    actual_total = float(order.get('total_amount', 0))

    pricing_correct = (
        abs(actual_subtotal - expected_subtotal) < 0.01 and
        abs(actual_service_fee - expected_service_fee) < 0.01 and
        abs(actual_total - expected_total) < 0.01
    )

    if pricing_correct:
        print_result("Pricing calculation", True,
                    f"Subtotal: ${actual_subtotal:.2f}, Service fee: ${actual_service_fee:.2f}, Total: ${actual_total:.2f}")
    else:
        print_result("Pricing calculation", False,
                    f"Expected: ${expected_total:.2f}, Got: ${actual_total:.2f}")

    # TEST 8: Order status flow
    print_section("TEST 8: Order Status Flow")

    # Staff accepts order (pending → confirmed)
    accept_response = requests.patch(
        f"{BASE_URL}/convenience/staff/orders/{order_id}/accept",
        headers=staff_headers,
        json={"estimated_ready_time": "30"}
    )

    if accept_response.status_code == 200:
        order = accept_response.json()
        print_result("Accept order (pending → confirmed)", True,
                    f"Status: {order.get('status', 'unknown')}")
    else:
        print_result("Accept order", False, f"Status: {accept_response.status_code}")

    # Start shopping (confirmed → shopping)
    shopping_response = requests.patch(
        f"{BASE_URL}/convenience/staff/orders/{order_id}/start-shopping",
        headers=staff_headers
    )

    if shopping_response.status_code == 200:
        order = shopping_response.json()
        print_result("Start shopping (confirmed → shopping)", True,
                    f"Status: {order.get('status', 'unknown')}")
    else:
        print_result("Start shopping", False, f"Status: {shopping_response.status_code}")

    # Complete shopping (shopping → purchased)
    complete_shopping_response = requests.patch(
        f"{BASE_URL}/convenience/staff/orders/{order_id}/complete-shopping",
        headers=staff_headers,
        json={
            "receipt_photo_url": "https://example.com/receipt.jpg",
            "notes": "All items found"
        }
    )

    if complete_shopping_response.status_code == 200:
        order = complete_shopping_response.json()
        print_result("Complete shopping (shopping → purchased)", True,
                    f"Status: {order.get('status', 'unknown')}")
    else:
        print_result("Complete shopping", False, f"Status: {complete_shopping_response.status_code}")

    # Store items (purchased → stored)
    store_response = requests.patch(
        f"{BASE_URL}/convenience/staff/orders/{order_id}/store",
        headers=staff_headers,
        json={
            "storage_location": "Front Desk",
            "notes": "Stored in main refrigerator"
        }
    )

    if store_response.status_code == 200:
        order = store_response.json()
        print_result("Store items (purchased → stored → ready)", True,
                    f"Status: {order.get('status', 'unknown')}, Location: {order.get('storage_location', 'N/A')}")
    else:
        print_result("Store items", False, f"Status: {store_response.status_code}")

    # Deliver to customer (ready → delivered → completed)
    deliver_response = requests.patch(
        f"{BASE_URL}/convenience/staff/orders/{order_id}/deliver",
        headers=staff_headers,
        json={
            "delivery_photo_url": "https://example.com/delivery.jpg",
            "notes": "Left in trunk as requested"
        }
    )

    if deliver_response.status_code == 200:
        order = deliver_response.json()
        print_result("Deliver order (ready → delivered → completed)", True,
                    f"Status: {order.get('status', 'unknown')}")
    else:
        print_result("Deliver order", False, f"Status: {deliver_response.status_code}")

    # TEST 9: Staff fulfillment - item updates
    print_section("TEST 9: Item Substitution and Updates")

    # Create another order for testing substitutions
    order_data2 = {
        "venue_id": venue_id,
        "items": [{"item_id": added_items[0]['id'], "quantity": 1}] if added_items else [],
        "delivery_instructions": "Test order",
        "payment_method": "card"
    }

    order2_response = requests.post(
        f"{BASE_URL}/convenience/orders",
        headers=customer_headers,
        json=order_data2
    )

    if order2_response.status_code in [200, 201]:
        order2 = order2_response.json()
        order2_id = order2['id']

        # Accept the order
        requests.patch(
            f"{BASE_URL}/convenience/staff/orders/{order2_id}/accept",
            headers=staff_headers
        )

        # Start shopping
        requests.patch(
            f"{BASE_URL}/convenience/staff/orders/{order2_id}/start-shopping",
            headers=staff_headers
        )

        # Update item status (e.g., out of stock, substituted)
        if added_items and 'order_items' in order2 and order2['order_items']:
            order_item_id = order2['order_items'][0]['id']

            update_item_response = requests.post(
                f"{BASE_URL}/convenience/staff/orders/{order2_id}/update-item",
                headers=staff_headers,
                json={
                    "order_item_id": order_item_id,
                    "status": "substituted",
                    "substitution_notes": "Original brand out of stock, substituted with store brand",
                    "actual_price": 4.49
                }
            )

            if update_item_response.status_code == 200:
                print_result("Item substitution", True, "Updated item with substitution")
            else:
                print_result("Item substitution", False, f"Status: {update_item_response.status_code}")
    else:
        print_result("Create test order for substitution", False,
                    f"Status: {order2_response.status_code}")

    # TEST 10: Customer views their orders
    print_section("TEST 10: Customer Order History")

    my_orders_response = requests.get(
        f"{BASE_URL}/convenience/my-orders",
        headers=customer_headers
    )

    if my_orders_response.status_code == 200:
        my_orders = my_orders_response.json()
        order_count = len(my_orders) if isinstance(my_orders, list) else my_orders.get('total', 0)
        print_result("View order history", True, f"Found {order_count} order(s)")
    else:
        print_result("View order history", False, f"Status: {my_orders_response.status_code}")

    # TEST 11: Order cancellation
    print_section("TEST 11: Order Cancellation")

    # Create another order to cancel
    order_data3 = {
        "venue_id": venue_id,
        "items": [{"item_id": added_items[0]['id'], "quantity": 1}] if added_items else [],
        "payment_method": "card"
    }

    order3_response = requests.post(
        f"{BASE_URL}/convenience/orders",
        headers=customer_headers,
        json=order_data3
    )

    if order3_response.status_code in [200, 201]:
        order3 = order3_response.json()
        order3_id = order3['id']

        # Customer cancels order
        cancel_response = requests.patch(
            f"{BASE_URL}/convenience/orders/{order3_id}/cancel",
            headers=customer_headers,
            json={"reason": "Changed my mind"}
        )

        if cancel_response.status_code == 200:
            cancelled_order = cancel_response.json()
            print_result("Cancel order", True,
                        f"Status: {cancelled_order.get('status', 'unknown')}")
        else:
            print_result("Cancel order", False, f"Status: {cancel_response.status_code}")
    else:
        print_result("Create order for cancellation test", False,
                    f"Status: {order3_response.status_code}")

    # TEST 12: Admin refund
    print_section("TEST 12: Admin Refund")

    # Create order for refund test
    order_data4 = {
        "venue_id": venue_id,
        "items": [{"item_id": added_items[0]['id'], "quantity": 1}] if added_items else [],
        "payment_method": "card"
    }

    order4_response = requests.post(
        f"{BASE_URL}/convenience/orders",
        headers=customer_headers,
        json=order_data4
    )

    if order4_response.status_code in [200, 201]:
        order4 = order4_response.json()
        order4_id = order4['id']

        # Staff accepts and then needs to refund
        requests.patch(
            f"{BASE_URL}/convenience/staff/orders/{order4_id}/accept",
            headers=staff_headers
        )

        # Admin issues refund
        refund_response = requests.patch(
            f"{BASE_URL}/convenience/admin/venues/{venue_id}/orders/{order4_id}/refund",
            headers=staff_headers,
            json={
                "refund_amount": order4.get('total_amount'),
                "reason": "Items not available"
            }
        )

        if refund_response.status_code == 200:
            refunded_order = refund_response.json()
            print_result("Issue refund", True,
                        f"Refunded ${refunded_order.get('refund_amount', 0):.2f}")
        else:
            print_result("Issue refund", False, f"Status: {refund_response.status_code}")
    else:
        print_result("Create order for refund test", False,
                    f"Status: {order4_response.status_code}")

    # TEST 13: Edge cases
    print_section("TEST 13: Edge Cases")

    # Test minimum order amount
    if len(added_items) > 0:
        small_order = {
            "venue_id": venue_id,
            "items": [{"item_id": added_items[0]['id'], "quantity": 1}],
            "payment_method": "card"
        }

        # Check if item price is below minimum
        if added_items[0]['final_price'] < 5.00:
            small_order_response = requests.post(
                f"{BASE_URL}/convenience/orders",
                headers=customer_headers,
                json=small_order
            )

            if small_order_response.status_code == 400:
                print_result("Minimum order validation", True, "Correctly rejected order below minimum")
            else:
                print_result("Minimum order validation", False,
                            f"Should reject orders below ${store_config['minimum_order_amount']}")

    # Test invalid item
    invalid_order = {
        "venue_id": venue_id,
        "items": [{"item_id": "00000000-0000-0000-0000-000000000000", "quantity": 1}],
        "payment_method": "card"
    }

    invalid_response = requests.post(
        f"{BASE_URL}/convenience/orders",
        headers=customer_headers,
        json=invalid_order
    )

    if invalid_response.status_code in [400, 404]:
        print_result("Invalid item validation", True, "Correctly rejected invalid item")
    else:
        print_result("Invalid item validation", False, "Should reject invalid items")

    # Test excessive quantity
    large_quantity_order = {
        "venue_id": venue_id,
        "items": [{"item_id": added_items[0]['id'], "quantity": 100}] if added_items else [],
        "payment_method": "card"
    }

    large_qty_response = requests.post(
        f"{BASE_URL}/convenience/orders",
        headers=customer_headers,
        json=large_quantity_order
    )

    # May or may not reject - depends on max_quantity_per_order
    if large_qty_response.status_code in [400, 422]:
        print_result("Quantity limit validation", True, "Correctly rejected excessive quantity")
    else:
        print_result("Quantity limit validation", False, "Should validate max quantity per order")

    # TEST 14: Customer rating
    print_section("TEST 14: Customer Rating")

    # Rate the first completed order
    rating_response = requests.post(
        f"{BASE_URL}/convenience/orders/{order_id}/rate",
        headers=customer_headers,
        json={
            "rating": 5,
            "feedback": "Great service! Items were fresh and delivered quickly."
        }
    )

    if rating_response.status_code == 200:
        rated_order = rating_response.json()
        print_result("Rate order", True,
                    f"Rating: {rated_order.get('rating', 'N/A')}/5")
    else:
        print_result("Rate order", False, f"Status: {rating_response.status_code}")

    # TEST 15: Toggle item availability
    print_section("TEST 15: Toggle Item Availability")

    if len(added_items) > 0:
        item_id = added_items[0]['id']

        toggle_response = requests.patch(
            f"{BASE_URL}/convenience/admin/venues/{venue_id}/items/{item_id}/toggle",
            headers=staff_headers
        )

        if toggle_response.status_code == 200:
            toggled_item = toggle_response.json()
            print_result("Toggle item availability", True,
                        f"Item is now {'active' if toggled_item.get('is_active') else 'inactive'}")
        else:
            print_result("Toggle item availability", False,
                        f"Status: {toggle_response.status_code}")

    # TEST 16: Admin order management
    print_section("TEST 16: Admin Order Management")

    admin_orders_response = requests.get(
        f"{BASE_URL}/convenience/admin/venues/{venue_id}/orders",
        headers=staff_headers
    )

    if admin_orders_response.status_code == 200:
        admin_orders = admin_orders_response.json()
        order_count = len(admin_orders) if isinstance(admin_orders, list) else admin_orders.get('total', 0)
        print_result("Admin view all orders", True, f"Found {order_count} order(s)")

        # Get specific order details
        if order_count > 0:
            detail_response = requests.get(
                f"{BASE_URL}/convenience/admin/venues/{venue_id}/orders/{order_id}",
                headers=staff_headers
            )

            if detail_response.status_code == 200:
                order_detail = detail_response.json()
                print_result("Admin view order details", True,
                            f"Order {order_detail.get('order_number', 'N/A')} - {order_detail.get('status', 'unknown')}")
            else:
                print_result("Admin view order details", False,
                            f"Status: {detail_response.status_code}")
    else:
        print_result("Admin view all orders", False, f"Status: {admin_orders_response.status_code}")

    # TEST 17: Get specific item details
    print_section("TEST 17: Get Item Details")

    if len(added_items) > 0:
        item_id = added_items[0]['id']

        # Customer view
        item_response = requests.get(
            f"{BASE_URL}/convenience/venues/{venue_id}/items/{item_id}",
            headers=customer_headers
        )

        if item_response.status_code == 200:
            item_detail = item_response.json()
            print_result("Get item details (customer)", True,
                        f"{item_detail.get('name', 'N/A')} - ${item_detail.get('final_price', 0):.2f}")
        else:
            print_result("Get item details (customer)", False,
                        f"Status: {item_response.status_code}")

        # Admin view
        admin_item_response = requests.get(
            f"{BASE_URL}/convenience/admin/venues/{venue_id}/items/{item_id}",
            headers=staff_headers
        )

        if admin_item_response.status_code == 200:
            admin_item = admin_item_response.json()
            print_result("Get item details (admin)", True,
                        f"Base: ${admin_item.get('base_price', 0):.2f}, Markup: {admin_item.get('markup_percent', 0)}%")
        else:
            print_result("Get item details (admin)", False,
                        f"Status: {admin_item_response.status_code}")

    # Summary
    print_section("TEST SUMMARY")
    print("All convenience store tests completed!")
    print("\n✅ Test Coverage:")
    print("   1. Configure convenience store for venue")
    print("   2. Add individual items")
    print("   3. Bulk import items")
    print("   4. Browse items as customer")
    print("   5. Create valet session (parking integration)")
    print("   6. Create convenience order")
    print("   7. Verify pricing calculations (base + markup + service fee)")
    print("   8. Order status flow (pending → confirmed → shopping → purchased → stored → ready → delivered → completed)")
    print("   9. Item substitutions and updates")
    print("   10. Customer order history")
    print("   11. Order cancellation")
    print("   12. Admin refund processing")
    print("   13. Edge cases (minimum order, invalid items, quantity limits)")
    print("   14. Customer ratings")
    print("   15. Toggle item availability")
    print("   16. Admin order management")
    print("   17. Get item details")
    print("\n📋 Manual Testing Needed:")
    print("   - Stripe payment integration (requires test cards)")
    print("   - Receipt photo upload")
    print("   - Delivery photo upload")
    print("   - Age verification for restricted items")
    print("   - Operating hours restrictions")
    print("   - Real-time notifications (SMS/push)")
    print("   - Multiple staff members working on different orders")
    print("   - Concurrent order handling")
    print("   - Performance with large item catalogs (1000+ items)")
    print()


if __name__ == "__main__":
    test_convenience_store()
