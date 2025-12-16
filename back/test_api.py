#!/usr/bin/env python3

import requests
import json
import os

# Set the API base URL
API_BASE_URL = "http://localhost:5000/api"

def test_get_restaurant_info():
    """Test getting restaurant information"""
    print("Testing GET /api/info...")
    try:
        response = requests.get(f"{API_BASE_URL}/info")
        if response.status_code == 200:
            print("✅ Success:", json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_get_menu():
    """Test getting menu"""
    print("\nTesting GET /api/menu...")
    try:
        response = requests.get(f"{API_BASE_URL}/menu")
        if response.status_code == 200:
            print("✅ Success:", json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_chat():
    """Test chat endpoint"""
    print("\nTesting POST /api/chat...")
    try:
        data = {
            "message": "Bonjour, je voudrais réserver une table pour ce soir",
            "history": []
        }
        response = requests.post(f"{API_BASE_URL}/chat", json=data)
        if response.status_code == 200:
            print("✅ Success:", json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_create_reservation():
    """Test creating a reservation"""
    print("\nTesting POST /api/reservations...")
    try:
        data = {
            "name": "Jean Dupont",
            "phone": "+33612345678",
            "date": "2023-12-15",
            "time": "20:00",
            "guests": 4
        }
        response = requests.post(f"{API_BASE_URL}/reservations", json=data)
        if response.status_code == 200:
            print("✅ Success:", json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_text_to_speech():
    """Test text to speech"""
    print("\nTesting POST /api/tts...")
    try:
        data = {
            "text": "Bonjour et bienvenue chez Les Pieds dans le Plat!"
        }
        response = requests.post(f"{API_BASE_URL}/tts", json=data)
        if response.status_code == 200:
            print("✅ Success: TTS generated successfully")
            # Save audio to file
            audio_data = bytes.fromhex(response.json()["audio"])
            with open("test_output.wav", "wb") as f:
                f.write(audio_data)
            print("Audio saved to test_output.wav")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("Testing Restaurant Assistant API...")
    print("=" * 50)
    
    # Run tests
    test_get_restaurant_info()
    test_get_menu()
    test_chat()
    test_create_reservation()
    test_text_to_speech()
    
    print("\n" + "=" * 50)
    print("API testing completed!")