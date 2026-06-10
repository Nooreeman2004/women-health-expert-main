"""
Generate and Save Embeddings Script

Generates vector embeddings for all text chunks using OpenAI's embedding API
and saves them locally for future use.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from embeddings.generate_embeddings import EmbeddingGenerator, load_chunks


def main():
    """Generate embeddings for all chunks and save locally."""
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
    dimensions = int(os.getenv("OPENAI_EMBEDDING_DIMENSIONS", "3072"))
    batch_size = int(os.getenv("BATCH_SIZE", "100"))
    max_retries = int(os.getenv("MAX_RETRIES", "3"))
    
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        return
    
    print("="*60)
    print("WOMEN'S HEALTH DATA - EMBEDDING GENERATION")
    print("="*60)
    print()
    
    # Define paths
    chunks_path = "data/chunked/all_chunks.json"
    output_path = "data/embeddings_data/embeddings.json"
    checkpoint_dir = "data/embeddings_data/checkpoints"
    
    print(f"📁 Input file: {chunks_path}")
    print(f"💾 Output file: {output_path}")
    print(f"📂 Checkpoint directory: {checkpoint_dir}")
    print()
    
    # Check if input file exists
    if not Path(chunks_path).exists():
        print(f"❌ Error: Input file not found: {chunks_path}")
        return
    
    # Load chunks
    try:
        chunks = load_chunks(chunks_path)
    except Exception as e:
        print(f"❌ Error loading chunks: {e}")
        return
    
    # Initialize generator
    print(f"\n🔧 Initializing embedding generator...")
    print(f"   Model: {model}")
    print(f"   Dimensions: {dimensions}")
    print(f"   Batch size: {batch_size}")
    print(f"   Max retries: {max_retries}")
    
    generator = EmbeddingGenerator(
        api_key=api_key,
        model=model,
        dimensions=dimensions,
        batch_size=batch_size,
        max_retries=max_retries
    )
    
    # Generate embeddings
    try:
        result = generator.process_all_chunks(
            chunks=chunks,
            output_path=output_path,
            checkpoint_dir=checkpoint_dir
        )
        
        # Print statistics
        generator.print_statistics(result)
        
        print(f"💾 Embeddings saved to: {output_path}")
        print(f"📂 Checkpoints saved to: {checkpoint_dir}")
        print()
        print("✨ Next step: Upload embeddings to Pinecone vector database")
        print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        print(f"   Checkpoints saved in: {checkpoint_dir}")
        print("   You can resume by running this script again")
        
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
