"""
Session Manager

Manages conversation sessions with in-memory storage.
In production, use Redis or database for persistence.
"""

import uuid
import os
import json
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
from generation import Generator


# Initialize Firebase Admin SDK
firebase_initialized = False
try:
    # Look for service account file
    cred_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'women-expert-firebase-adminsdk-fbsvc-7828287820.json')
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print(f"✅ [FIREBASE] Initialized with {cred_path}")
        firebase_initialized = True
    else:
        print(f"⚠️ [FIREBASE] Service account not found at {cred_path}")
except Exception as e:
    print(f"❌ [FIREBASE] Initialization failed: {e}")


class SessionManager:
    """
    Manages conversation sessions.
    """
    
    def __init__(self, session_timeout_minutes: int = 30):
        """
        Initialize session manager.
        
        Args:
            session_timeout_minutes: Session timeout in minutes
        """
        self.sessions: Dict[str, Dict] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.db = firestore.client() if firebase_initialized else None
    
    def _save_to_firestore(self, session_id: str, generator: Generator):
        """Save session state to Firestore."""
        if not self.db:
            return
            
        try:
            # Prepare messages data
            messages_data = []
            for msg in generator.conversation_manager.messages:
                messages_data.append({
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'tokens': msg.tokens
                })
                
            session_data = {
                'messages': messages_data,
                'summary': generator.conversation_manager.conversation_summary,
                'user_context': generator.conversation_manager.user_context,
                'last_activity': datetime.now(),
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            self.db.collection('sessions').document(session_id).set(session_data, merge=True)
            print(f"💾 [FIREBASE] Saved session {session_id}")
        except Exception as e:
            print(f"❌ [FIREBASE] Save failed for {session_id}: {e}")

    def _load_from_firestore(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session state from Firestore."""
        if not self.db:
            return None
            
        try:
            doc = self.db.collection('sessions').document(session_id).get()
            if doc.exists:
                return doc.to_dict()
        except Exception as e:
            print(f"❌ [FIREBASE] Load failed for {session_id}: {e}")
        return None

    def create_session(self, generator: Generator) -> str:
        """
        Create a new session.
        
        Args:
            generator: Generator instance
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'generator': generator,
            'created_at': datetime.now(),
            'last_activity': datetime.now()
        }
        # Initial save
        self._save_to_firestore(session_id, generator)
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Generator]:
        """
        Get session generator.
        
        Args:
            session_id: Session ID
            
        Returns:
            Generator instance or None
        """
        if session_id not in self.sessions:
            # Try loading from Firestore
            firestore_data = self._load_from_firestore(session_id)
            if firestore_data:
                print(f"☁️ [FIREBASE] Restoring session {session_id} from Firestore")
                # Create new generator and restore state
                from generation import Generator
                from retrieval import ProductionRetriever
                
                # Note: We need the retriever here. This is a bit messy because of circular imports
                # or missing context. In practice, should probably be passed in.
                # For now, let's assume we can re-init a basic one or it's handled in routes.py
                # better approach: SessionManager doesn't create Generators, it just manages them.
                # Let's return the data and let routes.py handle restoration if needed, 
                # OR pass a generator factory.
                
                # SIMPLER: Just return None and let routes.py handle "re-creation" with data injection
                return None
            return None
        
        session = self.sessions[session_id]
        
        # Check if session expired
        if datetime.now() - session['last_activity'] > self.session_timeout:
            self.delete_session(session_id)
            return None
        
        # Update last activity
        session['last_activity'] = datetime.now()
        
        # Sync with Firestore (optional but keeps it fresh)
        self._save_to_firestore(session_id, session['generator'])
        
        return session['generator']
    
    def save_session(self, session_id: str):
        """Manually trigger save to Firestore."""
        if session_id in self.sessions:
            self._save_to_firestore(session_id, self.sessions[session_id]['generator'])
    
    def delete_session(self, session_id: str):
        """
        Delete a session.
        
        Args:
            session_id: Session ID
        """
        if session_id in self.sessions:
            # Clear conversation
            self.sessions[session_id]['generator'].clear_conversation()
            del self.sessions[session_id]
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session['last_activity'] > self.session_timeout
        ]
        for sid in expired:
            self.delete_session(sid)
    
    def get_session_count(self) -> int:
        """Get number of active sessions."""
        return len(self.sessions)
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get raw session data from Firestore or RAM.
        Useful for session restoration.
        """
        # Try Firestore first as it's the source of truth for persistence
        data = self._load_from_firestore(session_id)
        if data:
            return data
            
        # Fallback to RAM if Firestore failed or not initialized
        if session_id in self.sessions:
            generator = self.sessions[session_id]['generator']
            messages_data = []
            for msg in generator.conversation_manager.messages:
                messages_data.append({
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'tokens': msg.tokens
                })
            return {
                'messages': messages_data,
                'summary': generator.conversation_manager.conversation_summary,
                'user_context': generator.conversation_manager.user_context
            }
            
        return None
