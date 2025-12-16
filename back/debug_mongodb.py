#!/usr/bin/env python3

import os
import sys
import dotenv

# Load environment variables first
dotenv.load_dotenv()

print("Environment variables loaded:")
print(f"MONGODB_URI: {os.environ.get('MONGODB_URI')}")
print(f"MONGODB_DB_NAME: {os.environ.get('MONGODB_DB_NAME')}")

# Add src to path
sys.path.append('src')

# Now import and test
try:
    from models.mongodb import MongoDBManager
    print("MongoDBManager imported successfully")
    
    # Create instance
    db = MongoDBManager()
    print(f"MongoDBManager instance created, connected: {db.connected}")
    
    # Try to get menu
    menu = db.get_menu()
    print(f"Menu retrieved: {menu is not None}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()