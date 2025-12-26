"""
Flask API for the Voice-Enabled GenAI Restaurant Assistant
This API connects the frontend with the agent system and database
"""

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import our agent system and models
from models.llm import MistralWrapper
from models.mongodb import MongoDBManager
from agents.restaurant_agent import RestaurantAgent

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize components
db_manager = MongoDBManager()

# Try to initialize LLM (will use mock if API key not available)
try:
    mistral_api_key = os.environ.get("MISTRAL_API_KEY")
    if mistral_api_key:
        llm = MistralWrapper(api_key=mistral_api_key)
        print("[SUCCESS] Mistral LLM initialized with API key")
    else:
        print("[WARNING] No Mistral API key found, using mock LLM")
        llm = None
        
    # Initialize agent
    agent = RestaurantAgent(llm=llm, use_mock_db=not db_manager.connected)
    print("[SUCCESS] Restaurant Agent initialized")
    
except Exception as e:
    print(f"[ERROR] Error initializing agent system: {e}")
    # Fallback to mock agent
    class MockLLM:
        def generate_from_prompt(self, prompt, history=None):
            return "Désolé, le système LLM n'est pas disponible pour le moment. Voici une réponse basique."
    
    llm = MockLLM()
    agent = RestaurantAgent(llm=llm, use_mock_db=True)
    print("[SUCCESS] Fallback Mock Agent initialized")

@app.route('/')
def home():
    """Home endpoint"""
    return jsonify({
        "status": "running",
        "service": "Restaurant Assistant API",
        "version": "1.0.0",
        "endpoints": [
            "/query",
            "/menu", 
            "/dishes",
            "/reservations",
            "/info"
        ]
    })

@app.route('/query', methods=['POST'])
def handle_query():
    """
    Handle user queries (both text and audio)
    Expected JSON: {"query": "user message"}
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "error": "Missing query parameter"
            }), 400
            
        user_query = data['query']
        
        if not user_query or user_query.strip() == "":
            return jsonify({
                "error": "Empty query"
            }), 400
            
        print(f"[RECEIVED] Query: {user_query}")
        
        # Process the query with our agent
        response = agent.process_user_input(user_query)
        
        # Get conversation history
        history = []
        for i in range(0, len(agent.conversation_history), 2):
            if i+1 < len(agent.conversation_history):
                history.append({
                    "role": "user",
                    "content": agent.conversation_history[i]["content"],
                    "timestamp": datetime.now().isoformat()
                })
                history.append({
                    "role": "assistant", 
                    "content": agent.conversation_history[i+1]["content"],
                    "timestamp": datetime.now().isoformat()
                })
        
        return jsonify({
            "response": response,
            "agent_processing": True,
            "history": history,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"[ERROR] Processing query failed: {e}")
        return jsonify({
            "error": "Failed to process query",
            "details": str(e)
        }), 500

@app.route('/menu', methods=['GET'])
def get_menu():
    """Get the restaurant menu"""
    try:
        if db_manager.connected:
            menu_data = db_manager.get_menu()
        else:
            menu_data = agent.tools.get_menu()
            
        if not menu_data:
            return jsonify({
                "error": "Menu not available"
            }), 404
            
        # Ensure consistent format
        if "categories" not in menu_data:
            menu_data = {"categories": []}
            
        return jsonify(menu_data)
        
    except Exception as e:
        print(f"[ERROR] Fetching menu failed: {e}")
        return jsonify({
            "error": "Failed to fetch menu",
            "details": str(e)
        }), 500

@app.route('/dishes', methods=['GET'])
def get_dishes():
    """Get all dishes grouped by category"""
    try:
        if db_manager.connected:
            dishes_by_category = db_manager.get_dishes_by_category()
        else:
            # Get from mock tools and format properly
            menu_data = agent.tools.get_menu()
            dishes_by_category = {}
            
            for category in menu_data.get("categories", []):
                category_name = category["name"]
                dishes = []
                
                for item in category.get("items", []):
                    dish = {
                        "_id": f"dish_{category_name.lower()}_{item['name'].lower().replace(' ', '_')}",
                        "name": item["name"],
                        "category": category_name,
                        "ingredients": [],  # Would be populated from real DB
                        "is_vegetarian": False,  # Would be populated from real DB
                        "price": float(item["price"].replace("€", "").strip())
                    }
                    dishes.append(dish)
                
                dishes_by_category[category_name] = dishes
        
        return jsonify(dishes_by_category)
        
    except Exception as e:
        print(f"[ERROR] Fetching dishes failed: {e}")
        return jsonify({
            "error": "Failed to fetch dishes",
            "details": str(e)
        }), 500

@app.route('/reservations', methods=['POST'])
def create_reservation():
    """Create a new reservation"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No reservation data provided"
            }), 400
            
        # Validate required fields
        required_fields = ['name', 'phone', 'date', 'time', 'guests']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Create reservation
        try:
            if db_manager.connected:
                reservation = db_manager.create_reservation(data)
            else:
                reservation = agent.tools.create_reservation(data)
            
            if not reservation:
                return jsonify({
                    "success": False,
                    "error": "Failed to create reservation"
                }), 500
                
        except Exception as e:
            print(f"[ERROR] Reservation creation failed: {e}")
            return jsonify({
                "success": False,
                "error": "Failed to create reservation",
                "details": str(e)
            }), 500
            
        # Format response to match frontend expectations
        formatted_reservation = {
            "success": True,
            "reservation": {
                "name": reservation.get("name", data["name"]),
                "phone": reservation.get("phone", data["phone"]),
                "date": reservation.get("date", data["date"]),
                "time": reservation.get("time", data["time"]),
                "guests": reservation.get("guests", data["guests"]),
                "specialRequests": reservation.get("specialRequests", data.get("specialRequests", "")),
                "createdAt": reservation.get("createdAt", datetime.now().isoformat()),
                "updatedAt": reservation.get("updatedAt", datetime.now().isoformat()),
                "status": reservation.get("status", "confirmed")
            }
        }
        
        return jsonify(formatted_reservation)
        
    except Exception as e:
        print(f"[ERROR] Creating reservation failed: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to create reservation",
            "details": str(e)
        }), 500

@app.route('/info', methods=['GET'])
def get_restaurant_info():
    """Get restaurant information"""
    try:
        if db_manager.connected:
            info = db_manager.get_restaurant_info()
        else:
            info = agent.tools.get_restaurant_info()
        
        # Ensure all required fields are present
        default_info = {
            "name": "Les Pieds dans le Plat",
            "address": "1 Avenue des Champs-Élysées, 75008 Paris, France",
            "phone": "+33 1 23 45 67 89",
            "openingHours": "11:00 AM - 01:00 AM",
            "description": "Un restaurant traditionnel français au cœur de Paris, offrant une cuisine raffinée dans une ambiance chaleureuse."
        }
        
        # Merge with actual info
        for key, value in default_info.items():
            if key not in info:
                info[key] = value
        
        return jsonify(info)
        
    except Exception as e:
        print(f"[ERROR] Fetching restaurant info failed: {e}")
        return jsonify({
            "error": "Failed to fetch restaurant information",
            "details": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if db_manager.connected else "mock",
        "llm": "connected" if llm and hasattr(llm, 'client') else "mock"
    })

@app.route('/reset', methods=['POST'])
def reset_conversation():
    """Reset the conversation history"""
    try:
        agent.reset_conversation()
        return jsonify({
            "success": True,
            "message": "Conversation history reset"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "details": str(error)
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "details": str(error)
    }), 500

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    print(f"[LAUNCH] Starting Restaurant Assistant API on port {port}")
    print(f"[INFO] Database status: {'Connected' if db_manager.connected else 'Using mock data'}")
    print(f"[INFO] LLM status: {'Connected' if llm and hasattr(llm, 'client') else 'Using mock LLM'}")
    print(f"[INFO] API will be available at: http://localhost:{port}")
    print("\n[INFO] Available endpoints:")
    print("   GET    /              - Home")
    print("   POST   /query         - Handle user queries")
    print("   GET    /menu          - Get restaurant menu")
    print("   GET    /dishes        - Get all dishes by category")
    print("   POST   /reservations  - Create reservation")
    print("   GET    /info          - Get restaurant info")
    print("   GET    /health        - Health check")
    print("   POST   /reset         - Reset conversation")
    
    app.run(host='0.0.0.0', port=port, debug=True)