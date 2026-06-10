"""
FastAPI Application

Main FastAPI application with CORS and middleware.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

from .routes import router

# Load environment
load_dotenv('env')

# Create FastAPI app
app = FastAPI(
    title="Women's Health Expert API",
    description="AI-powered women's health educational assistant with RAG",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
origins = [
    "http://localhost:3000",  # React default
    "http://localhost:5173",  # Vite default
    "http://localhost:8080",  # Vue default
    os.getenv("FRONTEND_URL", "*")  # Production frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Women's Health Expert API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api")
async def api_root():
    """API root endpoint."""
    return {
        "message": "Women's Health Expert API v1",
        "endpoints": {
            "chat": "/api/v1/chat",
            "health": "/api/v1/health",
            "stats": "/api/v1/stats"
        }
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "detail": str(exc)}
    )


@app.exception_handler(500)
async def server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )
