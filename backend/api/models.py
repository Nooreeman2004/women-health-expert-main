"""
API Models

Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    use_rag: bool = Field(True, description="Whether to use RAG retrieval")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What are the symptoms of menopause?",
                "session_id": "user-123-session-456",
                "use_rag": True
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="Assistant's response")
    session_id: str = Field(..., description="Session ID")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Menopause symptoms include hot flashes, night sweats...",
                "session_id": "user-123-session-456",
                "metadata": {
                    "red_flags_detected": [],
                    "rag_used": True,
                    "enforcer_used": True
                },
                "timestamp": "2025-12-25T23:00:00"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.now, description="Current timestamp")


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
