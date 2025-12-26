#!/usr/bin/env python3
"""
Test script to verify frontend-backend connection
"""

import requests
import json
import time
from threading import Thread
import subprocess
import sys
import os

def test_backend_endpoints():
    """Test all backend endpoints that the frontend expects"""
    
    base_url = "http://localhost:5000"
    
    print("Testing backend endpoints...")
    print("=" * 50)
    
    endpoints_to_test = [
        ("/", "GET", "Home endpoint"),
        ("/health", "GET", "Health check"),
        ("/menu", "GET", "Menu data"),
        ("/dishes", "GET", "Dishes data"),
        ("/info", "GET", "Restaurant info"),
        ("/query", "POST", "Query processing"),
        ("/conversation", "POST", "Conversation management"),
        ("/tools", "GET", "Tools listing"),
        ("/agents", "GET", "Agents listing"),
        ("/memory", "GET", "Memory access"),
        ("/debug", "GET", "Debug info"),
        ("/reset", "POST", "System reset")
    ]
    
    passed = 0
    failed = 0
    
    for endpoint, method, description in endpoints_to_test:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}")
            elif method == "POST":
                if endpoint == "/query":
                    response = requests.post(f"{base_url}{endpoint}", json={"query": "Hello"})
                elif endpoint == "/conversation":
                    response = requests.post(f"{base_url}{endpoint}", json={"action": "start"})
                elif endpoint == "/reservations":
                    response = requests.post(f"{base_url}{endpoint}", json={
                        "name": "Test User",
                        "phone": "1234567890",
                        "date": "2023-12-31",
                        "time": "19:00",
                        "guests": 2
                    })
                else:
                    response = requests.post(f"{base_url}{endpoint}", json={})
            
            status = "✓ PASS" if response.status_code < 400 else "✗ FAIL"
            print(f"{status} {method} {endpoint} - {description}")
            print(f"    Status: {response.status_code}")
            
            if response.status_code < 400:
                passed += 1
            else:
                failed += 1
                print(f"    Error: {response.text[:100]}")
                
        except Exception as e:
            print(f"✗ FAIL {method} {endpoint} - {description}")
            print(f"    Exception: {str(e)}")
            failed += 1
        
        print()
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    return failed == 0


def start_backend():
    """Start the backend server in a separate thread"""
    
    # Change to backend directory
    backend_dir = os.path.join("back", "src")
    os.chdir(backend_dir)
    
    # Start the Flask app
    cmd = [sys.executable, "run/app_langchain.py"]
    
    print("Starting backend server...")
    print(f"Command: {' '.join(cmd)}")
    print(f"Working directory: {os.getcwd()}")
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait a bit for server to start
    time.sleep(5)
    
    return process


def main():
    """Main test function"""
    
    print("Frontend-Backend Connection Test")
    print("=" * 50)
    
    # Start backend server
    backend_process = start_backend()
    
    try:
        # Test the endpoints
        success = test_backend_endpoints()
        
        if success:
            print("\n🎉 All tests passed! Frontend and backend are properly connected.")
            print("\nYou can now:")
            print("1. Start the frontend: cd front/resto-ai-voice && npm run dev")
            print("2. The frontend will connect to the backend at http://localhost:5000")
            print("3. All API endpoints are working correctly")
        else:
            print("\n❌ Some tests failed. Please check the backend implementation.")
            
    finally:
        # Clean up
        print("\nStopping backend server...")
        backend_process.terminate()
        backend_process.wait()


if __name__ == "__main__":
    main()