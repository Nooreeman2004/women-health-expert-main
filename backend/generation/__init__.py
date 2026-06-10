"""
Generation Module

Production-ready AI generation system for women's health chatbot.

Components:
- system_prompt.txt: Main system prompt with all rules
- conversation_manager.py: Sliding window context management
- safety_layer.py: Response validation and red flag detection
- enforcer.py: LLM-based safety enforcement
- generator.py: Main orchestrator

Features:
- Sliding context window (last 3-5 user + 2 assistant messages)
- RAG integration (top 3-5 chunks, ≤1200 tokens)
- Safety enforcement (no medicine names, no diagnosis)
- Red flag detection and escalation
- Clarification-first logic
"""

from .generator import Generator
from .conversation_manager import ConversationManager
from .safety_layer import SafetyLayer, SafetyViolation
from .enforcer import Enforcer

__all__ = [
    'Generator',
    'ConversationManager',
    'SafetyLayer',
    'SafetyViolation',
    'Enforcer'
]
