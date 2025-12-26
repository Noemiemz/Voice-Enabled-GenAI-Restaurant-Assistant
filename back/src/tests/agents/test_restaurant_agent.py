"""
Test cases for RestaurantAgent
"""

import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from agents.restaurant_agent import RestaurantAgent
from agents.tools.mock_mongodb_tools import MockMongoDBTool

class MockLLM:
    """Mock LLM for testing without actual API calls"""
    
    def __init__(self):
        self.call_count = 0
        self.last_prompt = ""
        
    def generate_from_prompt(self, prompt, history=None):
        """Mock generate_from_prompt method"""
        self.call_count += 1
        self.last_prompt = prompt
        
        # Simple response based on intent detection in prompt
        if "menu_request" in prompt:
            return "Voici notre menu du jour..."
        elif "dish_search" in prompt:
            return "J'ai trouvé ces plats pour vous..."
        elif "reservation_request" in prompt:
            return "Voici nos réservations disponibles..."
        elif "restaurant_info" in prompt:
            return "Notre restaurant est situé au 1 Avenue des Champs-Élysées..."
        elif "category_request" in prompt:
            return "Voici nos plats dans cette catégorie..."
        else:
            return "Je vous aide avec plaisir !"

def test_restaurant_agent_initialization():
    """Test that RestaurantAgent initializes correctly"""
    mock_llm = MockLLM()
    agent = RestaurantAgent(llm=mock_llm, use_mock_db=True)
    
    assert agent.llm is not None
    assert agent.tools is not None
    assert agent.conversation_history == []
    assert len(agent.available_tools) > 0
    
    print("[PASS] RestaurantAgent initialization test passed")

def test_menu_request():
    """Test menu request processing"""
    mock_llm = MockLLM()
    agent = RestaurantAgent(llm=mock_llm, use_mock_db=True)
    
    user_input = "Pouvez-vous me montrer le menu s'il vous plaît ?"
    response = agent.process_user_input(user_input)
    
    assert response is not None
    assert len(response) > 0
    assert mock_llm.call_count == 1
    assert "menu_request" in mock_llm.last_prompt
    
    print("[PASS] Menu request test passed")

def test_dish_search():
    """Test dish search processing"""
    mock_llm = MockLLM()
    agent = RestaurantAgent(llm=mock_llm, use_mock_db=True)
    
    user_input = "Je cherche un plat avec du poulet"
    response = agent.process_user_input(user_input)
    
    assert response is not None
    assert len(response) > 0
    assert mock_llm.call_count == 1
    assert "dish_search" in mock_llm.last_prompt
    
    print("[PASS] Dish search test passed")

def test_reservation_request():
    """Test reservation request processing"""
    mock_llm = MockLLM()
    agent = RestaurantAgent(llm=mock_llm, use_mock_db=True)
    
    user_input = "Je voudrais réserver une table pour ce soir"
    response = agent.process_user_input(user_input)
    
    assert response is not None
    assert len(response) > 0
    assert mock_llm.call_count == 1
    assert "reservation_request" in mock_llm.last_prompt
    
    print("[PASS] Reservation request test passed")

def test_restaurant_info_request():
    """Test restaurant info request processing"""
    mock_llm = MockLLM()
    agent = RestaurantAgent(llm=mock_llm, use_mock_db=True)
    
    user_input = "Quelles sont vos heures d'ouverture ?"
    response = agent.process_user_input(user_input)
    
    assert response is not None
    assert len(response) > 0
    assert mock_llm.call_count == 1
    assert "restaurant_info" in mock_llm.last_prompt
    
    print("[PASS] Restaurant info request test passed")

def test_category_request():
    """Test category-specific request processing"""
    mock_llm = MockLLM()
    agent = RestaurantAgent(llm=mock_llm, use_mock_db=True)
    
    user_input = "Quelles entrées avez-vous ?"
    response = agent.process_user_input(user_input)
    
    assert response is not None
    assert len(response) > 0
    assert mock_llm.call_count == 1
    assert "category_request" in mock_llm.last_prompt
    
    print("[PASS] Category request test passed")

def test_conversation_history():
    """Test conversation history management"""
    mock_llm = MockLLM()
    agent = RestaurantAgent(llm=mock_llm, use_mock_db=True)
    
    # Start with empty history
    assert len(agent.conversation_history) == 0
    
    # Process some inputs
    agent.process_user_input("Bonjour")
    agent.process_user_input("Comment ça va ?")
    
    # Check that history was updated
    assert len(agent.conversation_history) == 4  # 2 user + 2 assistant messages
    
    # Reset conversation
    agent.reset_conversation()
    assert len(agent.conversation_history) == 0
    
    print("[PASS] Conversation history test passed")

def test_tool_integration():
    """Test that tools are properly integrated and used"""
    mock_llm = MockLLM()
    agent = RestaurantAgent(llm=mock_llm, use_mock_db=True)
    
    # Test that tools are available
    assert "get_menu" in agent.available_tools
    assert "search_dishes" in agent.available_tools
    assert "get_reservations" in agent.available_tools
    
    # Test tool usage through intent detection
    user_input = "menu"
    intent, tool_name, tool_params = agent._determine_intent_and_tool(user_input)
    
    assert intent == "menu_request"
    assert tool_name == "get_menu"
    assert tool_params == {}
    
    print("[PASS] Tool integration test passed")

def test_error_handling():
    """Test error handling in the agent"""
    mock_llm = MockLLM()
    agent = RestaurantAgent(llm=mock_llm, use_mock_db=True)
    
    # Test with empty input
    response = agent.process_user_input("")
    assert response is not None
    assert len(response) > 0
    
    # Test with None input
    response = agent.process_user_input(None)
    assert response is not None
    assert len(response) > 0
    
    print("[PASS] Error handling test passed")

if __name__ == "__main__":
    print("Running RestaurantAgent tests...")
    
    test_restaurant_agent_initialization()
    test_menu_request()
    test_dish_search()
    test_reservation_request()
    test_restaurant_info_request()
    test_category_request()
    test_conversation_history()
    test_tool_integration()
    test_error_handling()
    
    print("\n[SUCCESS] All RestaurantAgent tests passed!")