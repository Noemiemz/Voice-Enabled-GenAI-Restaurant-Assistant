"""
Simple test for session manager
"""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from utils.session_manager import SessionManager

def main():
    print("Testing Session Manager...")
    
    # Create session manager
    session_manager = SessionManager(session_timeout_minutes=1)
    
    # Test basic functionality
    session_id = session_manager.create_session("test_user")
    print(f"Created session: {session_id}")
    
    session_info = session_manager.get_session(session_id)
    print(f"Session info: {session_info}")
    
    print(f"Active sessions: {session_manager.get_active_sessions_count()}")
    print(f"Total sessions: {session_manager.get_session_count()}")
    
    print("Session manager test completed successfully!")

if __name__ == "__main__":
    main()