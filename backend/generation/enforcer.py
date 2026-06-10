"""
Enforcer Model

Uses a separate LLM to validate responses for safety compliance.
Acts as a final check before sending responses to users.
"""

import os
from typing import Dict, List, Optional, Tuple
from groq import AsyncGroq


class Enforcer:
    """
    LLM-based enforcer for response validation.
    """
    
    ENFORCER_PROMPT = """You are a safety enforcer for a women's health chatbot.

Your job is to review responses and check for violations of these rules:

CRITICAL VIOLATIONS (Response must be rejected):
1. Mentions specific medicine/drug names (painkillers, antibiotics, hormones, brand names)
   - Allowed: General supplement names (Vitamin D, Calcium, Magnesium, etc.)
   - NOT allowed: Ibuprofen, Tylenol, Premarin, Prozac, etc.

2. Provides diagnosis ("you have X disease", "this is Y condition")
   - Allowed: "This can be associated with...", "Some people experience..."
   - NOT allowed: "You have endometriosis", "This is PCOS"

3. Gives specific dosages without clear "informational only" context
   - Allowed: "Typically 1000-2000 IU daily (informational only)"
   - NOT allowed: "Take 500mg twice daily"

4. Uses markdown formatting (CRITICAL - MUST REJECT):
   - NOT allowed: **bold text**, *italic text*, ### headings, | tables |, --- horizontal rules
   - NOT allowed: Any asterisks (*), hashtags (#), pipes (|), or underscores (_) for formatting
   - Allowed: Plain text with numbered lists (1. 2. 3.)
   - Check carefully for ANY asterisks, hashtags, pipes, or table formatting

MEDIUM VIOLATIONS (Warning, but may be acceptable):
5. Uses absolute statements without nuance
6. Provides treatment plans instead of educational information

Review the response below and respond with:

SAFE - if no critical violations
UNSAFE - if critical violations found (including markdown formatting)

Then list any violations found. Be especially strict about markdown formatting.

Response to review:
{response}

Your assessment:"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-oss-20b"
    ):
        """
        Initialize enforcer.
        
        Args:
            api_key: Groq API key
            model: Model to use for enforcement
        """
        self.client = AsyncGroq(api_key=api_key)
        self.model = model
    
    async def validate_response(
        self,
        response: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate response using enforcer model.
        
        Args:
            response: Generated response to validate
            
        Returns:
            Tuple of (is_safe, violation_message)
        """
        try:
            # Call enforcer model
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a safety enforcer. Be strict but fair."
                    },
                    {
                        "role": "user",
                        "content": self.ENFORCER_PROMPT.format(response=response)
                    }
                ],
                temperature=0.0,  # Deterministic
                max_tokens=500
            )
            
            assessment = completion.choices[0].message.content.strip()
            
            # Parse assessment
            is_safe = assessment.upper().startswith('SAFE')
            
            violation_message = None
            if not is_safe:
                # Extract violation details
                violation_message = assessment
            
            return is_safe, violation_message
            
        except Exception as e:
            # On error, be conservative and reject
            return False, f"Enforcer error: {str(e)}"
    
    async def suggest_fix(
        self,
        original_response: str,
        violation_message: str
    ) -> str:
        """
        Suggest a fixed version of the response.
        
        Args:
            original_response: Original unsafe response
            violation_message: What was wrong
            
        Returns:
            Suggested safe response
        """
        try:
            fix_prompt = f"""The following response violated safety rules:

Original response:
{original_response}

Violations:
{violation_message}

Please rewrite this response to be safe while maintaining helpfulness:
- Remove any medicine names (keep supplements OK)
- Remove diagnosis language
- Remove specific dosages
- Keep educational value
- Maintain empathy
- CRITICAL: Remove ALL markdown formatting (no asterisks, hashtags, pipes, tables, or underscores)
- Use ONLY plain text with numbered lists (1. 2. 3.) when needed
- Write in a conversational, natural style

Safe rewrite:"""
            
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are helping fix unsafe health responses."
                    },
                    {
                        "role": "user",
                        "content": fix_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            fixed_response = completion.choices[0].message.content.strip()
            return fixed_response
            
        except Exception as e:
            # Return a safe fallback
            return (
                "I apologize, but I need to be more careful with my response. "
                "For specific treatment recommendations, please consult with a "
                "healthcare provider who can assess your individual situation. "
                "Is there general educational information about this topic I can help with?"
            )
