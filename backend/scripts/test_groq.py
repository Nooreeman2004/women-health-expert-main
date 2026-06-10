"""
Test Groq Cloud Integration

Simple test to verify Groq API is working correctly.
"""

import os
import asyncio
from dotenv import load_dotenv
from groq import AsyncGroq

# Load environment variables
load_dotenv()

async def test_groq_connection():
    """Test basic Groq API connection."""
    print("Testing Groq Cloud connection...")
    
    # Get API key
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("❌ Error: GROQ_API_KEY not found in environment variables")
        return False
    
    print(f"✓ GROQ_API_KEY found")
    
    # Initialize client
    try:
        client = AsyncGroq(api_key=api_key)
        print("✓ Groq client initialized")
    except Exception as e:
        print(f"❌ Error initializing Groq client: {e}")
        return False
    
    # Test chat completion
    try:
        model = os.getenv('GROQ_GENERATION_MODEL', 'openai/gpt-oss-20b')
        print(f"✓ Using model: {model}")
        
        completion = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": "Say 'Hello, Groq!' in one sentence."
                }
            ],
            temperature=0.7,
            max_tokens=50
        )
        
        response = completion.choices[0].message.content.strip()
        print(f"✓ Response received: {response}")
        print("\n✅ Groq Cloud integration test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Error during chat completion: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_groq_connection())
    exit(0 if success else 1)
