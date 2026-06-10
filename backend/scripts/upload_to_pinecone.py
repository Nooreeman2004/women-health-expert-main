"""
Upload Embeddings to Pinecone Script

Uploads all generated embeddings to Pinecone vector database.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from vector_store.pinecone_client import PineconeVectorStore, load_embeddings


def main():
    """Upload embeddings to Pinecone vector database."""
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    api_key = os.getenv("PINECONE_API_KEY")
    environment = os.getenv("PINECONE_ENVIRONMENT")
    index_name = os.getenv("PINECONE_INDEX_NAME")
    dimensions = int(os.getenv("OPENAI_EMBEDDING_DIMENSIONS", "3072"))
    batch_size = int(os.getenv("BATCH_SIZE", "100"))
    
    if not api_key:
        print("❌ Error: PINECONE_API_KEY not found in .env file")
        return
    
    if not environment:
        print("❌ Error: PINECONE_ENVIRONMENT not found in .env file")
        return
    
    if not index_name:
        print("❌ Error: PINECONE_INDEX_NAME not found in .env file")
        return
    
    print("="*60)
    print("WOMEN'S HEALTH DATA - PINECONE UPLOAD")
    print("="*60)
    print()
    
    # Define paths
    embeddings_path = "data/embeddings_data/embeddings.json"
    
    print(f"📁 Embeddings file: {embeddings_path}")
    print(f"🗄️  Pinecone index: {index_name}")
    print(f"🌍 Environment: {environment}")
    print()
    
    # Check if embeddings file exists
    if not Path(embeddings_path).exists():
        print(f"❌ Error: Embeddings file not found: {embeddings_path}")
        print("   Please run generate_and_save_embeddings.py first")
        return
    
    # Load embeddings
    try:
        embeddings = load_embeddings(embeddings_path)
    except Exception as e:
        print(f"❌ Error loading embeddings: {e}")
        return
    
    # Initialize Pinecone client
    print(f"\n🔧 Initializing Pinecone client...")
    print(f"   Index: {index_name}")
    print(f"   Dimensions: {dimensions}")
    print(f"   Batch size: {batch_size}")
    
    try:
        vector_store = PineconeVectorStore(
            api_key=api_key,
            environment=environment,
            index_name=index_name,
            dimension=dimensions,
            metric="cosine",
            batch_size=batch_size
        )
        
        # Create index if it doesn't exist
        print("\n🔍 Checking index...")
        vector_store.create_index_if_not_exists()
        
        # Upload embeddings
        result = vector_store.upload_embeddings(
            embeddings=embeddings,
            show_progress=True
        )
        
        # Print statistics
        vector_store.print_statistics(result)
        
        print("✨ Embeddings are now available in Pinecone for RAG queries!")
        print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Upload interrupted by user")
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ ERROR OCCURRED")
        print("="*60)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
