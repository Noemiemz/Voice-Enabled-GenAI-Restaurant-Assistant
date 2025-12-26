"""
UI Agent for handling user interactions.
This agent receives user queries, clarifies if needed, and sends refined queries to the orchestrator.
"""

from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent, AgentMessage
from pydantic import BaseModel, Field
import uuid


class UserQuery(BaseModel):
    """Structure for user queries."""
    original_query: str = Field(..., description="Original user query")
    refined_query: Optional[str] = Field(None, description="Refined query after clarification")
    query_type: Optional[str] = Field(None, description="Type of query (menu, reservation, etc.)")
    needs_clarification: bool = Field(False, description="Whether query needs clarification")
    clarification_questions: List[str] = Field([], description="Questions to clarify the query")
    context: Dict[str, Any] = Field({}, description="Additional context for the query")


class UIAgent(BaseAgent):
    """UI Agent for handling user interactions."""
    
    def __init__(self, name: str = "ui_agent", description: str = "Handles user interactions and query refinement"):
        """
        Initialize the UI Agent.
        
        Args:
            name: Agent name
            description: Agent description
        """
        super().__init__(name, description)
        self.query_history = []
    
    def process_user_query(self, user_query: str, conversation_id: Optional[str] = None) -> UserQuery:
        """
        Process a user query and determine if clarification is needed.
        
        Args:
            user_query: The original user query
            conversation_id: Optional conversation identifier
            
        Returns:
            UserQuery object with processing results
        """
        # Create conversation ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Initialize query object
        query = UserQuery(
            original_query=user_query,
            context={"conversation_id": conversation_id}
        )
        
        # Analyze query and determine if clarification is needed
        self._analyze_query(query)
        
        # Store query in history
        self.query_history.append(query.model_dump())
        
        return query
    
    def _analyze_query(self, query: UserQuery) -> None:
        """
        Analyze the query to determine if clarification is needed and refine it.
        
        Args:
            query: UserQuery object to analyze
        """
        # Simple analysis for now - this would be enhanced with NLP in a real implementation
        original_query = query.original_query.lower()
        
        # Check for common query types
        if any(keyword in original_query for keyword in ["menu", "dish", "food", "meal"]):
            query.query_type = "menu"
            query.refined_query = self._refine_menu_query(original_query)
        elif any(keyword in original_query for keyword in ["reservation", "book", "table", "seat"]):
            query.query_type = "reservation"
            query.refined_query = self._refine_reservation_query(original_query)
        elif any(keyword in original_query for keyword in ["order", "buy", "purchase"]):
            query.query_type = "order"
            query.refined_query = self._refine_order_query(original_query)
        else:
            query.query_type = "general"
            query.refined_query = original_query
        
        # Determine if clarification is needed
        self._check_for_clarification(query)
    
    def _refine_menu_query(self, query: str) -> str:
        """Refine menu-related queries."""
        # Simple refinement - extract key information
        refined = query
        
        # Add context about menu query
        if "vegetarian" in query:
            refined = f"Show vegetarian menu options from {query}"
        elif "allergen" in query or "allergy" in query:
            refined = f"Show menu options without allergens, specifically {query}"
        
        return refined
    
    def _refine_reservation_query(self, query: str) -> str:
        """Refine reservation-related queries."""
        # Simple refinement - extract key information
        refined = query
        
        # Check for missing information that might need clarification
        if all(keyword not in query for keyword in ["time", "date", "when", "today", "tonight"]):
            self._add_clarification_question(query, "When would you like the reservation?")
        
        if all(keyword not in query for keyword in ["people", "person", "party", "group", "table for"]):
            self._add_clarification_question(query, "How many people will be in your party?")
        
        return refined
    
    def _refine_order_query(self, query: str) -> str:
        """Refine order-related queries."""
        # Simple refinement - extract key information
        return query
    
    def _check_for_clarification(self, query: UserQuery) -> None:
        """Check if the query needs clarification."""
        # If we have clarification questions, set the flag
        if query.clarification_questions:
            query.needs_clarification = True
        else:
            # Additional checks for ambiguous queries
            if len(query.original_query.split()) < 3:  # Very short queries
                self._add_clarification_question(query, "Could you please provide more details about your request?")
    
    def _add_clarification_question(self, query: UserQuery, question: str) -> None:
        """Add a clarification question to the query."""
        query.clarification_questions.append(question)
        query.needs_clarification = True
    
    def send_query_to_orchestrator(self, query: UserQuery, orchestrator_name: str = "orchestrator") -> AgentMessage:
        """
        Send the processed query to the orchestrator agent.
        
        Args:
            query: Processed UserQuery object
            orchestrator_name: Name of the orchestrator agent
            
        Returns:
            AgentMessage sent to orchestrator
        """
        # Prepare message content
        message_content = {
            "query": query.refined_query or query.original_query,
            "query_type": query.query_type,
            "needs_clarification": query.needs_clarification,
            "clarification_questions": query.clarification_questions,
            "context": query.context
        }
        
        # Send message to orchestrator
        message = self.send_message(
            receiver=orchestrator_name,
            message_type="user_query",
            content=message_content,
            conversation_id=query.context.get("conversation_id")
        )
        
        return message
    
    def _process_message(self, message: AgentMessage) -> Dict[str, Any]:
        """
        Process incoming messages (from orchestrator or other agents).
        
        Args:
            message: AgentMessage to process
            
        Returns:
            Response content
        """
        response_content = {
            "status": "processed",
            "message": f"UI Agent processed message of type {message.message_type}",
            "original_content": message.content
        }
        
        # Handle different message types
        if message.message_type == "orchestrator_response":
            response_content["response_for_user"] = self._format_response_for_user(message.content)
        elif message.message_type == "error":
            response_content["error"] = message.content.get("error", "Unknown error")
            response_content["user_message"] = self._format_error_for_user(message.content)
        
        return response_content
    
    def _format_response_for_user(self, orchestrator_response: Dict[str, Any]) -> str:
        """Format orchestrator response for the user."""
        # Extract relevant information from orchestrator response
        response_type = orchestrator_response.get("response_type", "general")
        
        if response_type == "menu_info":
            return self._format_menu_response(orchestrator_response)
        elif response_type == "reservation_info":
            return self._format_reservation_response(orchestrator_response)
        elif response_type == "order_info":
            return self._format_order_response(orchestrator_response)
        else:
            return orchestrator_response.get("message", "Thank you for your request.")
    
    def _format_menu_response(self, response: Dict[str, Any]) -> str:
        """Format menu information for user."""
        dishes = response.get("dishes", [])
        if not dishes:
            return "I'm sorry, no menu items were found matching your request."
        
        dish_list = "\n".join([
            f"• {dish.get('name', 'Unknown dish')} - ${dish.get('price', 'N/A')}"
            for dish in dishes
        ])
        
        return f"Here are some menu options that match your request:\n\n{dish_list}"
    
    def _format_reservation_response(self, response: Dict[str, Any]) -> str:
        """Format reservation information for user."""
        success = response.get("success", False)
        if success:
            return (f"Your reservation has been successfully made for "
                   f"{response.get('date', 'the requested date')} at "
                   f"{response.get('time', 'the requested time')}.")
        else:
            return (f"I'm sorry, there was an issue with your reservation. "
                   f"{response.get('message', 'Please try again later.')}")
    
    def _format_order_response(self, response: Dict[str, Any]) -> str:
        """Format order information for user."""
        success = response.get("success", False)
        if success:
            return (f"Your order has been successfully placed. "
                   f"Order ID: {response.get('order_id', 'N/A')}")
        else:
            return (f"I'm sorry, there was an issue with your order. "
                   f"{response.get('message', 'Please try again later.')}")
    
    def _format_error_for_user(self, error_content: Dict[str, Any]) -> str:
        """Format error messages for the user."""
        error_type = error_content.get("error_type", "general")
        
        if error_type == "database_error":
            return "I'm sorry, there was a problem accessing the restaurant information. Please try again later."
        elif error_type == "validation_error":
            return "I'm sorry, I didn't understand your request. Could you please rephrase it?"
        else:
            return "I'm sorry, an error occurred while processing your request. Please try again."