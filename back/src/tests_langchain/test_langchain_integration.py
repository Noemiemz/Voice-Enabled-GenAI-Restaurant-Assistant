"""
Integration tests for LangChain-enhanced agents.
Tests the complete LangChain integration and functionality.
"""

import pytest
import json
from agents_langchain.langchain_integration import setup_langchain_agents
from agents_langchain.ui_agent_langchain import LangChainUIAgent
from agents_langchain.orchestrator_agent_langchain import LangChainOrchestratorAgent
from agents_langchain.tools.db_tool_langchain import RestaurantDBTool
from langchain_classic.llms.fake import FakeListLLM
from langchain_classic.memory import ConversationBufferMemory


def test_langchain_agent_setup():
    """Test basic LangChain agent setup."""
    
    # Create mock LLM
    responses = [
        '{"query_type": "menu", "needs_clarification": false, "clarification_questions": [], "refined_query": "test query", "key_details": {}}',
        "Friendly response for user"
    ]
    mock_llm = FakeListLLM(responses=responses)
    
    # Set up agents
    system = setup_langchain_agents(llm=mock_llm)
    
    assert "ui_agent" in system
    assert "orchestrator" in system
    assert "db_tool" in system
    assert "llm" in system
    assert "memory" in system
    
    # Verify agent types
    assert isinstance(system["ui_agent"], LangChainUIAgent)
    assert isinstance(system["orchestrator"], LangChainOrchestratorAgent)
    assert isinstance(system["db_tool"], RestaurantDBTool)


def test_langchain_ui_agent_query_processing():
    """Test LangChain UI agent query processing."""
    
    # Create mock LLM with JSON response
    responses = [
        '{"query_type": "menu", "needs_clarification": false, "clarification_questions": [], "refined_query": "Show vegetarian menu", "key_details": {"dietary_preference": "vegetarian"}}'
    ]
    mock_llm = FakeListLLM(responses=responses)
    
    # Create UI agent
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    ui_agent = LangChainUIAgent(llm=mock_llm, memory=memory)
    
    # Process query
    query_data = ui_agent.process_user_query("What vegetarian options do you have?")
    
    assert "query_type" in query_data
    assert query_data["query_type"] == "menu"
    assert "llm_analysis" in query_data
    assert query_data["needs_clarification"] == False


def test_langchain_orchestrator_decision_making():
    """Test LangChain orchestrator decision making."""
    
    # Create mock LLM with decision response
    decision_response = """
    {
        "action": "db_query",
        "target": "menu_database",
        "parameters": {"collection": "Dish"},
        "needs_db_access": true,
        "reason": "Menu query requires database access",
        "confidence": 0.9
    }
    """
    
    mock_llm = FakeListLLM(responses=[decision_response])
    
    # Create orchestrator
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    orchestrator = LangChainOrchestratorAgent(llm=mock_llm, memory=memory)
    
    # Create a mock message
    from agents_langchain.base_agent_langchain import AgentMessage
    
    user_message = AgentMessage(
        sender="ui_agent",
        receiver="orchestrator",
        message_type="user_query",
        content={
            "query": "Show me the menu",
            "query_type": "menu",
            "needs_clarification": False,
            "context": {}
        }
    )
    
    # Process the message
    response = orchestrator.process_user_query(user_message)
    
    assert response.sender == "orchestrator"
    assert response.receiver == "ui_agent"
    assert response.message_type == "orchestrator_response"


def test_langchain_db_tool():
    """Test LangChain database tool."""
    
    # Create DB tool
    db_tool = RestaurantDBTool()
    
    # Test query
    test_query = {
        "collection": "Dish",
        "query": {"is_vegetarian": True}
    }
    
    result = db_tool._run(test_query)
    result_data = json.loads(result)
    
    assert result_data["success"] == True
    assert len(result_data["data"]) > 0
    assert all(dish["is_vegetarian"] for dish in result_data["data"])


def test_langchain_memory_integration():
    """Test LangChain memory integration."""
    
    # Create mock LLM
    mock_llm = FakeListLLM(responses=["test response"])
    
    # Create memory
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    # Create agents with shared memory
    ui_agent = LangChainUIAgent(llm=mock_llm, memory=memory)
    orchestrator = LangChainOrchestratorAgent(llm=mock_llm, memory=memory)
    
    # Verify memory is shared
    assert ui_agent.memory is orchestrator.memory
    
    # Test memory operations
    initial_memory = memory.load_memory_variables({})
    assert "chat_history" in initial_memory


def test_complete_langchain_flow():
    """Test complete LangChain agent flow."""
    
    # Create mock LLM responses
    responses = [
        # UI agent query analysis
        '{"query_type": "menu", "needs_clarification": false, "clarification_questions": [], "refined_query": "Show vegetarian menu", "key_details": {"dietary_preference": "vegetarian"}}',
        # Orchestrator decision
        '{"action": "db_query", "target": "menu_database", "parameters": {"collection": "Dish", "query": {"is_vegetarian": true}}, "needs_db_access": true, "reason": "Menu query", "confidence": 0.9}',
        # Response formatting
        "Here are some delicious vegetarian options from our menu:",
        # DB tool response will use mock data
    ]
    
    mock_llm = FakeListLLM(responses=responses)
    
    # Set up complete system
    system = setup_langchain_agents(llm=mock_llm)
    ui_agent = system["ui_agent"]
    orchestrator = system["orchestrator"]
    
    # Test complete flow
    user_query = "What vegetarian options do you have?"
    
    # Step 1: UI agent processes query
    query_data = ui_agent.process_user_query(user_query)
    assert query_data["query_type"] == "menu"
    
    # Step 2: Send to orchestrator
    message = ui_agent.send_query_to_orchestrator(query_data)
    assert message.message_type == "user_query"
    
    # Step 3: Orchestrator processes
    response = orchestrator.process_user_query(message)
    assert response.message_type == "orchestrator_response"
    
    # Step 4: UI agent formats response
    final_response = ui_agent.receive_message(response)
    assert "response_for_user" in final_response


def test_langchain_error_handling():
    """Test LangChain error handling."""
    
    # Create mock LLM that returns invalid JSON
    mock_llm = FakeListLLM(responses=["Invalid JSON response"])
    
    # Create UI agent
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    ui_agent = LangChainUIAgent(llm=mock_llm, memory=memory)
    
    # Process query - should handle JSON error gracefully
    query_data = ui_agent.process_user_query("Test query")
    
    # Should have fallback values
    assert "query_type" in query_data
    assert query_data["needs_clarification"] == True


def test_langchain_tool_registration():
    """Test LangChain tool registration."""
    
    mock_llm = FakeListLLM(responses=["test"])
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    orchestrator = LangChainOrchestratorAgent(llm=mock_llm, memory=memory)
    db_tool = RestaurantDBTool()
    
    # Register tool
    orchestrator.register_tool(db_tool)
    
    # Check that tool is registered
    assert len(orchestrator.tools) == 1
    assert orchestrator.tools[0].name == "restaurant_database"


def test_langchain_message_format():
    """Test LangChain message format compatibility."""
    
    mock_llm = FakeListLLM(responses=["test"])
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    ui_agent = LangChainUIAgent(llm=mock_llm, memory=memory)
    
    # Create a message
    message = ui_agent.send_message(
        receiver="orchestrator",
        message_type="user_query",
        content={"query": "test"}
    )
    
    # Test LangChain message conversion
    langchain_messages = message.to_langchain_messages()
    assert len(langchain_messages) == 2  # System + Human message
    assert langchain_messages[0].content.startswith("Agent communication:")


def test_langchain_agent_executor():
    """Test LangChain agent executor functionality."""
    
    # Create mock LLM
    mock_llm = FakeListLLM(responses=["Agent execution result"])
    
    # Create orchestrator with tool
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    orchestrator = LangChainOrchestratorAgent(llm=mock_llm, memory=memory)
    db_tool = RestaurantDBTool()
    orchestrator.register_tool(db_tool)
    
    # Test agent executor availability
    if orchestrator.agent_executor:
        result = orchestrator.use_agent_executor("Test query")
        assert result == "Agent execution result"
    else:
        # If agent executor isn't set up, this test is skipped
        assert False, "Agent executor should be available after tool registration"


def test_langchain_memory_persistence():
    """Test LangChain memory persistence across interactions."""
    
    mock_llm = FakeListLLM(responses=["response1", "response2", "response3"])
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    ui_agent = LangChainUIAgent(llm=mock_llm, memory=memory)
    
    # First interaction
    query_data1 = ui_agent.process_user_query("First query")
    message1 = ui_agent.send_query_to_orchestrator(query_data1)
    
    # Second interaction
    query_data2 = ui_agent.process_user_query("Second query")
    message2 = ui_agent.send_query_to_orchestrator(query_data2)
    
    # Check memory growth
    memory_vars = memory.load_memory_variables({})
    chat_history = memory_vars.get("chat_history", [])
    
    assert len(chat_history) >= 2  # Should have at least 2 interactions


def test_langchain_fallback_behavior():
    """Test LangChain fallback behavior when LLM fails."""
    
    # Create mock LLM that raises exceptions
    class FailingLLM(FakeListLLM):
        def _call(self, prompt: str, **kwargs: Any) -> str:
            raise Exception("LLM failed")
    
    failing_llm = FailingLLM(responses=[])
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    ui_agent = LangChainUIAgent(llm=failing_llm, memory=memory)
    
    # Process query - should handle LLM failure gracefully
    query_data = ui_agent.process_user_query("Test query")
    
    # Should have fallback values
    assert "query_type" in query_data
    assert "llm_error" in query_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])