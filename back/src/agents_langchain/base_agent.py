"""
Base agent class for the restaurant assistant system.
Provides common functionality for all agents.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json


class AgentMessage(BaseModel):
    """Base message format for agent communication."""
    sender: str = Field(..., description="Name of the sending agent")
    receiver: str = Field(..., description="Name of the receiving agent")
    message_type: str = Field(..., description="Type of message (query, response, error, etc.)")
    content: Dict[str, Any] = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return self.model_dump()
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return self.model_dump_json()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentMessage':
        """Create message from JSON string."""
        return cls(**json.loads(json_str))


class BaseAgent:
    """Base class for all agents in the system."""
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize the base agent.
        
        Args:
            name: Unique identifier for the agent
            description: Description of the agent's purpose
        """
        self.name = name
        self.description = description
        self.conversation_history = []
    
    def send_message(self, receiver: str, message_type: str, content: Dict[str, Any], 
                    conversation_id: Optional[str] = None) -> AgentMessage:
        """
        Create and send a message to another agent.
        
        Args:
            receiver: Name of the receiving agent
            message_type: Type of message
            content: Message content
            conversation_id: Optional conversation identifier
            
        Returns:
            AgentMessage object
        """
        message = AgentMessage(
            sender=self.name,
            receiver=receiver,
            message_type=message_type,
            content=content,
            conversation_id=conversation_id
        )
        
        # Store in conversation history
        self._add_to_conversation_history(message)
        
        return message
    
    def receive_message(self, message: AgentMessage) -> Dict[str, Any]:
        """
        Receive and process a message from another agent.
        
        Args:
            message: AgentMessage object
            
        Returns:
            Response content
        """
        # Store in conversation history
        self._add_to_conversation_history(message)
        
        # Process the message (to be implemented by subclasses)
        return self._process_message(message)
    
    def _add_to_conversation_history(self, message: AgentMessage) -> None:
        """Add message to conversation history."""
        self.conversation_history.append(message.to_dict())
    
    def _process_message(self, message: AgentMessage) -> Dict[str, Any]:
        """
        Process an incoming message. To be implemented by subclasses.
        
        Args:
            message: AgentMessage object
            
        Returns:
            Response content
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement _process_message method")
    
    def get_conversation_history(self, conversation_id: Optional[str] = None) -> list:
        """
        Get conversation history.
        
        Args:
            conversation_id: Optional conversation identifier to filter by
            
        Returns:
            List of message dictionaries
        """
        if conversation_id:
            return [msg for msg in self.conversation_history if msg.get('conversation_id') == conversation_id]
        return self.conversation_history
    
    def clear_conversation_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
    
    def __str__(self) -> str:
        return f"{self.name}: {self.description}"