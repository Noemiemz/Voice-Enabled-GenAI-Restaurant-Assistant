"""
Integration tests for the complete agent system.
Tests the interaction between UI agent, orchestrator, and tools.
"""

import pytest
from agents_langchain.ui_agent import UIAgent
from agents_langchain.orchestrator_agent import OrchestratorAgent
from agents_langchain.base_agent import AgentMessage


def test_complete_menu_query_flow():
    """Test the complete flow for a menu query."""
    # Initialize agents
    ui_agent = UIAgent()
    orchestrator = OrchestratorAgent()
    
    # User query
    user_query = "What vegetarian options do you have?"
    
    # Step 1: UI agent processes user query
    processed_query = ui_agent.process_user_query(user_query)
    
    assert processed_query.query_type == "menu"
    assert processed_query.needs_clarification == False
    assert "vegetarian" in processed_query.refined_query.lower()
    
    # Step 2: UI agent sends query to orchestrator
    message_to_orchestrator = ui_agent.send_query_to_orchestrator(processed_query)
    
    assert message_to_orchestrator.sender == "ui_agent"
    assert message_to_orchestrator.receiver == "orchestrator"
    assert message_to_orchestrator.message_type == "user_query"
    assert message_to_orchestrator.content["query_type"] == "menu"
    
    # Step 3: Orchestrator processes the query
    orchestrator_response = orchestrator.process_user_query(message_to_orchestrator)
    
    assert orchestrator_response.sender == "orchestrator"
    assert orchestrator_response.receiver == "ui_agent"
    assert orchestrator_response.message_type == "orchestrator_response"
    assert orchestrator_response.content["response_type"] == "menu_info"
    assert orchestrator_response.content["success"] == True
    assert len(orchestrator_response.content["dishes"]) > 0
    
    # Step 4: UI agent processes orchestrator response
    ui_response = ui_agent.receive_message(orchestrator_response)
    
    assert "response_for_user" in ui_response
    assert "vegetarian" in ui_response["response_for_user"].lower()
    
    # Verify that all dishes in response are vegetarian
    for dish in orchestrator_response.content["dishes"]:
        assert dish["is_vegetarian"] == True


def test_complete_reservation_query_flow():
    """Test the complete flow for a reservation query."""
    # Initialize agents
    ui_agent = UIAgent()
    orchestrator = OrchestratorAgent()
    
    # User query that needs clarification
    user_query = "I want to make a reservation"
    
    # Step 1: UI agent processes user query
    processed_query = ui_agent.process_user_query(user_query)
    
    assert processed_query.query_type == "reservation"
    assert processed_query.needs_clarification == True
    assert len(processed_query.clarification_questions) == 2
    
    # For this test, we'll proceed anyway
    
    # Step 2: UI agent sends query to orchestrator
    message_to_orchestrator = ui_agent.send_query_to_orchestrator(processed_query)
    
    # Step 3: Orchestrator processes the query
    orchestrator_response = orchestrator.process_user_query(message_to_orchestrator)
    
    assert orchestrator_response.content["response_type"] == "reservation_info"
    assert orchestrator_response.content["success"] == True
    assert len(orchestrator_response.content["available_tables"]) > 0
    
    # Step 4: UI agent processes orchestrator response
    ui_response = ui_agent.receive_message(orchestrator_response)
    
    assert "response_for_user" in ui_response
    assert "table" in ui_response["response_for_user"].lower()


def test_general_query_flow():
    """Test the complete flow for a general query."""
    # Initialize agents
    ui_agent = UIAgent()
    orchestrator = OrchestratorAgent()
    
    # User query
    user_query = "Hello, how are you?"
    
    # Step 1: UI agent processes user query
    processed_query = ui_agent.process_user_query(user_query)
    
    assert processed_query.query_type == "general"
    
    # Step 2: UI agent sends query to orchestrator
    message_to_orchestrator = ui_agent.send_query_to_orchestrator(processed_query)
    
    # Step 3: Orchestrator processes the query
    orchestrator_response = orchestrator.process_user_query(message_to_orchestrator)
    
    assert orchestrator_response.content["response_type"] == "direct_response"
    assert orchestrator_response.content["success"] == True
    assert "welcome" in orchestrator_response.content["message"].lower()
    
    # Step 4: UI agent processes orchestrator response
    ui_response = ui_agent.receive_message(orchestrator_response)
    
    assert "response_for_user" in ui_response
    assert "welcome" in ui_response["response_for_user"].lower()


def test_conversation_history():
    """Test that conversation history is maintained throughout the flow."""
    # Initialize agents
    ui_agent = UIAgent()
    orchestrator = OrchestratorAgent()
    
    # Process a query
    processed_query = ui_agent.process_user_query("Show me the menu")
    message_to_orchestrator = ui_agent.send_query_to_orchestrator(processed_query)
    orchestrator_response = orchestrator.process_user_query(message_to_orchestrator)
    ui_agent.receive_message(orchestrator_response)
    
    # Check UI agent conversation history
    ui_history = ui_agent.get_conversation_history()
    assert len(ui_history) == 2  # Sent message + received message
    
    # Check orchestrator conversation history
    orchestrator_history = orchestrator.get_conversation_history()
    assert len(orchestrator_history) == 1  # Received message
    
    # Check decision history
    assert len(orchestrator.decision_history) == 1


def test_error_handling():
    """Test error handling in the agent system."""
    # Initialize agents
    ui_agent = UIAgent()
    orchestrator = OrchestratorAgent()
    
    # Create a malformed message (missing required fields)
    try:
        bad_message = AgentMessage(
            sender="ui_agent",
            receiver="orchestrator",
            message_type="user_query",
            content={}  # Missing query and query_type
        )
        
        # This should still work but might produce unexpected results
        response = orchestrator.process_user_query(bad_message)
        
        # The orchestrator should handle this gracefully
        assert isinstance(response, AgentMessage)
        
    except Exception as e:
        pytest.fail(f"Agent system failed to handle malformed message: {e}")


def test_message_conversation_id_consistency():
    """Test that conversation IDs are maintained throughout the flow."""
    # Initialize agents
    ui_agent = UIAgent()
    orchestrator = OrchestratorAgent()
    
    # Process a query
    processed_query = ui_agent.process_user_query("Show me vegetarian options")
    conversation_id = processed_query.context["conversation_id"]
    
    # Send to orchestrator
    message_to_orchestrator = ui_agent.send_query_to_orchestrator(processed_query)
    assert message_to_orchestrator.conversation_id == conversation_id
    
    # Process by orchestrator
    orchestrator_response = orchestrator.process_user_query(message_to_orchestrator)
    assert orchestrator_response.conversation_id == conversation_id
    
    # Process by UI agent
    ui_response = ui_agent.receive_message(orchestrator_response)
    # The conversation ID should be maintained in the UI agent's history
    ui_history = ui_agent.get_conversation_history(conversation_id)
    assert len(ui_history) == 2


def test_multiple_queries_in_sequence():
    """Test handling multiple queries in sequence."""
    # Initialize agents
    ui_agent = UIAgent()
    orchestrator = OrchestratorAgent()
    
    # First query - menu
    query1 = ui_agent.process_user_query("Show me the menu")
    message1 = ui_agent.send_query_to_orchestrator(query1)
    response1 = orchestrator.process_user_query(message1)
    ui_agent.receive_message(response1)
    
    # Second query - reservation
    query2 = ui_agent.process_user_query("Book a table for 4 people")
    message2 = ui_agent.send_query_to_orchestrator(query2)
    response2 = orchestrator.process_user_query(message2)
    ui_agent.receive_message(response2)
    
    # Third query - general
    query3 = ui_agent.process_user_query("Thank you")
    message3 = ui_agent.send_query_to_orchestrator(query3)
    response3 = orchestrator.process_user_query(message3)
    ui_agent.receive_message(response3)
    
    # Check that all queries were processed correctly
    assert len(ui_agent.query_history) == 3
    assert len(ui_agent.conversation_history) == 6  # 3 sent + 3 received
    assert len(orchestrator.conversation_history) == 3
    assert len(orchestrator.decision_history) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])