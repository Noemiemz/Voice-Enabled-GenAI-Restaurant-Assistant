"""
Orchestrator Agent for coordinating between UI agent and tools.
This agent receives queries from the UI agent, decides what actions to take,
and coordinates responses back to the UI agent.
"""

from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent, AgentMessage
from pydantic import BaseModel, Field
import uuid


class OrchestratorDecision(BaseModel):
    """Structure for orchestrator decisions."""
    action: str = Field(..., description="Action to take (db_query, direct_response, etc.)")
    target: Optional[str] = Field(None, description="Target tool/agent for the action")
    parameters: Dict[str, Any] = Field({}, description="Parameters for the action")
    needs_db_access: bool = Field(False, description="Whether database access is needed")
    reason: str = Field(..., description="Reason for this decision")


class OrchestratorAgent(BaseAgent):
    """Orchestrator Agent for coordinating system operations."""
    
    def __init__(self, name: str = "orchestrator", description: str = "Coordinates between agents and tools"):
        """
        Initialize the Orchestrator Agent.
        
        Args:
            name: Agent name
            description: Agent description
        """
        super().__init__(name, description)
        self.available_tools = []  # Will be populated with available tools
        self.decision_history = []
    
    def register_tool(self, tool_name: str, tool_description: str = "") -> None:
        """
        Register a tool that the orchestrator can use.
        
        Args:
            tool_name: Name of the tool
            tool_description: Description of the tool
        """
        self.available_tools.append({
            "name": tool_name,
            "description": tool_description
        })
    
    def process_user_query(self, user_query_message: AgentMessage) -> AgentMessage:
        """
        Process a user query message from the UI agent.
        
        Args:
            user_query_message: AgentMessage containing user query
            
        Returns:
            AgentMessage with response or follow-up action
        """
        # Extract query information
        query_content = user_query_message.content
        query = query_content.get("query", "")
        query_type = query_content.get("query_type", "general")
        needs_clarification = query_content.get("needs_clarification", False)
        conversation_id = user_query_message.conversation_id
        
        # Store decision context
        decision_context = {
            "original_query": query,
            "query_type": query_type,
            "conversation_id": conversation_id,
            "user_query_message": query_content
        }
        
        # Make decision about how to handle the query
        decision = self._make_decision(decision_context)
        
        # Store decision in history
        self._store_decision(decision, decision_context)
        
        # Execute the decision
        response_message = self._execute_decision(decision, user_query_message)
        
        return response_message
    
    def _make_decision(self, context: Dict[str, Any]) -> OrchestratorDecision:
        """
        Make a decision about how to handle a query.
        
        Args:
            context: Context information for the decision
            
        Returns:
            OrchestratorDecision object
        """
        query_type = context.get("query_type", "general")
        query = context.get("original_query", "")
        
        # Decision logic based on query type
        if query_type == "menu":
            return self._decide_menu_action(query, context)
        elif query_type == "reservation":
            return self._decide_reservation_action(query, context)
        elif query_type == "order":
            return self._decide_order_action(query, context)
        else:
            return self._decide_general_action(query, context)
    
    def _decide_menu_action(self, query: str, context: Dict[str, Any]) -> OrchestratorDecision:
        """Make decision for menu-related queries."""
        # For menu queries, we typically need database access
        return OrchestratorDecision(
            action="db_query",
            target="menu_database",
            parameters={
                "query": query,
                "collection": "Dish",
                "filter": self._extract_menu_filters(query)
            },
            needs_db_access=True,
            reason="Menu queries require database access to retrieve dish information"
        )
    
    def _decide_reservation_action(self, query: str, context: Dict[str, Any]) -> OrchestratorDecision:
        """Make decision for reservation-related queries."""
        # For reservation queries, we typically need database access
        return OrchestratorDecision(
            action="db_query",
            target="reservation_database",
            parameters={
                "query": query,
                "collection": "Reservation",
                "filter": self._extract_reservation_filters(query)
            },
            needs_db_access=True,
            reason="Reservation queries require database access to check availability"
        )
    
    def _decide_order_action(self, query: str, context: Dict[str, Any]) -> OrchestratorDecision:
        """Make decision for order-related queries."""
        # For order queries, we might need database access or can handle directly
        if "status" in query.lower() or "check" in query.lower():
            # Checking order status
            return OrchestratorDecision(
                action="db_query",
                target="order_database",
                parameters={
                    "query": query,
                    "collection": "Order",
                    "filter": self._extract_order_filters(query)
                },
                needs_db_access=True,
                reason="Order status queries require database access"
            )
        else:
            # Placing a new order - might not need immediate DB access
            return OrchestratorDecision(
                action="direct_response",
                target="ui_agent",
                parameters={
                    "message": "Order processing initiated",
                    "next_steps": ["confirm_order_details", "payment_processing"]
                },
                needs_db_access=False,
                reason="New order can be processed without immediate database access"
            )
    
    def _decide_general_action(self, query: str, context: Dict[str, Any]) -> OrchestratorDecision:
        """Make decision for general queries."""
        # For general queries, try to provide a direct response
        return OrchestratorDecision(
            action="direct_response",
            target="ui_agent",
            parameters={
                "message": self._generate_general_response(query),
                "query_type": "general"
            },
            needs_db_access=False,
            reason="General queries can be handled with direct responses"
        )
    
    def _extract_menu_filters(self, query: str) -> Dict[str, Any]:
        """Extract filters for menu queries."""
        filters = {}
        query_lower = query.lower()
        
        if "vegetarian" in query_lower:
            filters["is_vegetarian"] = True
        
        if "allergen" in query_lower or "allergy" in query_lower:
            filters["ingredients.is_allergen"] = False
        
        # Extract category if mentioned
        categories = ["appetizer", "main", "dessert", "drink", "starter"]
        for category in categories:
            if category in query_lower:
                filters["category"] = category
                break
        
        return filters
    
    def _extract_reservation_filters(self, query: str) -> Dict[str, Any]:
        """Extract filters for reservation queries."""
        filters = {}
        # In a real implementation, this would extract dates, times, party sizes
        # For now, we'll keep it simple
        return filters
    
    def _extract_order_filters(self, query: str) -> Dict[str, Any]:
        """Extract filters for order queries."""
        filters = {}
        # In a real implementation, this would extract order IDs, customer info, etc.
        return filters
    
    def _generate_general_response(self, query: str) -> str:
        """Generate a response for general queries."""
        query_lower = query.lower()
        
        if any(greeting in query_lower for greeting in ["hello", "hi", "hey", "greetings"]):
            return "Hello! Welcome to our restaurant. How can I assist you today?"
        elif any(thanks in query_lower for thanks in ["thank", "thanks", "appreciate"]):
            return "You're welcome! Is there anything else I can help you with?"
        elif any(bye in query_lower for bye in ["bye", "goodbye", "see you", "farewell"]):
            return "Goodbye! We hope to see you at our restaurant soon."
        else:
            return "Thank you for your message. How can I assist you with our restaurant services?"
    
    def _store_decision(self, decision: OrchestratorDecision, context: Dict[str, Any]) -> None:
        """Store decision in history."""
        decision_record = {
            "decision": decision.model_dump(),
            "context": context,
            "timestamp": decision.model_dump().get("timestamp", str(uuid.uuid4()))
        }
        self.decision_history.append(decision_record)
    
    def _execute_decision(self, decision: OrchestratorDecision, original_message: AgentMessage) -> AgentMessage:
        """
        Execute the orchestrator's decision.
        
        Args:
            decision: Decision to execute
            original_message: Original message that triggered this decision
            
        Returns:
            AgentMessage with response
        """
        if decision.action == "db_query":
            return self._execute_db_query(decision, original_message)
        elif decision.action == "direct_response":
            return self._execute_direct_response(decision, original_message)
        else:
            return self._execute_default_response(decision, original_message)
    
    def _execute_db_query(self, decision: OrchestratorDecision, original_message: AgentMessage) -> AgentMessage:
        """Execute a database query decision."""
        # In a real implementation, this would call the actual DB tool
        # For now, we'll simulate it with mock data
        
        # Prepare response based on query type
        response_content = self._generate_mock_db_response(decision)
        
        # Send response back to UI agent
        return self.send_message(
            receiver=original_message.sender,
            message_type="orchestrator_response",
            content=response_content,
            conversation_id=original_message.conversation_id
        )
    
    def _generate_mock_db_response(self, decision: OrchestratorDecision) -> Dict[str, Any]:
        """Generate mock database responses for testing."""
        query_type = decision.parameters.get("query_type")
        collection = decision.parameters.get("collection")
        
        # Generate different responses based on collection
        if collection == "Dish":
            return self._generate_mock_menu_response(decision)
        elif collection == "Reservation":
            return self._generate_mock_reservation_response(decision)
        elif collection == "Order":
            return self._generate_mock_order_response(decision)
        else:
            return {
                "response_type": "general_db_response",
                "success": True,
                "message": "Database query executed successfully",
                "data": {}
            }
    
    def _generate_mock_menu_response(self, decision: OrchestratorDecision) -> Dict[str, Any]:
        """Generate mock menu response."""
        # Mock dish data based on filters
        filters = decision.parameters.get("filter", {})
        
        mock_dishes = [
            {
                "name": "Margherita Pizza",
                "category": "main",
                "price": 12.99,
                "is_vegetarian": True,
                "ingredients": [
                    {"name": "tomato sauce", "is_allergen": False, "allergen_type": None},
                    {"name": "mozzarella", "is_allergen": True, "allergen_type": "dairy"},
                    {"name": "basil", "is_allergen": False, "allergen_type": None}
                ]
            },
            {
                "name": "Grilled Salmon",
                "category": "main",
                "price": 18.99,
                "is_vegetarian": False,
                "ingredients": [
                    {"name": "salmon", "is_allergen": True, "allergen_type": "fish"},
                    {"name": "lemon", "is_allergen": False, "allergen_type": None},
                    {"name": "herbs", "is_allergen": False, "allergen_type": None}
                ]
            },
            {
                "name": "Chocolate Lava Cake",
                "category": "dessert",
                "price": 7.99,
                "is_vegetarian": True,
                "ingredients": [
                    {"name": "chocolate", "is_allergen": False, "allergen_type": None},
                    {"name": "flour", "is_allergen": True, "allergen_type": "gluten"},
                    {"name": "eggs", "is_allergen": True, "allergen_type": "eggs"}
                ]
            }
        ]
        
        # Apply filters
        filtered_dishes = []
        for dish in mock_dishes:
            include_dish = True
            
            # Apply vegetarian filter
            if filters.get("is_vegetarian") and not dish["is_vegetarian"]:
                include_dish = False
            
            # Apply allergen filter
            if filters.get("ingredients.is_allergen") is False:
                # Check if dish has any allergens
                has_allergens = any(ing["is_allergen"] for ing in dish["ingredients"])
                if has_allergens:
                    include_dish = False
            
            # Apply category filter
            if "category" in filters and dish["category"] != filters["category"]:
                include_dish = False
            
            if include_dish:
                filtered_dishes.append(dish)
        
        return {
            "response_type": "menu_info",
            "success": True,
            "message": "Menu information retrieved successfully",
            "dishes": filtered_dishes,
            "count": len(filtered_dishes)
        }
    
    def _generate_mock_reservation_response(self, decision: OrchestratorDecision) -> Dict[str, Any]:
        """Generate mock reservation response."""
        # Mock reservation data
        return {
            "response_type": "reservation_info",
            "success": True,
            "message": "Reservation information retrieved successfully",
            "available_tables": [
                {
                    "table_id": "T01",
                    "capacity": 4,
                    "location": "by the window",
                    "available_times": ["18:00", "19:30", "21:00"]
                },
                {
                    "table_id": "T05",
                    "capacity": 6,
                    "location": "center",
                    "available_times": ["18:30", "20:00", "21:30"]
                }
            ]
        }
    
    def _generate_mock_order_response(self, decision: OrchestratorDecision) -> Dict[str, Any]:
        """Generate mock order response."""
        # Mock order data
        return {
            "response_type": "order_info",
            "success": True,
            "message": "Order information retrieved successfully",
            "order": {
                "order_id": "ORD-2023-001",
                "status": "preparing",
                "items": [
                    {"name": "Margherita Pizza", "quantity": 1, "price": 12.99},
                    {"name": "Caesar Salad", "quantity": 2, "price": 8.99}
                ],
                "total": 30.97,
                "estimated_ready_time": "20 minutes"
            }
        }
    
    def _execute_direct_response(self, decision: OrchestratorDecision, original_message: AgentMessage) -> AgentMessage:
        """Execute a direct response decision."""
        # Prepare response content from decision parameters
        response_content = decision.parameters.copy()
        response_content["response_type"] = "direct_response"
        response_content["success"] = True
        
        # Send response back to UI agent
        return self.send_message(
            receiver=original_message.sender,
            message_type="orchestrator_response",
            content=response_content,
            conversation_id=original_message.conversation_id
        )
    
    def _execute_default_response(self, decision: OrchestratorDecision, original_message: AgentMessage) -> AgentMessage:
        """Execute a default response for unknown actions."""
        response_content = {
            "response_type": "default_response",
            "success": False,
            "message": "I'm sorry, I couldn't determine the appropriate action for your request.",
            "suggestion": "Could you please provide more details or rephrase your request?"
        }
        
        # Send response back to UI agent
        return self.send_message(
            receiver=original_message.sender,
            message_type="orchestrator_response",
            content=response_content,
            conversation_id=original_message.conversation_id
        )
    
    def _process_message(self, message: AgentMessage) -> Dict[str, Any]:
        """
        Process incoming messages (from UI agent or tools).
        
        Args:
            message: AgentMessage to process
            
        Returns:
            Response content
        """
        response_content = {
            "status": "processed",
            "message": f"Orchestrator processed message of type {message.message_type}",
            "original_content": message.content
        }
        
        # Handle different message types
        if message.message_type == "user_query":
            # Process user query
            response_message = self.process_user_query(message)
            response_content["response_message"] = response_message.to_dict()
        elif message.message_type == "tool_response":
            # Process tool response
            response_content["tool_response"] = self._handle_tool_response(message.content)
        
        return response_content
    
    def _handle_tool_response(self, tool_response: Dict[str, Any]) -> Dict[str, Any]:
        """Handle responses from tools."""
        # Process tool response and prepare for UI agent
        tool_name = tool_response.get("tool_name", "unknown")
        success = tool_response.get("success", False)
        
        if success:
            return {
                "status": "tool_success",
                "tool": tool_name,
                "message": "Tool executed successfully",
                "data": tool_response.get("data", {})
            }
        else:
            return {
                "status": "tool_error",
                "tool": tool_name,
                "message": "Tool execution failed",
                "error": tool_response.get("error", "Unknown error")
            }