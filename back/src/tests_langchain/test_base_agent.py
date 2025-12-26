"""
Test cases for the base agent functionality.
"""

import pytest
from agents_langchain.base_agent import BaseAgent, AgentMessage
from datetime import datetime


def test_base_agent_initialization():
    """Test that base agent initializes correctly."""
    agent = BaseAgent(name="test_agent", description="Test agent for unit tests")
    
    assert agent.name == "test_agent"
    assert agent.description == "Test agent for unit tests"
    assert agent.conversation_history == []
    assert str(agent) == "test_agent: Test agent for unit tests"


def test_agent_message_creation():
    """Test AgentMessage creation and serialization."""
    message = AgentMessage(
        sender="agent1",
        receiver="agent2",
        message_type="test",
        content={"key": "value"}
    )
    
    assert message.sender == "agent1"
    assert message.receiver == "agent2"
    assert message.message_type == "test"
    assert message.content == {"key": "value"}
    assert isinstance(message.timestamp, datetime)
    
    # Test serialization
    message_dict = message.to_dict()
    assert message_dict["sender"] == "agent1"
    assert "timestamp" in message_dict
    
    # Test JSON serialization
    message_json = message.to_json()
    assert "agent1" in message_json
    
    # Test deserialization
    new_message = AgentMessage.from_dict(message_dict)
    assert new_message.sender == message.sender
    
    new_message_from_json = AgentMessage.from_json(message_json)
    assert new_message_from_json.sender == message.sender


def test_send_message():
    """Test sending messages between agents."""
    agent1 = BaseAgent(name="agent1")
    agent2 = BaseAgent(name="agent2")
    
    message = agent1.send_message(
        receiver="agent2",
        message_type="test",
        content={"test": "data"}
    )
    
    assert message.sender == "agent1"
    assert message.receiver == "agent2"
    assert message.message_type == "test"
    assert message.content == {"test": "data"}
    
    # Check that message was added to conversation history
    assert len(agent1.conversation_history) == 1
    assert agent1.conversation_history[0]["sender"] == "agent1"


def test_receive_message():
    """Test receiving messages."""
    agent = BaseAgent(name="test_agent")
    
    # Create a message
    message = AgentMessage(
        sender="other_agent",
        receiver="test_agent",
        message_type="test",
        content={"action": "process"}
    )
    
    # This should raise NotImplementedError since _process_message is not implemented
    with pytest.raises(NotImplementedError):
        agent.receive_message(message)
    
    # But the message should still be added to conversation history
    assert len(agent.conversation_history) == 1


def test_conversation_history():
    """Test conversation history management."""
    agent = BaseAgent(name="test_agent")
    
    # Send some messages
    agent.send_message("agent2", "type1", {"data": "1"})
    agent.send_message("agent3", "type2", {"data": "2"})
    
    # Check history
    history = agent.get_conversation_history()
    assert len(history) == 2
    assert history[0]["message_type"] == "type1"
    assert history[1]["message_type"] == "type2"
    
    # Clear history
    agent.clear_conversation_history()
    assert len(agent.get_conversation_history()) == 0


def test_message_with_conversation_id():
    """Test messages with conversation IDs."""
    agent = BaseAgent(name="test_agent")
    
    # Send messages with different conversation IDs
    msg1 = agent.send_message("agent2", "type1", {"data": "1"}, conversation_id="conv1")
    msg2 = agent.send_message("agent2", "type1", {"data": "2"}, conversation_id="conv2")
    msg3 = agent.send_message("agent2", "type1", {"data": "3"}, conversation_id="conv1")
    
    # Check conversation-specific history
    conv1_history = agent.get_conversation_history("conv1")
    conv2_history = agent.get_conversation_history("conv2")
    
    assert len(conv1_history) == 2
    assert len(conv2_history) == 1
    assert conv1_history[0]["content"] == {"data": "1"}
    assert conv2_history[0]["content"] == {"data": "2"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])