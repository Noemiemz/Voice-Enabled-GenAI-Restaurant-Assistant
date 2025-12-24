"""
Test the agent system components directly
"""

import sys
import os
import unittest

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

try:
    from agents.orchestrator_agent import OrchestratorAgent
    from agents.ui_agent import UIAgent
    from agents.base_agent import BaseAgent
    from agents.integration_example import RestaurantInfoAgent, create_agent_system
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False


class MockAgent(BaseAgent):
    """Mock agent for testing"""
    
    def __init__(self, name, response_text, can_handle_keyword):
        super().__init__(name, f"Mock {name}")
        self.response_text = response_text
        self.can_handle_keyword = can_handle_keyword
        
    def execute(self, task, context=None):
        return {
            "message": self.response_text,
            "task": task,
            "context": context or {}
        }
        
    def can_handle(self, task):
        return self.can_handle_keyword in task.lower()


@unittest.skipUnless(AGENTS_AVAILABLE, "Agent system not available")
class TestAgentSystem(unittest.TestCase):
    """Test agent system components"""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        orchestrator = OrchestratorAgent()
        self.assertEqual(orchestrator.name, "OrchestratorAgent")
        self.assertEqual(len(orchestrator.agents), 0)
        self.assertEqual(len(orchestrator.task_history), 0)
        
    def test_agent_registration(self):
        """Test agent registration"""
        orchestrator = OrchestratorAgent()
        agent = MockAgent("TestAgent", "Test response", "test")
        
        orchestrator.register_agent(agent)
        
        self.assertEqual(len(orchestrator.agents), 1)
        self.assertIn("TestAgent", orchestrator.agents)
        
    def test_task_routing(self):
        """Test task routing to appropriate agent"""
        orchestrator = OrchestratorAgent()
        
        # Register multiple agents
        menu_agent = MockAgent("MenuAgent", "Menu response", "menu")
        info_agent = MockAgent("InfoAgent", "Info response", "info")
        
        orchestrator.register_agent(menu_agent)
        orchestrator.register_agent(info_agent)
        
        # Test routing to menu agent
        result = orchestrator.execute("Show me the menu")
        self.assertTrue(result["success"])
        self.assertEqual(result["response"]["message"], "Menu response")
        
        # Test routing to info agent
        result = orchestrator.execute("What is your information?")
        self.assertTrue(result["success"])
        self.assertEqual(result["response"]["message"], "Info response")
        
    def test_fallback_handling(self):
        """Test fallback handling when no agent can handle task"""
        orchestrator = OrchestratorAgent()
        
        # Register an agent that won't handle this task
        menu_agent = MockAgent("MenuAgent", "Menu response", "menu")
        orchestrator.register_agent(menu_agent)
        
        # Test task that no agent can handle
        result = orchestrator.execute("What is the weather?")
        self.assertTrue(result["success"])
        self.assertIn("orchestrator", result["response"]["handled_by"])
        
    def test_task_history(self):
        """Test task history tracking"""
        orchestrator = OrchestratorAgent()
        agent = MockAgent("TestAgent", "Test response", "test")
        orchestrator.register_agent(agent)
        
        # Execute some tasks
        orchestrator.execute("Test task 1")
        orchestrator.execute("Test task 2")
        orchestrator.execute("Test task 3")
        
        # Check history
        history = orchestrator.get_task_history()
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]["task"], "Test task 1")
        self.assertEqual(history[1]["task"], "Test task 2")
        self.assertEqual(history[2]["task"], "Test task 3")
        
        # Test history limit
        limited_history = orchestrator.get_task_history(limit=2)
        self.assertEqual(len(limited_history), 2)
        
    def test_ui_agent_initialization(self):
        """Test UI agent initialization"""
        orchestrator = OrchestratorAgent()
        ui_agent = UIAgent()
        
        # Initially not connected
        self.assertIsNone(ui_agent.orchestrator)
        
        # Connect to orchestrator
        ui_agent.connect_to_orchestrator(orchestrator)
        self.assertIsNotNone(ui_agent.orchestrator)
        self.assertEqual(ui_agent.orchestrator.name, "OrchestratorAgent")
        
    def test_ui_agent_execution(self):
        """Test UI agent execution"""
        orchestrator = OrchestratorAgent()
        ui_agent = UIAgent()
        ui_agent.connect_to_orchestrator(orchestrator)
        
        # Register a test agent
        test_agent = MockAgent("TestAgent", "Test response", "test")
        orchestrator.register_agent(test_agent)
        
        # Execute through UI agent
        result = ui_agent.execute("Test task", {"user_id": "test_user"})
        
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Test response")
        
    def test_ui_agent_conversation_history(self):
        """Test UI agent conversation history"""
        orchestrator = OrchestratorAgent()
        ui_agent = UIAgent()
        ui_agent.connect_to_orchestrator(orchestrator)
        
        # Register a test agent
        test_agent = MockAgent("TestAgent", "Response 1", "test")
        orchestrator.register_agent(test_agent)
        
        # Execute some tasks
        ui_agent.execute("Test task 1", {"user_id": "user1"})
        ui_agent.execute("Test task 2", {"user_id": "user1"})
        ui_agent.execute("Test task 3", {"user_id": "user1"})
        
        # Check conversation history
        history = ui_agent.get_conversation_history()
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]["task"], "Test task 1")
        self.assertEqual(history[1]["task"], "Test task 2")
        self.assertEqual(history[2]["task"], "Test task 3")
        
    def test_restaurant_agent(self):
        """Test restaurant info agent"""
        # Create test menu data
        test_menu = {
            "categories": [
                {
                    "name": "Test Category",
                    "items": [
                        {"name": "Test Dish", "price": "10€"}
                    ]
                }
            ]
        }
        
        agent = RestaurantInfoAgent(menu_data=test_menu)
        
        # Test menu request
        result = agent.execute("What is on the menu?")
        self.assertIn("menu", result)
        self.assertEqual(len(result["menu_items"]), 1)
        self.assertIn("Test Dish - 10€", result["menu_items"])
        
        # Test can_handle
        self.assertTrue(agent.can_handle("What is on the menu?"))
        self.assertTrue(agent.can_handle("Show me the dishes"))
        self.assertFalse(agent.can_handle("What time is it?"))
        
    def test_complete_agent_system(self):
        """Test complete agent system creation"""
        # Create agent system
        orchestrator, ui_agent = create_agent_system()
        
        # Should have agents registered
        self.assertGreater(len(orchestrator.agents), 0)
        
        # UI agent should be connected
        self.assertIsNotNone(ui_agent.orchestrator)
        
        # Test menu request
        result = ui_agent.execute("What is on the menu?")
        self.assertTrue(result["success"])
        self.assertIn("menu", result.get("message", "").lower())
        
    def test_agent_status(self):
        """Test agent status reporting"""
        orchestrator = OrchestratorAgent()
        
        # Add some agents
        agent1 = MockAgent("Agent1", "Response 1", "test1")
        agent2 = MockAgent("Agent2", "Response 2", "test2")
        
        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)
        
        # Execute some tasks
        orchestrator.execute("test1 task")
        orchestrator.execute("test2 task")
        
        # Get status
        status = orchestrator.get_agent_status()
        
        # Check status structure
        self.assertIn("orchestrator", status)
        self.assertIn("agents", status)
        
        orchestrator_status = status["orchestrator"]
        self.assertEqual(orchestrator_status["name"], "OrchestratorAgent")
        self.assertEqual(len(orchestrator_status["registered_agents"]), 2)
        self.assertEqual(orchestrator_status["total_tasks_processed"], 2)
        
        agents_status = status["agents"]
        self.assertIn("Agent1", agents_status)
        self.assertIn("Agent2", agents_status)


if __name__ == '__main__':
    unittest.main()