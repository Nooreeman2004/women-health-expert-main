"""
Test Generation System

Tests the complete generation pipeline with sample conversations.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generation import Generator
from retrieval import ProductionRetriever


async def test_basic_conversation():
    """Test basic conversation flow."""
    print("="*60)
    print("TEST 1: Basic Conversation")
    print("="*60)
    print()
    
    # Load environment
    load_dotenv()
    
    # Initialize retriever
    retriever = ProductionRetriever(
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_index_name=os.getenv('PINECONE_INDEX_NAME'),
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    
    # Initialize generator
    generator = Generator(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        retriever=retriever
    )
    
    # Test conversation
    messages = [
        "I've been having hot flashes for the past 2 months",
        "They happen about 5-6 times a day and are really affecting my work",
        "What can I do about them?"
    ]
    
    for i, msg in enumerate(messages, 1):
        print(f"User: {msg}")
        response, metadata = await generator.generate_response(msg)
        print(f"\nAssistant: {response}")
        print(f"\nMetadata: {metadata}")
        print("\n" + "-"*60 + "\n")
    
    generator.clear_conversation()


async def test_red_flag_detection():
    """Test red flag detection."""
    print("="*60)
    print("TEST 2: Red Flag Detection")
    print("="*60)
    print()
    
    load_dotenv()
    
    generator = Generator(
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    
    # Test red flag message
    msg = "I've been bleeding even though my periods stopped over a year ago"
    print(f"User: {msg}")
    response, metadata = await generator.generate_response(msg, use_rag=False)
    print(f"\nAssistant: {response}")
    print(f"\nRed Flags Detected: {metadata['red_flags_detected']}")
    print("\n" + "-"*60 + "\n")
    
    generator.clear_conversation()


async def test_clarification():
    """Test clarification logic."""
    print("="*60)
    print("TEST 3: Clarification Logic")
    print("="*60)
    print()
    
    load_dotenv()
    
    generator = Generator(
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    
    # Vague message
    msg = "I don't feel well"
    print(f"User: {msg}")
    response, metadata = await generator.generate_response(msg, use_rag=False)
    print(f"\nAssistant: {response}")
    print(f"\nClarification Needed: {metadata['clarification_needed']}")
    print("\n" + "-"*60 + "\n")
    
    generator.clear_conversation()


async def test_rag_integration():
    """Test RAG integration."""
    print("="*60)
    print("TEST 4: RAG Integration")
    print("="*60)
    print()
    
    load_dotenv()
    
    # Initialize retriever
    retriever = ProductionRetriever(
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_index_name=os.getenv('PINECONE_INDEX_NAME'),
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    
    generator = Generator(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        retriever=retriever
    )
    
    # Query that should use RAG
    msg = "What are the benefits of hormone replacement therapy?"
    print(f"User: {msg}")
    response, metadata = await generator.generate_response(msg, use_rag=True)
    print(f"\nAssistant: {response}")
    print(f"\nRAG Used: {metadata['rag_used']}")
    print(f"\nEnforcer Used: {metadata['enforcer_used']}")
    print("\n" + "-"*60 + "\n")
    
    generator.clear_conversation()


async def main():
    """Run all tests."""
    print("\n🧪 GENERATION SYSTEM TESTS\n")
    
    try:
        await test_basic_conversation()
        await test_red_flag_detection()
        await test_clarification()
        await test_rag_integration()
        
        print("="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
