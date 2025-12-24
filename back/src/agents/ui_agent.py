"""
UI Agent - Handles direct user interaction and interface management
"""
from typing import Dict, Any, Optional
from smolagents import ToolCallingAgent

class UIAgent(ToolCallingAgent):
    """
    User Interface Agent that handles direct interaction with users.
    Manages conversation flow, clarifies requests, and formats responses.
    """
    
    def __init__(self):
        """Initialize the UI agent"""
        self.orchestrator = None
        self.conversation_context: Dict[str, Any] = {}
        
    def connect_to_orchestrator(self, orchestrator) -> None:
        """
        Connect this UI agent to an orchestrator
        
        Args:
            orchestrator: The orchestrator agent to connect to
        """
        self.orchestrator = orchestrator
        print("[UI_AGENT] Connected to orchestrator")
        
    def execute(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute user input through the agent system
        
        Args:
            user_input: User's input text
            context: Additional context about the request
            
        Returns:
            Dictionary containing the result of the execution
        """
        if context is None:
            context = {}
            
        # Update conversation context
        self.conversation_context.update(context)
        
        try:
            # If connected to orchestrator, use it to process the request
            if self.orchestrator:
                result = self.orchestrator.execute(user_input, context)
                
                # Format the response for UI
                formatted_result = self.format_response(result)
                
                return formatted_result
            else:
                return {
                    'success': False,
                    'message': "UI agent not connected to orchestrator",
                    'error': 'No orchestrator connection'
                }
                
        except Exception as e:
            print(f"[UI_AGENT] Error processing request: {e}")
            return {
                'success': False,
                'message': f"Désolé, une erreur est survenue: {str(e)}",
                'error': str(e)
            }
    
    def format_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the response for UI display
        
        Args:
            result: Raw result from agent execution
            
        Returns:
            Formatted result for UI
        """
        formatted = result.copy()
        
        # Add UI-specific formatting
        if result.get('success', False):
            formatted['message'] = self._format_message(result.get('message', ''))
        else:
            formatted['message'] = f"❌ {result.get('message', 'Erreur inconnue')}"
            
        return formatted
        
    def _format_message(self, message: str) -> str:
        """
        Format a message for better UI display
        """
        if not message:
            return ""
            
        # Basic formatting - could be enhanced with markdown, etc.
        formatted = message.strip()
        
        # Add some basic formatting for better readability
        if not formatted.endswith(('.', '!', '?')):
            formatted += '.'
            
        return formatted
        
    def clarify_request(self, user_input: str) -> Optional[str]:
        """
        Clarify ambiguous user requests
        
        Args:
            user_input: User's input text
            
        Returns:
            Clarified input or None if no clarification needed
        """
        # This could be enhanced with more sophisticated clarification logic
        input_lower = user_input.lower()
        
        # Example: if user asks for "table" without specifying reservation
        if 'table' in input_lower and 'réservation' not in input_lower and 'réserver' not in input_lower:
            return user_input + " (pour une réservation)"
            
        return None
        
    def get_conversation_context(self) -> Dict[str, Any]:
        """
        Get the current conversation context
        """
        return self.conversation_context
        
    def update_conversation_context(self, context: Dict[str, Any]) -> None:
        """
        Update the conversation context
        """
        self.conversation_context.update(context)