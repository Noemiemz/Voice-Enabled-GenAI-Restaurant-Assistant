"""
Communication schemas for agent messages.
Defines the structure and validation for messages exchanged between agents.
"""

from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# Basic message types
class BaseMessage(BaseModel):
    """Base structure for all agent messages."""
    message_id: str = Field(..., description="Unique message identifier")
    sender: str = Field(..., description="Name of the sending agent")
    receiver: str = Field(..., description="Name of the receiving agent")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")
    message_type: str = Field(..., description="Type of message")


# UI Agent to Orchestrator messages
class UserQueryMessage(BaseMessage):
    """Message structure for user queries from UI agent to orchestrator."""
    message_type: Literal["user_query"] = "user_query"
    query: str = Field(..., description="User query text")
    query_type: str = Field(..., description="Type of query (menu, reservation, order, general)")
    needs_clarification: bool = Field(False, description="Whether query needs clarification")
    clarification_questions: List[str] = Field([], description="Questions to clarify the query")
    context: Dict[str, Any] = Field({}, description="Additional context for the query")
    original_query: Optional[str] = Field(None, description="Original query before refinement")


# Orchestrator to UI Agent messages
class OrchestratorResponseMessage(BaseMessage):
    """Message structure for responses from orchestrator to UI agent."""
    message_type: Literal["orchestrator_response"] = "orchestrator_response"
    response_type: str = Field(..., description="Type of response (menu_info, reservation_info, etc.)")
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: Dict[str, Any] = Field({}, description="Response data")
    error: Optional[str] = Field(None, description="Error message if any")


# Menu-specific response
class MenuResponseMessage(OrchestratorResponseMessage):
    """Message structure for menu-related responses."""
    response_type: Literal["menu_info"] = "menu_info"
    dishes: List[Dict[str, Any]] = Field([], description="List of dishes")
    count: int = Field(0, description="Number of dishes returned")


# Reservation-specific response
class ReservationResponseMessage(OrchestratorResponseMessage):
    """Message structure for reservation-related responses."""
    response_type: Literal["reservation_info"] = "reservation_info"
    available_tables: List[Dict[str, Any]] = Field([], description="List of available tables")


# Order-specific response
class OrderResponseMessage(OrchestratorResponseMessage):
    """Message structure for order-related responses."""
    response_type: Literal["order_info"] = "order_info"
    order: Dict[str, Any] = Field({}, description="Order information")


# Error message structure
class ErrorMessage(BaseMessage):
    """Message structure for error messages."""
    message_type: Literal["error"] = "error"
    error_type: str = Field(..., description="Type of error")
    error_message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    suggestion: Optional[str] = Field(None, description="Suggestion for resolution")


# Tool-related messages
class ToolRequestMessage(BaseMessage):
    """Message structure for tool requests."""
    message_type: Literal["tool_request"] = "tool_request"
    tool_name: str = Field(..., description="Name of the tool to use")
    tool_parameters: Dict[str, Any] = Field({}, description="Parameters for the tool")
    context: Dict[str, Any] = Field({}, description="Context for the tool execution")


class ToolResponseMessage(BaseMessage):
    """Message structure for tool responses."""
    message_type: Literal["tool_response"] = "tool_response"
    tool_name: str = Field(..., description="Name of the tool that responded")
    success: bool = Field(..., description="Whether the tool execution was successful")
    result: Dict[str, Any] = Field({}, description="Tool execution result")
    error: Optional[str] = Field(None, description="Error message if any")


# Database query messages
class DatabaseQueryMessage(BaseMessage):
    """Message structure for database queries."""
    message_type: Literal["db_query"] = "db_query"
    collection: str = Field(..., description="Database collection to query")
    query: Dict[str, Any] = Field({}, description="Query parameters")
    projection: Optional[Dict[str, int]] = Field(None, description="Field projection")
    limit: Optional[int] = Field(None, description="Result limit")
    skip: Optional[int] = Field(None, description="Results to skip")
    sort: Optional[List[tuple]] = Field(None, description="Sort criteria")


class DatabaseResponseMessage(BaseMessage):
    """Message structure for database query responses."""
    message_type: Literal["db_response"] = "db_response"
    success: bool = Field(..., description="Whether the query was successful")
    data: List[Dict[str, Any]] = Field([], description="Query results")
    count: int = Field(0, description="Number of results")
    error: Optional[str] = Field(None, description="Error message if any")


# Agent coordination messages
class AgentCoordinationMessage(BaseMessage):
    """Message structure for agent coordination."""
    message_type: Literal["coordination"] = "coordination"
    coordination_type: str = Field(..., description="Type of coordination (hand-off, status_update, etc.)")
    target_agent: str = Field(..., description="Target agent for coordination")
    payload: Dict[str, Any] = Field({}, description="Coordination payload")


# Message factory for easy message creation
class MessageFactory:
    """Factory for creating different types of agent messages."""
    
    @staticmethod
    def create_user_query(
        sender: str,
        receiver: str,
        query: str,
        query_type: str,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> UserQueryMessage:
        """Create a user query message."""
        return UserQueryMessage(
            message_id=str(uuid.uuid4()),
            sender=sender,
            receiver=receiver,
            conversation_id=conversation_id,
            query=query,
            query_type=query_type,
            **kwargs
        )
    
    @staticmethod
    def create_orchestrator_response(
        sender: str,
        receiver: str,
        response_type: str,
        success: bool,
        message: str,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> OrchestratorResponseMessage:
        """Create an orchestrator response message."""
        return OrchestratorResponseMessage(
            message_id=str(uuid.uuid4()),
            sender=sender,
            receiver=receiver,
            conversation_id=conversation_id,
            response_type=response_type,
            success=success,
            message=message,
            **kwargs
        )
    
    @staticmethod
    def create_error_message(
        sender: str,
        receiver: str,
        error_type: str,
        error_message: str,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> ErrorMessage:
        """Create an error message."""
        return ErrorMessage(
            message_id=str(uuid.uuid4()),
            sender=sender,
            receiver=receiver,
            conversation_id=conversation_id,
            error_type=error_type,
            error_message=error_message,
            **kwargs
        )


# Import uuid for message ID generation
import uuid