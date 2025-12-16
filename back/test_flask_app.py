#!/usr/bin/env python3

import os
import sys
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Add src to path
sys.path.append('src')

# Import Flask app
from run.app import app, get_db

# Test the database connection through the Flask app
db_instance = get_db()
print(f"Flask app database connected: {db_instance.connected if db_instance else False}")

# Test getting menu through the Flask route
with app.test_client() as client:
    response = client.get('/api/menu')
    print(f"Menu API response status: {response.status_code}")
    if response.status_code == 200:
        data = response.get_json()
        print(f"Menu categories: {len(data.get('categories', []))}")
    else:
        print(f"Menu API error: {response.get_json()}")

print("Flask app test completed!")