"""
Restaurant Agent System
This agent can interact with users, use tools to query the database,
and generate responses using the LLM
"""

from models.llm import MistralWrapper
from .tools.mongodb_tools import MongoDBTools
from .tools.mock_mongodb_tools import MockMongoDBTool
from .prompt_manager import PromptManager
from typing import Optional, Dict, Any, List
import json
import os
import os

class RestaurantAgent:
    def __init__(self, llm: Optional[MistralWrapper] = None, use_mock_db: bool = True):
        """
        Initialize the restaurant agent
        
        Args:
            llm: Optional MistralWrapper instance. If None, will create one.
            use_mock_db: Whether to use mock database for testing
        """
        self.llm = llm or MistralWrapper()
        self.use_mock_db = use_mock_db
        self.prompt_manager = PromptManager()
        
        # Initialize tools
        if use_mock_db:
            self.tools = MockMongoDBTool()
        else:
            self.tools = MongoDBTools()
        
        # Conversation history
        self.conversation_history = []
        
        # Available tools mapping
        self.available_tools = {
            "get_menu": self.tools.get_menu,
            "search_dishes": self.tools.search_dishes,
            "get_reservations": self.tools.get_reservations,
            "get_restaurant_info": self.tools.get_restaurant_info,
            "get_dishes_by_category": self.tools.get_dishes_by_category,
            "get_available_dishes": self.tools.get_available_dishes
        }



    def process_user_input(self, user_input: str) -> str:
        """
        Main processing method for user input
        
        Args:
            user_input: The user's input text
            
        Returns:
            The agent's response
        """
        print(f"[AGENT] Processing user input: {user_input}")
        
        try:
            # Step 1: Determine user intent
            intent, tool_name, tool_params = self._determine_intent_and_tool(user_input)
            print(f"[AGENT] Detected intent: {intent}, tool: {tool_name}")
            
            # Step 2: Use appropriate tool if needed
            tool_result = None
            if tool_name and tool_name in self.available_tools:
                tool_result = self._use_tool(tool_name, tool_params)
                print(f"[AGENT] Tool result: {tool_result}")
            
            # Step 3: Generate final response
            response = self._generate_response(user_input, intent, tool_name, tool_result)
            
            # Update conversation history
            self._update_conversation_history(user_input, response)
            
            return response
            
        except Exception as e:
            print(f"[ERROR] Agent processing failed: {e}")
            return "Désolé, une erreur est survenue. Veuillez réessayer."

    def _determine_intent_and_tool(self, user_input: str) -> tuple:
        """
        Determine user intent and select appropriate tool using LLM
        
        Returns:
            tuple: (intent, tool_name, tool_params)
        """
        # Get formatted prompt from prompt manager
        classification_prompt = self.prompt_manager.get_formatted_prompt(
            "intent_classification",
            user_input=user_input
        )

        try:
            # Use LLM to classify the intent
            llm_response = self.llm.generate_from_prompt(classification_prompt, [])
            
            # Parse the JSON response
            # Clean the response in case it contains markdown code blocks
            llm_response_clean = llm_response.strip()
            if llm_response_clean.startswith("```json"):
                llm_response_clean = llm_response_clean[7:]
            if llm_response_clean.startswith("```"):
                llm_response_clean = llm_response_clean[3:]
            if llm_response_clean.endswith("```"):
                llm_response_clean = llm_response_clean[:-3]
            llm_response_clean = llm_response_clean.strip()
            
            result = json.loads(llm_response_clean)
            
            intent = result.get("intent", "general_question")
            tool_name = result.get("tool_name")
            tool_params = result.get("tool_params", {})
            
            print(f"[AGENT] LLM-based classification: intent={intent}, tool={tool_name}, params={tool_params}")
            
            return intent, tool_name, tool_params
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse LLM response as JSON: {e}")
            print(f"[ERROR] Raw response: {llm_response}")
            # Fallback to general question if parsing fails
            return "general_question", None, {}
        except Exception as e:
            print(f"[ERROR] LLM-based intent detection failed: {e}")
            # Fallback to general question
            return "general_question", None, {}

    def _use_tool(self, tool_name: str, params: dict) -> Any:
        """
        Use a specific tool with given parameters
        
        Args:
            tool_name: Name of the tool to use
            params: Parameters for the tool
            
        Returns:
            Result from the tool
        """
        if tool_name not in self.available_tools:
            return None
            
        try:
            tool_function = self.available_tools[tool_name]
            
            # Handle different parameter requirements
            if tool_name == "search_dishes":
                return tool_function(params.get("query", ""))
            elif tool_name == "get_dishes_by_category":
                return tool_function(params.get("category_name", ""))
            else:
                return tool_function()
                
        except Exception as e:
            print(f"[ERROR] Tool {tool_name} failed: {e}")
            return None

    def _generate_response(self, user_input: str, intent: str, tool_name: str, tool_result: Any) -> str:
        """
        Generate a response using the LLM based on intent and tool results
        
        Args:
            user_input: Original user input
            intent: Detected intent
            tool_name: Tool that was used
            tool_result: Result from the tool
            
        Returns:
            Generated response
        """
        context = {
            "user_input": user_input,
            "intent": intent,
            "tool_used": tool_name,
            "tool_result": tool_result
        }
        
        # Convert tool result to string if it's complex
        tool_result_str = ""
        if tool_result:
            if isinstance(tool_result, dict):
                tool_result_str = json.dumps(tool_result, ensure_ascii=False, indent=2)
            elif isinstance(tool_result, list):
                tool_result_str = json.dumps(f'{{"results": {tool_result} }}', ensure_ascii=False, indent=2)
            else:
                tool_result_str = str(tool_result)
        
        # Get formatted prompt from manager
        prompt = self.prompt_manager.get_formatted_prompt(
            "system_prompt",
            intent=intent,
            tool_name=tool_name,
            tool_result=tool_result_str,
            user_input=user_input
        )
        
        # Use LLM to generate response
        response = self.llm.generate_from_prompt(prompt, self.conversation_history)
        
        return response

    def _update_conversation_history(self, user_input: str, agent_response: str):
        """
        Update conversation history with the latest exchange
        
        Args:
            user_input: User's input
            agent_response: Agent's response
        """
        # Limit history to last 5 exchanges to prevent memory issues
        if len(self.conversation_history) >= 10:
            self.conversation_history = self.conversation_history[-8:]  # Keep last 4 pairs
        
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": agent_response})

    def close(self):
        """Clean up resources"""
        if hasattr(self.tools, 'close'):
            self.tools.close()

    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = []