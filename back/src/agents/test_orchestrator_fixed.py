"""
Test script for the Orchestrator Agent (fixed imports)
"""

import sys
import os

# Add the parent directory to Python path so we can import agents module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.orchestrator_agent import OrchestratorAgent
from agents.base_agent import BaseAgent


class MockUIAgent(BaseAgent):
    """Mock UI Agent for testing"""
    
    def __init__(self):
        super().__init__("UIAgent", "Mock UI Agent for testing")
        
    def execute(self, task, context=None):
        print(f"UI Agent received response for task: {task}")
        return {"ui_response": f"Processed: {task}"}
        
    def can_handle(self, task):
        # UI agent handles display/response tasks
        return "display" in task.lower() or "response" in task.lower()


class MockRestaurantAgent(BaseAgent):
    """Mock Restaurant Agent for testing"""
    
    def __init__(self):
        super().__init__("RestaurantAgent", "Handles restaurant-specific tasks")
        
    def execute(self, task, context=None):
        if "menu" in task.lower():
            return {"menu_items": ["Pasta", "Pizza", "Salad"]}
        elif "reservation" in task.lower():
            return {"reservation_status": "confirmed"}
        else:
            return {"restaurant_info": "Open from 12PM to 10PM"}
        
    def can_handle(self, task):
        # Restaurant agent handles menu, reservation, and info tasks
        keywords = ["menu", "reservation", "restaurant", "food", "dish"]
        return any(keyword in task.lower() for keyword in keywords)


def test_orchestrator():
    """Test the orchestrator agent"""
    
    print("=== Testing Orchestrator Agent ===\n")
    
    # Create orchestrator
    orchestrator = OrchestratorAgent()
    
    # Create and register agents
    ui_agent = MockUIAgent()
    restaurant_agent = MockRestaurantAgent()
    
    orchestrator.register_agent(ui_agent)
    orchestrator.register_agent(restaurant_agent)
    
    # Test agent status
    print("Agent Status:")
    status = orchestrator.get_agent_status()
    print(f"Registered agents: {status['orchestrator']['registered_agents']}")
    print()
    
    # Test tasks
    test_tasks = [
        "Get the restaurant menu",
        "Make a reservation for 4 people",
        "Display the response to the user",
        "What are your opening hours?",
        "Process payment for table 5"
    ]
    
    for i, task in enumerate(test_tasks, 1):
        print(f"Task {i}: {task}")
        result = orchestrator.execute(task, {"user_id": "test_user"})
        
        if result["success"]:
            print(f"  [OK] Success: {result['response']}")
        else:
            print(f"  [ERROR] Failed: {result['error']}")
        print()
    
    # Show task history
    print("Recent Task History:")
    history = orchestrator.get_task_history(3)
    for task in history:
        print(f"  - {task['task']} ({task['status']}) at {task['timestamp']}")
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    test_orchestrator()