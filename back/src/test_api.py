"""
Simple test script to verify the API is working
"""

import requests
import json
import time

# Wait a moment for the API to start
print("Waiting for API to start...")
time.sleep(2)

base_url = "http://localhost:5000"

def test_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    url = f"{base_url}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        
        print(f"\n[TEST] Testing {method} {endpoint}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("[SUCCESS] Success!")
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except:
                print(f"Response: {response.text[:200]}...")
        else:
            print("[ERROR] Failed!")
            print(f"Response: {response.text}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"[ERROR] Testing {endpoint} failed: {e}")
        return False

def main():
    """Run all API tests"""
    print("[LAUNCH] Testing Restaurant Assistant API")
    print("=" * 50)
    
    # Test endpoints
    tests = [
        ("/", "GET"),
        ("/health", "GET"),
        ("/menu", "GET"),
        ("/dishes", "GET"),
        ("/info", "GET"),
        ("/query", "POST", {"query": "Bonjour, je voudrais voir le menu"}),
        ("/reservations", "POST", {
            "name": "Test User",
            "phone": "+33 6 00 00 00 00",
            "date": "2023-12-01",
            "time": "19:00",
            "guests": 2
        }),
        ("/reset", "POST")
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if len(test) == 3:
            endpoint, method, data = test
            if test_endpoint(endpoint, method, data):
                passed += 1
        else:
            endpoint, method = test
            if test_endpoint(endpoint, method):
                passed += 1
    
    print(f"\n[RESULTS] Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("[SUCCESS] All tests passed! API is working correctly.")
    else:
        print("[WARNING] Some tests failed. Check the API server.")

if __name__ == "__main__":
    main()