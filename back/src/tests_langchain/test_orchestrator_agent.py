"""
Test cases for the orchestrator agent functionality.
"""

import pytest
from agents_langchain.orchestrator_agent import OrchestratorAgent, OrchestratorDecision
from agents_langchain.base_agent import AgentMessage


def test_orchestrator_initialization():
    """Test orchestrator agent initialization."""
    agent = OrchestratorAgent()
    
    assert agent.name == "orchestrator"
    assert "coordinates" in agent.description.lower()
    assert agent.available_tools == []
    assert agent.decision_history == []


def test_register_tool():
    """Test tool registration."""
    agent = OrchestratorAgent()
    
    agent.register_tool("menu_database", "Database for menu items")
    agent.register_tool("reservation_system", "System for table reservations")
    
    assert len(agent.available_tools) == 2
    assert agent.available_tools[0]["name"] == "menu_database"
    assert agent.available_tools[1]["name"] == "reservation_system"


def test_process_user_query():
    """Test processing user queries."""
    agent = OrchestratorAgent()
    
    # Create a user query message
    user_query_message = AgentMessage(
        sender="ui_agent",
        receiver="orchestrator",
        message_type="user_query",
        content={
            "query": "Show me vegetarian menu options",
            "query_type": "menu",
            "needs_clarification": False,
            "clarification_questions": [],
            "context": {}
        }
    )
    
    # Process the query
    response_message = agent.process_user_query(user_query_message)
    
    assert isinstance(response_message, AgentMessage)
    assert response_message.sender == "orchestrator"
    assert response_message.receiver == "ui_agent"
    assert response_message.message_type == "orchestrator_response"
    assert "response_type" in response_message.content


def test_menu_query_decision():
    """Test decision making for menu queries."""
    agent = OrchestratorAgent()
    
    context = {
        "original_query": "vegetarian options",
        "query_type": "menu",
        "conversation_id": "test_conv"
    }
    
    decision = agent._make_decision(context)
    
    assert isinstance(decision, OrchestratorDecision)
    assert decision.action == "db_query"
    assert decision.target == "menu_database"
    assert decision.needs_db_access == True
    assert decision.parameters["collection"] == "Dish"
    assert "is_vegetarian" in decision.parameters["filter"]
    assert decision.parameters["filter"]["is_vegetarian"] == True


def test_reservation_query_decision():
    """Test decision making for reservation queries."""
    agent = OrchestratorAgent()
    
    context = {
        "original_query": "book table for 4",
        "query_type": "reservation",
        "conversation_id": "test_conv"
    }
    
    decision = agent._make_decision(context)
    
    assert decision.action == "db_query"
    assert decision.target == "reservation_database"
    assert decision.needs_db_access == True
    assert decision.parameters["collection"] == "Reservation"


def test_order_query_decision():
    """Test decision making for order queries."""
    agent = OrchestratorAgent()
    
    # Test order status query
    context = {
        "original_query": "check my order status",
        "query_type": "order",
        "conversation_id": "test_conv"
    }
    
    decision = agent._make_decision(context)
    
    assert decision.action == "db_query"
    assert decision.needs_db_access == True
    assert decision.parameters["collection"] == "Order"
    
    # Test new order query
    context["original_query"] = "place a new order"
    decision = agent._make_decision(context)
    
    assert decision.action == "direct_response"
    assert decision.needs_db_access == False


def test_general_query_decision():
    """Test decision making for general queries."""
    agent = OrchestratorAgent()
    
    context = {
        "original_query": "hello there",
        "query_type": "general",
        "conversation_id": "test_conv"
    }
    
    decision = agent._make_decision(context)
    
    assert decision.action == "direct_response"
    assert decision.needs_db_access == False
    assert "welcome" in decision.parameters["message"].lower()


def test_decision_execution():
    """Test decision execution."""
    agent = OrchestratorAgent()
    
    # Create a decision
    decision = OrchestratorDecision(
        action="direct_response",
        target="ui_agent",
        parameters={
            "message": "Test response",
            "query_type": "general"
        },
        needs_db_access=False,
        reason="Testing"
    )
    
    # Create original message
    original_message = AgentMessage(
        sender="ui_agent",
        receiver="orchestrator",
        message_type="user_query",
        content={"query": "test"}
    )
    
    # Execute decision
    response_message = agent._execute_decision(decision, original_message)
    
    assert response_message.sender == "orchestrator"
    assert response_message.receiver == "ui_agent"
    assert response_message.message_type == "orchestrator_response"
    assert response_message.content["message"] == "Test response"


def test_menu_filters_extraction():
    """Test extraction of menu filters from queries."""
    agent = OrchestratorAgent()
    
    # Test vegetarian filter
    filters = agent._extract_menu_filters("vegetarian options")
    assert filters["is_vegetarian"] == True
    
    # Test allergen filter
    filters = agent._extract_menu_filters("no allergens please")
    assert filters["ingredients.is_allergen"] == False
    
    # Test category filter
    filters = agent._extract_menu_filters("show me dessert options")
    assert filters["category"] == "dessert"


def test_mock_menu_response():
    """Test generation of mock menu responses."""
    agent = OrchestratorAgent()
    
    # Create a decision for menu query
    decision = OrchestratorDecision(
        action="db_query",
        target="menu_database",
        parameters={
            "collection": "Dish",
            "filter": {"is_vegetarian": True}
        },
        needs_db_access=True,
        reason="Test"
    )
    
    # Generate mock response
    response = agent._generate_mock_menu_response(decision)
    
    assert response["response_type"] == "menu_info"
    assert response["success"] == True
    assert len(response["dishes"]) > 0
    
    # Check that all returned dishes are vegetarian
    for dish in response["dishes"]:
        assert dish["is_vegetarian"] == True


def test_mock_reservation_response():
    """Test generation of mock reservation responses."""
    agent = OrchestratorAgent()
    
    decision = OrchestratorDecision(
        action="db_query",
        target="reservation_database",
        parameters={
            "collection": "Reservation"
        },
        needs_db_access=True,
        reason="Test"
    )
    
    response = agent._generate_mock_reservation_response(decision)
    
    assert response["response_type"] == "reservation_info"
    assert response["success"] == True
    assert len(response["available_tables"]) > 0


def test_message_processing():
    """Test orchestrator message processing."""
    agent = OrchestratorAgent()
    
    # Create a user query message
    user_message = AgentMessage(
        sender="ui_agent",
        receiver="orchestrator",
        message_type="user_query",
        content={
            "query": "show menu",
            "query_type": "menu"
        }
    )
    
    # Process the message
    response = agent.receive_message(user_message)
    
    assert "response_message" in response
    assert isinstance(response["response_message"], dict)


def test_decision_history():
    """Test decision history tracking."""
    agent = OrchestratorAgent()
    
    # Process a query to generate a decision
    user_message = AgentMessage(
        sender="ui_agent",
        receiver="orchestrator",
        message_type="user_query",
        content={
            "query": "vegetarian menu",
            "query_type": "menu"
        }
    )
    
    agent.process_user_query(user_message)
    
    # Check decision history
    assert len(agent.decision_history) == 1
    decision_record = agent.decision_history[0]
    assert "decision" in decision_record
    assert "context" in decision_record


if __name__ == "__main__":
    pytest.main([__file__, "-v"])