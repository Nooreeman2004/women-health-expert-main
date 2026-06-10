"""
Vector Store Module

Handles interactions with Pinecone vector database for storing and retrieving embeddings.
"""

from .pinecone_client import PineconeVectorStore

__all__ = ['PineconeVectorStore']
