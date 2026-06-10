"""
Metadata Schema for Chunked Women's Health Data

Defines the structure and validation for metadata attached to each chunk.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Metadata schema for each chunk stored in Pinecone."""
    
    # Original metadata from JSON
    id: str = Field(..., description="Original entry ID from source JSON")
    title: str = Field(..., description="Title of the entry")
    category: str = Field(..., description="Main category (e.g., symptoms, treatments, general)")
    subcategory: str = Field(..., description="Subcategory (e.g., physical, hormonal)")
    tags: List[str] = Field(default_factory=list, description="Tags for the entry")
    related_topics: List[str] = Field(default_factory=list, description="Related topic identifiers")
    severity: str = Field(default="n/a", description="Severity level from source data")
    
    # Computed metadata
    content_type: Literal[
        "educational", 
        "faq", 
        "symptom_guide", 
        "treatment_info", 
        "lifestyle_tip",
        "warning_sign",
        "medical_test",
        "decision_tool"
    ] = Field(..., description="Type of content")
    
    urgency_level: Literal[
        "informational",
        "monitor", 
        "consult_doctor",
        "emergency"
    ] = Field(..., description="Urgency level for medical action")
    
    chunk_index: int = Field(..., description="Position of chunk in source entry (0-indexed)")
    total_chunks: int = Field(..., description="Total number of chunks from source entry")
    source_file: str = Field(..., description="Relative path to source JSON file")
    last_updated: str = Field(..., description="Last update date from source")
    audience: Literal["general", "adolescents", "adults"] = Field(
        default="general", 
        description="Target audience"
    )
    requires_disclaimer: bool = Field(
        default=False, 
        description="Whether medical disclaimer is required"
    )
    chunk_id: str = Field(..., description="Unique identifier for this chunk")
    
    # Optional fields
    embedding_model: Optional[str] = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model used"
    )


class ProcessingStats(BaseModel):
    """Statistics from the chunking process."""
    
    total_files_processed: int = 0
    total_entries_processed: int = 0
    total_chunks_created: int = 0
    average_chunks_per_entry: float = 0.0
    average_chunk_size_tokens: float = 0.0
    files_with_errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# Content type mapping based on file paths and entry characteristics
CONTENT_TYPE_MAPPING = {
    "faqs": "faq",
    "overview": "educational",
    "myths": "educational",
    "research_evidence": "educational",
    "symptoms": "symptom_guide",
    "treatments": "treatment_info",
    "lifestyle": "lifestyle_tip",
    "nutrition": "lifestyle_tip",
    "exercise": "lifestyle_tip",
    "stress_management": "lifestyle_tip",
    "sleep_management": "lifestyle_tip",
    "workplace_strategies": "lifestyle_tip",
    "warning_signs": "warning_sign",
    "red_flags": "warning_sign",
    "emergency_protocols": "warning_sign",
    "medical_tests": "medical_test",
    "stages": "educational",
    "comparison_decision_tools": "decision_tool",
    "alternative_therapies": "treatment_info",
    "hormonal_treatments": "treatment_info",
    "non_hormonal_treatments": "treatment_info",
}

# Severity to urgency mapping
SEVERITY_TO_URGENCY = {
    "n/a": "informational",
    "low": "informational",
    "medium": "monitor",
    "high": "consult_doctor",
    "critical": "emergency",
}
