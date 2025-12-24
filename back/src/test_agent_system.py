"""
Test script for the agent system
Demonstrates the complete agent system functionality
"""
import sys
sys.path.insert(0, '.')

from agents.orchestrator_agent import OrchestratorAgent
from agents.ui_agent import UIAgent
from agents.restaurant_info_agent import RestaurantInfoAgent
from agents.reservation_agent import ReservationAgent

def test_agent_system():
    """Test the complete agent system"""
    print("Testing Restaurant AI Agent System")
    print("=" * 50)
    
    # Create orchestrator
    print("Creating orchestrator...")
    orchestrator = OrchestratorAgent()
    
    # Create and register restaurant info agent
    print("Creating restaurant info agent...")
    restaurant_agent = RestaurantInfoAgent()
    orchestrator.register_agent(restaurant_agent)
    
    # Create and register reservation agent
    print("Creating reservation agent...")
    reservation_agent = ReservationAgent()
    orchestrator.register_agent(reservation_agent, "makeReservationAgent")
    
    # Create UI agent and connect to orchestrator
    print("Creating UI agent...")
    ui_agent = UIAgent()
    ui_agent.connect_to_orchestrator(orchestrator)
    orchestrator.register_agent(ui_agent)
    
    print(f"Agent system initialized with {len(orchestrator.get_available_agents())} agents")
    print(f"Available agents: {orchestrator.get_available_agents()}")
    
    # Test various types of queries
    print("\n" + "=" * 50)
    print("Testing User Queries")
    print("=" * 50)
    
    test_cases = [
        {
            'query': 'Bonjour, quels sont vos plats principaux?',
            'expected_agent': 'RestaurantInfoAgent',
            'expected_intent': 'menu_info'
        },
        {
            'query': 'Je voudrais réserver une table pour 4 personnes samedi à 20h',
            'expected_agent': 'makeReservationAgent',
            'expected_intent': 'reservation'
        },
        {
            'query': 'À quelle heure ouvrez-vous?',
            'expected_agent': 'RestaurantInfoAgent',
            'expected_intent': 'general_info'
        },
        {
            'query': 'Pouvez-vous me parler de votre tarte tatin?',
            'expected_agent': 'RestaurantInfoAgent',
            'expected_intent': 'menu_info'
        },
        {
            'query': 'Où êtes-vous situés?',
            'expected_agent': 'RestaurantInfoAgent',
            'expected_intent': 'general_info'
        }
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}/{total_tests}:")
        print(f"User: {test_case['query']}")
        
        try:
            result = ui_agent.execute(test_case['query'])
            
            print(f"Agent: {result.get('message', 'No response')}")
            print(f"Used agent: {result.get('agent', 'Unknown')}")
            print(f"Intent: {result.get('intent', 'Unknown')}")
            print(f"Success: {result.get('success', False)}")
            
            # Check if the expected agent was used
            if result.get('agent') == test_case['expected_agent']:
                print("Correct agent routing!")
                success_count += 1
            else:
                print(f"Expected {test_case['expected_agent']}, got {result.get('agent')}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    print(f"\n" + "=" * 50)
    print(f"Test Results: {success_count}/{total_tests} tests passed")
    print("=" * 50)
    
    # Test conversation history
    print(f"Conversation history length: {len(orchestrator.get_conversation_history())}")
    
    # Test agent capabilities
    print(f"Menu categories: {len(restaurant_agent.get_menu()['categories'])}")
    print(f"Reservations made: {reservation_agent.get_reservation_count()}")
    
    print("\nAgent system test completed successfully!")
    
    return success_count == total_tests

if __name__ == "__main__":
    success = test_agent_system()
    if success:
        print("\nAll tests passed! Agent system is working correctly.")
    else:
        print("\nSome tests failed. Please check the output above.")