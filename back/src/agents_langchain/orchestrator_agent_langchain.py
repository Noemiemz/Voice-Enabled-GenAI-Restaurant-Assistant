"""
LangChain-enhanced Orchestrator Agent for coordinating between UI agent and tools.
This agent uses LangChain for advanced decision making and tool calling.
"""

from typing import Dict, Any, Optional, List
from .base_agent_langchain import LangChainBaseAgent, AgentMessage
from .communication_schemas import MessageFactory
from langchain_classic.llms.base import LLM
from langchain_classic.memory import ConversationBufferMemory
from langchain.tools import BaseTool
from langchain_classic.agents import Tool
import json
import uuid


class LangChainOrchestratorAgent(LangChainBaseAgent):
    """LangChain-enhanced Orchestrator Agent for coordinating system operations."""
    
    def __init__(self, llm: LLM, memory: Optional[ConversationBufferMemory] = None):
        """
        Initialize the LangChain Orchestrator Agent.
        
        Args:
            llm: Language model to use
            memory: Optional conversation memory
        """
        super().__init__(
            name="orchestrator",
            llm=llm,
            description="Coordinates between agents and tools using LangChain",
            memory=memory
        )
        self.decision_history = []
        
        # Set up decision making chain
        self.decision_chain = self._create_decision_chain()
        
        # Set up tool selection chain
        self.tool_selection_chain = self._create_tool_selection_chain()
    
    def _create_decision_chain(self) -> Any:
        """Create a chain for making orchestration decisions."""
        from langchain_classic.prompts import PromptTemplate
        from langchain_classic.chains import LLMChain
        
        template = """
        You are the orchestrator agent for a restaurant assistant system.
        Analyze the following user query and make a decision about how to handle it:
        
        User Query: {query}
        Query Type: {query_type}
        Context: {context}
        Available Tools: {available_tools}
        
        Provide a JSON response with the following structure:
        {{
            "action": "db_query|direct_response|multi_step",  # Action to take
            "target": "tool_name|ui_agent",  # Target for the action
            "parameters": {{}},  # Parameters for the action
            "needs_db_access": true|false,  # Whether database access is needed
            "reason": "",  # Reason for this decision
            "confidence": 0.0-1.0  # Confidence in this decision
        }}
        
        Consider:
        - Menu queries typically need database access to the Dish collection
        - Reservation queries need access to Reservation and Table collections
        - Order queries may need Order collection access
        - General queries can often be handled with direct responses
        - Complex queries may require multi-step processing
        - Always provide a clear reason for your decision
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["query", "query_type", "context", "available_tools"]
        )
        
        return LLMChain(
            llm=self.llm,
            prompt=prompt,
            output_key="decision"
        )
    
    def _create_tool_selection_chain(self) -> Any:
        """Create a chain for selecting the appropriate tool."""
        from langchain_classic.prompts import PromptTemplate
        from langchain_classic.chains import LLMChain
        
        template = """
        Select the most appropriate tool for the following task:
        
        Task: {task}
        Available Tools: {available_tools}
        Context: {context}
        
        Provide a JSON response with:
        {{
            "selected_tool": "tool_name",
            "tool_parameters": {{}},
            "reason": ""
        }}
        
        If no tool is appropriate, return:
        {{
            "selected_tool": null,
            "reason": "No tool needed"
        }}
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["task", "available_tools", "context"]
        )
        
        return LLMChain(
            llm=self.llm,
            prompt=prompt,
            output_key="tool_selection"
        )
    
    def register_tool(self, tool: BaseTool) -> None:
        """Register a LangChain tool with the orchestrator."""
        super().register_tool(tool)
        
        # Also register as a LangChain Tool for the agent executor
        if hasattr(tool, 'name') and hasattr(tool, 'description'):
            langchain_tool = Tool(
                name=tool.name,
                func=tool.run,
                description=tool.description,
                return_direct=False
            )
            # Note: The actual tool registration for agent executor
            # happens in the parent class _setup_agent_executor method
    
    def process_user_query(self, user_query_message: AgentMessage) -> AgentMessage:
        """
        Process a user query message from the UI agent using LangChain.
        
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
        context = query_content.get("context", {})
        
        # Get available tools
        available_tools = self._get_available_tools_description()
        
        # Store decision context
        decision_context = {
            "original_query": query,
            "query_type": query_type,
            "conversation_id": conversation_id,
            "user_query_message": query_content,
            "available_tools": available_tools
        }
        
        # Make decision using LangChain
        decision = self._make_decision_with_langchain(decision_context)
        
        # Store decision in history
        self._store_decision(decision, decision_context)
        
        # Execute the decision
        response_message = self._execute_decision(decision, user_query_message)
        
        return response_message
    
    def _get_available_tools_description(self) -> str:
        """Get descriptions of available tools."""
        if not self.tools:
            return "No tools available"
        
        return ", ".join([tool.description for tool in self.tools if hasattr(tool, 'description')])
    
    def _make_decision_with_langchain(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a decision using LangChain.
        
        Args:
            context: Context information for the decision
            
        Returns:
            Decision dictionary
        """
        # Use LangChain to make the decision
        decision_result = self.decision_chain.run({
            "query": context["original_query"],
            "query_type": context["query_type"],
            "context": json.dumps(context["context"]),
            "available_tools": context["available_tools"]
        })
        
        try:
            # Parse the JSON decision
            decision = json.loads(decision_result)
            
            # Add additional metadata
            decision["conversation_id"] = context["conversation_id"]
            decision["original_query"] = context["original_query"]
            
            return decision
            
        except json.JSONDecodeError:
            # Fallback decision
            return self._create_fallback_decision(context)
    
    def _create_fallback_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fallback decision if LangChain processing fails."""
        query_type = context.get("query_type", "general")
        
        # Simple fallback logic based on query type
        if query_type == "menu":
            return {
                "action": "db_query",
                "target": "menu_database",
                "parameters": {"collection": "Dish"},
                "needs_db_access": True,
                "reason": "Menu queries require database access",
                "confidence": 0.8,
                "conversation_id": context["conversation_id"],
                "original_query": context["original_query"]
            }
        elif query_type == "reservation":
            return {
                "action": "db_query",
                "target": "reservation_database",
                "parameters": {"collection": "Reservation"},
                "needs_db_access": True,
                "reason": "Reservation queries require database access",
                "confidence": 0.8,
                "conversation_id": context["conversation_id"],
                "original_query": context["original_query"]
            }
        else:
            return {
                "action": "direct_response",
                "target": "ui_agent",
                "parameters": {"message": "Thank you for your request."},
                "needs_db_access": False,
                "reason": "General query handled with direct response",
                "confidence": 0.7,
                "conversation_id": context["conversation_id"],
                "original_query": context["original_query"]
            }
    
    def _store_decision(self, decision: Dict[str, Any], context: Dict[str, Any]) -> None:
        """Store decision in history."""
        decision_record = {
            "decision": decision,
            "context": context,
            "timestamp": str(uuid.uuid4())
        }
        self.decision_history.append(decision_record)
    
    def _execute_decision(self, decision: Dict[str, Any], original_message: AgentMessage) -> AgentMessage:
        """
        Execute the orchestrator's decision.
        
        Args:
            decision: Decision to execute
            original_message: Original message that triggered this decision
            
        Returns:
            AgentMessage with response
        """
        action = decision.get("action", "direct_response")
        
        if action == "db_query":
            return self._execute_db_query(decision, original_message)
        elif action == "direct_response":
            return self._execute_direct_response(decision, original_message)
        elif action == "multi_step":
            return self._execute_multi_step(decision, original_message)
        else:
            return self._execute_default_response(decision, original_message)
    
    def _execute_db_query(self, decision: Dict[str, Any], original_message: AgentMessage) -> AgentMessage:
        """Execute a database query decision using LangChain tools."""
        # Check if we have the agent executor set up
        if self.agent_executor:
            try:
                # Use LangChain agent to execute the query
                query_description = f"{decision['original_query']} - {decision.get('reason', '')}"
                
                result = self.agent_executor.run(input=query_description)
                
                # Parse and format the result
                response_content = self._format_agent_executor_result(result, decision)
                
            except Exception as e:
                print(f"LangChain agent execution failed: {e}")
                # Fallback to mock response
                response_content = self._generate_mock_db_response(decision)
        else:
            # Fallback to mock response if no agent executor
            response_content = self._generate_mock_db_response(decision)
        
        # Send response back to UI agent
        return self.send_message(
            receiver=original_message.sender,
            message_type="orchestrator_response",
            content=response_content,
            conversation_id=original_message.conversation_id
        )
    
    def _format_agent_executor_result(self, result: str, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Format the result from LangChain agent executor."""
        try:
            # Try to parse as JSON first
            parsed_result = json.loads(result)
            
            # Determine response type based on decision
            collection = decision.get("parameters", {}).get("collection", "Dish")
            
            if collection == "Dish":
                return {
                    "response_type": "menu_info",
                    "success": True,
                    "message": "Menu information retrieved successfully",
                    "dishes": parsed_result if isinstance(parsed_result, list) else [parsed_result],
                    "count": len(parsed_result) if isinstance(parsed_result, list) else 1
                }
            elif collection == "Reservation":
                return {
                    "response_type": "reservation_info",
                    "success": True,
                    "message": "Reservation information retrieved successfully",
                    "available_tables": parsed_result if isinstance(parsed_result, list) else [parsed_result]
                }
            else:
                return {
                    "response_type": "general_db_response",
                    "success": True,
                    "message": "Database query executed successfully",
                    "data": parsed_result
                }
                
        except json.JSONDecodeError:
            # If not JSON, return as general response
            return {
                "response_type": "general_response",
                "success": True,
                "message": result,
                "data": {"raw_response": result}
            }
    
    def _generate_mock_db_response(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock database responses for testing (fallback)."""
        collection = decision.get("parameters", {}).get("collection", "Dish")
        
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
    
    def _generate_mock_menu_response(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock menu response."""
        # Mock dish data based on filters
        filters = decision.get("parameters", {}).get("filter", {})
        
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
    
    def _generate_mock_reservation_response(self, decision: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def _generate_mock_order_response(self, decision: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def _execute_direct_response(self, decision: Dict[str, Any], original_message: AgentMessage) -> AgentMessage:
        """Execute a direct response decision."""
        # Prepare response content from decision parameters
        response_content = decision.get("parameters", {})
        response_content["response_type"] = "direct_response"
        response_content["success"] = True
        
        # Send response back to UI agent
        return self.send_message(
            receiver=original_message.sender,
            message_type="orchestrator_response",
            content=response_content,
            conversation_id=original_message.conversation_id
        )
    
    def _execute_multi_step(self, decision: Dict[str, Any], original_message: AgentMessage) -> AgentMessage:
        """Execute a multi-step decision using LangChain."""
        # For multi-step processes, we would use LangChain's plan-and-execute approach
        # This is a simplified version
        
        response_content = {
            "response_type": "multi_step_response",
            "success": True,
            "message": "Multi-step process initiated",
            "steps": [
                {"step": 1, "action": "Analyzing request", "status": "completed"},
                {"step": 2, "action": "Gathering information", "status": "in_progress"},
                {"step": 3, "action": "Preparing response", "status": "pending"}
            ]
        }
        
        return self.send_message(
            receiver=original_message.sender,
            message_type="orchestrator_response",
            content=response_content,
            conversation_id=original_message.conversation_id
        )
    
    def _execute_default_response(self, decision: Dict[str, Any], original_message: AgentMessage) -> AgentMessage:
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
        Process incoming messages using LangChain.
        
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
    
    def create_langchain_decision_message(self, decision: Dict[str, Any], conversation_id: Optional[str] = None):
        """Create a LangChain-compatible decision message."""
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        return MessageFactory.create_orchestrator_response(
            sender=self.name,
            receiver="ui_agent",
            response_type=decision.get("response_type", "decision"),
            success=True,
            message=decision.get("reason", "Decision made"),
            conversation_id=conversation_id,
            decision=decision
        )
    
    def use_llm_for_decision_optimization(self, current_decision: Dict[str, Any], additional_context: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to optimize a decision with additional context."""
        from langchain_classic.prompts import PromptTemplate
        from langchain_classic.chains import LLMChain
        
        template = """
        Optimize the following decision with additional context:
        
        Current Decision: {decision}
        Additional Context: {context}
        
        Provide an improved decision or confirm the current one.
        Return the decision in the same JSON format.
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["decision", "context"]
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = chain.run({
            "decision": json.dumps(current_decision),
            "context": json.dumps(additional_context)
        })
        
        try:
            return json.loads(result)
        except:
            return current_decision  # Return original if parsing fails