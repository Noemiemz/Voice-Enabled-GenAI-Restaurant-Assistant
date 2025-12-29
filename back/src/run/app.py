"""
Flask API for the Voice-Enabled GenAI Restaurant Assistant
This API connects the frontend with the new agent system and database
"""

import os
import sys
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import our agent system and models
from models.llm import MistralWrapper
from models.mongodb import MongoDBManager
from tools.mongodb_tools import MongoDBTools
from agents.orchestrator import create_orchestrator_agent
from agents.agent_manager import AgentManager
from utils.utils import Context
from utils.timing import log_timing, start_timing, end_timing


# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize components
db_manager = MongoDBManager()
agent_manager = AgentManager()

# Try to initialize LLM (will use mock if API key not available)
try:
    mistral_api_key = os.environ.get("MISTRAL_API_KEY")
    if mistral_api_key:
        llm = MistralWrapper(api_key=mistral_api_key)
        print("[SUCCESS] Mistral LLM initialized with API key")
    else:
        print("[WARNING] No Mistral API key found, using mock LLM")
        llm = None

    # Initialize agents using the agent manager
    agent_manager.initialize()
    orchestrator = create_orchestrator_agent(agent_manager)
    database = MongoDBTools()
    print("[SUCCESS] Agents initialized")

except Exception as e:
    print(f"[ERROR] Error initializing agent system: {e}")
    llm = None
    orchestrator = None
    database = None


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
            "/info",
            "/performance/logs"
        ]
    })

@app.route('/query', methods=['POST'])
def handle_query():
    """
    Handle user queries (both text and audio)
    Expected JSON: {"query": "user message"}
    """
    # Start timing the entire query processing
    query_start = time.time()
    
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

        # Process the query with our orchestrator agent
        if orchestrator is None:
            return jsonify({
                "error": "Orchestrator not initialized"
            }), 500
        
        # Create a unique session/user ID (you can customize this based on your needs)
        user_id = request.headers.get('X-User-ID', 'default_user')
        
        # Create context for the agent
        context = Context(user_id=user_id, verbose=True)
        
        # Create config for thread management
        config = {"configurable": {"thread_id": user_id}}
        
        # Start timing orchestrator processing
        orchestrator_start = time.time()
        
        # Invoke the orchestrator
        result = orchestrator.invoke(
            {"messages": [{"role": "user", "content": user_query}]},
            config=config,
            context=context,
        )
        
        # Extract the response
        response = result["messages"][-1].content if result.get("messages") else "No response"
        
        # Log orchestrator processing time
        orchestrator_duration = time.time() - orchestrator_start
        log_timing("agent_invocation", orchestrator_duration, {
            "user_id": user_id,
            "agent_name": "orchestrator",
            "query_length": len(user_query),
            "query_preview": user_query[:50] + "..." if len(user_query) > 50 else user_query,
            "query_full": user_query,
            "invoked_by": "api_endpoint",
            "endpoint": "/query",
            "messages_count": len(result.get("messages", [])),
            "response_length": len(response),
            "response_preview": response[:100] + "..." if len(response) > 100 else response,
            "response_full": response
        })
        
        
        # Build history (last 5 messages)
        history = []
        if result.get("messages"):
            for msg in result["messages"][-5:]:
                history.append({
                    "role": getattr(msg, 'role', 'assistant'),
                    "content": getattr(msg, 'content', str(msg))
                })

        # Calculate total query processing time
        total_duration = time.time() - query_start
        
        # Log total processing time
        log_timing("total_query_processing", total_duration, {
            "user_id": user_id,
            "query_length": len(user_query),
            "response_length": len(response),
            "orchestrator_time": round(orchestrator_duration, 6),
            "overhead_time": round(total_duration - orchestrator_duration, 6),
            "success": True,
            "endpoint": "/query"
        })

        return jsonify({
            "response": response,
            "agent_processing": True,
            "history": history,
            "timestamp": datetime.now().isoformat(),
            "performance": {
                "total_processing_time": round(total_duration, 6),
                "orchestrator_time": round(orchestrator_duration, 6)
            }
        })

    except Exception as e:
        print(f"[ERROR] Processing query failed: {e}")
        
        # Log error processing time
        error_duration = time.time() - query_start
        log_timing("query_error_processing", error_duration, {
            "error": str(e),
            "user_id": request.headers.get('X-User-ID', 'default_user')
        })
        
        return jsonify({
            "error": "Failed to process query",
            "details": str(e),
            "performance": {
                "error_processing_time": round(error_duration, 6)
            }
        }), 500

@app.route('/menu', methods=['GET'])
def get_menu():
    """Get the restaurant menu"""
    try:
        menu_data = database.get_menu()
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
        menu_data = database.get_menu()
        dishes_by_category = {}

        for category in menu_data.get("categories", []):
            category_name = category["name"]
            dishes = []

            for item in category.get("items", []):
                dish = {
                    "_id": f"dish_{category_name.lower()}_{item['name'].lower().replace(' ', '_')}",
                    "name": item["name"],
                    "category": category_name,
                    "ingredients": [],
                    "is_vegetarian": False,
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

        # Create reservation (assuming db_manager or database agent handles this)
        try:
            if db_manager.connected:
                reservation = db_manager.create_reservation(data)
            else:
                return jsonify({
                    "success": False,
                    "error": "Reservations not supported in mock mode"
                }), 500

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
        info = database.get_restaurant_info()

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
        # Note: With LangChain agents using checkpointer, 
        # conversation history is managed per thread_id
        # To reset, the frontend should use a new thread_id/user_id
        return jsonify({
            "success": True,
            "message": "To reset conversation, use a new session ID in X-User-ID header"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/performance/logs', methods=['GET'])
def get_performance_logs():
    """Get performance timing logs"""
    try:
        from pathlib import Path
        import json
        
        # Get log directory
        log_dir = Path(__file__).parent.parent / "data" / "logs"
        
        # Check if directory exists
        if not log_dir.exists():
            return jsonify({
                "success": True,
                "logs": [],
                "count": 0,
                "message": "No performance logs found"
            })
        
        # Find all performance log files
        log_files = sorted(log_dir.glob("performance_log_*.jsonl"), reverse=True)
        
        logs = []
        for log_file in log_files:
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            line = line.strip()
                            if line:  # Skip empty lines
                                log_entry = json.loads(line)
                                logs.append(log_entry)
                        except json.JSONDecodeError as e:
                            print(f"[WARNING] Failed to parse log line: {e}")
                            continue
            except (IOError, OSError) as e:
                print(f"[WARNING] Failed to read log file {log_file}: {e}")
                continue
        
        return jsonify({
            "success": True,
            "logs": logs,
            "count": len(logs)
        })
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch performance logs: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "logs": [],
            "count": 0
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

def shutdown_handler():
    """Clean up resources when the application shuts down."""
    if 'agent_manager' in globals() and agent_manager.is_initialized:
        agent_manager.cleanup()
        print("[SHUTDOWN] Agent manager cleaned up")

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
    print("   GET    /performance/logs - Get performance logs")

    # Register shutdown handler
    import atexit
    atexit.register(shutdown_handler)

    app.run(host='0.0.0.0', port=port, debug=True)
