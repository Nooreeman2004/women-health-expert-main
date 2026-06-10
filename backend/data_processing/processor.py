"""
Main Processing Module for Women's Health Data

Orchestrates the complete data processing pipeline:
1. Discovers all JSON files in the data directory
2. Processes each file through the semantic chunking engine
3. Collects statistics and errors
4. Saves all chunks and statistics to output files
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

from .chunking import SemanticChunkingEngine
from .utils import save_json_file


@dataclass
class ProcessingStats:
    """Statistics from processing all files."""
    total_files_processed: int = 0
    total_entries_processed: int = 0
    total_chunks_created: int = 0
    average_chunks_per_entry: float = 0.0
    average_chunk_size_tokens: float = 0.0
    files_with_errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.files_with_errors is None:
            self.files_with_errors = []
        if self.warnings is None:
            self.warnings = []


def discover_json_files(data_dir: str) -> List[str]:
    """
    Recursively discover all JSON files in the data directory.
    
    Args:
        data_dir: Root directory to search
        
    Returns:
        List of absolute paths to JSON files
    """
    json_files = []
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"❌ Error: Directory does not exist: {data_dir}")
        return json_files
    
    # Recursively find all .json files
    for json_file in data_path.rglob("*.json"):
        if json_file.is_file():
            json_files.append(str(json_file))
    
    return sorted(json_files)


def process_all_files(
    data_dir: str, 
    output_dir: str, 
    openai_api_key: str
) -> ProcessingStats:
    """
    Process all JSON files in the data directory.
    
    Args:
        data_dir: Directory containing JSON files to process
        output_dir: Directory to save output chunks and statistics
        openai_api_key: OpenAI API key for embeddings
        
    Returns:
        ProcessingStats object with processing statistics
    """
    # Initialize statistics
    stats = ProcessingStats()
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Initialize chunking engine
    print("🔧 Initializing semantic chunking engine...")
    engine = SemanticChunkingEngine(openai_api_key=openai_api_key)
    
    # Discover all JSON files
    print(f"\n🔍 Discovering JSON files in {data_dir}...")
    json_files = discover_json_files(data_dir)
    
    if not json_files:
        print(f"⚠️  No JSON files found in {data_dir}")
        return stats
    
    print(f"✅ Found {len(json_files)} JSON files to process")
    print()
    
    # Process each file
    all_chunks = []
    total_token_count = 0
    
    for idx, file_path in enumerate(json_files, 1):
        # Get relative path for display
        try:
            rel_path = Path(file_path).relative_to(Path(data_dir))
        except ValueError:
            rel_path = Path(file_path).name
        
        print(f"📄 [{idx}/{len(json_files)}] Processing: {rel_path}")
        
        try:
            # Process the file
            chunks, errors = engine.process_json_file(file_path)
            
            # Update statistics
            stats.total_files_processed += 1
            
            # Count entries in this file
            with open(file_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                entries_count = len(file_data.get("entries", []))
                stats.total_entries_processed += entries_count
            
            # Add chunks
            all_chunks.extend(chunks)
            stats.total_chunks_created += len(chunks)
            
            # Calculate token counts
            from .utils import count_tokens
            for chunk in chunks:
                total_token_count += count_tokens(chunk["text"])
            
            # Track errors
            if errors:
                stats.files_with_errors.append(str(rel_path))
                stats.warnings.extend(errors)
            
            # Validate chunks
            for chunk in chunks:
                is_valid, warnings = engine.validate_chunk(chunk)
                if warnings:
                    for warning in warnings:
                        stats.warnings.append(f"{rel_path}: {warning}")
            
            print(f"   ✓ Created {len(chunks)} chunks from {entries_count} entries")
            
        except Exception as e:
            error_msg = f"Failed to process {rel_path}: {e}"
            print(f"   ❌ {error_msg}")
            stats.files_with_errors.append(str(rel_path))
            stats.warnings.append(error_msg)
    
    # Calculate averages
    if stats.total_entries_processed > 0:
        stats.average_chunks_per_entry = stats.total_chunks_created / stats.total_entries_processed
    
    if stats.total_chunks_created > 0:
        stats.average_chunk_size_tokens = total_token_count / stats.total_chunks_created
    
    # Save all chunks to a single file
    chunks_file = Path(output_dir) / "all_chunks.json"
    print(f"\n💾 Saving {len(all_chunks)} chunks to {chunks_file}...")
    
    if save_json_file(all_chunks, str(chunks_file), indent=2):
        print(f"   ✓ Chunks saved successfully")
    else:
        print(f"   ❌ Failed to save chunks")
    
    # Save statistics
    stats_file = Path(output_dir) / "processing_stats.json"
    print(f"📊 Saving statistics to {stats_file}...")
    
    stats_dict = asdict(stats)
    if save_json_file(stats_dict, str(stats_file), indent=2):
        print(f"   ✓ Statistics saved successfully")
    else:
        print(f"   ❌ Failed to save statistics")
    
    return stats
