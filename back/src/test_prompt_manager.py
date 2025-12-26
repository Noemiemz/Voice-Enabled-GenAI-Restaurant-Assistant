"""
Test script for PromptManager and updated RestaurantAgent
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agents.prompt_manager import PromptManager
from agents.restaurant_agent import RestaurantAgent

def test_prompt_manager():
    """Test the PromptManager functionality"""
    print("=== Testing PromptManager ===")
    
    # Test initialization
    prompt_manager = PromptManager()
    print("+ PromptManager initialized successfully")
    
    # Test loading existing prompt
    prompt = prompt_manager.load_prompt("response_generation_prompt")
    if prompt and "You are a helpful restaurant assistant" in prompt:
        print("+ Successfully loaded response_generation_prompt")
    else:
        print("- Failed to load response_generation_prompt")
        return False
    
    # Test formatting prompt
    formatted_prompt = prompt_manager.get_formatted_prompt(
        "response_generation_prompt",
        intent="menu_request",
        tool_name="get_menu",
        tool_result='{"menu": "test"}',
        user_input="Quelle est votre carte ?"
    )
    
    if "menu_request" in formatted_prompt and "Quelle est votre carte ?" in formatted_prompt:
        print("+ Successfully formatted prompt with variables")
    else:
        print("- Failed to format prompt correctly")
        return False
    
    # Test missing prompt fallback
    fallback_prompt = prompt_manager.get_formatted_prompt(
        "nonexistent_prompt",
        user_input="Test"
    )
    
    if "helpful restaurant assistant" in fallback_prompt:
        print("+ Successfully fell back to default prompt")
    else:
        print("- Failed to fall back to default prompt")
        return False
    
    print("+ All PromptManager tests passed!")
    return True

def test_restaurant_agent():
    """Test the updated RestaurantAgent with PromptManager"""
    print("\n=== Testing RestaurantAgent with PromptManager ===")
    
    try:
        # Initialize agent
        agent = RestaurantAgent(use_mock_db=True)
        print("+ RestaurantAgent initialized successfully")
        
        # Test that agent has prompt_manager
        if hasattr(agent, 'prompt_manager') and agent.prompt_manager:
            print("+ RestaurantAgent has PromptManager instance")
        else:
            print("- RestaurantAgent missing PromptManager")
            return False
        
        # Test basic query processing
        response = agent.process_user_input("Quelle est votre carte ?")
        
        if response and len(response) > 0:
            print("+ RestaurantAgent processed query successfully")
            print(f"   Response: {response[:100]}...")  # Show first 100 chars
        else:
            print("- RestaurantAgent failed to process query")
            return False
        
        print("+ All RestaurantAgent tests passed!")
        return True
        
    except Exception as e:
        print(f"- RestaurantAgent test failed with error: {e}")
        return False

if __name__ == "__main__":
    print("Testing PromptManager and RestaurantAgent integration...\n")
    
    success = True
    success &= test_prompt_manager()
    success &= test_restaurant_agent()
    
    if success:
        print("\nSUCCESS: All tests passed! The system is working correctly.")
    else:
        print("\nFAILURE: Some tests failed. Please check the implementation.")
    
    print("\nTest completed.")