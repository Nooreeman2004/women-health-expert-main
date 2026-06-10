"""
Pinecone Vector Store Client

Handles uploading and managing vectors in Pinecone database.
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from pinecone import Pinecone, ServerlessSpec


class PineconeVectorStore:
    """Client for interacting with Pinecone vector database."""
    
    def __init__(
        self,
        api_key: str,
        environment: str,
        index_name: str,
        dimension: int = 3072,
        metric: str = "cosine",
        batch_size: int = 100
    ):
        """
        Initialize Pinecone client.
        
        Args:
            api_key: Pinecone API key
            environment: Pinecone environment
            index_name: Name of the index to use
            dimension: Dimension of vectors
            metric: Distance metric (cosine, euclidean, dotproduct)
            batch_size: Number of vectors to upload per batch
        """
        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self.dimension = dimension
        self.metric = metric
        self.batch_size = batch_size
        
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=api_key)
        
        # Statistics
        self.total_vectors = 0
        self.uploaded_vectors = 0
        self.failed_vectors = []
        self.start_time = None
    
    def create_index_if_not_exists(self):
        """Create Pinecone index if it doesn't exist."""
        existing_indexes = [index.name for index in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            print(f"📝 Creating new index: {self.index_name}")
            print(f"   Dimension: {self.dimension}")
            print(f"   Metric: {self.metric}")
            
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric=self.metric,
                spec=ServerlessSpec(
                    cloud='aws',
                    region=self.environment
                )
            )
            
            # Wait for index to be ready
            print("   Waiting for index to be ready...")
            time.sleep(5)
            print("   ✓ Index created successfully")
        else:
            print(f"✓ Index '{self.index_name}' already exists")
    
    def get_index(self):
        """Get the Pinecone index."""
        return self.pc.Index(self.index_name)
    
    def prepare_vectors(self, embeddings: List[Dict[str, Any]]) -> List[tuple]:
        """
        Prepare vectors for upload to Pinecone.
        
        Args:
            embeddings: List of embedding dictionaries
            
        Returns:
            List of tuples (id, vector, metadata)
        """
        vectors = []
        
        for emb in embeddings:
            chunk_id = emb.get("chunk_id")
            vector = emb.get("embedding")
            metadata = emb.get("metadata", {})
            
            # Add text to metadata for retrieval
            metadata["text"] = emb.get("text", "")
            
            # Ensure metadata values are JSON serializable
            clean_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    clean_metadata[key] = value
                elif isinstance(value, list):
                    # Convert lists to comma-separated strings
                    clean_metadata[key] = ", ".join(str(v) for v in value)
                elif value is None:
                    clean_metadata[key] = ""
                else:
                    clean_metadata[key] = str(value)
            
            vectors.append((chunk_id, vector, clean_metadata))
        
        return vectors
    
    def upload_batch(self, index, vectors: List[tuple]) -> int:
        """
        Upload a batch of vectors to Pinecone.
        
        Args:
            index: Pinecone index
            vectors: List of (id, vector, metadata) tuples
            
        Returns:
            Number of successfully uploaded vectors
        """
        try:
            index.upsert(vectors=vectors)
            return len(vectors)
        except Exception as e:
            print(f"❌ Error uploading batch: {e}")
            # Try uploading one by one to identify failures
            success_count = 0
            for vec_id, vector, metadata in vectors:
                try:
                    index.upsert(vectors=[(vec_id, vector, metadata)])
                    success_count += 1
                except Exception as e:
                    print(f"   Failed to upload {vec_id}: {e}")
                    self.failed_vectors.append(vec_id)
            return success_count
    
    def upload_embeddings(
        self,
        embeddings: List[Dict[str, Any]],
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Upload all embeddings to Pinecone.
        
        Args:
            embeddings: List of embedding dictionaries
            show_progress: Whether to show progress updates
            
        Returns:
            Dictionary with upload statistics
        """
        self.total_vectors = len(embeddings)
        self.uploaded_vectors = 0
        self.failed_vectors = []
        self.start_time = time.time()
        
        print(f"\n🚀 Starting upload to Pinecone")
        print(f"   Index: {self.index_name}")
        print(f"   Total vectors: {self.total_vectors}")
        print(f"   Batch size: {self.batch_size}")
        print()
        
        # Get index
        index = self.get_index()
        
        # Prepare vectors
        print("📦 Preparing vectors...")
        vectors = self.prepare_vectors(embeddings)
        print(f"   ✓ Prepared {len(vectors)} vectors")
        print()
        
        # Upload in batches
        for i in range(0, len(vectors), self.batch_size):
            batch_num = i // self.batch_size + 1
            total_batches = (len(vectors) + self.batch_size - 1) // self.batch_size
            
            batch = vectors[i:i + self.batch_size]
            
            if show_progress:
                print(f"📤 Uploading batch {batch_num}/{total_batches} ({len(batch)} vectors)...")
            
            success_count = self.upload_batch(index, batch)
            self.uploaded_vectors += success_count
            
            if show_progress:
                elapsed = time.time() - self.start_time
                rate = self.uploaded_vectors / elapsed if elapsed > 0 else 0
                remaining = (self.total_vectors - self.uploaded_vectors) / rate if rate > 0 else 0
                print(f"   ✓ Uploaded {success_count}/{len(batch)} vectors")
                print(f"   Progress: {self.uploaded_vectors}/{self.total_vectors} "
                      f"({self.uploaded_vectors/self.total_vectors*100:.1f}%) - "
                      f"Est. remaining: {remaining:.1f}s")
            
            # Small delay between batches
            if i + self.batch_size < len(vectors):
                time.sleep(0.5)
        
        # Get final index stats
        print("\n📊 Fetching index statistics...")
        time.sleep(2)  # Wait for index to update
        stats = index.describe_index_stats()
        
        elapsed_time = time.time() - self.start_time
        
        result = {
            "index_name": self.index_name,
            "total_vectors": self.total_vectors,
            "uploaded_vectors": self.uploaded_vectors,
            "failed_vectors": len(self.failed_vectors),
            "failed_vector_ids": self.failed_vectors,
            "index_total_count": stats.get('total_vector_count', 0),
            "processing_time_seconds": elapsed_time,
            "uploaded_at": datetime.now().isoformat()
        }
        
        return result
    
    def print_statistics(self, result: Dict[str, Any]):
        """
        Print upload statistics.
        
        Args:
            result: Result dictionary from upload_embeddings
        """
        print("\n" + "="*60)
        print("✅ UPLOAD TO PINECONE COMPLETE!")
        print("="*60)
        print()
        print(f"📊 Statistics:")
        print(f"   • Index: {result['index_name']}")
        print(f"   • Total vectors: {result['total_vectors']}")
        print(f"   • Successfully uploaded: {result['uploaded_vectors']}")
        print(f"   • Failed: {result['failed_vectors']}")
        print(f"   • Index total count: {result['index_total_count']}")
        print(f"   • Upload time: {result['processing_time_seconds']:.2f} seconds")
        print()
        
        if result['failed_vectors'] > 0:
            print(f"⚠️  Failed vector IDs:")
            for vec_id in result['failed_vector_ids'][:10]:
                print(f"   - {vec_id}")
            if len(result['failed_vector_ids']) > 10:
                print(f"   ... and {len(result['failed_vector_ids']) - 10} more")
            print()
    
    def query(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query the index for similar vectors.
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filter: Metadata filter
            include_metadata: Whether to include metadata in results
            
        Returns:
            List of matching results
        """
        index = self.get_index()
        
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            filter=filter,
            include_metadata=include_metadata
        )
        
        return results.get('matches', [])
    
    def delete_all(self):
        """Delete all vectors from the index."""
        index = self.get_index()
        index.delete(delete_all=True)
        print(f"✓ Deleted all vectors from index '{self.index_name}'")


def load_embeddings(embeddings_path: str) -> List[Dict[str, Any]]:
    """
    Load embeddings from JSON file.
    
    Args:
        embeddings_path: Path to embeddings JSON file
        
    Returns:
        List of embedding dictionaries
    """
    print(f"📂 Loading embeddings from {embeddings_path}...")
    
    with open(embeddings_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    embeddings = data.get('embeddings', [])
    print(f"   ✓ Loaded {len(embeddings)} embeddings")
    
    return embeddings
