"""
Test script to verify session management and history conservation
"""

import sys
import os
import json
import time
from datetime import datetime

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from utils.session_manager import SessionManager

def test_session_manager():
    """Test the session manager functionality"""
    print("=== Testing Session Manager ===")
    
    # Create session manager
    session_manager = SessionManager(session_timeout_minutes=1)
    
    # Test 1: Create sessions for different users
    print("\n1. Testing session creation...")
    user1_session1 = session_manager.create_session("user1")
    user1_session2 = session_manager.create_session("user1")
    user2_session1 = session_manager.create_session("user2")
    
    print(f"   User1 Session1: {user1_session1}")
    print(f"   User1 Session2: {user1_session2}")
    print(f"   User2 Session1: {user2_session1}")
    
    # Test 2: Get session information
    print("\n2. Testing session retrieval...")
    session_info = session_manager.get_session(user1_session1)
    print(f"   Session {user1_session1} info: {session_info}")
    
    # Test 3: Get user sessions
    print("\n3. Testing user session retrieval...")
    user1_sessions = session_manager.get_user_sessions("user1")
    print(f"   User1 has {len(user1_sessions)} sessions")
    
    # Test 4: Reset session
    print("\n4. Testing session reset...")
    new_session_id = session_manager.reset_session("user1", user1_session1)
    print(f"   Reset session {user1_session1}, new session: {new_session_id}")
    
    # Test 5: Session statistics
    print("\n5. Testing session statistics...")
    print(f"   Active sessions: {session_manager.get_active_sessions_count()}")
    print(f"   Total sessions: {session_manager.get_session_count()}")
    
    # Test 6: Session cleanup
    print("\n6. Testing session cleanup...")
    # Create an inactive session
    inactive_session = session_manager.create_session("test_user")
    session_info = session_manager.get_session(inactive_session)
    session_info["last_used"] = (datetime.now() - timedelta(minutes=61)).isoformat()
    session_info["active"] = False
    
    cleaned_up = session_manager.cleanup_inactive_sessions()
    print(f"   Cleaned up {cleaned_up} inactive sessions")
    print(f"   Active sessions after cleanup: {session_manager.get_active_sessions_count()}")
    
    print("\n=== Session Manager Test Completed ===")


def test_history_conservation():
    """Test history conservation in the API"""
    print("\n=== Testing History Conservation ===")
    
    # This would normally test the Flask API endpoints
    # For now, we'll just show the expected behavior
    print("\nExpected behavior:")
    print("1. Each query with a session_id maintains conversation history")
    print("2. New sessions start with fresh history")
    print("3. Sub-agent interactions are logged in the main conversation")
    print("4. History includes timestamps and message metadata")
    
    print("\nTo test the actual API:")
    print("1. Start the Flask server: python back/src/run/app.py")
    print("2. Use curl or Postman to send requests:")
    print("   - POST /session to create a new session")
    print("   - POST /query with session_id to maintain conversation")
    print("   - POST /reset to start a new conversation")
    print("   - GET /health to check session statistics")
    
    print("\nExample curl commands:")
    print('   curl -X POST -H "X-User-ID: test_user" http://localhost:5000/session')
    print('   curl -X POST -H "X-User-ID: test_user" -H "Content-Type: application/json" -d "{\"query\": \"What is on the menu?\", \"session_id\": \"YOUR_SESSION_ID\"}" http://localhost:5000/query')
    print('   curl -X POST -H "X-User-ID: test_user" -H "Content-Type: application/json" -d "{\"session_id\": \"YOUR_SESSION_ID\"}" http://localhost:5000/reset')
    
    print("\n=== History Conservation Test Completed ===")


if __name__ == "__main__":
    print("Running Session Management and History Conservation Tests")
    print("=" * 60)
    
    test_session_manager()
    test_history_conservation()
    
    print("\n" + "=" * 60)
    print("All tests completed!")