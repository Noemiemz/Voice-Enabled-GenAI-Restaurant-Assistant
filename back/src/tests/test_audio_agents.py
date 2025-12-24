"""
Test audio processing through the agent system
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
from io import BytesIO
import json
import tempfile

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from run.app import app


class TestAudioAgentIntegration(unittest.TestCase):
    """Test audio processing integration with agent system"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app
        self.client = self.app.test_client()
        
    def test_audio_processing_with_agents(self):
        """Test audio processing through agent system"""
        
        # Create a mock audio file with proper structure (larger than 1KB)
        audio_data = b'RIFF....WAVEfmt ' + b'\x00' * 1500  # Make it > 1KB  # Minimal WAV header
        
        with patch('run.app.tempfile.NamedTemporaryFile') as mock_temp_file, \
             patch('run.app.transcribe_audio') as mock_stt, \
             patch('run.app.process_text_through_agents') as mock_agents, \
             patch('run.app.os.unlink'), \
             patch('builtins.open', mock_open()):
            
            # Mock temporary file
            mock_file = MagicMock()
            mock_file.name = '/tmp/test_audio.wav'
            mock_temp_file.return_value.__enter__.return_value = mock_file
            
            # Mock file size (needs to be > 1KB for validation)
            mock_file.tell.return_value = 2048
            
            # Mock STT to return transcribed text
            mock_stt.return_value = "What is on the menu?"
            
            # Mock agent processing
            mock_agents.return_value = ("Here is our menu", [{"role": "assistant", "content": "Here is our menu"}])
            
            # Send audio request with proper multipart form data
            response = self.client.post('/api/process-audio',
                data={'audio': (BytesIO(audio_data), 'test.wav')},
                content_type='multipart/form-data')
                
            # Check response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['textResponse'], "Here is our menu")
            self.assertEqual(len(data['history']), 1)
            
            # Verify agent system was called with correct text
            mock_agents.assert_called_once()
            call_args = mock_agents.call_args[0]
            self.assertEqual(call_args[0], "What is on the menu?")
            self.assertEqual(call_args[1]['interface'], 'voice')
            
    def test_audio_processing_fallback(self):
        """Test audio processing fallback to LLM when agents fail"""
        
        # Create a mock audio file (larger than 1KB)
        audio_data = b'RIFF....WAVEfmt ' + b'\x00' * 1500
        
        with patch('run.app.tempfile.NamedTemporaryFile') as mock_temp_file, \
             patch('run.app.transcribe_audio') as mock_stt, \
             patch('run.app.process_text_through_agents') as mock_agents, \
             patch('run.app.os.unlink'), \
             patch('run.app.llm.generate') as mock_llm, \
             patch('builtins.open', mock_open()):
            
            # Mock temporary file
            mock_file = MagicMock()
            mock_file.name = '/tmp/test_audio.wav'
            mock_temp_file.return_value.__enter__.return_value = mock_file
            
            # Mock file size (needs to be > 1KB for validation)
            mock_file.tell.return_value = 2048
            
            # Mock STT
            mock_stt.return_value = "What are your hours?"
            
            # Mock agent processing to fail
            mock_agents.side_effect = Exception("Agent error")
            
            # Mock LLM fallback
            mock_llm.return_value = ("We are open from 12PM to 10PM", 
                                   [{"role": "assistant", "content": "We are open from 12PM to 10PM"}])
            
            # Send audio request
            response = self.client.post('/api/process-audio',
                data={'audio': (BytesIO(audio_data), 'test.wav')},
                content_type='multipart/form-data')
                
            # Should return 500 error when agent processing fails
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.data)
            self.assertIn("Agent error", data['error'])
            
            # Should have tried to call agent system
            mock_agents.assert_called_once()
            
    def test_audio_processing_stt_failure(self):
        """Test audio processing when STT fails"""
        
        audio_data = b'RIFF....WAVEfmt ' + b'\x00' * 1500  # Make it > 1KB
        
        with patch('run.app.tempfile.NamedTemporaryFile') as mock_temp_file, \
             patch('run.app.transcribe_audio') as mock_stt, \
             patch('run.app.os.unlink'), \
             patch('builtins.open', mock_open()):
            
            # Mock temporary file
            mock_file = MagicMock()
            mock_file.name = '/tmp/test_audio.wav'
            mock_temp_file.return_value.__enter__.return_value = mock_file
            
            # Mock file size
            mock_file.tell.return_value = 1024
            
            # Mock STT to fail
            mock_stt.return_value = ""
            
            # Send audio request
            response = self.client.post('/api/process-audio',
                data={'audio': (BytesIO(audio_data), 'test.wav')},
                content_type='multipart/form-data')
                
            # Should return error
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.data)
            self.assertIn('Could not transcribe audio', data['error'])
            
    def test_audio_processing_invalid_file(self):
        """Test audio processing with invalid file"""
        
        # Send request with no audio file
        response = self.client.post('/api/process-audio',
            data={},
            content_type='multipart/form-data')
            
        # Should return error
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('No audio file provided', data['error'])
        
    def test_audio_processing_empty_file(self):
        """Test audio processing with empty file"""
        
        audio_data = b''
        
        with patch('run.app.tempfile.NamedTemporaryFile') as mock_temp_file, \
             patch('run.app.os.unlink'):
            
            # Mock temporary file
            mock_file = MagicMock()
            mock_file.name = '/tmp/test_audio.wav'
            mock_temp_file.return_value.__enter__.return_value = mock_file
            
            # Send request with empty audio
            response = self.client.post('/api/process-audio',
                data={'audio': (audio_data, 'test.wav')},
                content_type='multipart/form-data')
                
            # Should return error
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.data)
            self.assertIn('Empty audio file', data['error'])


if __name__ == '__main__':
    unittest.main()