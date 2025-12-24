"""
Integration Example - Shows how to use the agents together
This file demonstrates the agent system integration
"""
from orchestrator_agent import OrchestratorAgent
from ui_agent import UIAgent
from restaurant_info_agent import RestaurantInfoAgent
from reservation_agent import ReservationAgent

def create_agent_system():
    """
    Create and configure the complete agent system
    """
    print("Creating agent system...")
    
    # Create orchestrator
    orchestrator = OrchestratorAgent()
    
    # Create and register restaurant info agent
    restaurant_agent = RestaurantInfoAgent()
    orchestrator.register_agent(restaurant_agent)
    
    # Create and register reservation agent
    reservation_agent = ReservationAgent()
    orchestrator.register_agent(reservation_agent, "makeReservationAgent")
    
    # Create UI agent and connect to orchestrator
    ui_agent = UIAgent()
    ui_agent.connect_to_orchestrator(orchestrator)
    orchestrator.register_agent(ui_agent)
    
    print("Agent system created successfully!")
    print(f"Available agents: {orchestrator.get_available_agents()}")
    
    return ui_agent

if __name__ == "__main__":
    # Example usage
    ui_agent = create_agent_system()
    
    # Test some example queries
    test_queries = [
        "Bonjour, je voudrais réserver une table pour 4 personnes samedi soir",
        "Quels sont vos plats principaux?",
        "À quelle heure ouvrez-vous?",
        "Pouvez-vous me parler de votre tarte tatin?"
    ]
    
    print("\nTesting agent system with example queries:")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nUser: {query}")
        result = ui_agent.execute(query)
        print(f"Agent: {result.get('message', 'No response')}")
        print(f"Agent used: {result.get('agent', 'Unknown')}")
        print(f"Intent: {result.get('intent', 'Unknown')}")
        print("-" * 30)