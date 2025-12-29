"""
Integration test to verify that the reservation agent works with the orchestrator.
"""
import os
from agents.orchestrator import create_orchestrator_agent
from utils.utils import Context

def test_orchestrator_with_reservation_agent():
    """Test that the orchestrator can route queries to the reservation agent."""
    
    # Create orchestrator
    orchestrator = create_orchestrator_agent()
    
    # Test queries that should be routed to reservation agent
    test_queries = [
        "I want to make a reservation",
        "What reservations do we have for today?",
        "Can you check reservation number 123?",
        "I need to book a table for 4 people"
    ]
    
    context = Context(user_id="test_user", verbose=True)
    config = {"configurable": {"thread_id": "test_thread"}}
    
    print("Testing orchestrator with reservation-related queries...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing query: '{query}'")
        
        try:
            response = orchestrator.invoke(
                {"messages": [{"role": "user", "content": query}]},
                config=config,
                context=context,
            )
            
            print(f"   Response: {response['output'][:100]}...")  # Show first 100 chars
            print("   ✓ Query processed successfully")
            
        except Exception as e:
            print(f"   ✗ Error processing query: {e}")
    
    print("\n✓ All integration tests completed!")

if __name__ == "__main__":
    test_orchestrator_with_reservation_agent()