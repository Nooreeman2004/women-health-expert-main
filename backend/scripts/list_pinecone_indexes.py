"""
List Pinecone Indexes Script

Lists all existing indexes in your Pinecone account to help decide which to use or delete.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pinecone import Pinecone

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """List all Pinecone indexes."""
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    api_key = os.getenv("PINECONE_API_KEY")
    
    if not api_key:
        print("❌ Error: PINECONE_API_KEY not found in .env file")
        return
    
    print("="*60)
    print("PINECONE INDEXES")
    print("="*60)
    print()
    
    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=api_key)
        
        # List all indexes
        indexes = pc.list_indexes()
        
        if not indexes:
            print("📭 No indexes found in your Pinecone account")
            print()
            print("✨ You can create a new index by running:")
            print("   python scripts\\upload_to_pinecone.py")
            return
        
        print(f"📊 Found {len(indexes)} index(es):")
        print()
        
        for idx, index_info in enumerate(indexes, 1):
            print(f"{idx}. {index_info.name}")
            print(f"   Dimension: {index_info.dimension}")
            print(f"   Metric: {index_info.metric}")
            print(f"   Status: {index_info.status.state}")
            
            # Get index stats
            try:
                index = pc.Index(index_info.name)
                stats = index.describe_index_stats()
                print(f"   Vector count: {stats.get('total_vector_count', 0)}")
            except:
                print(f"   Vector count: Unable to fetch")
            
            print()
        
        print("="*60)
        print()
        print("💡 Options:")
        print("   1. Delete an unused index from Pinecone console")
        print("   2. Use an existing index (update PINECONE_INDEX_NAME in .env)")
        print("   3. Use namespaces in an existing index")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
