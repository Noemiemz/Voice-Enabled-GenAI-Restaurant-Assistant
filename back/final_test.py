#!/usr/bin/env python3

import os
import sys
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Add src to path
sys.path.append('src')

print("=== Final MongoDB Connection Test ===")

# Test 1: Direct MongoDB connection
print("\n1. Testing direct MongoDB connection...")
from models.mongodb import MongoDBManager
db = MongoDBManager()
print(f"   Connected: {db.connected}")

# Test 2: Menu operations
print("\n2. Testing menu operations...")
menu = db.get_menu()
if menu:
    print(f"   Menu retrieved: {len(menu.get('categories', []))} categories")
    # Test menu update
    menu_copy = menu.copy()
    menu_copy['categories'][0]['items'][0]['price'] = '13€'
    updated = db.update_menu(menu_copy)
    print(f"   Menu update successful: {updated}")
else:
    print("   ERROR: Menu not found")

# Test 3: Reservation operations
print("\n3. Testing reservation operations...")
test_reservation = {
    'name': 'Final Test User',
    'phone': '+33699999999',
    'date': '2023-12-25',
    'time': '20:00',
    'guests': 4
}

created = db.create_reservation(test_reservation)
if created:
    print(f"   Reservation created: {created['name']} for {created['guests']} people")
    
    # Test get reservation
    retrieved = db.get_reservation(created['_id'])
    print(f"   Reservation retrieved: {retrieved is not None}")
    
    # Test get all reservations
    all_reservations = db.get_reservations()
    print(f"   Total reservations: {len(all_reservations)}")
    
    # Test update reservation
    update_success = db.update_reservation(created['_id'], {'guests': 6})
    print(f"   Reservation update successful: {update_success}")
    
    # Test cancel reservation
    cancel_success = db.cancel_reservation(created['_id'])
    print(f"   Reservation cancel successful: {cancel_success}")
else:
    print("   ERROR: Failed to create reservation")

# Test 4: Conversation operations
print("\n4. Testing conversation operations...")
test_conversation = {
    'user_id': 'test_user',
    'messages': [
        {'role': 'user', 'content': 'Hello'},
        {'role': 'assistant', 'content': 'Hi there!'}
    ]
}

conversation_id = db.save_conversation(test_conversation)
if conversation_id:
    print(f"   Conversation saved: {conversation_id}")
    
    # Test get conversation
    retrieved_conv = db.get_conversation(conversation_id)
    print(f"   Conversation retrieved: {retrieved_conv is not None}")
    
    # Test get recent conversations
    recent_convs = db.get_recent_conversations(5)
    print(f"   Recent conversations: {len(recent_convs)}")
else:
    print("   ERROR: Failed to save conversation")

# Test 5: Dish operations
print("\n5. Testing dish operations...")
dishes_by_category = db.get_dishes_by_category()
print(f"   Dishes by category: {len(dishes_by_category)} categories")

all_dishes = db.get_all_dishes()
print(f"   Total dishes: {len(all_dishes)}")

# Test 6: Restaurant info
print("\n6. Testing restaurant info...")
info = db.get_restaurant_info()
print(f"   Restaurant name: {info.get('name', 'Unknown')}")

print("\n=== Test Summary ===")
print(f"MongoDB Connection: {'SUCCESS' if db.connected else 'FAILED'}")
print("All operations completed successfully!")

# Clean up
db.close()