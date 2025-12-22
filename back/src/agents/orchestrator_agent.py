"""
Orchestrator Agent
This agent receives input from the UI agent and coordinates with other agents.
"""

from .base_agent import BaseAgent
from typing import Dict, List, Any, Optional
import json


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent that coordinates between UI and other agents.
    
    This agent:
    - Receives requests from the UI agent
    - Routes tasks to appropriate specialized agents
    - Aggregates responses
    - Returns final answers to the UI agent
    """
    
    def __init__(self, name="OrchestratorAgent", description="Coordinates tasks between UI and specialized agents"):
        super().__init__(name, description)
        self.agents = {}  # Dictionary to store registered agents
        self.task_history = []  # History of processed tasks
        
    def register_agent(self, agent: BaseAgent):
        """
        Register an agent with the orchestrator
        
        Args:
            agent (BaseAgent): The agent to register
        """
        self.agents[agent.name] = agent
        print(f"Registered agent: {agent.name}")
        
    def execute(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a task by routing it to the appropriate agent
        
        Args:
            task (str): The task to execute
            context (dict): Additional context for the task
            
        Returns:
            dict: Result containing response and metadata
        """
        if context is None:
            context = {}
            
        # Log the task
        task_record = {
            "task": task,
            "context": context,
            "timestamp": self._get_current_timestamp()
        }
        
        try:
            # Route the task to the appropriate agent
            result = self._route_task(task, context)
            
            # Update task record with result
            task_record["result"] = result
            task_record["status"] = "success"
            
            # Store in history
            self.task_history.append(task_record)
            
            return {
                "success": True,
                "response": result,
                "agent": self.name,
                "task_id": len(self.task_history) - 1
            }
            
        except Exception as e:
            task_record["error"] = str(e)
            task_record["status"] = "failed"
            self.task_history.append(task_record)
            
            return {
                "success": False,
                "error": str(e),
                "agent": self.name,
                "task_id": len(self.task_history) - 1
            }
    
    def _route_task(self, task: str, context: Dict) -> Any:
        """
        Route a task to the appropriate agent
        
        Args:
            task (str): The task to route
            context (dict): Context for the task
            
        Returns:
            Any: Result from the agent that handled the task
            
        Raises:
            Exception: If no agent can handle the task
        """
        # Check if any registered agent can handle this task
        for agent_name, agent in self.agents.items():
            if agent.can_handle(task):
                print(f"Routing task to {agent_name}: {task}")
                return agent.execute(task, context)
        
        # If no specific agent can handle it, try to process it generally
        if self._can_handle_generally(task):
            return self._handle_general_task(task, context)
        
        raise Exception(f"No agent available to handle task: {task}")
    
    def _can_handle_generally(self, task: str) -> bool:
        """
        Check if the orchestrator can handle the task generally
        
        Args:
            task (str): The task to check
            
        Returns:
            bool: True if the orchestrator can handle it
        """
        # Add general task handling logic here
        # For now, orchestrator can handle any task as a fallback
        return True
    
    def _handle_general_task(self, task: str, context: Dict) -> Dict[str, Any]:
        """
        Handle a general task that no specific agent can handle
        
        Args:
            task (str): The task to handle
            context (dict): Context for the task
            
        Returns:
            dict: Result of handling the task
        """
        # This is a fallback handler
        # In a real implementation, this might use an LLM or other logic
        return {
            "message": f"Task processed by orchestrator: {task}",
            "details": {
                "task": task,
                "context": context,
                "handled_by": "orchestrator_fallback"
            }
        }
    
    def get_task_history(self, limit: int = 10) -> List[Dict]:
        """
        Get recent task history
        
        Args:
            limit (int): Maximum number of tasks to return
            
        Returns:
            list: List of recent tasks
        """
        return self.task_history[-limit:]
        
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status information about registered agents
        
        Returns:
            dict: Status information
        """
        return {
            "orchestrator": {
                "name": self.name,
                "description": self.description,
                "registered_agents": list(self.agents.keys()),
                "total_tasks_processed": len(self.task_history)
            },
            "agents": {
                agent_name: {
                    "description": agent.description,
                    "tools": len(agent.tools)
                }
                for agent_name, agent in self.agents.items()
            }
        }
    
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
        Determine if this orchestrator can handle the given task
        
        Args:
            task (str): The task to check
            
        Returns:
            bool: True (orchestrator can always try to handle tasks)
        """
        return True