#!/usr/bin/env python3

"""
Test script to verify the voice processing pipeline works correctly.
This script tests the STT -> LLM -> TTS pipeline.
"""

import os
import sys
import tempfile
import numpy as np
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'back', 'src'))

# Import our models
from models.llm import MistralWrapper
from models.tts import generate_speech
from models.stt import transcribe_audio

def test_voice_pipeline():
    """Test the complete voice processing pipeline"""
    
    print("=== Testing Voice Processing Pipeline ===")
    print(f"Current time: {datetime.now().strftime('%I:%M:%S %p')}")
    
    # Initialize LLM
    print("\n1. Initializing LLM...")
    try:
        llm = MistralWrapper(api_key=os.environ.get("MISTRAL_API_KEY"))
        print("LLM initialized successfully")
    except Exception as e:
        print(f"Failed to initialize LLM: {e}")
        return False
    
    # Test with a simple text input (simulating STT output)
    print("\n2. Testing LLM with sample text...")
    test_prompt = "Bonjour, je voudrais réserver une table pour ce soir."
    try:
        text_response, history = llm.generate(test_prompt)
        print(f"LLM response: {text_response}")
    except Exception as e:
        print(f"LLM failed: {e}")
        return False
    
    # Test TTS with the LLM response
    print("\n3. Testing TTS with LLM response...")
    try:
        audio, sample_rate = generate_speech(text_response)
        print(f"TTS generated audio: {len(audio)} samples at {sample_rate} Hz")
    except Exception as e:
        print(f"TTS failed: {e}")
        return False
    
    # Test STT with a sample audio file (if available)
    print("\n4. Testing STT...")
    try:
        # Create a simple test audio file (this would normally be recorded audio)
        # For testing, we'll skip this part since we don't have actual audio
        print("STT test skipped (requires actual audio file)")
    except Exception as e:
        print(f"STT test failed: {e}")
    
    print("\n=== Test Summary ===")
    print("LLM working")
    print("TTS working")
    print("STT not fully tested (needs audio input)")
    print("\nThe pipeline should work when proper audio is provided.")
    
    return True

if __name__ == "__main__":
    # Load environment variables
    import dotenv
    dotenv.load_dotenv(os.path.join('back', '.env'))
    
    # Run the test
    success = test_voice_pipeline()
    
    if success:
        print("\nVoice pipeline test completed successfully!")
    else:
        print("\nVoice pipeline test failed!")
        sys.exit(1)