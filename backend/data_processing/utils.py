"""
Utility Functions for Data Processing

Helper functions for token counting, ID generation, and data transformation.
"""

import json
import tiktoken
from pathlib import Path
from typing import Dict, Any, Optional
from .metadata_schema import CONTENT_TYPE_MAPPING, SEVERITY_TO_URGENCY


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    Count the number of tokens in a text string.
    
    Args:
        text: The text to count tokens for
        model: The model to use for tokenization (default: gpt-3.5-turbo)
        
    Returns:
        Number of tokens in the text
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    
    return len(encoding.encode(text))


def map_severity_to_urgency(severity: str) -> str:
    """
    Map severity level to urgency level.
    
    Args:
        severity: Severity level from source data
        
    Returns:
        Urgency level (informational, monitor, consult_doctor, emergency)
    """
    return SEVERITY_TO_URGENCY.get(severity.lower(), "informational")


def generate_chunk_id(entry_id: str, chunk_index: int) -> str:
    """
    Generate a unique chunk ID.
    
    Args:
        entry_id: Original entry ID from JSON
        chunk_index: Index of the chunk (0-based)
        
    Returns:
        Unique chunk ID in format: {entry_id}_chunk_{index}
    """
    return f"{entry_id}_chunk_{chunk_index}"


def extract_content_type(file_path: str, entry: Dict[str, Any]) -> str:
    """
    Determine content type based on file path and entry characteristics.
    
    Args:
        file_path: Path to the source JSON file
        entry: The entry dictionary
        
    Returns:
        Content type string
    """
    # Extract subcategory from file path
    path = Path(file_path)
    file_stem = path.stem  # e.g., "faqs", "physical_symptoms"
    
    # Check for direct matches
    for key, content_type in CONTENT_TYPE_MAPPING.items():
        if key in file_stem.lower():
            return content_type
    
    # Check category/subcategory from entry
    category = entry.get("category", "").lower()
    subcategory = entry.get("subcategory", "").lower()
    
    if "faq" in subcategory or "faq" in category:
        return "faq"
    elif "symptom" in category or "symptom" in subcategory:
        return "symptom_guide"
    elif "treatment" in category or "treatment" in subcategory:
        return "treatment_info"
    elif "lifestyle" in category or "lifestyle" in subcategory:
        return "lifestyle_tip"
    elif "warning" in subcategory or "red_flag" in subcategory:
        return "warning_sign"
    
    # Default to educational
    return "educational"


def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Safely load a JSON file with error handling.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON data or None if error occurs
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def save_json_file(data: Any, file_path: str, indent: int = 2) -> bool:
    """
    Safely save data to a JSON file.
    
    Args:
        data: Data to save
        file_path: Path to save the file
        indent: JSON indentation level
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create parent directory if it doesn't exist
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving to {file_path}: {e}")
        return False


def determine_audience(entry: Dict[str, Any]) -> str:
    """
    Determine the target audience for an entry.
    
    Args:
        entry: The entry dictionary
        
    Returns:
        Audience type (general, adolescents, adults)
    """
    # Check tags and content for audience indicators
    tags = entry.get("tags", [])
    content = entry.get("content", "").lower()
    title = entry.get("title", "").lower()
    
    # Check for adolescent-specific content
    adolescent_keywords = ["teen", "adolescent", "young", "puberty"]
    if any(keyword in " ".join(tags).lower() for keyword in adolescent_keywords):
        return "adolescents"
    if any(keyword in content or keyword in title for keyword in adolescent_keywords):
        return "adolescents"
    
    # Default to general audience
    return "general"


def should_add_disclaimer(entry: Dict[str, Any], urgency_level: str) -> bool:
    """
    Determine if a medical disclaimer should be added to the chunk.
    
    Args:
        entry: The entry dictionary
        urgency_level: The urgency level of the content
        
    Returns:
        True if disclaimer should be added
    """
    # Add disclaimer for medical advice
    if urgency_level in ["consult_doctor", "emergency"]:
        return True
    
    # Check for treatment/medication keywords
    content = entry.get("content", "").lower()
    treatment_keywords = [
        "medication", "treatment", "therapy", "prescription", 
        "drug", "hormone", "surgery", "procedure"
    ]
    
    if any(keyword in content for keyword in treatment_keywords):
        return True
    
    # Check management field if present
    management = entry.get("management", [])
    if management and any("medication" in str(item).lower() or "therapy" in str(item).lower() 
                          for item in management):
        return True
    
    return False


def create_context_header(entry: Dict[str, Any], chunk_index: int, total_chunks: int) -> str:
    """
    Create a context header for multi-chunk entries.
    
    Args:
        entry: The entry dictionary
        chunk_index: Current chunk index
        total_chunks: Total number of chunks
        
    Returns:
        Context header string or empty string if not needed
    """
    if total_chunks <= 1:
        return ""
    
    title = entry.get("title", "this topic")
    
    if chunk_index == 0:
        return ""  # First chunk doesn't need context
    else:
        return f"Context: This information continues from '{title}'. "
