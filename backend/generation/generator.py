"""
Main Generator

Orchestrates the entire generation process:
- Loads system prompt
- Manages conversation context
- Integrates RAG retrieval
- Applies safety layer
- Enforces response validation
- Structures responses properly
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from groq import AsyncGroq
from dotenv import load_dotenv

from .conversation_manager import ConversationManager
from .safety_layer import SafetyLayer
from .enforcer import Enforcer


class Generator:
    """
    Main generator orchestrator for women's health chatbot.
    """
    
    def __init__(
        self,
        openai_api_key: str,
        generation_model: Optional[str] = None,
        enforcer_model: Optional[str] = None,
        retriever = None  # ProductionRetriever instance
    ):
        """
        Initialize generator.
        
        Args:
            openai_api_key: OpenAI API key (for embeddings only)
            generation_model: Model for generation (from .env)
            enforcer_model: Model for enforcement (from .env)
            retriever: ProductionRetriever instance for RAG
        """
        # Load environment variables
        load_dotenv()
        
        # Get Groq API key
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        # Models
        self.generation_model = generation_model or os.getenv('GROQ_GENERATION_MODEL', 'openai/gpt-oss-20b')
        self.enforcer_model = enforcer_model or os.getenv('GROQ_ENFORCER_MODEL', 'openai/gpt-oss-20b')
        
        # Initialize components
        self.client = AsyncGroq(api_key=groq_api_key)
        self.conversation_manager = ConversationManager(
            max_user_messages=10,
            max_assistant_messages=5,
            max_context_tokens=2000,
            model=self.generation_model
        )
        self.safety_layer = SafetyLayer()
        self.enforcer = Enforcer(api_key=groq_api_key, model=self.enforcer_model)
        self.retriever = retriever
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt()
        
        # Load decision trees and templates
        self.decision_trees = self._load_decision_trees()
        self.conversation_templates = self._load_conversation_templates()
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from file."""
        prompt_path = Path(__file__).parent / 'system_prompt.txt'
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _load_decision_trees(self) -> Dict[str, Any]:
        """Load decision trees from JSON."""
        trees_path = Path(__file__).parent.parent / 'data' / 'processed' / 'chatbot' / 'decision_trees_medication.json'
        try:
            with open(trees_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load decision trees: {e}")
            return {}
    
    def _load_conversation_templates(self) -> Dict[str, Any]:
        """Load conversation templates from JSON."""
        templates_path = Path(__file__).parent.parent / 'data' / 'processed' / 'chatbot' / 'conversation_templates.json'
        try:
            with open(templates_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load conversation templates: {e}")
            return {}
    
    def _strip_markdown(self, text: str) -> str:
        """
        Strip all forbidden markdown symbols from text.
        
        Removes:
        - Asterisks (*)
        - Dashes/Hyphens (-)
        - Hashtags (#)
        - Underscores (_)
        - Pipes (|)
        
        Preserves:
        - Numbers for lists (1., 2., etc.)
        
        Args:
            text: Text with potential markdown formatting
            
        Returns:
            Strictly plain text
        """
        import re
        
        # Remove asterisks (*) completely (used for bold, italic, or bullets)
        text = text.replace('*', '')
        
        # Remove underscores (_) completely
        text = text.replace('_', '')
        
        # Remove hashtags (#) from headings (but keep the text)
        # Case 1: Start of line hashtag
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # Case 2: Hashtag anywhere else (just in case)
        text = text.replace('#', '')
        
        # Remove horizontal rules (often made of --- or ***)
        text = re.sub(r'^[\-\*_]{3,}\s*$', '', text, flags=re.MULTILINE)
        
        # Remove dashes/hyphens (-) completely
        # Replacing with space to prevent joining words like "self-care" -> "selfcare"
        # as per system prompt instructions.
        text = text.replace('-', ' ')
        
        # Remove table formatting pipes
        text = text.replace('|', '')
        
        # Clean up any triple/quadruple spaces created by replacements
        text = re.sub(r' +', ' ', text)
        
        # Clean up multiple blank lines
        text = re.sub(r'\n\n\n+', '\n\n', text)
        
        return text.strip()

    
    def _detect_safety_context(self, user_message: str, detected_red_flags: List[str]) -> Optional[str]:
        """
        Detect if user input requires safety context injection.
        Uses red flag detection as source of truth.
        
        Args:
            user_message: User's message
            detected_red_flags: Red flags detected by safety layer
            
        Returns:
            Safety context note if needed
        """
        if not detected_red_flags:
            return None
        
        message_lower = user_message.lower()
        
        # Critical red flags
        critical_keywords = ['suicidal', 'want to die', 'severe chest pain', 'chest pain']
        if any(keyword in detected_red_flags for keyword in critical_keywords):
            return "CRITICAL: User mentions life-threatening symptoms. Provide emergency resources immediately."
        
        # Bleeding
        if any('bleeding' in flag for flag in detected_red_flags):
            return "Be extra cautious. User mentions bleeding. Strongly encourage immediate professional consultation."
        
        # Severe pain
        if 'severe pain' in message_lower or 'extreme pain' in message_lower:
            return "Be extra cautious. User mentions severe pain. Encourage professional consultation."
        
        # Pregnancy
        if any(word in message_lower for word in ['pregnant', 'pregnancy', 'expecting']):
            return "Be extra cautious. User may be pregnant. Encourage professional consultation."
        
        # General red flag
        return "Be extra cautious. User mentions concerning symptoms. Encourage professional consultation."
    
    def _needs_clarification(self, user_message: str, has_context: bool = False) -> bool:
        """
        Determine if query needs clarification.
        Only returns True for VERY vague messages (< 3 words) IF no prior context exists.
        
        Args:
            user_message: User's message
            has_context: Whether there is prior conversation context
            
        Returns:
            True if clarification needed
        """
        # Common greetings should NOT trigger clarification
        greetings = ['hey', 'hi', 'hello', 'hiya', 'howdy', 'greetings', 
                     'good morning', 'good afternoon', 'good evening', 'thanks', 'thank you', 'ok', 'okay', 'got it']
        
        message_lower = user_message.lower().strip().strip('?!.')
        
        # If it's a greeting or simple acknowledgment, don't ask for clarification
        if message_lower in greetings:
            return False
        
        # If we have context, almost any message is valid as an answer or follow-up
        if has_context:
            return False
            
        # Only very short messages need clarification (< 3 words) if NO context
        if len(user_message.split()) < 3:
            return True
        
        return False
    
    async def _retrieve_context(self, query: str, top_k: int = 5) -> str:
        """
        Retrieve relevant context from RAG.
        
        Args:
            query: User query
            top_k: Number of chunks to retrieve
            
        Returns:
            Assembled context string
        """
        if not self.retriever:
            return ""
        
        try:
            # Retrieve context (max 1200 tokens)
            context, results = await self.retriever.get_context(
                query=query,
                top_k=top_k,
                max_context_length=1200
            )
            return context
        except Exception as e:
            print(f"Warning: RAG retrieval failed: {e}")
            return ""
    
    async def generate_response(
        self,
        user_message: str,
        use_rag: bool = True,
        max_retries: int = 2
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a safe, helpful response.
        
        Args:
            user_message: User's message
            use_rag: Whether to use RAG retrieval
            max_retries: Max retries if enforcer rejects
            
        Returns:
            Tuple of (response, metadata)
        """
        metadata = {
            'red_flags_detected': [],
            'safety_violations': [],
            'enforcer_used': False,
            'rag_used': False,
            'clarification_needed': False
        }
        
        # 1. Check for red flags (SINGLE SOURCE OF TRUTH)
        red_flags = self.safety_layer.detect_red_flags(user_message)
        
        # Determine severity level for metadata
        metadata['red_flags_detected'] = red_flags
        if red_flags:
            metadata['escalation_triggered'] = True
            critical_keywords = ['post-menopausal bleeding', 'bleeding after menopause', 
                               'severe chest pain', 'chest pain', 'suicidal', 'want to die']
            is_critical = any(keyword in red_flags for keyword in critical_keywords)
            metadata['escalation_level'] = 'CRITICAL' if is_critical else 'HIGH'
            
        # We NO LONGER return early here. Instead, we use this info to guide the LLM
        # and append a specific warning later.
        
        # 2. Add user message to conversation
        self.conversation_manager.add_message('user', user_message)
        
        # 3. Check if clarification needed (ONLY if no prior context)
        # We check has_prior_conversation() which looks for at least 2 messages (1 user + 1 assistant)
        has_prior = self.conversation_manager.has_prior_conversation() or self.conversation_manager.has_context()
        
        if self._needs_clarification(user_message, has_context=has_prior):
            # Only ask for clarification on the FIRST message if it's very vague (< 3 words)
            metadata['clarification_needed'] = True
            clarification = (
                "I'd like to help you better. Could you tell me a bit more about what you're experiencing? "
                "For example, how long has this been happening, and how is it affecting you?"
            )
            self.conversation_manager.add_message('assistant', clarification)
            return clarification, metadata
        
        # 4. Retrieve RAG context
        rag_context = ""
        if use_rag:
            rag_context = await self._retrieve_context(user_message, top_k=5)
            if rag_context:
                metadata['rag_used'] = True
        
        # 5. Detect safety context (using red flags as source of truth)
        safety_context = self._detect_safety_context(user_message, red_flags)
        
        # 6. Assemble messages for LLM
        messages = []
        
        # System prompt
        messages.append({
            "role": "system",
            "content": self.system_prompt
        })
        
        # Safety context (if needed)
        if safety_context:
            messages.append({
                "role": "system",
                "content": f"SAFETY NOTE: {safety_context}"
            })
            
        # Red flag context (if needed)
        if red_flags:
            messages.append({
                "role": "system",
                "content": f"USER HAS MENTIONED RED FLAGS: {', '.join(red_flags)}. "
                           f"You MUST emphasize seeking professional medical help while providing general educational context. "
                           f"Be empathetic but very cautious."
            })
        
        # RAG context (if available)
        if rag_context:
            messages.append({
                "role": "system",
                "content": f"RELEVANT INFORMATION FROM KNOWLEDGE BASE:\n\n{rag_context}\n\nUse this information to provide accurate, evidence-based guidance."
            })
        
        # Conversation context (ALWAYS include summary, even if empty)
        conversation_context = self.conversation_manager.get_context_for_llm(include_summary=True)
        
        # New: Structured User Profile (Memory across turns)
        user_profile = self.conversation_manager.get_profile_for_llm()
        if user_profile:
            messages.append({
                "role": "system",
                "content": user_profile
            })
        
        # DEBUG: Log conversation state
        print(f"💬 [DEBUG] Conversation has {len(self.conversation_manager.messages)} messages")
        print(f"💬 [DEBUG] User profile: {user_profile if user_profile else 'None'}")
        
        # CRITICAL: Always inject memory summary if it exists, even when RAG returns nothing
        if self.conversation_manager.conversation_summary:
            # Check if not already added via conversation_context
            if not any(m.get('content', '').startswith('Previous conversation context:') for m in conversation_context):
                messages.append({
                    "role": "system",
                    "content": f"CONVERSATION MEMORY: {self.conversation_manager.conversation_summary}"
                })
        
        messages.extend(conversation_context)
        
        # DEBUG: Log final message count being sent to LLM
        print(f"📤 [DEBUG] Sending {len(messages)} total messages to LLM (system + context + current)")
        
        # 7. Generate response
        for attempt in range(max_retries + 1):
            try:
                # Call generation model
                completion = await self.client.chat.completions.create(
                    model=self.generation_model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                response = completion.choices[0].message.content.strip()
                
                # 8. Safety layer check
                is_safe, violations = self.safety_layer.check_response(response)
                if violations:
                    metadata['safety_violations'] = [
                        {'type': v.type, 'severity': v.severity, 'message': v.message}
                        for v in violations
                    ]
                
                # 9. Enforcer validation
                if not is_safe or attempt == 0:  # Always check on first attempt
                    metadata['enforcer_used'] = True
                    enforcer_safe, violation_msg = await self.enforcer.validate_response(response)
                    
                    if not enforcer_safe:
                        if attempt < max_retries:
                            # Try to fix
                            print(f"Enforcer rejected response (attempt {attempt + 1}). Trying to fix...")
                            response = await self.enforcer.suggest_fix(response, violation_msg)
                            # Check again
                            is_safe, _ = self.safety_layer.check_response(response)
                            if is_safe:
                                break
                        else:
                            # Fallback to safe response
                            response = (
                                "I want to be careful with my guidance. For specific treatment recommendations, "
                                "please consult with a healthcare provider who can assess your individual situation. "
                                "Is there general educational information about this topic I can help with?"
                            )
                            break
                    else:
                        break
                else:
                    break
                    
            except Exception as e:
                if attempt == max_retries:
                    response = (
                        "I apologize, but I'm having trouble generating a response right now. "
                        "Please try rephrasing your question, or consult with a healthcare provider "
                        "for personalized guidance."
                    )
                    metadata['error'] = str(e)
                    break
                else:
                    continue
        
        # 10. Strip markdown formatting from response
        response = self._strip_markdown(response)
        
        # 11b. Append Red Flag warning if needed
        if red_flags:
            red_flag_warning = self.safety_layer.get_red_flag_response(red_flags)
            # Avoid duplicate emojis or redundant text if possible
            response = f"{response}\n\n{red_flag_warning}"
            
        # 11c. Add final response to conversation
        self.conversation_manager.add_message('assistant', response)
        
        # 12. UPDATE USER PROFILE (Proactive Memory)
        # We run this after the response is ready to improve context for the NEXT turn
        # In a real high-traffic app, this would be a background task
        asyncio.create_task(self._update_user_profile())
        
        return response, metadata
    
    async def _update_user_profile(self):
        """
        Internal method to extract user health facts from the conversation history.
        Updates the conversation_manager.user_context dictionary.
        """
        try:
            # Only summarize if there's history
            if not self.conversation_manager.messages:
                return
                
            # Construct a prompt for extraction
            history = ""
            for m in self.conversation_manager.messages[-6:]: # Last 3 turns
                history += f"{m.role.upper()}: {m.content}\n"
                
            extraction_prompt = f"""Extract key health facts from this conversation as a JSON object.
Focus on: age, current symptoms, duration of symptoms, life stage (menopause, pregnancy, etc.), and health goals.
If a value is unknown, do NOT include it.
If a value is updated (like a new symptom), capture the latest state.

Recent conversation:
{history}

Respond ONLY with valid JSON."""

            completion = await self.client.chat.completions.create(
                model=self.enforcer_model, # Use the smaller/cheaper model for extraction
                messages=[{"role": "system", "content": "You are a health data extractor. Output ONLY JSON."},
                          {"role": "user", "content": extraction_prompt}],
                temperature=0.0,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            raw_json = completion.choices[0].message.content.strip()
            new_facts = json.loads(raw_json)
            
            # Merge into user_context
            for key, value in new_facts.items():
                if value and value != "unknown":
                    self.conversation_manager.update_user_context(key, value)
                    print(f"🧠 [MEMORY] Extracted fact: {key} = {value}")
                    
        except Exception as e:
            print(f"⚠️ [MEMORY] Failed to update user profile: {e}")

    def clear_conversation(self):
        """Clear conversation history."""
        self.conversation_manager.clear()
    
    def get_conversation_summary(self) -> Optional[str]:
        """Get current conversation summary."""
        return self.conversation_manager.conversation_summary
