"""
Process and Save Chunks Script

Simple script to process all women's health data and save chunks locally.
Run this before uploading to Pinecone.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_processing.processor import process_all_files


def main():
    """Process all data files and save chunks."""
    
    # Load environment variables
    load_dotenv()
    
    # Get OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        return
    
    print("="*60)
    print("WOMEN'S HEALTH DATA CHUNKING")
    print("="*60)
    print()
    
    # Define paths
    data_dir = "data/processed"
    output_dir = "data/chunked"
    
    print(f"📁 Input directory: {data_dir}")
    print(f"💾 Output directory: {output_dir}")
    print()
    
    # Check if input directory exists
    if not Path(data_dir).exists():
        print(f"❌ Error: Input directory not found: {data_dir}")
        return
    
    # Process all files
    print("🚀 Starting processing...")
    print()
    
    try:
        stats = process_all_files(data_dir, output_dir, api_key)
        
        print()
        print("="*60)
        print("✅ PROCESSING COMPLETE!")
        print("="*60)
        print()
        print(f"📊 Results:")
        print(f"   • Files processed: {stats.total_files_processed}")
        print(f"   • Entries processed: {stats.total_entries_processed}")
        print(f"   • Chunks created: {stats.total_chunks_created}")
        print(f"   • Average chunks per entry: {stats.average_chunks_per_entry:.2f}")
        print(f"   • Average chunk size: {stats.average_chunk_size_tokens:.0f} tokens")
        print()
        
        if stats.files_with_errors:
            print(f"⚠️  Files with errors: {len(stats.files_with_errors)}")
            for file in stats.files_with_errors:
                print(f"   - {file}")
            print()
        
        if stats.warnings:
            print(f"⚠️  Total warnings: {len(stats.warnings)}")
            if len(stats.warnings) <= 10:
                for warning in stats.warnings:
                    print(f"   - {warning}")
            else:
                print(f"   (First 10 warnings shown)")
                for warning in stats.warnings[:10]:
                    print(f"   - {warning}")
            print()
        
        print(f"💾 Chunks saved to: {output_dir}/all_chunks.json")
        print(f"📈 Statistics saved to: {output_dir}/processing_stats.json")
        print()
        print("✨ Next step: Upload chunks to Pinecone vector database")
        print()
        
    except Exception as e:
        print()
        print("="*60)
        print("❌ ERROR OCCURRED")
        print("="*60)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
