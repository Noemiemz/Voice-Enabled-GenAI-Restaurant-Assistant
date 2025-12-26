"""
Test cases for the UI agent functionality.
"""

import pytest
from agents_langchain.ui_agent import UIAgent, UserQuery
from agents_langchain.base_agent import AgentMessage


def test_ui_agent_initialization():
    """Test UI agent initialization."""
    agent = UIAgent()
    
    assert agent.name == "ui_agent"
    assert "user interactions" in agent.description.lower()
    assert agent.query_history == []


def test_process_user_query():
    """Test processing user queries."""
    agent = UIAgent()
    
    # Test menu query
    query = agent.process_user_query("What vegetarian options do you have?")
    
    assert isinstance(query, UserQuery)
    assert query.original_query == "What vegetarian options do you have?"
    assert query.query_type == "menu"
    assert query.needs_clarification == False
    assert len(query.clarification_questions) == 0
    assert "vegetarian" in query.refined_query.lower()
    assert "conversation_id" in query.context
    
    # Check query history
    assert len(agent.query_history) == 1


def test_reservation_query_clarification():
    """Test reservation queries that need clarification."""
    agent = UIAgent()
    
    # Test reservation query without time/party size
    query = agent.process_user_query("I want to make a reservation")
    
    assert query.query_type == "reservation"
    assert query.needs_clarification == True
    assert len(query.clarification_questions) == 2
    assert any("time" in q.lower() for q in query.clarification_questions)
    assert any("people" in q.lower() or "party" in q.lower() for q in query.clarification_questions)


def test_short_query_clarification():
    """Test very short queries that need clarification."""
    agent = UIAgent()
    
    # Test very short query
    query = agent.process_user_query("Menu")
    
    assert query.needs_clarification == True
    assert len(query.clarification_questions) == 1
    assert "details" in query.clarification_questions[0].lower()


def test_send_query_to_orchestrator():
    """Test sending queries to orchestrator."""
    agent = UIAgent()
    
    # Process a query first
    user_query = agent.process_user_query("Show me the menu")
    
    # Send to orchestrator
    message = agent.send_query_to_orchestrator(user_query)
    
    assert isinstance(message, AgentMessage)
    assert message.sender == "ui_agent"
    assert message.receiver == "orchestrator"
    assert message.message_type == "user_query"
    assert "query" in message.content
    assert "query_type" in message.content
    assert message.content["query_type"] == "menu"
    assert message.conversation_id == user_query.context["conversation_id"]


def test_menu_query_refinement():
    """Test menu query refinement."""
    agent = UIAgent()
    
    # Test vegetarian menu query
    query = agent.process_user_query("vegetarian options")
    assert "vegetarian" in query.refined_query.lower()
    assert "show vegetarian" in query.refined_query.lower()
    
    # Test allergen query
    query = agent.process_user_query("menu without allergens")
    assert "allergen" in query.refined_query.lower()


def test_query_types():
    """Test different query type detection."""
    agent = UIAgent()
    
    # Menu query
    query = agent.process_user_query("show me the food options")
    assert query.query_type == "menu"
    
    # Reservation query
    query = agent.process_user_query("book a table for 4")
    assert query.query_type == "reservation"
    
    # Order query
    query = agent.process_user_query("place an order")
    assert query.query_type == "order"
    
    # General query
    query = agent.process_user_query("hello there")
    assert query.query_type == "general"


def test_message_processing():
    """Test UI agent message processing."""
    agent = UIAgent()
    
    # Create an orchestrator response message
    orchestrator_message = AgentMessage(
        sender="orchestrator",
        receiver="ui_agent",
        message_type="orchestrator_response",
        content={
            "response_type": "menu_info",
            "success": True,
            "message": "Menu retrieved",
            "dishes": [
                {"name": "Pizza", "price": 12.99},
                {"name": "Pasta", "price": 10.99}
            ]
        }
    )
    
    # Process the message
    response = agent.receive_message(orchestrator_message)
    
    assert "response_for_user" in response
    assert "Pizza" in response["response_for_user"]
    assert "Pasta" in response["response_for_user"]


def test_error_message_processing():
    """Test UI agent error message processing."""
    agent = UIAgent()
    
    # Create an error message
    error_message = AgentMessage(
        sender="orchestrator",
        receiver="ui_agent",
        message_type="error",
        content={
            "error_type": "database_error",
            "error": "Connection failed"
        }
    )
    
    # Process the message
    response = agent.receive_message(error_message)
    
    assert "user_message" in response
    assert "problem accessing" in response["user_message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])