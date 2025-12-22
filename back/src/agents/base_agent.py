"""
Base Agent Class
This module provides the foundation for all agents in the system.
"""

class BaseAgent:
    """
    Base class for all agents in the system.
    
    Attributes:
        name (str): The name of the agent
        description (str): Description of the agent's purpose
        tools (list): List of tools available to the agent
    """
    
    def __init__(self, name, description=""):
        self.name = name
        self.description = description
        self.tools = []
        
    def add_tool(self, tool):
        """Add a tool to the agent's toolkit"""
        self.tools.append(tool)
        
    def execute(self, task, context=None):
        """
        Execute a task with optional context
        
        Args:
            task (str): The task to execute
            context (dict): Additional context for the task
            
        Returns:
            dict: Result of the execution
        """
        raise NotImplementedError("Subclasses must implement the execute method")
        
    def can_handle(self, task):
        """
        Determine if this agent can handle the given task
        
        Args:
            task (str): The task to check
            
        Returns:
            bool: True if the agent can handle the task
        """
        return False