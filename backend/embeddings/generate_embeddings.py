"""
Embedding Generation Module

Generates vector embeddings for text chunks using OpenAI's embedding API.
Implements batch processing, error handling, and incremental saving.
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import openai
from openai import OpenAI


class EmbeddingGenerator:
    """Generate embeddings for text chunks using OpenAI API."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-large",
        dimensions: int = 3072,
        batch_size: int = 100,
        max_retries: int = 3
    ):
        """
        Initialize the embedding generator.
        
        Args:
            api_key: OpenAI API key
            model: Embedding model to use
            dimensions: Embedding dimensions
            batch_size: Number of chunks to process per batch
            max_retries: Maximum number of retries for failed requests
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.dimensions = dimensions
        self.batch_size = batch_size
        self.max_retries = max_retries
        
        # Statistics
        self.total_chunks = 0
        self.processed_chunks = 0
        self.failed_chunks = []
        self.start_time = None
    
    def generate_embedding(self, text: str, retry_count: int = 0) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            retry_count: Current retry attempt
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimensions
            )
            return response.data[0].embedding
            
        except openai.RateLimitError as e:
            if retry_count < self.max_retries:
                wait_time = (2 ** retry_count) * 2  # Exponential backoff
                print(f"⚠️  Rate limit hit. Waiting {wait_time}s before retry {retry_count + 1}/{self.max_retries}...")
                time.sleep(wait_time)
                return self.generate_embedding(text, retry_count + 1)
            else:
                print(f"❌ Failed after {self.max_retries} retries: {e}")
                return None
                
        except openai.APIError as e:
            if retry_count < self.max_retries:
                wait_time = (2 ** retry_count) * 2
                print(f"⚠️  API error. Waiting {wait_time}s before retry {retry_count + 1}/{self.max_retries}...")
                time.sleep(wait_time)
                return self.generate_embedding(text, retry_count + 1)
            else:
                print(f"❌ API error after {self.max_retries} retries: {e}")
                return None
                
        except Exception as e:
            print(f"❌ Unexpected error generating embedding: {e}")
            return None
    
    def generate_embeddings_batch(
        self, 
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for a batch of chunks.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of chunks with embeddings added
        """
        results = []
        
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id", "unknown")
            text = chunk.get("text", "")
            
            if not text:
                print(f"⚠️  Skipping chunk {chunk_id}: No text content")
                self.failed_chunks.append(chunk_id)
                continue
            
            # Generate embedding
            embedding = self.generate_embedding(text)
            
            if embedding is None:
                print(f"❌ Failed to generate embedding for chunk {chunk_id}")
                self.failed_chunks.append(chunk_id)
                continue
            
            # Validate embedding dimensions
            if len(embedding) != self.dimensions:
                print(f"⚠️  Warning: Embedding for {chunk_id} has {len(embedding)} dimensions, expected {self.dimensions}")
            
            # Add embedding to chunk
            result = {
                "chunk_id": chunk_id,
                "text": text,
                "embedding": embedding,
                "metadata": chunk.get("metadata", {})
            }
            results.append(result)
            
            self.processed_chunks += 1
            
            # Progress update
            if self.processed_chunks % 10 == 0:
                elapsed = time.time() - self.start_time
                rate = self.processed_chunks / elapsed if elapsed > 0 else 0
                remaining = (self.total_chunks - self.processed_chunks) / rate if rate > 0 else 0
                print(f"   Progress: {self.processed_chunks}/{self.total_chunks} chunks "
                      f"({self.processed_chunks/self.total_chunks*100:.1f}%) - "
                      f"Est. remaining: {remaining/60:.1f} min")
        
        return results
    
    def process_all_chunks(
        self,
        chunks: List[Dict[str, Any]],
        output_path: str,
        checkpoint_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process all chunks and generate embeddings.
        
        Args:
            chunks: List of all chunks to process
            output_path: Path to save final embeddings
            checkpoint_dir: Optional directory for saving checkpoints
            
        Returns:
            Dictionary with embeddings and statistics
        """
        self.total_chunks = len(chunks)
        self.processed_chunks = 0
        self.failed_chunks = []
        self.start_time = time.time()
        
        print(f"\n🚀 Starting embedding generation for {self.total_chunks} chunks")
        print(f"   Model: {self.model}")
        print(f"   Dimensions: {self.dimensions}")
        print(f"   Batch size: {self.batch_size}")
        print()
        
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(chunks), self.batch_size):
            batch_num = i // self.batch_size + 1
            total_batches = (len(chunks) + self.batch_size - 1) // self.batch_size
            
            batch = chunks[i:i + self.batch_size]
            print(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} chunks)...")
            
            batch_embeddings = self.generate_embeddings_batch(batch)
            all_embeddings.extend(batch_embeddings)
            
            # Save checkpoint
            if checkpoint_dir:
                checkpoint_path = Path(checkpoint_dir) / f"checkpoint_batch_{batch_num}.json"
                checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
                with open(checkpoint_path, 'w', encoding='utf-8') as f:
                    json.dump(batch_embeddings, f, indent=2)
                print(f"   💾 Checkpoint saved: {checkpoint_path}")
            
            # Small delay between batches to avoid rate limits
            if i + self.batch_size < len(chunks):
                time.sleep(1)
        
        # Calculate statistics
        elapsed_time = time.time() - self.start_time
        
        result = {
            "embedding_model": self.model,
            "embedding_dimensions": self.dimensions,
            "total_chunks": self.total_chunks,
            "successful_embeddings": len(all_embeddings),
            "failed_chunks": len(self.failed_chunks),
            "failed_chunk_ids": self.failed_chunks,
            "processing_time_seconds": elapsed_time,
            "generated_at": datetime.now().isoformat(),
            "embeddings": all_embeddings
        }
        
        # Save final results
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\n💾 Saving embeddings to {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        print(f"   ✓ Embeddings saved successfully")
        
        return result
    
    def print_statistics(self, result: Dict[str, Any]):
        """
        Print generation statistics.
        
        Args:
            result: Result dictionary from process_all_chunks
        """
        print("\n" + "="*60)
        print("✅ EMBEDDING GENERATION COMPLETE!")
        print("="*60)
        print()
        print(f"📊 Statistics:")
        print(f"   • Model: {result['embedding_model']}")
        print(f"   • Dimensions: {result['embedding_dimensions']}")
        print(f"   • Total chunks: {result['total_chunks']}")
        print(f"   • Successful: {result['successful_embeddings']}")
        print(f"   • Failed: {result['failed_chunks']}")
        print(f"   • Processing time: {result['processing_time_seconds']/60:.2f} minutes")
        print()
        
        if result['failed_chunks'] > 0:
            print(f"⚠️  Failed chunk IDs:")
            for chunk_id in result['failed_chunk_ids'][:10]:
                print(f"   - {chunk_id}")
            if len(result['failed_chunk_ids']) > 10:
                print(f"   ... and {len(result['failed_chunk_ids']) - 10} more")
            print()


def load_chunks(chunks_path: str) -> List[Dict[str, Any]]:
    """
    Load chunks from JSON file.
    
    Args:
        chunks_path: Path to chunks JSON file
        
    Returns:
        List of chunk dictionaries
    """
    print(f"📂 Loading chunks from {chunks_path}...")
    
    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    print(f"   ✓ Loaded {len(chunks)} chunks")
    return chunks
