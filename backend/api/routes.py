"""
FastAPI Routes

Main API endpoints for women's health chatbot.
"""

import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from .models import ChatRequest, ChatResponse, HealthResponse, ErrorResponse
from .session_manager import SessionManager
from generation import Generator
from retrieval import ProductionRetriever

# Load environment
load_dotenv('env')

# Initialize router
router = APIRouter()

# Initialize retriever (singleton)
retriever = ProductionRetriever(
    pinecone_api_key=os.getenv('PINECONE_API_KEY'),
    pinecone_index_name=os.getenv('PINECONE_INDEX_NAME'),
    openai_api_key=os.getenv('OPENAI_API_KEY')
)

# Initialize session manager
session_manager = SessionManager(session_timeout_minutes=30)


def cleanup_sessions():
    """Background task to cleanup expired sessions."""
    session_manager.cleanup_expired_sessions()


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks
):
    """
    Chat endpoint for women's health assistant.
    
    - **message**: User's message (required)
    - **session_id**: Session ID for conversation continuity (optional)
    - **use_rag**: Whether to use RAG retrieval (default: true)
    
    Returns assistant's response with metadata.
    """
    try:
        # Get or create session
        if request.session_id:
            print(f"🔍 [DEBUG] Received session_id: {request.session_id}")
            generator = session_manager.get_session(request.session_id)
            if not generator:
                # Session expired or invalid in RAM, try restoring from Firestore
                print(f"⚠️ [DEBUG] Session {request.session_id} not found in RAM, checking Firestore")
                session_data = session_manager.get_session_data(request.session_id)
                
                # Create and register a new generator anyway
                generator = Generator(
                    openai_api_key=os.getenv('OPENAI_API_KEY'),
                    retriever=retriever
                )
                
                if session_data:
                    print(f"✅ [DEBUG] Restoring Session {request.session_id} from Firestore data")
                    generator.conversation_manager.restore_state(
                        messages_data=session_data.get('messages', []),
                        summary=session_data.get('summary'),
                        user_context=session_data.get('user_context', {})
                    )
                
                # Re-register this restored session in SessionManager RAM
                session_manager.sessions[request.session_id] = {
                    'generator': generator,
                    'created_at': datetime.now(),
                    'last_activity': datetime.now()
                }
                session_id = request.session_id
            else:
                session_id = request.session_id
                msg_count = generator.conversation_manager.get_user_message_count()
                print(f"✅ [DEBUG] Retrieved existing session: {session_id}, conversation has {msg_count} user messages")
        else:
            # Create new session
            print(f"🆕 [DEBUG] No session_id provided, creating new session")
            generator = Generator(
                openai_api_key=os.getenv('OPENAI_API_KEY'),
                retriever=retriever
            )
            session_id = session_manager.create_session(generator)
            print(f"✅ [DEBUG] Created new session: {session_id}")
        
        # Log conversation state before generating response
        print(f"📊 [DEBUG] Before generation - Total messages in conversation: {len(generator.conversation_manager.messages)}")
        print(f"📊 [DEBUG] User message: '{request.message}'")
        
        # Generate response
        response, metadata = await generator.generate_response(
            user_message=request.message,
            use_rag=request.use_rag
        )
        
        # Log conversation state after generating response
        print(f"📊 [DEBUG] After generation - Total messages in conversation: {len(generator.conversation_manager.messages)}")
        
        # Schedule cleanup task
        background_tasks.add_task(cleanup_sessions)
        
        return ChatResponse(
            response=response,
            session_id=session_id,
            metadata=metadata
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )


@router.delete("/chat/{session_id}", tags=["Chat"])
async def delete_session(session_id: str):
    """
    Delete a chat session.
    
    - **session_id**: Session ID to delete
    """
    session_manager.delete_session(session_id)
    return {"message": "Session deleted successfully"}


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns service status and version.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )


@router.get("/stats", tags=["Health"])
async def get_stats():
    """
    Get service statistics.
    
    Returns active session count and other metrics.
    """
    return {
        "active_sessions": session_manager.get_session_count(),
        "status": "operational"
    }
