"""
Agent Manager for the Restaurant Assistant System

This module provides a centralized way to manage agent lifecycle and dependencies,
replacing the global variable approach with a more structured dependency injection pattern.
"""

from agents.menu_agent import create_menu_agent
from agents.faq_agent import create_faq_agent
from agents.reservation_agent import create_reservation_agent


class AgentManager:
    """Manages the lifecycle and access to all agents in the system."""
    
    def __init__(self):
        """Initialize the agent manager."""
        self._agents = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize all agents.
        
        This method should be called once during application startup.
        """
        if self._initialized:
            return
            
        try:
            # Initialize agents
            self._agents['menu'] = create_menu_agent()
            self._agents['faq'] = create_faq_agent()
            self._agents['reservation'] = create_reservation_agent()
            
            self._initialized = True
            print("[AGENT_MANAGER] All agents initialized successfully")
            
        except Exception as e:
            print(f"[AGENT_MANAGER] Error initializing agents: {e}")
            raise
    
    def get_agent(self, agent_name):
        """Get an agent by name.
        
        Args:
            agent_name (str): Name of the agent ('menu', 'faq', 'reservation')
            
        Returns:
            Agent instance or None if not found
            
        Raises:
            RuntimeError: If agents are not initialized
        """
        if not self._initialized:
            raise RuntimeError("AgentManager not initialized. Call initialize() first.")
            
        return self._agents.get(agent_name)
    
    def cleanup(self):
        """Clean up resources and shutdown agents.
        
        This should be called during application shutdown.
        """
        if not self._initialized:
            return
            
        # Add any cleanup logic here if needed
        # For now, just clear the agents dictionary
        self._agents.clear()
        self._initialized = False
        print("[AGENT_MANAGER] Agents cleaned up")
    
    @property
    def is_initialized(self):
        """Check if the agent manager is initialized."""
        return self._initialized
    
    def get_all_agents(self):
        """Get all agents as a dictionary."""
        if not self._initialized:
            raise RuntimeError("AgentManager not initialized. Call initialize() first.")
            
        return self._agents.copy()