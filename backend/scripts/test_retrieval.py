"""
Test Production Retriever

Quick test script for the production retriever with Cohere reranking.
"""

import os
import sys
import asyncio
import time
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from retrieval import ProductionRetriever


async def main():
    """Test the production retriever."""
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not all([pinecone_api_key, pinecone_index_name, openai_api_key]):
        print("❌ Error: Missing required environment variables")
        print("   Required: PINECONE_API_KEY, PINECONE_INDEX_NAME, OPENAI_API_KEY")
        return
    
    print("="*60)
    print("PRODUCTION RETRIEVER TEST")
    print("="*60)
    print()
    
    # Initialize retriever
    print(f"🚀 Initializing production retriever...")
    print(f"   Using lightweight built-in reranking")
    
    retriever = ProductionRetriever(
        pinecone_api_key=pinecone_api_key,
        pinecone_index_name=pinecone_index_name,
        openai_api_key=openai_api_key
    )
    print("✓ Retriever ready")
    print()
    
    # Test queries
    test_queries = [
        "What are the symptoms of menopause?",
        "How to manage hot flashes?",
        "Is hormone replacement therapy safe?",
    ]
    
    total_time = 0
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {query}")
        print('='*60)
        
        # Time the retrieval
        start_time = time.time()
        
        results = await retriever.retrieve(
            query=query,
            top_k=5,
            initial_k=10,
            verbose=True
        )
        
        elapsed = time.time() - start_time
        total_time += elapsed
        
        print(f"\n⚡ Retrieved in {elapsed:.2f} seconds")
        print(f"✅ Got {len(results)} results\n")
        
        # Display top 3 results
        for j, result in enumerate(results[:3], 1):
            print(f"{j}. {result.chunk_id}")
            print(f"   Semantic: {result.score:.3f}", end="")
            if result.rerank_score is not None:
                print(f" | Rerank: {result.rerank_score:.3f}")
            else:
                print()
            print(f"   {result.text[:150]}...")
            print()
    
    print("="*60)
    print(f"✅ ALL TESTS COMPLETED")
    print(f"⚡ Total time: {total_time:.2f} seconds")
    print(f"⚡ Average per query: {total_time/3:.2f} seconds")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
