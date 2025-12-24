"""
Orchestrator Agent - Main coordinator for the restaurant assistant system
Uses smolagents framework for agent coordination
"""
from typing import Dict, List, Any, Optional
from smolagents import ToolCallingAgent, Model
from models.llm import MistralModel
import json

class OrchestratorAgent(ToolCallingAgent):
    """
    Main orchestrator agent that coordinates between different specialized agents.
    Handles routing of user requests to appropriate agents and manages the conversation flow.
    """
    
    def __init__(self, model: Optional[Model] = None):
        """Initialize the orchestrator agent"""
        # Use MistralModel as the base model
        self.model = model if model else MistralModel()
        self.agents: Dict[str, 'ToolCallingAgent'] = {}  # Registry of available agents
        self.conversation_history: List[Dict[str, str]] = []
        
    def register_agent(self, agent: 'ToolCallingAgent', name: Optional[str] = None) -> None:
        """
        Register an agent with the orchestrator
        
        Args:
            agent: The agent to register
            name: Optional name for the agent (uses class name if not provided)
        """
        agent_name = name if name else agent.__class__.__name__
        self.agents[agent_name] = agent
        print(f"[ORCHESTRATOR] Registered agent: {agent_name}")
        
    def unregister_agent(self, name: str) -> None:
        """
        Unregister an agent from the orchestrator
        
        Args:
            name: Name of the agent to unregister
        """
        if name in self.agents:
            del self.agents[name]
            print(f"[ORCHESTRATOR] Unregistered agent: {name}")
        
    def route_request(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route user requests to the appropriate agent based on intent detection
        
        Args:
            user_input: User's input text
            context: Additional context about the request
            
        Returns:
            Dictionary containing routing decision and agent to use
        """
        # Simple intent detection based on keywords
        user_input_lower = user_input.lower()
        
        # Check for reservation-related requests
        if any(keyword in user_input_lower for keyword in 
               ['réservation', 'réserver', 'table', 'réserve', 'réservations']):
            return {
                'agent': 'makeReservationAgent',
                'intent': 'reservation',
                'confidence': 0.9
            }
        
        # Check for menu-related requests
        elif any(keyword in user_input_lower for keyword in 
                ['menu', 'plat', 'plats', 'manger', 'nourriture', 'repas', 
                 'entrée', 'dessert', 'boisson', 'spécialité', 'tarte', 'crème', 
                 'mousse', 'salade', 'soupe', 'boeuf', 'poulet', 'saumon']):
            return {
                'agent': 'RestaurantInfoAgent',
                'intent': 'menu_info',
                'confidence': 0.85
            }
        
        # Check for order-related requests
        elif any(keyword in user_input_lower for keyword in 
                ['commande', 'commander', 'livraison', 'emporter', 'à emporter',
                 'livrer', 'plat à emporter']):
            return {
                'agent': 'OrderAgent',
                'intent': 'order',
                'confidence': 0.8
            }
        
        # Check for general information requests
        elif any(keyword in user_input_lower for keyword in 
                ['horaire', 'heure', 'ouvert', 'fermé', 'adresse', 'téléphone',
                 'localisation', 'où', 'quand', 'contact']):
            return {
                'agent': 'RestaurantInfoAgent',
                'intent': 'general_info',
                'confidence': 0.75
            }
        
        # Default to UI agent for general conversation
        else:
            return {
                'agent': 'UIAgent',
                'intent': 'general_conversation',
                'confidence': 0.6
            }
    
    def execute(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main execution method that processes user input and routes to appropriate agents
        
        Args:
            user_input: User's input text
            context: Additional context about the request
            
        Returns:
            Dictionary containing the result of the execution
        """
        if context is None:
            context = {}
            
        # Add to conversation history
        self.conversation_history.append({
            'role': 'user',
            'content': user_input,
            'context': context
        })
        
        try:
            # Route the request to determine which agent should handle it
            routing_decision = self.route_request(user_input, context)
            agent_name = routing_decision['agent']
            intent = routing_decision['intent']
            
            print(f"[ORCHESTRATOR] Routing '{intent}' request to {agent_name}")
            
            # Check if the agent exists
            if agent_name not in self.agents:
                print(f"[ORCHESTRATOR] Agent {agent_name} not found, falling back to LLM")
                # Fallback to direct LLM processing
                return self.fallback_to_llm(user_input, context)
            
            # Get the agent and execute the request
            agent = self.agents[agent_name]
            
            # Prepare agent-specific context
            agent_context = {
                **context,
                'intent': intent,
                'orchestrator': self,
                'user_input': user_input
            }
            
            # Execute the agent
            result = agent.execute(user_input, agent_context)
            
            # Prevent infinite loops - if UI agent is routing back to itself, use fallback
            if agent_name == 'UIAgent' and result.get('agent') == 'UIAgent':
                print(f"[ORCHESTRATOR] Preventing infinite loop, using fallback")
                return self.fallback_to_llm(user_input, context)
            
            # Add agent response to conversation history
            self.conversation_history.append({
                'role': 'assistant',
                'content': result.get('message', ''),
                'agent': agent_name,
                'intent': intent
            })
            
            return {
                'success': True,
                'message': result.get('message', ''),
                'type': result.get('type', 'text'),
                'data': result.get('data'),
                'agent': agent_name,
                'intent': intent
            }
            
        except Exception as e:
            print(f"[ORCHESTRATOR] Error processing request: {e}")
            return {
                'success': False,
                'message': f"Désolé, une erreur est survenue lors du traitement de votre demande: {str(e)}",
                'error': str(e)
            }
    
    def fallback_to_llm(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback method when no specific agent is available or appropriate
        Uses the base LLM model directly
        """
        try:
            # Use the model directly for general conversation
            messages = [
                {"role": "system", "content": "You are a helpful restaurant assistant."},
                {"role": "user", "content": user_input}
            ]
            
            # Generate response using the model
            response = self.model.generate(messages)
            
            return {
                'success': True,
                'message': response.content,
                'type': 'text',
                'data': None,
                'agent': 'LLM_Fallback',
                'intent': 'general_conversation'
            }
            
        except Exception as e:
            print(f"[ORCHESTRATOR] LLM fallback error: {e}")
            return {
                'success': False,
                'message': "Désolé, je n'ai pas pu traiter votre demande. Veuillez réessayer.",
                'error': str(e)
            }
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Get the current conversation history
        """
        return self.conversation_history
        
    def clear_conversation_history(self) -> None:
        """
        Clear the conversation history
        """
        self.conversation_history = []
        print("[ORCHESTRATOR] Conversation history cleared")
    
    def get_available_agents(self) -> List[str]:
        """
        Get list of available agents
        """
        return list(self.agents.keys())