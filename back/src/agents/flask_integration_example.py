"""
Flask Integration Example
This shows how to integrate the agent system with the existing Flask application.
"""

import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request, jsonify
from agents.orchestrator_agent import OrchestratorAgent
from agents.ui_agent import UIAgent
from agents.base_agent import BaseAgent
from typing import Dict, Any


class RestaurantInfoAgent(BaseAgent):
    """Agent that handles restaurant information using existing app data"""
    
    def __init__(self, menu_data=None, restaurant_info=None):
        super().__init__("RestaurantInfoAgent", "Handles restaurant information")
        self.menu_data = menu_data or {}
        self.restaurant_info = restaurant_info or {}
        
    def execute(self, task: str, context: Dict = None) -> Dict[str, Any]:
        if context is None:
            context = {}
            
        task_lower = task.lower()
        
        if any(keyword in task_lower for keyword in ["menu", "dish", "food"]):
            return self._get_menu_info()
        elif any(keyword in task_lower for keyword in ["info", "restaurant", "hours", "address"]):
            return self._get_restaurant_info()
        else:
            return {"message": "I can provide information about our menu and restaurant"}
            
    def _get_menu_info(self) -> Dict[str, Any]:
        """Get menu information"""
        if not self.menu_data:
            return {"message": "Menu information not available"}
        
        # Format menu for response
        menu_items = []
        for category in self.menu_data.get("categories", []):
            for item in category.get("items", []):
                menu_items.append(f"{item['name']} - {item['price']}")
        
        return {
            "menu": self.menu_data,
            "menu_items": menu_items,
            "message": "Here is our menu"
        }
        
    def _get_restaurant_info(self) -> Dict[str, Any]:
        """Get restaurant information"""
        if not self.restaurant_info:
            return {"message": "Restaurant information not available"}
        
        return {
            "info": self.restaurant_info,
            "message": f"Welcome to {self.restaurant_info.get('name', 'our restaurant')}!"
        }
    
    def can_handle(self, task: str) -> bool:
        keywords = ["menu", "dish", "food", "restaurant", "info", "hours", "address"]
        return any(keyword in task.lower() for keyword in keywords)


def create_flask_app_with_agents(menu_data=None, restaurant_info=None):
    """
    Create a Flask app with integrated agent system
    
    Args:
        menu_data (dict): Menu data to use
        restaurant_info (dict): Restaurant information
        
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    
    # Create agent system
    orchestrator = OrchestratorAgent()
    
    # Create and register agents
    restaurant_agent = RestaurantInfoAgent(menu_data, restaurant_info)
    orchestrator.register_agent(restaurant_agent)
    
    # Create UI agent and connect to orchestrator
    ui_agent = UIAgent()
    ui_agent.connect_to_orchestrator(orchestrator)
    orchestrator.register_agent(ui_agent)
    
    # Store agents in app context for access in routes
    app.agents = {
        'orchestrator': orchestrator,
        'ui_agent': ui_agent
    }
    
    @app.route('/api/agent-process', methods=['POST'])
    def agent_process():
        """
        Process user requests through the agent system
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
                
            user_input = data.get('message', '').strip()
            if not user_input:
                return jsonify({"error": "No message provided"}), 400
                
            # Get context from request
            context = {
                'user_id': data.get('user_id', 'anonymous'),
                'interface': data.get('interface', 'text'),
                'session_id': data.get('session_id'),
                'metadata': data.get('metadata', {})
            }
            
            # Process through agent system
            result = app.agents['ui_agent'].execute(user_input, context)
            
            # Format response for API
            response_data = {
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "type": result.get("type", "text")
            }
            
            # Include additional data if available
            if result.get("data"):
                response_data["data"] = result["data"]
                
            return jsonify(response_data)
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "message": "An error occurred while processing your request"
            }), 500
    
    @app.route('/api/agent-status', methods=['GET'])
    def agent_status():
        """
        Get status information about the agent system
        """
        try:
            status = app.agents['orchestrator'].get_agent_status()
            return jsonify({
                "success": True,
                "status": status
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/api/conversation-history', methods=['GET'])
    def conversation_history():
        """
        Get conversation history for a user
        """
        try:
            user_id = request.args.get('user_id', 'anonymous')
            limit = int(request.args.get('limit', 10))
            
            # In a real implementation, you would filter by user_id
            # For this example, we return the full history
            history = app.agents['ui_agent'].get_conversation_history(limit)
            
            return jsonify({
                "success": True,
                "history": history,
                "user_id": user_id
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    return app


def example_flask_usage():
    """Example of using the Flask app with agents"""
    
    # Example data (this would come from your existing app)
    example_menu = {
        "categories": [
            {
                "name": "Entrées",
                "items": [
                    {"name": "Terrine de campagne", "price": "12€", "description": "Maison avec pain grillé"},
                    {"name": "Salade niçoise", "price": "14€", "description": "Thon, œufs, olives, légumes frais"}
                ]
            },
            {
                "name": "Plats principaux",
                "items": [
                    {"name": "Boeuf bourguignon", "price": "22€", "description": "Viande fondante, champignons, carottes"},
                    {"name": "Poulet rôti", "price": "18€", "description": "Avec pommes de terre et légumes de saison"}
                ]
            }
        ]
    }
    
    example_restaurant_info = {
        "name": "Le Bistro Gourmand",
        "hours": "12:00 - 22:00",
        "phone": "+33 1 23 45 67 89",
        "address": "123 Rue de Paris, 75001 Paris",
        "description": "Cuisine française traditionnelle dans un cadre élégant"
    }
    
    # Create Flask app with agents
    app = create_flask_app_with_agents(example_menu, example_restaurant_info)
    
    print("=== Flask Agent Integration Example ===")
    print(f"Available routes:")
    print(f"  POST /api/agent-process - Process user requests")
    print(f"  GET /api/agent-status - Get agent system status")
    print(f"  GET /api/conversation-history - Get conversation history")
    print()
    print("Example requests:")
    print(f"  POST /api/agent-process {{'message': 'What's on the menu?'}}")
    print(f"  POST /api/agent-process {{'message': 'What are your opening hours?'}}")
    print()
    print("Agent system ready!")
    
    return app


if __name__ == "__main__":
    # Create and run the example app
    app = example_flask_usage()
    
    # You can run this with: python flask_integration_example.py
    # Then test the endpoints with curl, Postman, or your frontend
    print("\nTo test the API:")
    print("1. Run: python flask_integration_example.py")
    print("2. Test with curl:")
    print("   curl -X POST -H 'Content-Type: application/json' \\")
    print("        -d '{\"message\": \"What is on the menu?\"}' \\")
    print("        http://localhost:5000/api/agent-process")
    
    # Uncomment to run the Flask app
    # app.run(debug=True, port=5000)