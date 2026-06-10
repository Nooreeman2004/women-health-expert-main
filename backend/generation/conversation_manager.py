"""
Conversation Manager

Handles conversation context with sliding window approach:
- Maintains last 3-5 user messages + 2 assistant replies
- Summarizes older messages
- Manages token limits
- Assembles context for LLM
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import tiktoken


@dataclass
class Message:
    """Single conversation message."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    tokens: int = 0


class ConversationManager:
    """
    Manages conversation history with sliding window.
    """
    
    def __init__(
        self,
        max_user_messages: int = 5,
        max_assistant_messages: int = 2,
        max_context_tokens: int = 2000,
        model: str = "gpt-4"
    ):
        """
        Initialize conversation manager.
        
        Args:
            max_user_messages: Maximum recent user messages to keep
            max_assistant_messages: Maximum recent assistant messages to keep
            max_context_tokens: Maximum tokens for conversation context
            model: Model name for token counting
        """
        self.max_user_messages = max_user_messages
        self.max_assistant_messages = max_assistant_messages
        self.max_context_tokens = max_context_tokens
        
        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.encoding_for_model(model)
        except:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Conversation state
        self.messages: List[Message] = []
        self.conversation_summary: Optional[str] = None
        self.user_context: Dict[str, Any] = {}  # Store user info (symptoms, stage, etc.)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenizer.encode(text))
    
    def add_message(self, role: str, content: str):
        """
        Add a message to conversation history.
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
        """
        tokens = self.count_tokens(content)
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            tokens=tokens
        )
        self.messages.append(message)
        
        # Trim if needed
        self._trim_messages()
    
    def _trim_messages(self):
        """Trim messages to maintain sliding window."""
        # Separate user and assistant messages
        user_messages = [m for m in self.messages if m.role == 'user']
        assistant_messages = [m for m in self.messages if m.role == 'assistant']
        
        # Keep only recent messages
        recent_user = user_messages[-self.max_user_messages:]
        recent_assistant = assistant_messages[-self.max_assistant_messages:]
        
        # Combine and sort by timestamp
        recent_messages = recent_user + recent_assistant
        recent_messages.sort(key=lambda x: x.timestamp)
        
        # If we're dropping messages, create summary
        if len(self.messages) > len(recent_messages):
            dropped_messages = [m for m in self.messages if m not in recent_messages]
            self._create_summary(dropped_messages)
        
        self.messages = recent_messages
    
    def _create_summary(self, messages: List[Message]):
        """
        Create summary of dropped messages.
        
        Args:
            messages: Messages to summarize
        """
        if not messages:
            return
        
        # In production, this would call an LLM to generate a concise summary.
        # For now, we'll use an improved rule-based approach to capture key details.
        
        summary_parts = []
        if self.conversation_summary:
            summary_parts.append(self.conversation_summary.rstrip('.'))
        
        # Identify key symptoms or topics mentioned
        symptoms_found = []
        topics_found = []
        
        for m in messages:
            content_lower = m.content.lower()
            
            # User symptoms
            if m.role == 'user':
                if any(word in content_lower for word in ['eye', 'vision', 'white spot', 'bump']):
                    symptoms_found.append('eye concerns/white spots')
                if any(word in content_lower for word in ['period', 'menstruation', 'cycle']):
                    symptoms_found.append('menstrual cycle changes')
                if any(word in content_lower for word in ['pain', 'cramp', 'ache']):
                    symptoms_found.append('pain')
                if any(word in content_lower for word in ['hot flash', 'night sweat']):
                    symptoms_found.append('vasomotor symptoms')
            
            # Assistant guidance/questions
            if m.role == 'assistant':
                if 'dermatologist' in content_lower or 'doctor' in content_lower:
                    topics_found.append('recommendation to see professional')
                if 'clean' in content_lower or 'protect' in content_lower:
                    topics_found.append('skin care/hygiene advice')
        
        # Build the summary string
        new_details = []
        if symptoms_found:
            new_details.append(f"discussed {', '.join(set(symptoms_found))}")
        if topics_found:
            new_details.append(f"provided advice on {', '.join(set(topics_found))}")
        
        if new_details:
            summary_parts.append("; ".join(new_details))
        elif not self.conversation_summary:
            summary_parts.append(f"Conversation covers {len(messages)} previous interactions")
            
        self.conversation_summary = ". ".join(summary_parts).strip() + "."
        
        # Ensure the summary doesn't grow too large
        if len(self.conversation_summary) > 1000:
            self.conversation_summary = self.conversation_summary[:997] + "..."
    
    def update_user_context(self, key: str, value: Any):
        """
        Update user context information.
        
        Args:
            key: Context key (e.g., 'menopause_stage', 'primary_symptoms')
            value: Context value
        """
        self.user_context[key] = value
    
    def get_context_for_llm(
        self,
        include_summary: bool = True
    ) -> List[Dict[str, str]]:
        """
        Get conversation context formatted for LLM.
        
        Args:
            include_summary: Whether to include conversation summary
            
        Returns:
            List of message dicts for LLM
        """
        context = []
        
        # Add summary if exists
        if include_summary and self.conversation_summary:
            context.append({
                "role": "system",
                "content": f"Previous conversation context: {self.conversation_summary}"
            })
        
        # Add recent messages
        for msg in self.messages:
            context.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return context
    
    def get_profile_for_llm(self) -> str:
        """
        Get structured user profile as a string for LLM injection.
        
        Returns:
            Formatted profile string or empty string
        """
        if not self.user_context:
            return ""
            
        profile_parts = []
        for key, value in self.user_context.items():
            formatted_key = key.replace('_', ' ').title()
            profile_parts.append(f"- {formatted_key}: {value}")
            
        return "USER HEALTH PROFILE (Extracted from chat):\n" + "\n".join(profile_parts)
    
    def get_total_tokens(self) -> int:
        """Get total tokens in current context."""
        total = sum(m.tokens for m in self.messages)
        if self.conversation_summary:
            total += self.count_tokens(self.conversation_summary)
        return total
    
    def clear(self):
        """Clear conversation history."""
        self.messages = []
        self.conversation_summary = None
        self.user_context = {}
    
    def get_last_user_message(self) -> Optional[str]:
        """Get the last user message."""
        user_messages = [m for m in self.messages if m.role == 'user']
        return user_messages[-1].content if user_messages else None
    
    def get_last_assistant_message(self) -> Optional[str]:
        """Get the last assistant message."""
        assistant_messages = [m for m in self.messages if m.role == 'assistant']
        return assistant_messages[-1].content if assistant_messages else None
    
    def has_context(self) -> bool:
        """Check if conversation has any context."""
        return len(self.messages) > 0 or self.conversation_summary is not None
    
    def get_user_message_count(self) -> int:
        """Get the count of user messages in conversation history."""
        return len([m for m in self.messages if m.role == 'user'])
    
    def has_prior_conversation(self) -> bool:
        """Check if there are previous messages (excluding the current one being processed)."""
        # Since messages are added before this check, we need at least 2 messages
        # (1 user message + 1 assistant response) to have "prior" conversation
        return len(self.messages) >= 2

    def restore_state(self, messages_data: List[Dict[str, Any]], summary: Optional[str], user_context: Dict[str, Any]):
        """
        Restore conversation state from dictionary data.
        
        Args:
            messages_data: List of message dictionaries
            summary: Conversation summary
            user_context: User context/profile data
        """
        self.messages = []
        for m in messages_data:
            # Parse timestamp if it's a string
            ts = m['timestamp']
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
                
            self.messages.append(Message(
                role=m['role'],
                content=m['content'],
                timestamp=ts,
                tokens=m.get('tokens', 0)
            ))
            
        self.conversation_summary = summary
        self.user_context = user_context
        print(f"🔄 [MEMORY] Restored {len(self.messages)} messages and profile")
