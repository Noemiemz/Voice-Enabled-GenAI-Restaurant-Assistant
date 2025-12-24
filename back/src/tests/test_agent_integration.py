"""
Test the agent system integration with the Flask application
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import json

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from run.app import app, setup_agent_system, process_text_through_agents


class TestAgentIntegration(unittest.TestCase):
    """Test agent system integration with Flask app"""
    
    def setUp(self):
        """Set up test client and mocks"""
        self.app = app
        self.client = self.app.test_client()
        
        # Mock the agent system setup
        self.mock_ui_agent = MagicMock()
        
        # Patch the setup function
        self.setup_patcher = patch('run.app.setup_agent_system', return_value=self.mock_ui_agent)
        self.mock_setup = self.setup_patcher.start()
        
        # Reload the app to get the mocked agent
        from run.app import ui_agent
        self.ui_agent = ui_agent
        
    def tearDown(self):
        """Clean up mocks"""
        self.setup_patcher.stop()
        
    def test_agent_system_setup(self):
        """Test that agent system is properly initialized"""
        # Call the setup function directly
        mock_ui_agent = setup_agent_system()
        
        # Should return a UIAgent instance (agents are available)
        self.assertIsNotNone(mock_ui_agent)
        self.assertEqual(mock_ui_agent.name, "UIAgent")
        
    def test_process_text_through_agents_with_agents(self):
        """Test text processing with agents available"""
        # Process text (should use agents)
        response, history = process_text_through_agents("Test message")
        
        # Should use agents (not LLM fallback)
        self.assertIsNotNone(response)
        self.assertIsInstance(history, list)
            
    def test_process_text_through_agents_with_context(self):
        """Test text processing with context"""
        # Process text with context (should use agents)
        response, history = process_text_through_agents("Test message", {"user_id": "test_user"})
        
        # Should use agents
        self.assertIsNotNone(response)
        self.assertIsInstance(history, list)
            
    @patch('run.app.ui_agent')
    def test_agent_process_endpoint(self, mock_ui_agent):
        """Test the agent process endpoint"""
        # Mock agent response
        mock_ui_agent.execute.return_value = {
            "success": True,
            "message": "Agent response",
            "type": "text",
            "data": {"test": "data"}
        }
        
        # Test the endpoint
        response = self.client.post('/api/agent-process',
            data=json.dumps({'message': 'Test message'}),
            content_type='application/json')
            
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Agent response')
        self.assertEqual(data['type'], 'text')
        self.assertEqual(data['data'], {"test": "data"})
        
    @patch('run.app.ui_agent')
    def test_agent_process_endpoint_with_context(self, mock_ui_agent):
        """Test the agent process endpoint with context"""
        # Mock agent response
        mock_ui_agent.execute.return_value = {
            "success": True,
            "message": "Agent response",
            "type": "menu"
        }
        
        # Test the endpoint with context
        response = self.client.post('/api/agent-process',
            data=json.dumps({
                'message': 'What is on the menu?',
                'user_id': 'test_user',
                'interface': 'voice'
            }),
            content_type='application/json')
            
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Agent response')
        self.assertEqual(data['type'], 'menu')
        
        # Check that agent was called with correct context
        mock_ui_agent.execute.assert_called_once()
        call_args = mock_ui_agent.execute.call_args[0]
        self.assertEqual(call_args[0], 'What is on the menu?')
        self.assertEqual(call_args[1]['user_id'], 'test_user')
        self.assertEqual(call_args[1]['interface'], 'voice')
        
    @patch('run.app.ui_agent', None)
    def test_agent_process_endpoint_no_agent(self):
        """Test agent process endpoint when agent system not available"""
        # Test the endpoint when ui_agent is None
        response = self.client.post('/api/agent-process',
            data=json.dumps({'message': 'Test message'}),
            content_type='application/json')
            
        # Should return 503 error
        self.assertEqual(response.status_code, 503)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('Agent system not available', data['error'])
        
    def test_agent_process_endpoint_no_message(self):
        """Test agent process endpoint with no message"""
        # Test the endpoint with no message
        response = self.client.post('/api/agent-process',
            data=json.dumps({}),
            content_type='application/json')
            
        # Should return 400 error
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('No message provided', data['error'])
        
    def test_agent_process_endpoint_error(self):
        """Test agent process endpoint error handling"""
        # Test the endpoint with invalid JSON
        response = self.client.post('/api/agent-process',
            data='invalid json',
            content_type='application/json')
            
        # Should return 500 error
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        
    @patch('run.app.ui_agent')
    def test_chat_endpoint_uses_agents(self, mock_ui_agent):
        """Test that chat endpoint now uses agents"""
        # Mock agent response
        mock_ui_agent.execute.return_value = {
            "success": True,
            "message": "Chat response"
        }
        
        # Test the chat endpoint
        response = self.client.post('/api/chat',
            data=json.dumps({'message': 'Hello'}),
            content_type='application/json')
            
        # Should succeed
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['textResponse'], 'Chat response')
        
        # Should have called the agent system
        mock_ui_agent.execute.assert_called_once()
        
    @patch('run.app.ui_agent', None)
    def test_chat_endpoint_fallback(self):
        """Test chat endpoint fallback when agents not available"""
        # Mock the LLM generate method
        with patch('run.app.llm.generate') as mock_llm:
            mock_llm.return_value = ("LLM fallback response", [{"role": "assistant", "content": "LLM fallback response"}])
            
            # Test the chat endpoint
            response = self.client.post('/api/chat',
                data=json.dumps({'message': 'Hello'}),
                content_type='application/json')
                
            # Should succeed with LLM fallback
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['textResponse'], 'LLM fallback response')
            
            # Should have called LLM fallback
            mock_llm.assert_called_once()


if __name__ == '__main__':
    unittest.main()