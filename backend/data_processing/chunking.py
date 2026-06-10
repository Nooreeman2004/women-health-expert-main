"""
Semantic Chunking Engine for Women's Health Data

Processes JSON entries into semantically coherent chunks with rich metadata.
Uses LangChain's SemanticChunker for natural topic boundaries.
"""

import os
from typing import List, Dict, Any, Tuple
from pathlib import Path

from langchain_experimental.text_splitter import SemanticChunker
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

from .utils import (
    count_tokens,
    generate_chunk_id,
    extract_content_type,
    map_severity_to_urgency,
    determine_audience,
    should_add_disclaimer,
    create_context_header,
    load_json_file,
)
from .metadata_schema import ChunkMetadata


# Constants
TARGET_CHUNK_SIZE = 400  # tokens
MIN_CHUNK_SIZE = 50  # tokens (reduced from 100 to capture more content)
MAX_CHUNK_SIZE = 600  # tokens (increased from 500 for better context)
CHUNK_OVERLAP = 100  # tokens

MEDICAL_DISCLAIMER = (
    "This is educational information. "
    "Consult a healthcare provider for personalized medical advice."
)


class SemanticChunkingEngine:
    """Engine for semantically chunking women's health data."""
    
    def __init__(self, openai_api_key: str = None):
        """
        Initialize the chunking engine.
        
        Args:
            openai_api_key: OpenAI API key (if not set in environment)
        """
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Initialize semantic splitter
        self.semantic_splitter = SemanticChunker(
            OpenAIEmbeddings(model="text-embedding-3-small"),
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=75
        )
        
        # Initialize fallback recursive splitter
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=TARGET_CHUNK_SIZE * 4,  # Approximate character count
            chunk_overlap=CHUNK_OVERLAP * 4,
            length_function=count_tokens,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def chunk_entry(
        self, 
        entry: Dict[str, Any], 
        file_metadata: Dict[str, Any],
        source_file: str
    ) -> List[Dict[str, Any]]:
        """
        Chunk a single JSON entry into semantically coherent pieces.
        
        Args:
            entry: The entry dictionary from JSON
            file_metadata: Metadata from the parent JSON file
            source_file: Relative path to source JSON file
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        # Extract text content
        text_content = self._extract_text_content(entry)
        
        if not text_content or len(text_content.strip()) < 30:
            return []  # Skip empty or very short entries
        
        # Perform semantic chunking
        chunks = self._split_text(text_content)
        
        # Create chunk objects with metadata
        chunk_objects = []
        total_chunks = len(chunks)
        
        for idx, chunk_text in enumerate(chunks):
            # Validate chunk size
            token_count = count_tokens(chunk_text)
            if token_count < MIN_CHUNK_SIZE:
                continue  # Skip chunks that are too small
            
            # Add context header for multi-chunk entries
            context_header = create_context_header(entry, idx, total_chunks)
            if context_header:
                chunk_text = context_header + chunk_text
            
            # Determine metadata
            chunk_id = generate_chunk_id(entry.get("id", "unknown"), idx)
            content_type = extract_content_type(source_file, entry)
            urgency_level = map_severity_to_urgency(entry.get("severity", "n/a"))
            audience = determine_audience(entry)
            requires_disclaimer = should_add_disclaimer(entry, urgency_level)
            
            # Add medical disclaimer if needed
            if requires_disclaimer:
                chunk_text = f"{chunk_text}\n\n{MEDICAL_DISCLAIMER}"
            
            # Create metadata object
            metadata = ChunkMetadata(
                id=entry.get("id", "unknown"),
                title=entry.get("title", entry.get("question", "")),
                category=file_metadata.get("category", "general"),
                subcategory=file_metadata.get("subcategory", ""),
                tags=entry.get("tags", []),
                related_topics=entry.get("related_topics", []),
                severity=entry.get("severity", "n/a"),
                content_type=content_type,
                urgency_level=urgency_level,
                chunk_index=idx,
                total_chunks=total_chunks,
                source_file=source_file,
                last_updated=file_metadata.get("last_updated", ""),
                audience=audience,
                requires_disclaimer=requires_disclaimer,
                chunk_id=chunk_id
            )
            
            chunk_objects.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "metadata": metadata.model_dump()
            })
        
        return chunk_objects
    
    def _extract_text_content(self, entry: Dict[str, Any]) -> str:
        """
        Extract and combine text content from an entry.
        Recursively processes nested structures to ensure no content is skipped.
        
        Args:
            entry: The entry dictionary
            
        Returns:
            Combined text content
        """
        parts = []
        
        # Add title
        if "title" in entry and entry["title"]:
            parts.append(f"# {entry['title']}\n")
        
        # Add question for FAQ entries
        if "question" in entry and entry["question"]:
            parts.append(f"**Q: {entry['question']}**\n")
        
        # Add description if present
        if "description" in entry and entry["description"]:
            parts.append(f"{entry['description']}\n")
        
        # Add main content
        if "content" in entry and entry["content"]:
            parts.append(entry["content"])
        
        # Add answer for FAQ entries
        if "answer" in entry and entry["answer"]:
            parts.append(f"\n**A:** {entry['answer']}")
        
        # Process all other fields recursively
        # Skip metadata fields that don't contain useful content
        skip_fields = {
            'id', 'title', 'description', 'content', 'answer', 'question',
            'tags', 'related_topics', 'severity', 'category', 'subcategory',
            'last_updated', 'version'
        }
        
        for key, value in entry.items():
            if key in skip_fields or value is None:
                continue
            
            # Format the field name nicely
            field_name = key.replace('_', ' ').title()
            
            # Process based on type
            if isinstance(value, list) and len(value) > 0:
                parts.append(f"\n\n**{field_name}:**")
                parts.extend(self._format_list(value))
            elif isinstance(value, dict) and len(value) > 0:
                parts.append(f"\n\n**{field_name}:**")
                parts.extend(self._format_dict(value))
            elif isinstance(value, str) and value.strip():
                parts.append(f"\n\n**{field_name}:** {value}")
        
        return "\n".join(parts)
    
    def _format_list(self, items: list, indent: int = 0) -> list:
        """
        Format a list of items into readable text.
        
        Args:
            items: List to format
            indent: Indentation level
            
        Returns:
            List of formatted strings
        """
        formatted = []
        prefix = "  " * indent
        
        for item in items:
            if isinstance(item, dict):
                # Handle dictionary items in list
                for key, value in item.items():
                    field_name = key.replace('_', ' ').title()
                    if isinstance(value, list):
                        formatted.append(f"{prefix}- **{field_name}:**")
                        formatted.extend(self._format_list(value, indent + 1))
                    elif isinstance(value, dict):
                        formatted.append(f"{prefix}- **{field_name}:**")
                        formatted.extend(self._format_dict(value, indent + 1))
                    elif value:
                        formatted.append(f"{prefix}- **{field_name}:** {value}")
            elif isinstance(item, str) and item.strip():
                formatted.append(f"{prefix}- {item}")
        
        return formatted
    
    def _format_dict(self, data: dict, indent: int = 0) -> list:
        """
        Format a dictionary into readable text.
        
        Args:
            data: Dictionary to format
            indent: Indentation level
            
        Returns:
            List of formatted strings
        """
        formatted = []
        prefix = "  " * indent
        
        for key, value in data.items():
            field_name = key.replace('_', ' ').title()
            
            if isinstance(value, list) and len(value) > 0:
                formatted.append(f"{prefix}- **{field_name}:**")
                formatted.extend(self._format_list(value, indent + 1))
            elif isinstance(value, dict) and len(value) > 0:
                formatted.append(f"{prefix}- **{field_name}:**")
                formatted.extend(self._format_dict(value, indent + 1))
            elif value:
                formatted.append(f"{prefix}- **{field_name}:** {value}")
        
        return formatted
    
    def _split_text(self, text: str) -> List[str]:
        """
        Split text into chunks using semantic chunking with fallback.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        try:
            # Try semantic chunking first
            chunks = self.semantic_splitter.split_text(text)
            
            # Check if any chunks are too large
            final_chunks = []
            for chunk in chunks:
                token_count = count_tokens(chunk)
                
                if token_count > MAX_CHUNK_SIZE:
                    # Use recursive splitter for oversized chunks
                    sub_chunks = self.recursive_splitter.split_text(chunk)
                    final_chunks.extend(sub_chunks)
                else:
                    final_chunks.append(chunk)
            
            return final_chunks
            
        except Exception as e:
            print(f"Semantic chunking failed: {e}. Falling back to recursive splitter.")
            # Fallback to recursive splitter
            return self.recursive_splitter.split_text(text)
    
    def process_json_file(self, file_path: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Process an entire JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Tuple of (list of chunks, list of errors)
        """
        errors = []
        all_chunks = []
        
        # Load JSON file
        data = load_json_file(file_path)
        if not data:
            errors.append(f"Failed to load {file_path}")
            return all_chunks, errors
        
        # Extract file metadata
        file_metadata = {
            "category": data.get("category", "general"),
            "subcategory": data.get("subcategory", ""),
            "last_updated": data.get("last_updated", ""),
            "description": data.get("description", "")
        }
        
        # Get relative path for source_file
        try:
            source_file = str(Path(file_path).relative_to(Path(file_path).parents[1]))
        except:
            source_file = Path(file_path).name
        
        # Process each entry
        entries = data.get("entries", [])
        for entry in entries:
            try:
                chunks = self.chunk_entry(entry, file_metadata, source_file)
                all_chunks.extend(chunks)
            except Exception as e:
                error_msg = f"Error processing entry {entry.get('id', 'unknown')} in {file_path}: {e}"
                errors.append(error_msg)
                print(error_msg)
        
        return all_chunks, errors
    
    def validate_chunk(self, chunk: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a chunk for quality and completeness.
        
        Args:
            chunk: Chunk dictionary
            
        Returns:
            Tuple of (is_valid, list of warnings)
        """
        warnings = []
        
        # Check text is present
        if not chunk.get("text"):
            return False, ["Missing text content"]
        
        # Check token count
        token_count = count_tokens(chunk["text"])
        if token_count < MIN_CHUNK_SIZE:
            warnings.append(f"Chunk too small: {token_count} tokens")
        elif token_count > MAX_CHUNK_SIZE:
            warnings.append(f"Chunk too large: {token_count} tokens")
        
        # Check metadata is present
        if not chunk.get("metadata"):
            return False, ["Missing metadata"]
        
        # Check required metadata fields
        required_fields = ["chunk_id", "category", "content_type", "urgency_level"]
        metadata = chunk["metadata"]
        for field in required_fields:
            if field not in metadata:
                warnings.append(f"Missing metadata field: {field}")
        
        # Valid if no critical errors (only warnings)
        return True, warnings
