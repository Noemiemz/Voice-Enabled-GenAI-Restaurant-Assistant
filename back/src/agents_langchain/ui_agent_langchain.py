"""
LangChain-enhanced UI Agent for handling user interactions.
This agent uses LangChain for advanced query processing and response generation.
"""

from typing import Dict, Any, Optional, List
from .base_agent_langchain import LangChainBaseAgent, AgentMessage
from .communication_schemas import UserQueryMessage, MessageFactory
from pydantic import BaseModel, Field
from langchain_classic.llms.base import LLM
from langchain_classic.memory import ConversationBufferMemory
from langchain.tools import BaseTool
import uuid
import json


class LangChainUIAgent(LangChainBaseAgent):
    """LangChain-enhanced UI Agent for handling user interactions."""
    
    def __init__(self, llm: LLM, memory: Optional[ConversationBufferMemory] = None):
        """
        Initialize the LangChain UI Agent.
        
        Args:
            llm: Language model to use
            memory: Optional conversation memory
        """
        super().__init__(
            name="ui_agent",
            llm=llm,
            description="Handles user interactions and query refinement with LangChain",
            memory=memory
        )
        self.query_history = []
        
        # Set up query analysis chain
        self.query_analysis_chain = self._create_query_analysis_chain()
        
        # Set up response formatting chain
        self.response_formatting_chain = self._create_response_formatting_chain()
    
    def _create_query_analysis_chain(self) -> Any:
        """Create a chain for analyzing user queries."""
        from langchain_classic.prompts import PromptTemplate
        from langchain_classic.chains import LLMChain
        
        template = """
        Analyze the following restaurant query and extract key information:
        
        Query: {query}
        
        Provide a JSON response with the following structure:
        {{
            "query_type": "menu|reservation|order|general",  # Type of query
            "needs_clarification": true|false,  # Whether clarification is needed
            "clarification_questions": [],  # Questions to ask for clarification
            "refined_query": "",  # Refined version of the query
            "key_details": {{}}  # Extracted details (dietary preferences, time, etc.)
        }}
        
        Consider:
        - Dietary preferences (vegetarian, vegan, gluten-free, allergies)
        - Party size for reservations
        - Time/date preferences
        - Specific dish or menu requests
        - Order status or placement requests
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["query"]
        )
        
        return LLMChain(
            llm=self.llm,
            prompt=prompt,
            output_key="analysis"
        )
    
    def _create_response_formatting_chain(self) -> Any:
        """Create a chain for formatting responses to users."""
        from langchain_classic.prompts import PromptTemplate
        from langchain_classic.chains import LLMChain
        
        template = """
        Format the following restaurant information into a friendly, helpful response for a customer:
        
        Response Type: {response_type}
        Data: {data}
        
        Guidelines:
        - Be warm and welcoming
        - Provide clear, concise information
        - Use bullet points for lists
        - Include prices where relevant
        - Offer additional help if appropriate
        - Keep responses under 3 sentences for simple answers
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["response_type", "data"]
        )
        
        return LLMChain(
            llm=self.llm,
            prompt=prompt,
            output_key="formatted_response"
        )
    
    def process_user_query(self, user_query: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user query using LangChain for advanced analysis.
        
        Args:
            user_query: The original user query
            conversation_id: Optional conversation identifier
            
        Returns:
            Dictionary with processing results
        """
        # Create conversation ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Use LangChain to analyze the query
        analysis_result = self.query_analysis_chain.run(query=user_query)
        
        try:
            # Parse the JSON analysis
            analysis = json.loads(analysis_result)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            analysis = {
                "query_type": "general",
                "needs_clarification": True,
                "clarification_questions": ["Could you please provide more details about your request?"],
                "refined_query": user_query,
                "key_details": {}
            }
        
        # Create query object
        query_data = {
            "original_query": user_query,
            "refined_query": analysis.get("refined_query", user_query),
            "query_type": analysis.get("query_type", "general"),
            "needs_clarification": analysis.get("needs_clarification", False),
            "clarification_questions": analysis.get("clarification_questions", []),
            "key_details": analysis.get("key_details", {}),
            "context": {"conversation_id": conversation_id},
            "llm_analysis": analysis
        }
        
        # Store query in history
        self.query_history.append(query_data)
        
        return query_data
    
    def send_query_to_orchestrator(self, query_data: Dict[str, Any], orchestrator_name: str = "orchestrator") -> AgentMessage:
        """
        Send the processed query to the orchestrator agent.
        
        Args:
            query_data: Processed query data
            orchestrator_name: Name of the orchestrator agent
            
        Returns:
            AgentMessage sent to orchestrator
        """
        # Prepare message content
        message_content = {
            "query": query_data["refined_query"],
            "query_type": query_data["query_type"],
            "needs_clarification": query_data["needs_clarification"],
            "clarification_questions": query_data["clarification_questions"],
            "key_details": query_data["key_details"],
            "context": query_data["context"],
            "llm_analysis": query_data.get("llm_analysis", {})
        }
        
        # Send message to orchestrator
        message = self.send_message(
            receiver=orchestrator_name,
            message_type="user_query",
            content=message_content,
            conversation_id=query_data["context"]["conversation_id"]
        )
        
        return message
    
    def _process_message(self, message: AgentMessage) -> Dict[str, Any]:
        """
        Process incoming messages using LangChain for response formatting.
        
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
        """Format orchestrator response for the user using LangChain."""
        response_type = orchestrator_response.get("response_type", "general")
        
        # Use LangChain to format the response
        try:
            formatted_response = self.response_formatting_chain.run({
                "response_type": response_type,
                "data": json.dumps(orchestrator_response.get("data", {}))
            })
            return formatted_response
            
        except Exception as e:
            print(f"LangChain response formatting failed: {e}")
            # Fallback to manual formatting
            return self._manual_format_response(orchestrator_response)
    
    def _manual_format_response(self, response: Dict[str, Any]) -> str:
        """Fallback manual response formatting."""
        response_type = response.get("response_type", "general")
        
        if response_type == "menu_info":
            return self._format_menu_response(response)
        elif response_type == "reservation_info":
            return self._format_reservation_response(response)
        elif response_type == "order_info":
            return self._format_order_response(response)
        else:
            return response.get("message", "Thank you for your request.")
    
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
    
    def create_langchain_user_query_message(self, user_query: str, conversation_id: Optional[str] = None) -> UserQueryMessage:
        """Create a LangChain-compatible user query message."""
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        return MessageFactory.create_user_query(
            sender=self.name,
            receiver="orchestrator",
            query=user_query,
            query_type="user_query",  # Will be determined by analysis
            conversation_id=conversation_id
        )
    
    def use_llm_for_clarification(self, ambiguous_query: str) -> Dict[str, Any]:
        """Use LLM to generate clarification questions for ambiguous queries."""
        from langchain_classic.prompts import PromptTemplate
        from langchain_classic.chains import LLMChain
        
        template = """
        The following restaurant query is ambiguous or incomplete:
        
        Query: {query}
        
        Generate 1-3 clarification questions that would help provide a better response.
        Return as a JSON list of questions.
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["query"]
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = chain.run(query=ambiguous_query)
        
        try:
            questions = json.loads(result)
            if not isinstance(questions, list):
                questions = [questions]
            return {"clarification_questions": questions}
        except:
            return {"clarification_questions": ["Could you please provide more details about your request?"]}
    
    def enhance_query_with_context(self, query: str, context: Dict[str, Any]) -> str:
        """Use LLM to enhance query with additional context."""
        from langchain_classic.prompts import PromptTemplate
        from langchain_classic.chains import LLMChain
        
        template = """
        Enhance the following restaurant query with the given context:
        
        Query: {query}
        Context: {context}
        
        Provide an improved query that incorporates relevant context.
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["query", "context"]
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.run({
            "query": query,
            "context": json.dumps(context)
        })