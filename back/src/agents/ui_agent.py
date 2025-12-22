"""
UI Agent
This agent handles communication with the user interface.
"""

from .base_agent import BaseAgent
from typing import Dict, Any, Optional, List


class UIAgent(BaseAgent):
    """
    UI Agent that handles communication with the user interface.
    
    This agent:
    - Receives user input
    - Sends requests to the orchestrator
    - Formats responses for display
    - Handles UI-specific logic
    """
    
    def __init__(self, name="UIAgent", description="Handles user interface communication"):
        super().__init__(name, description)
        self.orchestrator = None
        self.conversation_history = []
        
    def connect_to_orchestrator(self, orchestrator):
        """
        Connect this UI agent to an orchestrator
        
        Args:
            orchestrator: The orchestrator agent to connect to
        """
        self.orchestrator = orchestrator
        print(f"UI Agent connected to orchestrator: {orchestrator.name}")
        
    def execute(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a task by sending it to the orchestrator
        
        Args:
            task (str): The task to execute
            context (dict): Additional context for the task
            
        Returns:
            dict: Result from the orchestrator
        """
        if context is None:
            context = {}
            
        # Add UI-specific context
        context["source"] = "ui"
        context["interface"] = "voice"  # Could be "voice", "text", "chat", etc.
        
        if not self.orchestrator:
            return {
                "success": False,
                "error": "UI Agent not connected to orchestrator",
                "agent": self.name
            }
        
        try:
            # Send task to orchestrator
            result = self.orchestrator.execute(task, context)
            
            # Format the response for UI display
            formatted_result = self._format_for_ui(result)
            
            # Store in conversation history
            self._add_to_conversation_history(task, formatted_result)
            
            return formatted_result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"UI Agent error: {str(e)}",
                "agent": self.name
            }
    
    def _format_for_ui(self, result: Dict) -> Dict:
        """
        Format the orchestrator result for UI display
        
        Args:
            result (dict): Result from orchestrator
            
        Returns:
            dict: Formatted result for UI
        """
        if not result["success"]:
            return {
                "success": False,
                "message": f"Error: {result.get('error', 'Unknown error')}",
                "type": "error"
            }
        
        # Extract and format the response
        response = result["response"]
        
        # Simple formatting based on response type
        if isinstance(response, dict):
            if "menu_items" in response:
                formatted_message = "Menu items:\n" + "\n".join(f"- {item}" for item in response["menu_items"])
                return {
                    "success": True,
                    "message": formatted_message,
                    "type": "menu",
                    "data": response
                }
            elif "reservation_status" in response:
                return {
                    "success": True,
                    "message": f"Reservation {response['reservation_status']}",
                    "type": "reservation",
                    "data": response
                }
        
        # Default formatting
        return {
            "success": True,
            "message": str(response),
            "type": "text",
            "data": response
        }
    
    def _add_to_conversation_history(self, task: str, result: Dict):
        """
        Add a task and result to conversation history
        
        Args:
            task (str): The task that was executed
            result (dict): The result from execution
        """
        history_entry = {
            "task": task,
            "response": result,
            "timestamp": self._get_current_timestamp(),
            "success": result.get("success", False)
        }
        
        self.conversation_history.append(history_entry)
        
        # Keep history size manageable
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """
        Get recent conversation history
        
        Args:
            limit (int): Maximum number of entries to return
            
        Returns:
            list: List of conversation entries
        """
        return self.conversation_history[-limit:]
    
    def _get_current_timestamp(self) -> str:
        """
        Get current timestamp as ISO format string
        
        Returns:
            str: Current timestamp
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def can_handle(self, task: str) -> bool:
        """
        Determine if this UI agent can handle the given task
        
        Args:
            task (str): The task to check
            
        Returns:
            bool: True if the task is UI-related
        """
        # UI agent handles tasks related to user interaction
        ui_keywords = [
            "display", "show", "render", "format", "ui", "interface",
            "response", "output", "present", "notify", "alert"
        ]
        
        return any(keyword in task.lower() for keyword in ui_keywords)