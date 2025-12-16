#!/usr/bin/env python3

import os
import sys
import dotenv

# Load environment variables first
sys.path.append('src')
dotenv.load_dotenv()

from models.mongodb import MongoDBManager

def test_mongodb_connection():
    """Test MongoDB connection with fallback"""
    print("Testing MongoDB connection...")
    
    try:
        # This will trigger the singleton initialization
        db = MongoDBManager()
        
        if db.connected:
            print("[SUCCESS] MongoDB connected successfully!")
            
            # Test getting menu
            menu = db.get_menu()
            if menu:
                print(f"[SUCCESS] Menu retrieved: {len(menu.get('categories', []))} categories")
            else:
                print("[ERROR] Menu not found")
                
            # Test creating a reservation
            test_reservation = {
                "name": "Test User",
                "phone": "+33612345678",
                "date": "2023-12-15",
                "time": "20:00",
                "guests": 2
            }
            
            created = db.create_reservation(test_reservation)
            if created:
                print(f"[SUCCESS] Reservation created: {created['name']} for {created['guests']} people")
            else:
                print("[ERROR] Failed to create reservation")
                
        else:
            print("[WARNING] MongoDB not connected, using fallback mode")
            print("[INFO] Application will use in-memory storage")
            
    except Exception as e:
        print(f"[ERROR] Error during MongoDB test: {e}")
        
    print("\nTest completed!")

if __name__ == "__main__":
    test_mongodb_connection()