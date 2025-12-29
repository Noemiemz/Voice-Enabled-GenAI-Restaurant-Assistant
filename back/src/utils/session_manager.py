"""
Session Manager for the Restaurant Assistant System

This module provides session management capabilities for conversation history.
"""

import uuid
from typing import Dict, Optional
from datetime import datetime, timedelta
import threading


class SessionManager:
    """Manages conversation sessions for users."""
    
    def __init__(self, session_timeout_minutes: int = 60):
        """Initialize the session manager.
        
        Args:
            session_timeout_minutes: Session timeout in minutes (default: 60)
        """
        self.sessions: Dict[str, Dict] = {}  # session_id -> session_info
        self.user_sessions: Dict[str, Dict] = {}  # user_id -> {session_id: session_info}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.lock = threading.Lock()
        
    def create_session(self, user_id: str = "default_user") -> str:
        """Create a new session for a user.
        
        Args:
            user_id: The user ID to associate with this session
            
        Returns:
            The new session ID
        """
        with self.lock:
            session_id = str(uuid.uuid4())
            
            session_info = {
                "session_id": session_id,
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat(),
                "active": True
            }
            
            # Store session
            self.sessions[session_id] = session_info
            
            # Associate session with user
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {}
            self.user_sessions[user_id][session_id] = session_info
            
            return session_id
            
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session information by session ID.
        
        Args:
            session_id: The session ID to retrieve
            
        Returns:
            Session information dictionary or None if not found
        """
        with self.lock:
            session = self.sessions.get(session_id)
            if session:
                # Update last used timestamp
                session["last_used"] = datetime.now().isoformat()
            return session
            
    def get_user_sessions(self, user_id: str) -> Dict[str, Dict]:
        """Get all sessions for a specific user.
        
        Args:
            user_id: The user ID to get sessions for
            
        Returns:
            Dictionary of session_id -> session_info for the user
        """
        with self.lock:
            return self.user_sessions.get(user_id, {})
            
    def reset_session(self, user_id: str, current_session_id: str = None) -> str:
        """Reset conversation by creating a new session.
        
        Args:
            user_id: The user ID
            current_session_id: Optional current session ID to deactivate
            
        Returns:
            The new session ID
        """
        with self.lock:
            # Deactivate current session if provided
            if current_session_id and current_session_id in self.sessions:
                self.sessions[current_session_id]["active"] = False
                self.sessions[current_session_id]["ended_at"] = datetime.now().isoformat()
                
            # Create new session
            return self.create_session(user_id)
            
    def cleanup_inactive_sessions(self):
        """Clean up inactive sessions that have timed out."""
        with self.lock:
            now = datetime.now()
            inactive_sessions = []
            
            for session_id, session in self.sessions.items():
                if not session["active"]:
                    inactive_sessions.append(session_id)
                    continue
                    
                last_used = datetime.fromisoformat(session["last_used"])
                if now - last_used > self.session_timeout:
                    session["active"] = False
                    session["ended_at"] = now.isoformat()
                    inactive_sessions.append(session_id)
                    
                    # Clean up from user sessions
                    user_id = session["user_id"]
                    if user_id in self.user_sessions and session_id in self.user_sessions[user_id]:
                        del self.user_sessions[user_id][session_id]
            
            # Remove inactive sessions
            for session_id in inactive_sessions:
                if session_id in self.sessions:
                    del self.sessions[session_id]
            
            return len(inactive_sessions)
            
    def get_active_sessions_count(self) -> int:
        """Get the number of active sessions."""
        with self.lock:
            return sum(1 for session in self.sessions.values() if session["active"])
            
    def get_session_count(self) -> int:
        """Get the total number of sessions (active and inactive)."""
        with self.lock:
            return len(self.sessions)