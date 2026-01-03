from models.mongodb import db
from bson.objectid import ObjectId

def test_connection():
    """Test MongoDB connection"""
    if db.connected:
        print("[TEST] MongoDB is connected ✅")
    else:
        print("[TEST] MongoDB connection failed ❌")

def test_get_restaurant_info():
    info = db.get_restaurant_info()
    print("[TEST] Restaurant Info:")
    print(info)

def test_reservation_crud():
    # Create a test reservation
    test_reservation = {
        "date_time": "2025-12-31T20:00:00",
        "customer_name": "Alice Test",
        "customer_phone": "0600000000",
        "nb_person": 2,
        "table_id": ObjectId("691e0c068f62a199364285bc"),
        "special_requests": "Window seat"
    }

    created = db.create_reservation(test_reservation)
    if created:
        print("[TEST] Created reservation ✅", created)
    else:
        print("[TEST] Failed to create reservation ❌")
        return

    res_id = created["_id"]

    # Get reservation
    fetched = db.get_reservation(res_id)
    print("[TEST] Fetched reservation:", fetched)

    # Update reservation
    updated = db.update_reservation(res_id, {"nb_person": 3})
    print("[TEST] Updated reservation:", updated)

    # Cancel reservation
    cancelled = db.cancel_reservation(res_id)
    print("[TEST] Cancelled reservation:", cancelled)

def test_dishes():
    all_dishes = db.get_all_dishes()
    print(f"[TEST] All dishes ({len(all_dishes)}):")
    for d in all_dishes[:3]:  # print only first 3 for brevity
        print(d)

    by_category = db.get_dishes_by_category()
    print("[TEST] Dishes by category:")
    for cat, dishes in by_category.items():
        print(f"Category '{cat}': {len(dishes)} dishes")

def test_tables_and_orders():
    tables = db.get_tables()
    print(f"[TEST] Tables ({len(tables)}):")
    for t in tables:
        print(t)

    # Create a test order
    test_order = {
        "order_type": "delivery",
        "customer_name": "Alice Test",
        "customer_phone": "0600000000",
        "delivery_address": {
            "street": "123 Test St",
            "city": "Paris",
            "postal_code": "75001"
        },
        "delivery_time": "2025-12-25T19:00:00",
        "items": [],
        "menus": [],
        "order_status": "pending"
    }

    created_order = db.create_order(test_order)
    print("[TEST] Created order:", created_order)

if __name__ == "__main__":
    test_connection()
    test_get_restaurant_info()
    test_reservation_crud()
    test_dishes()
    test_tables_and_orders()

    db.close()
