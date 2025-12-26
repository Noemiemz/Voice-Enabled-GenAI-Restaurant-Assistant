"""
Flask application for the LangChain-enhanced restaurant assistant system.
Provides REST API endpoints for interacting with the agent system.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from agents_langchain.langchain_integration import setup_langchain_agents
from agents_langchain.base_agent_langchain import AgentMessage
from agents_langchain.ui_agent_langchain import LangChainUIAgent
from agents_langchain.orchestrator_agent_langchain import LangChainOrchestratorAgent
from langchain_classic.llms.fake import FakeListLLM
from models.llm_langchain import create_default_mistral_llm, create_default_mistral_chat_model
import json
import uuid
from datetime import datetime
import logging
from typing import Dict, Any, Optional


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Create Flask app
app = Flask(__name__)

# Configure CORS with explicit settings
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": True,
        "max_age": 3600
    }
})


# Global agent system (will be initialized on first request)
agent_system: Optional[Dict[str, Any]] = None


def initialize_agent_system() -> Dict[str, Any]:
    """Initialize the LangChain agent system."""
    global agent_system
    
    if agent_system is None:
        logger.info("Initializing LangChain agent system...")
        
        try:
            # Try to use Mistral LLM first
            llm = create_default_mistral_llm()
            logger.info("Using Mistral LLM for agent system")
        except Exception as e:
            logger.warning(f"Mistral LLM not available: {e}, falling back to mock LLM")
            # Fallback to mock LLM for testing
            responses = [
                # UI Agent responses
                '{"query_type": "menu", "needs_clarification": false, "clarification_questions": [], "refined_query": "Show vegetarian menu options", "key_details": {"dietary_preference": "vegetarian"}}',
                '{"query_type": "reservation", "needs_clarification": true, "clarification_questions": ["When would you like the reservation?", "How many people?"], "refined_query": "Book table", "key_details": {}}',
                '{"query_type": "general", "needs_clarification": false, "clarification_questions": [], "refined_query": "Hello there", "key_details": {}}',
                
                # Orchestrator responses
                '{"action": "db_query", "target": "menu_database", "parameters": {"collection": "Dish", "query": {"is_vegetarian": true}}, "needs_db_access": true, "reason": "Menu query requires database access", "confidence": 0.9}',
                '{"action": "db_query", "target": "reservation_database", "parameters": {"collection": "Table", "query": {"is_available": true}}, "needs_db_access": true, "reason": "Reservation query requires database access", "confidence": 0.8}',
                '{"action": "direct_response", "target": "ui_agent", "parameters": {"message": "Hello! Welcome to our restaurant. How can I assist you today?"}, "needs_db_access": false, "reason": "General greeting handled with direct response", "confidence": 0.95}',
                
                # Response formatting
                "Here are some delicious vegetarian options from our menu:",
                "We have several tables available. When would you like to book?",
                "Hello! Welcome to our restaurant. How can I assist you today?"
            ]
            
            llm = FakeListLLM(responses=responses)
        
        # Set up agent system
        agent_system = setup_langchain_agents(llm=llm, use_mock_db=True)
        
        logger.info("LangChain agent system initialized successfully")
    
    return agent_system


@app.route('/')
def home():
    """Home endpoint."""
    return jsonify({
        'status': 'success',
        'message': 'LangChain Restaurant Assistant API',
        'version': '1.0',
        'endpoints': {
            '/query': 'POST - Process user queries',
            '/conversation': 'POST - Manage conversations',
            '/memory': 'GET - Get conversation memory',
            '/tools': 'GET - List available tools',
            '/health': 'GET - Health check'
        }
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Initialize system to check if everything works
        system = initialize_agent_system()
        
        # Get LLM info
        llm_info = {
            'type': system['llm'].__class__.__name__,
            'is_mistral': 'Mistral' in system['llm'].__class__.__name__
        }
        
        return jsonify({
            'status': 'healthy',
            'agents': list(system.keys()),
            'llm': llm_info,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@app.route('/query', methods=['POST'])
def process_query():
    """Process a user query through the LangChain agent system."""
    
    try:
        # Initialize agent system
        system = initialize_agent_system()
        ui_agent = system["ui_agent"]
        orchestrator = system["orchestrator"]
        
        # Get query from request
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'error': 'Missing query parameter'
            }), 400
        
        # Extract parameters
        user_query = data['query']
        conversation_id = data.get('conversation_id', str(uuid.uuid4()))
        
        logger.info(f"Processing query: {user_query} (Conversation: {conversation_id})")
        
        # Step 1: UI Agent processes the query
        query_data = ui_agent.process_user_query(user_query, conversation_id)
        
        # Step 2: Send to orchestrator
        message = ui_agent.send_query_to_orchestrator(query_data)
        
        # Step 3: Orchestrator processes and makes decision
        orchestrator_response = orchestrator.process_user_query(message)
        
        # Step 4: UI Agent formats the final response
        final_response = ui_agent.receive_message(orchestrator_response)
        
        # Prepare response
        response_data = {
            'status': 'success',
            'conversation_id': conversation_id,
            'query': user_query,
            'query_type': query_data['query_type'],
            'needs_clarification': query_data['needs_clarification'],
            'clarification_questions': query_data['clarification_questions'],
            'response': final_response['response_for_user'],
            'response_type': orchestrator_response.content.get('response_type', 'general'),
            'timestamp': datetime.now().isoformat(),
            'agent_processing': {
                'ui_agent_analysis': query_data.get('llm_analysis', {}),
                'orchestrator_decision': {
                    'action': orchestrator.decision_history[-1]['decision'].get('action') if orchestrator.decision_history else 'unknown',
                    'reason': orchestrator.decision_history[-1]['decision'].get('reason') if orchestrator.decision_history else 'unknown'
                }
            }
        }
        
        logger.info(f"Query processed successfully: {conversation_id}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/conversation', methods=['POST'])
def manage_conversation():
    """Manage conversation state."""
    
    try:
        data = request.get_json()
        action = data.get('action', 'start')
        
        if action == 'start':
            # Start new conversation
            conversation_id = str(uuid.uuid4())
            
            return jsonify({
                'status': 'success',
                'conversation_id': conversation_id,
                'message': 'New conversation started'
            })
        
        elif action == 'clear':
            # Clear conversation history
            system = initialize_agent_system()
            ui_agent = system["ui_agent"]
            orchestrator = system["orchestrator"]
            
            ui_agent.clear_conversation_history()
            orchestrator.clear_conversation_history()
            
            return jsonify({
                'status': 'success',
                'message': 'Conversation history cleared'
            })
        
        elif action == 'history':
            # Get conversation history
            conversation_id = data.get('conversation_id')
            system = initialize_agent_system()
            ui_agent = system["ui_agent"]
            
            if conversation_id:
                history = ui_agent.get_conversation_history(conversation_id)
            else:
                history = ui_agent.get_conversation_history()
            
            return jsonify({
                'status': 'success',
                'conversation_id': conversation_id,
                'history': history
            })
        
        else:
            return jsonify({
                'error': f'Unknown action: {action}'
            }), 400
            
    except Exception as e:
        logger.error(f"Error managing conversation: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/memory', methods=['GET'])
def get_memory():
    """Get conversation memory content."""
    
    try:
        system = initialize_agent_system()
        memory = system["memory"]
        
        memory_content = memory.load_memory_variables({})
        
        return jsonify({
            'status': 'success',
            'memory': memory_content
        })
        
    except Exception as e:
        logger.error(f"Error getting memory: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/tools', methods=['GET'])
def list_tools():
    """List available LangChain tools."""
    
    try:
        system = initialize_agent_system()
        orchestrator = system["orchestrator"]
        
        tools_info = []
        for tool in orchestrator.tools:
            tools_info.append({
                'name': tool.name,
                'description': tool.description,
                'type': tool.__class__.__name__
            })
        
        return jsonify({
            'status': 'success',
            'tools': tools_info,
            'count': len(tools_info)
        })
        
    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/agents', methods=['GET'])
def list_agents():
    """List information about the agents."""
    
    try:
        system = initialize_agent_system()
        
        agents_info = []
        for agent_name, agent in system.items():
            if isinstance(agent, (LangChainUIAgent, LangChainOrchestratorAgent)):
                agents_info.append({
                    'name': agent.name,
                    'type': agent.__class__.__name__,
                    'description': agent.description,
                    'conversation_history_length': len(agent.conversation_history)
                })
        
        return jsonify({
            'status': 'success',
            'agents': agents_info,
            'count': len(agents_info)
        })
        
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/debug', methods=['GET'])
def debug_info():
    """Get debug information about the system."""
    
    try:
        system = initialize_agent_system()
        
        debug_info = {
            'agents': {
                'ui_agent': {
                    'name': system['ui_agent'].name,
                    'query_history_length': len(system['ui_agent'].query_history),
                    'conversation_history_length': len(system['ui_agent'].conversation_history)
                },
                'orchestrator': {
                    'name': system['orchestrator'].name,
                    'decision_history_length': len(system['orchestrator'].decision_history),
                    'conversation_history_length': len(system['orchestrator'].conversation_history),
                    'tools_count': len(system['orchestrator'].tools)
                }
            },
            'memory': {
                'type': system['memory'].__class__.__name__,
                'memory_key': system['memory'].memory_key
            },
            'llm': {
                'type': system['llm'].__class__.__name__,
                'description': str(system['llm'])
            }
        }
        
        return jsonify({
            'status': 'success',
            'debug_info': debug_info
        })
        
    except Exception as e:
        logger.error(f"Error getting debug info: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/reset', methods=['POST'])
def reset_system():
    """Reset the agent system (for testing)."""
    
    try:
        global agent_system
        agent_system = None
        
        logger.info("Agent system reset successfully")
        
        return jsonify({
            'status': 'success',
            'message': 'Agent system reset successfully'
        })
        
    except Exception as e:
        logger.error(f"Error resetting system: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/menu', methods=['GET'])
def get_menu():
    """Get restaurant menu (mock data for frontend compatibility)."""
    
    try:
        # Mock menu data for frontend
        menu_data = {
            "categories": [
                {
                    "name": "Entrées",
                    "items": [
                        {
                            "name": "Bruschetta Tomate Basilique",
                            "price": "8.50",
                            "description": "Tomates fraîches, basilic, huile d'olive sur pain grillé"
                        },
                        {
                            "name": "Carpaccio de Bœuf",
                            "price": "12.00",
                            "description": "Fines tranches de bœuf, roquette, parmesan, huile d'olive"
                        }
                    ]
                },
                {
                    "name": "Plats Principaux",
                    "items": [
                        {
                            "name": "Poulet Rôti aux Herbes",
                            "price": "18.50",
                            "description": "Poulet rôti aux herbes de Provence, accompagnement du jour"
                        },
                        {
                            "name": "Filet de Saumon Grillé",
                            "price": "22.00",
                            "description": "Saumon grillé, sauce citronnée, légumes de saison"
                        }
                    ]
                },
                {
                    "name": "Desserts",
                    "items": [
                        {
                            "name": "Tiramisu Maison",
                            "price": "7.50",
                            "description": "Classique italien avec café et mascarpone"
                        },
                        {
                            "name": "Crème Brûlée",
                            "price": "6.50",
                            "description": "Crème vanille avec croûte de sucre caramélisé"
                        }
                    ]
                }
            ]
        }
        
        return jsonify(menu_data)
        
    except Exception as e:
        logger.error(f"Error getting menu: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/dishes', methods=['GET'])
def get_dishes():
    """Get dishes grouped by category (mock data for frontend compatibility)."""
    
    try:
        # Mock dishes data for frontend
        dishes_data = {
            "Starter": [
                {
                    "_id": "1",
                    "name": "Bruschetta Tomate Basilique",
                    "category": "Starter",
                    "ingredients": [
                        {"name": "Tomates", "is_allergen": False, "allergen_type": None},
                        {"name": "Basilic", "is_allergen": False, "allergen_type": None},
                        {"name": "Huile d'olive", "is_allergen": False, "allergen_type": None},
                        {"name": "Pain", "is_allergen": True, "allergen_type": "Gluten"}
                    ],
                    "is_vegetarian": True,
                    "price": 8.50
                },
                {
                    "_id": "2",
                    "name": "Carpaccio de Bœuf",
                    "category": "Starter",
                    "ingredients": [
                        {"name": "Bœuf", "is_allergen": False, "allergen_type": None},
                        {"name": "Roquette", "is_allergen": False, "allergen_type": None},
                        {"name": "Parmesan", "is_allergen": True, "allergen_type": "Lait"}
                    ],
                    "is_vegetarian": False,
                    "price": 12.00
                }
            ],
            "Main": [
                {
                    "_id": "3",
                    "name": "Poulet Rôti aux Herbes",
                    "category": "Main",
                    "ingredients": [
                        {"name": "Poulet", "is_allergen": False, "allergen_type": None},
                        {"name": "Herbes de Provence", "is_allergen": False, "allergen_type": None},
                        {"name": "Légumes de saison", "is_allergen": False, "allergen_type": None}
                    ],
                    "is_vegetarian": False,
                    "price": 18.50
                },
                {
                    "_id": "4",
                    "name": "Filet de Saumon Grillé",
                    "category": "Main",
                    "ingredients": [
                        {"name": "Saumon", "is_allergen": True, "allergen_type": "Poisson"},
                        {"name": "Citron", "is_allergen": False, "allergen_type": None},
                        {"name": "Légumes de saison", "is_allergen": False, "allergen_type": None}
                    ],
                    "is_vegetarian": False,
                    "price": 22.00
                }
            ],
            "Dessert": [
                {
                    "_id": "5",
                    "name": "Tiramisu Maison",
                    "category": "Dessert",
                    "ingredients": [
                        {"name": "Café", "is_allergen": False, "allergen_type": None},
                        {"name": "Mascarpone", "is_allergen": True, "allergen_type": "Lait"},
                        {"name": "Œufs", "is_allergen": True, "allergen_type": "Œufs"},
                        {"name": "Biscuits", "is_allergen": True, "allergen_type": "Gluten"}
                    ],
                    "is_vegetarian": True,
                    "price": 7.50
                },
                {
                    "_id": "6",
                    "name": "Crème Brûlée",
                    "category": "Dessert",
                    "ingredients": [
                        {"name": "Crème", "is_allergen": True, "allergen_type": "Lait"},
                        {"name": "Sucre", "is_allergen": False, "allergen_type": None},
                        {"name": "Vanille", "is_allergen": False, "allergen_type": None}
                    ],
                    "is_vegetarian": True,
                    "price": 6.50
                }
            ],
            "Drink": [
                {
                    "_id": "7",
                    "name": "Vin Rouge",
                    "category": "Drink",
                    "ingredients": [
                        {"name": "Vin", "is_allergen": False, "allergen_type": None}
                    ],
                    "is_vegetarian": True,
                    "price": 6.00
                },
                {
                    "_id": "8",
                    "name": "Eau Minérale",
                    "category": "Drink",
                    "ingredients": [
                        {"name": "Eau", "is_allergen": False, "allergen_type": None}
                    ],
                    "is_vegetarian": True,
                    "price": 2.50
                }
            ]
        }
        
        return jsonify(dishes_data)
        
    except Exception as e:
        logger.error(f"Error getting dishes: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/reservations', methods=['POST'])
def create_reservation():
    """Create a new reservation (mock functionality for frontend compatibility)."""
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No reservation data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['name', 'phone', 'date', 'time', 'guests']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Mock reservation creation
        reservation_data = {
            'name': data['name'],
            'phone': data['phone'],
            'date': data['date'],
            'time': data['time'],
            'guests': data['guests'],
            'specialRequests': data.get('specialRequests', ''),
            'createdAt': datetime.now().isoformat(),
            'updatedAt': datetime.now().isoformat(),
            'status': 'confirmed'
        }
        
        logger.info(f"Reservation created: {reservation_data['name']} for {reservation_data['guests']} guests on {reservation_data['date']}")
        
        return jsonify({
            'success': True,
            'reservation': reservation_data
        })
        
    except Exception as e:
        logger.error(f"Error creating reservation: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/info', methods=['GET'])
def get_restaurant_info():
    """Get restaurant information (mock data for frontend compatibility)."""
    
    try:
        # Mock restaurant info
        restaurant_info = {
            'name': 'Les Pieds dans le Plat',
            'address': '1 Avenue des Champs-Élysées, 75008 Paris',
            'phone': '+33 1 23 45 67 89',
            'openingHours': 'Ouvert de 11h à 1h',
            'description': 'L\'art culinaire à Paris - Cuisine française traditionnelle avec une touche moderne'
        }
        
        return jsonify(restaurant_info)
        
    except Exception as e:
        logger.error(f"Error getting restaurant info: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


if __name__ == '__main__':
    logger.info("Starting LangChain Restaurant Assistant API...")
    
    # Initialize system on startup
    initialize_agent_system()
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )